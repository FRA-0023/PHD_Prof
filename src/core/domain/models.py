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

    @property
    def file_path(self) -> Path:
        # ARCHITETTURA: Alias retrocompatibile verso self.path per garantire tolleranza
        # ai contratti di interfaccia outbound che invocano file_path.
        return self.path

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

@dataclass
class CourseProfile:
    """
    Persistent course configuration profile.
    Encapsulates subject metadata, professor role, document type, local folder, and Notion target.
    """
    subject: str
    professor_type: str
    doc_type: DocumentType
    folder_path: Path
    target: NotionTarget

    @property
    def key(self) -> str:
        return self.subject.strip().lower().replace(" ", "_")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "professor_type": self.professor_type,
            "doc_type": self.doc_type.value,
            "folder_path": str(self.folder_path),
            "target": {
                "database_id": self.target.database_id,
                "course_name": self.target.course_name,
                "database_title": self.target.database_title,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CourseProfile":
        target_data = data.get("target", {})
        target = NotionTarget(
            database_id=target_data.get("database_id", ""),
            course_name=target_data.get("course_name", data.get("subject", "")),
            database_title=target_data.get("database_title", "Notes"),
        )
        doc_type_val = data.get("doc_type", "slides")
        try:
            doc_type = DocumentType(doc_type_val)
        except ValueError:
            doc_type = DocumentType.SLIDES

        return cls(
            subject=data.get("subject", ""),
            professor_type=data.get("professor_type", f"PhD Professor in {data.get('subject', '')}"),
            doc_type=doc_type,
            folder_path=Path(data.get("folder_path", "")),
            target=target,
        )

