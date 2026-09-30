"""
web_adapter.py
--------------
Inbound Web Adapter for PHD Prof.
Implements the local HTTP/SSE/WebSocket server via FastAPI, providing REST endpoints
for course profiles, file queues, live batch execution, and telemetric observability.
Adheres strictly to Hexagonal Architecture, keeping Core Domain and Use Cases decoupled.
"""
import os
import sys
import time
import asyncio
import pathlib
import threading
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.core.domain.models import Document, DocumentType, NotionTarget, CourseProfile, SyncStatus
from src.core.domain.prompt_templates import get_prompt_template
from src.core.usecases.process_document import ProcessDocumentUseCase, compute_file_hash
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.course_profile_repository_port import ICourseProfileRepository
from src.ports.outbound.state_repository_port import IStateRepository
from src.adapters.inbound.web.telemetry_streamer import TelemetryStreamer

SUPPORTED_EXTENSIONS = {".pdf", ".pptx"}
SLEEP_BETWEEN_FILES = 5

def scan_documents(folder: pathlib.Path) -> List[pathlib.Path]:
    """Scans for supported academic documents (.pdf, .pptx) sorted deterministically."""
    if not folder.is_dir():
        return []
    return sorted([
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ])

def format_size(bytes_num: int) -> str:
    """Format byte count into human-readable industrial units."""
    if bytes_num < 1024:
        return f"{bytes_num} B"
    elif bytes_num < 1024 * 1024:
        return f"{bytes_num / 1024:.1f} KB"
    return f"{bytes_num / (1024 * 1024):.1f} MB"

# Pydantic Request Models
class NotionTargetSchema(BaseModel):
    database_id: str
    course_name: str
    database_title: str

class CourseProfileSchema(BaseModel):
    subject: str
    professor_type: str = ""
    doc_type: str = "slides"
    folder_path: str
    target: NotionTargetSchema

class BatchStartRequest(BaseModel):
    profile_key: str
    file_names: Optional[List[str]] = None

