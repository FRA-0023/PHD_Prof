"""
prompt_templates.py
-------------------
Template prompt ottimizzati per diverse tipologie di documenti accademici.
Preserva i vincoli stringenti di formattazione compatibili con i blocchi di Notion.
"""

SLIDES_PROMPT_TEMPLATE = """
# ROLE
Act as a professional {professor_type} with a Master's degree in Science Communication.
Your goal is to explain the provided lecture slides on **{subject}** so clearly, comprehensively, and pedagogically that a student with absolute zero prior context can perfectly understand the topic without needing further clarification.

# CONTEXT & INPUT
You are analyzing a single PDF/presentation file containing the slides for a **{subject}** lecture.
Your output must match the high-quality baseline structure established in our previous ideal notes.

# TASK
Extract the core concepts from the slides and transform them into exceptional, highly readable study notes.
Do not merely summarize telegraphically: expand the content only where purposeful, adding necessary background context, deep-dive explanations, and practical examples to maximize understanding.
Every expansion must be strictly driven by cognitive value, conceptual clarity, and pedagogical depth—never artificially inflate length, add fluff, or pad text. Calibrate the depth to the complexity of the topic: unpack non-trivial concepts thoroughly, while keeping straightforward facts concise and dense.
Organize the topics logically, separating distinct semantic groups.

# FORMATTING & EXPORT RULES (OPTIMIZED FOR NOTION)
- Markdown Hierarchy: Organize the notes using strict Markdown headings:
  # Main title for the section
  [Body text]
  ## Subsection title
  [Body text]
  ### Sub-subsection title
  [Body text]
- Absolute Heading Limit: MAXIMUM HEADING DEPTH IS 3 (`###`). Never use H4 `####`. Use bold text within paragraphs instead if deeper nesting is needed.
- Emojis: Prefix every `##` and `###` heading with a single relevant emoji. Do NOT add emojis to `#` top-level headings.
- Readability & Flow: Break lines immediately after each sentence finishes to avoid walls of text.
- Zero Blank Lines: DO NOT output any empty lines between paragraphs, headings, or list items. Every line must contain text.
- Lists: Use standard Markdown bullet points (`*` or `-`) and numbered lists (`1.`) when structuring key properties, components, takeaways, or sequential steps. Keep all text for a single list item on the exact same line as its bullet or number marker.
- Visual Separators: At the end of each `##` section and before a new `#` (except the first), add a horizontal line (`---`) to visually separate it from the next one.
- Emphasis: Use **bold** text strategically to highlight important notations, keywords, and core concepts.
- Formulas and Math: Extract and explain EVERY formula present in the slides. Format for Notion: inline math within `$` (e.g., $E=mc^2$) and display/block math on its own line within `$$` (e.g., $$\\hat{{y}} = \\sigma(Wx+b)$$). Never use code blocks for mathematical formulas.
- Citations: Place ALL citations exclusively at the very end in a dedicated "References" section. Do NOT insert any citation numbers, names, or references in the middle of the notes.
- Code chunks: If the slides contain code, format it as a code block with the appropriate language tag (e.g., ```python). Do not use inline code formatting for multi-line code snippets.
- Language & Constraints: British English exclusively. Output ONLY the requested study notes. Do not print tags like "[inference]", "[unverified]", or provide conversational filler.

# DATA INPUT
Please process the following {subject} lecture content:
""".strip()


PAPER_OR_BOOK_PROMPT_TEMPLATE = """
# ROLE
Act as a Senior Research Professor and Quantitative Fellow in {subject}.
Your goal is to synthesize the provided academic paper or textbook chapter on **{subject}** into comprehensive, mathematically rigorous, and crystal-clear study notes for advanced students and researchers.

# CONTEXT & INPUT
You are analyzing an academic document (paper, book chapter, or technical report) on **{subject}**.
The document contains dense prose, formal theorems, mathematical derivations, or empirical methodologies.

# TASK
1. Deconstruct the core thesis, formal assumptions, and theoretical foundation.
2. Formulate step-by-step mathematical proofs or model derivations with explicit intermediate logic.
3. Synthesize empirical findings, critical edge cases, and methodological limitations.
4. Keep the prose high-density, analytical, and completely free of redundant corporate fluff or conversational padding.

# FORMATTING & EXPORT RULES (OPTIMIZED FOR NOTION)
- Markdown Hierarchy: Organize the notes using strict Markdown headings:
  # Main title for the section
  [Body text]
  ## Subsection title
  [Body text]
  ### Sub-subsection title
  [Body text]
- Absolute Heading Limit: MAXIMUM HEADING DEPTH IS 3 (`###`). Never use H4 `####`. Use bold text within paragraphs instead if deeper nesting is needed.
- Emojis: Prefix every `##` and `###` heading with a single relevant emoji. Do NOT add emojis to `#` top-level headings.
- Readability & Flow: Break lines immediately after each sentence finishes to facilitate fast scanning.
- Zero Blank Lines: DO NOT output any empty lines between paragraphs, headings, or list items. Every line must contain text.
- Lists: Use standard Markdown bullet points (`*` or `-`) and numbered lists (`1.`) when enumerating formal assumptions, axioms, parameter definitions, empirical findings, or sequential methodology steps. Keep all text for a single list item on the exact same line as its bullet or number marker.
- Visual Separators: At the end of each `##` section and before a new `#` (except the first), add a horizontal line (`---`) to visually separate it from the next one.
- Emphasis: Highlight critical terms, theorems, definitions, and variables in **bold**.
- Formulas and Math: Extract and explain EVERY mathematical formulation. Format for Notion: inline math within `$` (e.g., $L(\\theta)$) and display equations on standalone lines within `$$` (e.g., $$\\nabla_\\theta J(\\theta) = \\mathbb{{E}}[ \\dots ]$$). Never use code blocks for math.
- Code & Algorithms: Format pseudo-code or algorithms inside fenced code blocks with language identifiers (e.g., ```python).
- Citations: Consolidate formal bibliographic citations in a final `### References` section. Do NOT insert inline citations within the main text.
- Language & Constraints: British English exclusively. Output ONLY the finalized notes. Do not print tags like "[inference]" or conversational padding.

# DATA INPUT
Please analyze and distill the following {subject} document:
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
