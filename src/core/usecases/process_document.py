import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.domain.models import (
    Document,
    DocumentType,
    SyncStatus,
    SyncEntry,
    ProcessingResult,
    NotionTarget,
)
from src.ports.outbound.document_reader_port import IDocumentReader
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.state_repository_port import IStateRepository
from src.ports.outbound.staging_storage_port import IStagingStorage
from src.adapters.outbound.notion_block_builder import build_notion_blocks

def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of a file on disk."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

class ProcessDocumentUseCase:
    """
    Crash-Only ETL Pipeline Use Case.
    Orchestrates:
      1. Cryptographic state check (idempotency)
      2. Self-healing rollback of orphaned pages
      3. Decoupled extraction & LLM inference (staging disk cache)
      4. Safe loading into Notion with batching and state finalization
    """
    def __init__(
        self,
        readers: Dict[DocumentType, IDocumentReader],
        llm_client: ILlmClient,
        notion_client: INotionClient,
        state_repo: IStateRepository,
        staging_storage: IStagingStorage,
    ):
        self.readers = readers
        self.llm_client = llm_client
        self.notion_client = notion_client
        self.state_repo = state_repo
        self.staging_storage = staging_storage

    def execute(self, document: Document, target: NotionTarget, prompt: str) -> ProcessingResult:
        file_hash = document.file_hash
        entry = self.state_repo.get_entry(file_hash)

        # 1. Idempotency Check
        if entry and entry.status == SyncStatus.SYNCED:
            print("    [Local] File già sincronizzato (Hash invariato) — skip.\n")
            return ProcessingResult(document=document, success=True, page_id=entry.page_id, skipped=True)

        # 2. Self-Healing Rollback
        if entry and entry.status == SyncStatus.SYNCING:
            if entry.page_id:
                print(f"    [Rollback] Rilevato caricamento incompleto. Archiviazione pagina orfana ({entry.page_id})...")
                self.notion_client.archive_page(entry.page_id)
            self.state_repo.remove_entry(file_hash)

        # 3. Extraction & Inference (Staging Cache)
        if self.staging_storage.exists(file_hash):
            print("    [Local] Markdown già presente in staging. Salto inference LLM.")
            markdown_text = self.staging_storage.read(file_hash) or ""
        else:
            reader = self.readers.get(document.doc_type) or self.readers[DocumentType.SLIDES]
            payload = reader.read(document)
            try:
                print("    [LLM] Generazione note...")
                markdown_text = self.llm_client.generate_notes(prompt, payload)
                print(f"    [LLM] Ricevuti {len(markdown_text)} caratteri. Salvataggio in staging...")
                self.staging_storage.save(file_hash, markdown_text)
            finally:
                reader.cleanup(payload)

        # 4. Notion Loading
        print("    [Notion] Creazione pagina...")
        page_id = self.notion_client.create_page(target.database_id, document.stem)

        # Mark as SYNCING
        self.state_repo.set_entry(SyncEntry(file_hash=file_hash, status=SyncStatus.SYNCING, page_id=page_id))

        # Build and append blocks
        blocks = build_notion_blocks(markdown_text)
        self.notion_client.append_blocks(page_id, blocks)

        # Mark as SYNCED
        self.state_repo.set_entry(SyncEntry(file_hash=file_hash, status=SyncStatus.SYNCED, page_id=page_id))
        print(f"    [Notion] OK — {len(blocks)} blocchi archiviati.\n")

        return ProcessingResult(document=document, success=True, page_id=page_id, skipped=False)
