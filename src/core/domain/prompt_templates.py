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
Synthesize the provided {subject} lecture content into exceptional, highly engaging study notes that form a fluid, logically coherent narrative rather than a flat collection of bullet points:
1. The Inefficiency Solved: For every core framework, model, or concept, explicitly articulate the structural bottleneck, fragility, or friction it was invented to overcome.
2. Mental Model & Mechanics: Unpack how the system functions through intuitive narrative prose, cause-effect feedback loops, and architectural dynamics. When slide notes (### Notes:), footnotes, or speaker commentary are present, seamlessly weave their explanatory depth, recommended readings, and industrial insights directly into the story.
3. Grounded Examples: Where a concept or trade-off is abstract or non-trivial, provide a sharp, realistic example (e.g., legacy migration, API decoupling, failure cascades) to make the mechanics immediately tangible.
4. Boundary Conditions & Inversion: Detail where the framework breaks down, its operational anti-patterns, and systemic trade-offs.
5. Mathematical & Technical Deconstruction: When formulas or code are present, extract and deconstruct all variables, parameters, and assumptions explicitly rather than presenting monolithic blocks.

Calibrate depth to conceptual complexity: thoroughly unpack intricate mechanisms while keeping straightforward facts dense and concise. Zero artificial padding.
</task>

<formatting_rules>
- Hierarchy:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
- Visual Separators: Add a single horizontal rule (---) before each ## section (except the first). NEVER add a horizontal rule before ### subsections. NEVER place consecutive or duplicate horizontal rules.
- Narrative Flow & Paragraph Structure:
  * Deliver explanations primarily through rich, well-crafted narrative paragraphs (2 to 4 sentences each). Connect ideas logically from problem to mechanism to consequence.
  * Avoid "flat" formatting: do NOT rely on endless bullet points or bold pseudo-headings to structure entire sections.
  * Always ensure standard punctuation spacing: exactly one space after a period (`.`), comma (`,`), colon (`:`), or semicolon (`;`). Never attach the next word directly to punctuation (e.g. write `concept. Next`, never `concept.Next`).
- Lists & Boundaries:
  * Restrict bullet points (`-`) to concise enumerations of 3 to 6 items maximum (e.g., distinct architectural properties, axioms, or components).
  * Once the list items are stated, IMMEDIATELY terminate the list and return to standard narrative paragraphs without bullet points. Do not continue bullet points for explanatory commentary.
  * Keep lists strictly distinct: use numbered lists (`1.`, `2.`) ONLY for sequential execution steps, chronological procedures, or algorithms; use bullet points (`-`) ONLY for unordered collections or attributes. NEVER mix numbered items and bullets within the same section.
  * Keep each list item entirely on a single line.
- Emphasis: Use **bold** text strategically for key terms, definitions, and core concepts within the narrative.
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
Deconstruct and synthesize the provided academic document (paper, book chapter, or report) on {subject} into rigorous, crystal-clear study notes with a compelling narrative arc and clear logical progression, avoiding flat bullet lists:
1. The Inefficiency Solved: Identify the fundamental research question, market failure, theoretical limitation, or empirical gap the work addresses.
2. Theoretical Framework & Mechanics: Formulate the core thesis, formal assumptions, and model mechanics using intuitive narrative prose and causal links.
3. Concrete Empirical / Applied Examples: Anchor abstract theoretical propositions or complex models with a concrete empirical or applied scenario to illuminate how the dynamics play out in practice.
4. Mathematical Derivations & Deconstruction: Provide step-by-step derivations, explicitly unpacking each variable, coefficient, and operator rather than presenting isolated formulas.
5. Boundary Conditions & Inversion: Clarify theoretical boundary conditions, identification threats, empirical limitations, and structural trade-offs.

Calibrate depth to conceptual complexity: unpack intricate proofs with mathematical rigor, while keeping descriptive facts dense and concise. Zero conversational filler.
</task>

<formatting_rules>
- Hierarchy:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
- Visual Separators: Add a single horizontal rule (---) before each ## section (except the first). NEVER add a horizontal rule before ### subsections. NEVER place consecutive or duplicate horizontal rules.
- Narrative Flow & Paragraph Structure:
  * Deliver explanations primarily through rich, cohesive narrative paragraphs (2 to 4 sentences each). Connect theoretical motivation, formal models, and empirical implications in a smooth logical chain.
  * Avoid "flat" formatting: do NOT rely on endless bullet points or bold pseudo-headings to structure entire sections.
  * Always ensure standard punctuation spacing: exactly one space after a period (`.`), comma (`,`), colon (`:`), or semicolon (`;`). Never attach the next word directly to punctuation (e.g. write `concept. Next`, never `concept.Next`).
- Lists & Boundaries:
  * Restrict bullet points (`-`) to concise enumerations of 3 to 6 items maximum (e.g., formal axioms, parameter definitions, or boundary conditions).
  * Once the list items are stated, IMMEDIATELY terminate the list and return to standard narrative paragraphs without bullet points. Do not continue bullet points for explanatory commentary.
  * Keep lists strictly distinct: use numbered lists (`1.`, `2.`) ONLY for sequential methodology steps, algorithms, or chronological procedures; use bullet points (`-`) ONLY for unordered collections or axioms. NEVER mix numbered items and bullets within the same section.
  * Keep each item entirely on a single line.
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
