"""
telemetry_streamer.py
---------------------
Real-time telemetry event bus and log streaming infrastructure for PHD Prof Web Cockpit.
Captures pipeline events, console output, quota telemetry, and broadcasts them
to connected SSE / WebSocket subscribers with zero blocking of ETL inference threads.
"""
import io
import sys
import json
import asyncio
import datetime
import threading
from collections import deque
from contextlib import contextmanager
from typing import AsyncGenerator, Dict, Any, List, Optional

class StdoutInterceptor:
    """
    Thread-safe stream interceptor that duplicates output between the native
    terminal stream and the TelemetryStreamer event queue.
    """
    def __init__(self, original_stream, streamer: "TelemetryStreamer", source: str = "app"):
        self.original_stream = original_stream
        self.streamer = streamer
        self.source = source
        self._buffer = io.StringIO()
        self._lock = threading.Lock()

    def write(self, s: str):
        try:
            self.original_stream.write(s)
            self.original_stream.flush()
        except Exception:
            pass

        with self._lock:
            self._buffer.write(s)
            if "\n" in s:
                content = self._buffer.getvalue()
                lines = content.split("\n")
                for line in lines[:-1]:
                    clean = line.strip()
                    if clean:
                        self.streamer.log(clean, source=self.source)
                self._buffer = io.StringIO()
                self._buffer.write(lines[-1])

    def flush(self):
        try:
            self.original_stream.flush()
        except Exception:
            pass

        with self._lock:
            remaining = self._buffer.getvalue().strip()
            if remaining:
                self.streamer.log(remaining, source=self.source)
                self._buffer = io.StringIO()

class TelemetryStreamer:
    """
    Asynchronous event broadcaster maintaining an in-memory ring buffer
    for reconnecting clients and distributing real-time ETL progress.
    """
    def __init__(self, buffer_size: int = 300):
        self._buffer_size = buffer_size
        self._history: deque = deque(maxlen=buffer_size)
        self._subscribers: List[asyncio.Queue] = []
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def get_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._history)

    def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        payload = {
            "type": event_type,
            "data": data,
            "timestamp": timestamp,
        }

        with self._lock:
            self._history.append(payload)
            subs = list(self._subscribers)

        for q in subs:
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(q.put_nowait, payload)
            else:
                try:
                    q.put_nowait(payload)
                except Exception:
                    pass

    def log(self, message: str, level: str = "info", source: str = "sys") -> None:
        """Helper to broadcast formatted console/system log lines."""
        # Detect log level and source tag if embedded in string
        clean_msg = message
        detected_source = source
        detected_level = level

        if clean_msg.startswith("[") and "]" in clean_msg:
            tag_end = clean_msg.find("]")
            tag = clean_msg[1:tag_end].strip().lower()
            if tag in ("local", "llm", "notion", "rollback", "stop", "errore", "sys"):
                detected_source = tag
                if tag in ("stop", "errore"):
                    detected_level = "error"
                clean_msg = clean_msg[tag_end + 1:].strip()

        self.broadcast("log", {
            "message": clean_msg,
            "source": detected_source,
            "level": detected_level,
        })

    @contextmanager
    def capture_stdout(self, source: str = "etl"):
        """Context manager to duplicate stdout to telemetry log subscribers."""
        old_stdout = sys.stdout
        interceptor = StdoutInterceptor(old_stdout, self, source=source)
        sys.stdout = interceptor
        try:
            yield
        finally:
            interceptor.flush()
            sys.stdout = old_stdout

    async def subscribe(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator yielding events for a specific subscriber queue."""
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._subscribers.append(q)

        try:
            while True:
                item = await q.get()
                yield item
        finally:
            with self._lock:
                if q in self._subscribers:
                    self._subscribers.remove(q)

    async def sse_event_stream(self) -> AsyncGenerator[str, None]:
        """Yields Server-Sent Events formatted strings for HTTP streaming."""
        async for payload in self.subscribe():
            yield f"event: {payload['type']}\ndata: {json.dumps(payload)}\n\n"
