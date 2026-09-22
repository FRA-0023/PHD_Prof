from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any

class DocumentType(str, Enum):
    """
    Distinguishes the nature of the academic PDF.
    - SLIDES: Lecture slides, bullet points, visual charts -> expanded pedagogically.
    - PAPER_OR_BOOK: Dense academic papers, books, notes -> distilled into structured study summaries.
    """
    SLIDES = "slides"
    PAPER_OR_BOOK = "paper_or_book"

class SyncStatus(str, Enum):
    IDLE = "IDLE"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"

@dataclass
class Document:
    path: Path
    file_hash: str
    doc_type: DocumentType = DocumentType.SLIDES

    @property
    def stem(self) -> str:
        return self.path.stem

@dataclass
class NotionTarget:
    database_id: str
    course_name: str
    database_title: str

@dataclass
class StudyNotes:
    document_hash: str
    title: str
    markdown_content: str

@dataclass
class SyncEntry:
    file_hash: str
    status: SyncStatus
    page_id: Optional[str] = None
    last_updated: Optional[str] = None

@dataclass
class ProcessingResult:
    document: Document
    success: bool
    page_id: Optional[str] = None
    error_message: Optional[str] = None
    skipped: bool = False
