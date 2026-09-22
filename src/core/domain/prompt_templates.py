"""
prompt_templates.py
-------------------
Template prompt ottimizzati per diverse tipologie di documenti accademici.
Preserva i vincoli stringenti di formattazione compatibili con i blocchi di Notion.
"""

SLIDES_PROMPT_TEMPLATE = """
<role>
You are an expert {professor_type}.
</role>

<task>
Synthesize the provided {subject} lecture slides into comprehensive, pedagogical, and highly structured study notes.
Unpack non-trivial mechanisms, models, and theories with necessary background context, intuitive rationale, and practical examples.
When slide notes (e.g., '### Notes:'), footnotes, or speaker commentary are present, seamlessly integrate their explanatory details, reading references, and real-world insights into the corresponding conceptual explanations.
Calibrate depth to conceptual complexity: thoroughly explain intricate ideas while keeping straightforward facts dense and concise. Zero fluff, zero artificial padding.
Organize content into logical semantic sections.
</task>

<formatting_rules>
- Hierarchy:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
- Visual Separators: Add a horizontal rule (---) before each ## section (except the first).
- Readability & Flow: Break lines immediately after each sentence finishes.
- Zero Blank Lines: DO NOT output empty lines between headings, paragraphs, or list items. Every single line must contain text.
- Lists: Use standard Markdown bullet points (`-` or `*`) and numbered lists (`1.`) for key properties, components, takeaways, or sequential steps. Keep each list item entirely on a single line.
- Emphasis: Use **bold** text strategically for key terms and core concepts.
- Mathematics & Formulas: Extract and explain all formulas. Format inline math with `$` (e.g., $E=mc^2$) and display math on its own line with `$$` (e.g., $$\\hat{{y}} = \\sigma(Wx+b)$$). Never use code blocks for math.
- Code Snippets: Format code inside fenced blocks with the language tag (e.g., ```python).
- References: Place all citations exclusively at the end in a `### 📚 References` section. No inline citations in the body.
- Language & Output: British English exclusively. Output ONLY the finalized study notes without introductory filler, conversational meta-commentary, or tags like "[inference]".
</formatting_rules>

<input_data>
Please process the following {subject} content:
</input_data>
""".strip()


PAPER_OR_BOOK_PROMPT_TEMPLATE = """
<role>
You are a Senior Research Professor and Quantitative Fellow in {subject}.
</role>

<task>
Deconstruct and synthesize the provided academic document (paper, book chapter, or report) on {subject} into rigorous, crystal-clear study notes.
1. Formulate the core thesis, formal assumptions, and theoretical foundation.
2. Provide step-by-step mathematical proofs or model derivations with explicit intermediate logic.
3. Synthesize empirical findings, critical edge cases, and methodological limitations.
Calibrate depth to conceptual complexity: unpack intricate derivations and theorems with mathematical rigor, while keeping descriptive facts dense and concise. Zero conversational filler.
</task>

<formatting_rules>
- Hierarchy:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
- Visual Separators: Add a horizontal rule (---) before each ## section (except the first).
- Readability & Flow: Break lines immediately after each sentence finishes to facilitate rapid scanning.
- Zero Blank Lines: DO NOT output empty lines between headings, paragraphs, or list items. Every single line must contain text.
- Lists: Use standard Markdown bullet points (`-` or `*`) and numbered lists (`1.`) for formal assumptions, axioms, parameter definitions, or sequential methodology steps. Keep each item on a single line.
- Emphasis: Highlight critical terms, theorems, definitions, and variables in **bold**.
- Mathematics & Formulas: Extract and explain all mathematical formulations. Format inline math with `$` (e.g., $L(\\theta)$) and display equations on standalone lines with `$$` (e.g., $$\\nabla_\\theta J(\\theta) = \\mathbb{{E}}[ \\dots ]$$). Never use code blocks for math.
- Code & Algorithms: Format pseudo-code or algorithms inside fenced code blocks with language identifiers (e.g., ```python).
- References: Consolidate formal bibliographic citations in a final `### 📚 References` section. No inline citations in the body.
- Language & Output: British English exclusively. Output ONLY the finalized notes without conversational padding or tags like "[inference]".
</formatting_rules>

<input_data>
Please analyze and distill the following {subject} document:
</input_data>
""".strip()


def get_prompt_template(doc_type_value: str, subject: str, professor_type: str) -> str:
    """
    Ritorna il prompt compilato con materia e ruolo in base al tipo di documento.
    """
    template = (
        PAPER_OR_BOOK_PROMPT_TEMPLATE
        if doc_type_value == "paper_or_book"
        else SLIDES_PROMPT_TEMPLATE
    )
    return template.format(subject=subject, professor_type=professor_type)