class WebAdapter:
    """
    Inbound Web Adapter.
    Exposes a local API and serves the single-page cockpit frontend.
    """
    def __init__(
        self,
        notion_client: INotionClient,
        llm_client: ILlmClient,
        usecase: ProcessDocumentUseCase,
        root_page_id: str,
        course_profile_repo: Optional[ICourseProfileRepository] = None,
        state_repo: Optional[IStateRepository] = None,
        host: str = "127.0.0.1",
        port: int = 8000,
    ):
        self.notion_client = notion_client
        self.llm_client = llm_client
        self.usecase = usecase
        self.root_page_id = root_page_id
        self.course_profile_repo = course_profile_repo
        self.state_repo = state_repo
        self.host = host
        self.port = port

        self.streamer = TelemetryStreamer()
        self.is_batch_running = False
        self.stop_requested = False
        self.active_profile_key: Optional[str] = None
        self._batch_lock = threading.Lock()
        self.static_dir = pathlib.Path(__file__).parent / "static"
        
        # Watchdog & automatic shutdown state
        self.last_heartbeat = time.time()
        self.enable_watchdog = False
        self.watchdog_timeout = 60.0  # 60s silence timeout (handles background tab throttling)
        self.watchdog_grace_period = 25.0
        self.unload_requested_at: Optional[float] = None
        self.server = None
        self.server_stopping = False

        self.app = self.create_app()

    def create_app(self) -> FastAPI:
        app = FastAPI(
            title="PHD Prof Cockpit",
            description="Local Academic Document ETL Cockpit",
            version="2.0.0",
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.on_event("startup")
        async def on_startup():
            self.streamer.set_loop(asyncio.get_running_loop())
            self.streamer.log("PHD Prof local server initialized on http://" + self.host + ":" + str(self.port))

        @app.get("/")
        async def serve_index():
            index_path = self.static_dir / "index.html"
            if not index_path.exists():
                return JSONResponse({"status": "error", "message": "static/index.html missing"}, status_code=404)
            return FileResponse(index_path)

        @app.get("/api/profiles")
        async def get_profiles():
            profiles = self.course_profile_repo.list_profiles() if self.course_profile_repo else []
            result = []
            for p in profiles:
                d = p.to_dict()
                d["key"] = p.key
                d["files_count"] = len(scan_documents(p.folder_path)) if p.folder_path.is_dir() else 0
                d["folder_exists"] = p.folder_path.is_dir()
                result.append(d)
            return result

        @app.post("/api/profiles")
        async def save_profile(data: CourseProfileSchema):
            if not self.course_profile_repo:
                raise HTTPException(status_code=500, detail="Profile repository not configured")

            folder = pathlib.Path(data.folder_path).expanduser().resolve()
            if not folder.is_dir():
                raise HTTPException(status_code=400, detail=f"Folder does not exist: {data.folder_path}")

            try:
                doc_type = DocumentType(data.doc_type.lower())
            except ValueError:
                doc_type = DocumentType.SLIDES

            prof_type = data.professor_type.strip() or f"PhD Professor in {data.subject.strip()}"

            profile = CourseProfile(
                subject=data.subject.strip(),
                professor_type=prof_type,
                doc_type=doc_type,
                folder_path=folder,
                target=NotionTarget(
                    database_id=data.target.database_id,
                    course_name=data.target.course_name,
                    database_title=data.target.database_title,
                ),
            )
            self.course_profile_repo.save_profile(profile)
            self.streamer.log(f"Profile saved: {profile.subject} [{profile.doc_type.value.upper()}]")
            return {"status": "ok", "key": profile.key}

        @app.get("/api/profiles/{key}/files")
        async def get_profile_files(key: str):
            profile = self._find_profile(key)
            if not profile:
                raise HTTPException(status_code=404, detail=f"Profile '{key}' not found")

            if not profile.folder_path.is_dir():
                return {"files": [], "error": f"Cartella non trovata: {profile.folder_path}"}

            raw_files = scan_documents(profile.folder_path)
            items = []
            for path in raw_files:
                try:
                    stat = path.stat()
                    file_hash = compute_file_hash(path)
                    entry = self.state_repo.get_entry(file_hash) if self.state_repo else None

                    status_str = entry.status.value if entry else "IDLE"
                    page_id = entry.page_id if entry else None
                    last_updated = entry.last_updated if entry else None

                    items.append({
                        "name": path.name,
                        "path": str(path),
                        "extension": path.suffix.lower(),
                        "size_bytes": stat.st_size,
                        "size_formatted": format_size(stat.st_size),
                        "file_hash": file_hash,
                        "status": status_str,
                        "page_id": page_id,
                        "last_updated": last_updated,
                    })
                except Exception as exc:
                    items.append({
                        "name": path.name,
                        "path": str(path),
                        "extension": path.suffix.lower(),
                        "size_bytes": 0,
                        "size_formatted": "0 B",
                        "file_hash": "",
                        "status": "ERROR",
                        "error": str(exc),
                    })
            return {"files": items, "total": len(items)}

        @app.get("/api/quota")
        async def get_quota():
            remaining = self.llm_client.get_remaining_calls()
            model_name = getattr(self.llm_client, "model", "gemini-2.5-flash")
            return {
                "remaining": remaining,
                "model": model_name,
                "is_exhausted": remaining <= 0,
            }

        @app.get("/api/batch/status")
        async def get_batch_status():
            return {
                "is_running": self.is_batch_running,
                "active_profile": self.active_profile_key,
                "stop_requested": self.stop_requested,
            }

        @app.post("/api/batch/start")
        async def start_batch(req: BatchStartRequest, background_tasks: BackgroundTasks):
            with self._batch_lock:
                if self.is_batch_running:
                    raise HTTPException(status_code=409, detail="Un batch è già in corso")

                profile = self._find_profile(req.profile_key)
                if not profile:
                    raise HTTPException(status_code=404, detail=f"Profilo '{req.profile_key}' non trovato")

                self.is_batch_running = True
                self.stop_requested = False
                self.active_profile_key = profile.key

            background_tasks.add_task(self._run_batch_worker, profile, req.file_names)
            return {"status": "started", "profile": profile.subject}

        @app.post("/api/batch/stop")
        async def stop_batch():
            if not self.is_batch_running:
                return {"status": "not_running"}
            self.stop_requested = True
            self.streamer.log("Richiesta di interruzione batch ricevuta. Arresto al termine del file corrente...", level="warn")
            return {"status": "stopping"}

        @app.get("/api/notion/courses")
        async def get_notion_courses():
            try:
                courses = self.notion_client.fetch_courses(self.root_page_id)
                return courses
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc))

        @app.get("/api/notion/targets/{course_id}")
        async def get_notion_targets(course_id: str):
            try:
                targets = self.notion_client.fetch_targets_in_course(course_id)
                resolved = []
                for t in targets:
                    db_id = self.notion_client.resolve_database_id(t)
                    resolved.append({
                        "id": t.get("id"),
                        "title": t.get("title", "Notes"),
                        "database_id": db_id,
                    })
                return resolved
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc))

        @app.get("/api/events")
        async def sse_events():
            return StreamingResponse(
                self.streamer.sse_event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        @app.get("/api/history")
        async def get_history():
            return self.streamer.get_history()

        @app.post("/api/heartbeat")
        async def heartbeat():
            self.last_heartbeat = time.time()
            self.unload_requested_at = None  # Reset any pending unload (user is active)
            return {"status": "alive"}

        @app.post("/api/unload")
        async def browser_unload():
            # Explicit tab/window close beacon received
            self.unload_requested_at = time.time()
            return {"status": "acknowledged"}

        # Mount static directory for JS, CSS, SVG
        if self.static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

        return app

    def _find_profile(self, key: str) -> Optional[CourseProfile]:
        if not self.course_profile_repo:
            return None
        profiles = self.course_profile_repo.list_profiles()
        for p in profiles:
            if p.key == key:
                return p
        return None

    def _run_batch_worker(self, profile: CourseProfile, selected_file_names: Optional[List[str]] = None) -> None:
        """
        Background worker thread executing the batch pipeline.
        Emits real-time telemetric events and respects graceful stop requests.
        """
        try:
            folder = profile.folder_path
            all_files = scan_documents(folder)
            if selected_file_names:
                target_names = set(selected_file_names)
                doc_files = [f for f in all_files if f.name in target_names]
            else:
                doc_files = all_files

            total = len(doc_files)
            success = 0

            self.streamer.broadcast("batch_state", {
                "running": True,
                "profile": profile.subject,
                "total": total,
                "success": 0,
            })
            self.streamer.log(f"Inizio elaborazione batch: {profile.subject} ({total} file)")

            prompt = get_prompt_template(profile.doc_type.value, profile.subject, profile.professor_type)

            for index, doc_path in enumerate(doc_files, start=1):
                if self.stop_requested:
                    self.streamer.log("Batch interrotto dall'utente.", level="warn")
                    break

                self.streamer.broadcast("file_progress", {
                    "file_name": doc_path.name,
                    "index": index,
                    "total": total,
                    "status": "SYNCING",
                })
                self.streamer.log(f"[{index}/{total}] Elaborazione {doc_path.name}...")

                try:
                    file_hash = compute_file_hash(doc_path)
                    doc = Document(path=doc_path, file_hash=file_hash, doc_type=profile.doc_type)

                    with self.streamer.capture_stdout(source="etl"):
                        result = self.usecase.execute(doc, profile.target, prompt)

                    if result.success:
                        success += 1
                        new_status = "SYNCED"
                    else:
                        new_status = "FAILED"

                    self.streamer.broadcast("file_progress", {
                        "file_name": doc_path.name,
                        "file_hash": file_hash,
                        "index": index,
                        "total": total,
                        "status": new_status,
                        "page_id": result.page_id,
                        "skipped": result.skipped,
                    })

                    # Broadcast quota update after each file
                    remaining = self.llm_client.get_remaining_calls()
                    self.streamer.broadcast("quota_update", {"remaining": remaining})

                except Exception as exc:
                    self.streamer.log(f"Errore su {doc_path.name}: {exc}", level="error")
                    self.streamer.broadcast("file_progress", {
                        "file_name": doc_path.name,
                        "index": index,
                        "total": total,
                        "status": "FAILED",
                        "error": str(exc),
                    })

                # Pacing pause with quick interruption responsiveness
                if index < total and not self.stop_requested:
                    self.streamer.log(f"Pausa di sicurezza ({SLEEP_BETWEEN_FILES}s)...")
                    for _ in range(SLEEP_BETWEEN_FILES * 2):
                        if self.stop_requested:
                            break
                        time.sleep(0.5)

            self.streamer.log(f"Batch completato: {success}/{total} sincronizzati con successo.")
            self.streamer.broadcast("batch_state", {
                "running": False,
                "profile": profile.subject,
                "total": total,
                "success": success,
                "stopped": self.stop_requested,
            })

        finally:
            with self._batch_lock:
                self.is_batch_running = False
                self.stop_requested = False
                self.active_profile_key = None

    def stop_server(self) -> None:
        """Triggers graceful server shutdown and process termination."""
        if self.server_stopping:
            return
        self.server_stopping = True
        self.streamer.log("Nessun client browser attivo rilevato. Arresto automatico del processo locale...")
        if self.server:
            self.server.should_exit = True
        threading.Timer(2.0, lambda: os._exit(0)).start()

    def _watchdog_loop(self) -> None:
        """
        Monitors heartbeat pings from the browser.
        If the browser tab is closed (unload beacon received + 6s grace without reconnect),
        or if no heartbeat arrives for watchdog_timeout seconds (and no batch is executing),
        automatically shuts down the background server.
        """
        time.sleep(self.watchdog_grace_period)
        while not self.server_stopping:
            time.sleep(2.0)
            now = time.time()
            if self.is_batch_running:
                # Never kill while active batch execution is taking place!
                self.last_heartbeat = now
                self.unload_requested_at = None
                continue

            # Case A: explicit unload beacon was sent, and 6s have elapsed without a new heartbeat (tab truly closed)
            if self.unload_requested_at is not None and (now - self.unload_requested_at) > 6.0:
                self.stop_server()
                break

            # Case B: silence for > watchdog_timeout (e.g. browser crash or hard process kill)
            if (now - self.last_heartbeat) > self.watchdog_timeout:
                self.stop_server()
                break

    def start(self, enable_watchdog: bool = True) -> None:
        """Starts Uvicorn server synchronously with auto-shutdown watchdog."""
        import uvicorn
        if enable_watchdog:
            self.enable_watchdog = True
            watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            watchdog_thread.start()

        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server.run()
