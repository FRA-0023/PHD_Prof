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
You are analyzing a single PDF file containing the slides for a **{subject}** lecture.
Your output must match the high-quality baseline structure established in our previous ideal notes.

# TASK
Extract the core concepts from the slides and transform them into exceptional, highly readable study notes.
Provide necessary background information and deep-dive explanations, but keep the output concise and highly dense with information. Avoid dispersive verbosity, fluff, or overly long text.

# FORMATTING & EXPORT RULES (OPTIMIZED FOR NOTION)
- Format Requirement: You MUST write in continuous narrative paragraphs (Essay format). You are STRICTLY FORBIDDEN from using bullet points (`-`, `*`) or numbered lists for standard explanations. 
    Only use lists if you are stating raw data properties.
- Absolute Heading Limit: MAXIMUM HEADING DEPTH IS 3 (`###`). Never use H4 `####`.
- Readability & Flow: Break lines immediately after each sentence finishes to avoid walls of text.
- Zero Blank Lines: DO NOT output any empty lines between paragraphs or headings. Every line must contain text.
- Emphasis: Use **bold** text strategically.
- Formulas and Math: Format for Notion: inline math within `$` (e.g., $E=mc^2$) and display/block math on its own line within `$$` (e.g., $$\\hat{{y}} = \\sigma(Wx+b)$$). Never use code blocks for mathematical formulas.
- Citations: Place ALL citations exclusively at the very end in a "References" section.
- Language: British English exclusively. Output ONLY the study notes without "[inference]" tags.
- Code chunks: If the slides contain code, format it as a code block with the appropriate language tag (e.g., ```python). Do not use inline code formatting for multi-line code snippets.

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
- Format Requirement: Write in structured, continuous analytical paragraphs. Avoid superficial bullet points; reserve lists only for explicit axiomatic enumerations or parameter definitions.
- Absolute Heading Limit: MAXIMUM HEADING DEPTH IS 3 (`###`). Never use H4 `####`.
- Readability & Flow: Break lines immediately after each sentence finishes to facilitate fast scanning.
- Zero Blank Lines: DO NOT output any empty lines between paragraphs or headings.
- Emphasis: Highlight critical terms, theorems, and variables in **bold**.
- Formulas and Math: Format for Notion: inline math within `$` (e.g., $L(\\theta)$) and display equations on standalone lines within `$$` (e.g., $$\\nabla_\\theta J(\\theta) = \\mathbb{{E}}[ \\dots ]$$).
- Code & Algorithms: Format pseudo-code or algorithms inside fenced code blocks with language identifiers (e.g., ```python).
- Citations: Consolidate formal bibliographic citations in a final `### References` section.
- Language: British English exclusively. Output ONLY the finalized notes.

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
