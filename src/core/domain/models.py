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

class GenerationMode(str, Enum):
    """
    Specifies which artifacts to generate and upload:
    - BOTH: Standard full pipeline (chapter notes + conceptual mindmaps & study artifacts).
    - NOTES_ONLY: Only academic textbook chapter notes without graphs/study schemas.
    - GRAPHS_ONLY: Only conceptual graphs and study artifacts (OPML / Mermaid / active recall).
    """
    BOTH = "both"
    NOTES_ONLY = "notes_only"
    GRAPHS_ONLY = "graphs_only"

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
        # ARCHITETTURA: Parsing difensivo per isolamento guasti sul file di configurazione profili.
        # Garantisce che dati parzialmente mancanti o formattati male su un altro PC
        # non causino eccezioni non gestite nel dominio.
        if not isinstance(data, dict):
            raise ValueError("Expected dictionary for CourseProfile")
        target_raw = data.get("target")
        target_data = target_raw if isinstance(target_raw, dict) else {}
        subject_str = str(data.get("subject", "") or "").strip()
        target = NotionTarget(
            database_id=str(target_data.get("database_id", "") or "").strip(),
            course_name=str(target_data.get("course_name", subject_str) or subject_str).strip(),
            database_title=str(target_data.get("database_title", "Notes") or "Notes").strip(),
        )
        doc_type_val = str(data.get("doc_type", "slides") or "slides").lower().strip()
        try:
            doc_type = DocumentType(doc_type_val)
        except ValueError:
            doc_type = DocumentType.SLIDES

        prof_type = str(data.get("professor_type", "") or "").strip()
        if not prof_type:
            prof_type = f"PhD Professor in {subject_str}" if subject_str else "PhD Professor"

        raw_folder = str(data.get("folder_path", "") or "").strip()
        if raw_folder:
            if raw_folder.startswith("Users/") or raw_folder.startswith("home/"):
                raw_folder = f"/{raw_folder}"
            folder_path = Path(raw_folder).expanduser()
        else:
            folder_path = Path(".")

        return cls(
            subject=subject_str,
            professor_type=prof_type,
            doc_type=doc_type,
            folder_path=folder_path,
            target=target,
        )

# ARCHITETTURA: StudyArtifact incapsula gli artefatti di studio avanzati (Mermaid, OPML, Active Recall)
# estrapolati a valle o in append. Disaccoppia la rappresentazione di dominio dalle specificità dei tool (Notion, EdrawMind).
@dataclass
class StudyArtifact:
    document_hash: str
    title: str
    mindmap_mermaid: Optional[str] = None
    flowchart_mermaid: Optional[str] = None
    opml_content: Optional[str] = None
    active_recall_markdown: Optional[str] = None
    boundary_matrix_markdown: Optional[str] = None

