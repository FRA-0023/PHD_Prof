from abc import ABC, abstractmethod
from src.core.domain.models import StudyArtifact

# ARCHITETTURA: Porta esagonale outbound per la manipolazione ed esportazione
# di schemi concettuali e artefatti di studio. Disaccoppia completamente
# il core di dominio da EdrawMind (OPML), Notion o Mermaid.js.
class IStudySchemaExporter(ABC):
    """
    Outbound port for parsing, converting, and exporting study schemas.
    Decoupled from Notion and local file formats.
    """
    @abstractmethod
    def extract_artifacts(self, markdown_text: str, document_hash: str, title: str) -> StudyArtifact:
        """
        Parses Markdown text to isolate Mermaid code blocks, outline, and study drills.
        Generates the internal StudyArtifact aggregate.
        """
        pass

    @abstractmethod
    def to_opml(self, artifact: StudyArtifact) -> str:
        """
        Converts the extracted mindmap into standard OPML 2.0 XML
        natively importable into EdrawMind, XMind, MindNode, and OmniOutliner.
        """
        pass
