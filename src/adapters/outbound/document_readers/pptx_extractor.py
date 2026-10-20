from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

def _iter_shapes_recursive(shapes):
    """
    # ARCHITETTURA: Attraversamento ricorsivo dell'albero di shape OpenXML (GroupShape).
    # TRADE-OFF: I convertitori lineari (incluso MarkItDown standard) ispezionano solo
    # il primo livello `slide.shapes`, ignorando completamente i box di testo, i diagrammi
    # di processo e le tabelle raggruppati dentro `GroupShape` (`shape_type == 6`).
    # La discesa ricorsiva garantisce zero perdita di contenuto testuale o tabellare.
    """
    for shape in shapes:
        yield shape
        is_group = (
            getattr(shape, "shape_type", None) == 6
            or type(shape).__name__ == "GroupShape"
            or isinstance(getattr(shape, "shapes", None), (list, tuple))
        )
        if is_group and getattr(shape, "shapes", None) is not None:
            yield from _iter_shapes_recursive(shape.shapes)


def extract_pptx_to_markdown(path: Path) -> str:
    """
    Extracts structured Markdown from a PowerPoint (.pptx) file.
    Follows a 3-tier resilient extraction pipeline:
    1. Primary: python-pptx with recursive GroupShape, table, and speaker notes parsing.
    2. Secondary: Microsoft's MarkItDown.
    3. Antifragile Zero-Dependency Fallback: Python standard library (zipfile + xml.etree)
       which extracts all slide texts, shapes, and presenter notes directly from OpenXML without any third-party packages.
    """
    path_str = str(path)

    # Tier 1: python-pptx (direct structural parsing with recursive GroupShape traversal)
    try:
        from pptx import Presentation
        prs = Presentation(path_str)
        slides_text = []
        for idx, slide in enumerate(prs.slides, 1):
            parts = [f"## Slide {idx}"]
            for shape in _iter_shapes_recursive(slide.shapes):
                if getattr(shape, "has_text_frame", False) and shape.text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        line = paragraph.text.strip()
                        if line:
                            parts.append(line)
                elif getattr(shape, "has_table", False) and shape.table:
                    table = shape.table
                    for row_idx, row in enumerate(table.rows):
                        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                        parts.append("| " + " | ".join(cells) + " |")
                        if row_idx == 0:
                            parts.append("| " + " | ".join(["---"] * len(cells)) + " |")
            if getattr(slide, "has_notes_slide", False) and slide.notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    parts.append(f"> **Note del relatore**: {notes}")
            if len(parts) > 1:
                slides_text.append("\n\n".join(parts))

        full_text = "\n\n---\n\n".join(slides_text).strip()
        if full_text:
            return full_text
    except Exception:
        pass

    # Tier 2: MarkItDown (official markdown converter)
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(path_str)
        text = result.text_content.strip()
        if text:
            return text
    except Exception:
        pass

    # Tier 3: Zero-dependency OpenXML extraction via Python standard library (zipfile + xml.etree)
    try:
        slides_content = []
        with zipfile.ZipFile(path_str, "r") as z:
            names = z.namelist()
            slide_names = sorted(
                [n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")],
                key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0,
            )

            for idx, sname in enumerate(slide_names, 1):
                root = ET.fromstring(z.read(sname))
                paragraphs = []
                for p in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}p"):
                    texts = [t.text for t in p.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t") if t.text]
                    line = "".join(texts).strip()
                    if line:
                        paragraphs.append(line)

                # Check if there are presenter notes
                note_name = f"ppt/notesSlides/notesSlide{idx}.xml"
                if note_name in names:
                    note_root = ET.fromstring(z.read(note_name))
                    notes_paragraphs = []
                    for p in note_root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}p"):
                        texts = [t.text for t in p.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t") if t.text]
                        line = "".join(texts).strip()
                        if line and line != str(idx):
                            notes_paragraphs.append(line)
                    if notes_paragraphs:
                        paragraphs.append("> **Note del relatore**: " + " ".join(notes_paragraphs))

                if paragraphs:
                    slides_content.append(f"## Slide {idx}\n" + "\n\n".join(paragraphs))

            full_text = "\n\n---\n\n".join(slides_content).strip()
            if full_text:
                return full_text
    except Exception as exc:
        raise RuntimeError(f"Impossibile estrarre testo dal file PPTX '{path_str}': {exc}")

    raise RuntimeError(f"Nessun contenuto estraibile trovato nel file PPTX '{path_str}'.")
