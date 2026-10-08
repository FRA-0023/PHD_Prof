import re
import html
from typing import List, Tuple, Optional
from xml.sax.saxutils import escape as xml_escape

from src.core.domain.models import StudyArtifact
from src.ports.outbound.study_schema_exporter_port import IStudySchemaExporter

class StudySchemaExporterAdapter(IStudySchemaExporter):
    """
    Adapter per l'estrazione e serializzazione degli schemi di studio.
    # ARCHITETTURA: Converte deterministicamente artefatti generati da LLM (Mermaid)
    # o strutture di testo in formato standard OPML 2.0 per EdrawMind/XMind a costo 0 token.
    """

    def extract_artifacts(self, markdown_text: str, document_hash: str, title: str) -> StudyArtifact:
        """
        Scansiona il markdown alla ricerca di blocchi Mermaid, active recall drills
        e boundary conditions. Produce un'istanza coerente di StudyArtifact.
        """
        # 1. Estrazione Mermaid Mindmap
        mindmap_match = re.search(r"```mermaid\s*\n(mindmap[\s\S]*?)```", markdown_text, re.IGNORECASE)
        mindmap_mermaid = mindmap_match.group(1).strip() if mindmap_match else None

        # 2. Estrazione Mermaid Flowchart / Graph
        flowchart_match = re.search(r"```mermaid\s*\n((?:graph|flowchart)[\s\S]*?)```", markdown_text, re.IGNORECASE)
        flowchart_mermaid = flowchart_match.group(1).strip() if flowchart_match else None

        # 3. Estrazione Active Recall & Examination Drills
        drills_match = re.search(
            r"(##\s*[^\n]*(?:Active Recall|Examination Drills|Drills)[^\n]*\n[\s\S]*?)(?=\n---\n|\n##\s|\Z)",
            markdown_text,
            re.IGNORECASE,
        )
        active_recall = drills_match.group(1).strip() if drills_match else None

        # 4. Estrazione Model Boundary Conditions
        boundary_match = re.search(
            r"(##\s*[^\n]*(?:Boundary Conditions|Failure Modes)[^\n]*\n[\s\S]*?)(?=\n---\n|\n##\s|\Z)",
            markdown_text,
            re.IGNORECASE,
        )
        boundary_matrix = boundary_match.group(1).strip() if boundary_match else None

        # 5. Generazione OPML
        artifact = StudyArtifact(
            document_hash=document_hash,
            title=title,
            mindmap_mermaid=mindmap_mermaid,
            flowchart_mermaid=flowchart_mermaid,
            active_recall_markdown=active_recall,
            boundary_matrix_markdown=boundary_matrix,
        )
        artifact.opml_content = self.to_opml(artifact, fallback_markdown=markdown_text)
        return artifact

    def _clean_mermaid_node_label(self, raw_label: str) -> str:
        """
        Rimuove la sintassi delle forme Mermaid ((circle)), [rect], (round), {{hex}}
        restituendo il testo semantico puro per l'outline OPML.
        """
        clean = raw_label.strip()
        # Rimuove prefisso id se presente (es. id((Label)) o id[Label])
        if re.match(r"^[a-zA-Z0-9_-]+(\(\(|\[|\(|\{\{)", clean):
            clean = re.sub(r"^[a-zA-Z0-9_-]+", "", clean).strip()

        # Rimuove delimitatori di forma
        if clean.startswith("((") and clean.endswith("))"):
            clean = clean[2:-2].strip()
        elif clean.startswith("[") and clean.endswith("]"):
            clean = clean[1:-1].strip()
        elif clean.startswith("(") and clean.endswith(")"):
            clean = clean[1:-1].strip()
        elif clean.startswith("{{") and clean.endswith("}}"):
            clean = clean[2:-2].strip()
        elif clean.startswith("))") and clean.endswith("(("):
            clean = clean[2:-2].strip()

        # Rimuove doppi apici residui
        if clean.startswith('"') and clean.endswith('"'):
            clean = clean[1:-1].strip()

        return clean

    def _parse_mermaid_mindmap_to_tree(self, mermaid_code: str) -> List[Tuple[int, str]]:
        """
        # ALGORITMO: Parsing ad albero gerarchico basato sull'indentazione della sintassi mindmap.
        # Mappa i livelli di spazi relativi per costruire le relazioni padre-figlio.
        """
        lines = mermaid_code.splitlines()
        tree_items: List[Tuple[int, str]] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.lower() == "mindmap":
                continue

            indent = len(line) - len(line.lstrip(" "))
            label = self._clean_mermaid_node_label(stripped)
            if label:
                tree_items.append((indent, label))

        return tree_items

    def _parse_markdown_headings_to_tree(self, markdown_text: str) -> List[Tuple[int, str]]:
        """
        # TRADE-OFF: Fallback difensivo antifragile.
        # Se il documento sintetizzato non include un blocco Mermaid mindmap (es. file storici
        # pre-esistenti in staging), estrae l'albero gerarchico dai tag H1/H2/H3 e dalle liste puntate.
        """
        tree_items: List[Tuple[int, str]] = []
        for line in markdown_text.splitlines():
            s = line.strip()
            if s.startswith("# "):
                tree_items.append((0, s[2:].strip()))
            elif s.startswith("## "):
                tree_items.append((2, s[3:].strip()))
            elif s.startswith("### "):
                tree_items.append((4, s[4:].strip()))
            elif s.startswith("- ") and len(s) > 2:
                # Estrae bullet point di primo livello limitando il testo a 60 caratteri per chiarezza di mappa
                bullet_text = s[2:].strip().split(".")[0][:80]
                tree_items.append((6, bullet_text))
        return tree_items

    def to_opml(self, artifact: StudyArtifact, fallback_markdown: Optional[str] = None) -> str:
        """
        # ARCHITETTURA: Genera un documento XML conforme allo standard OPML 2.0.
        # Supportato nativamente da EdrawMind, XMind, MindNode e OmniOutliner.
        """
        tree_items: List[Tuple[int, str]] = []

        if artifact.mindmap_mermaid:
            tree_items = self._parse_mermaid_mindmap_to_tree(artifact.mindmap_mermaid)

        # Fallback su titoli se la mappa Mermaid è assente o vuota
        if not tree_items and fallback_markdown:
            tree_items = self._parse_markdown_headings_to_tree(fallback_markdown)

        if not tree_items:
            tree_items = [(0, artifact.title or "Study Map")]

        # Costruzione dell'albero gerarchico XML tramite stack di indentazione
        title_escaped = xml_escape(artifact.title or "Lecture Notes", {'"': "&quot;"})
        opml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<opml version="2.0">',
            "  <head>",
            f"    <title>{title_escaped}</title>",
            "  </head>",
            "  <body>",
        ]

        # Stack che memorizza (indent_level, depth_in_xml)
        stack: List[int] = []

        for indent, label in tree_items:
            clean_text = xml_escape(label, {'"': "&quot;"})

            # Chiudi elementi a livelli pari o superiori
            while stack and indent <= stack[-1]:
                stack.pop()
                opml_lines.append(f"{'  ' * (len(stack) + 2)}</outline>")

            # Apri nuovo elemento outline
            xml_indent = "  " * (len(stack) + 2)
            opml_lines.append(f'{xml_indent}<outline text="{clean_text}">')
            stack.append(indent)

        # Chiudi tutti i tag aperti rimasti nello stack
        while stack:
            stack.pop()
            opml_lines.append(f"{'  ' * (len(stack) + 2)}</outline>")

        opml_lines.extend([
            "  </body>",
            "</opml>",
        ])

        return "\n".join(opml_lines)
