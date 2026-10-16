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
Synthesize the provided {subject} lecture content into authoritative, intellectually dense study notes with maximum technical signal-to-noise ratio:
1. Foundational Anchoring & Pedagogical Calibration (Target Audience Invariant):
   - Assume the target reader has solid training in classical foundational disciplines (probability, expected value, variance, OLS regression, t-test, F-test, LLN, CLT; or systems architecture and hardware memory hierarchies), but is studying the specific specialized subject for the first time.
   - For every specialized framework or model, explicitly articulate **which baseline assumption breaks down and why** before presenting the advanced tool (e.g., cross-sectional independent draws -> single time trajectory; stationary regressors -> random walk variance exploding at T^2; i.i.d. errors -> serial correlation; compute-bound -> memory-bandwidth wall).
   - Disclose the underlying statistical or physical intuition for transformations and distribution shifts (e.g., why OLS suffers from downward Hurwicz bias by chasing sample means, why Said-Dickey parameterization isolates long-run scalar persistence while absorbing short-run nuisance dynamics in stationary differences, why deterministic dominance collapses non-standard distributions to standard Gaussian).
   - Explicitly state why choosing the wrong transformation/model is fatal (e.g., spurious regression vs over-differencing; lock contention vs memory thrashing).
2. Core Theory & Mathematical Mechanics: Formulate models, formal equations, stochastic properties, and causal identification mechanisms with exact mathematical rigor. Integrate slide notes (### Notes:), footnotes, and speaker commentary directly into the analytical substance.
3. Direct Technical Progression (Zero-Slop Transitions): Never use conversational, rhetorical, or formulaic transition phrases ("In the previous section we saw...", "Now we turn to...", "It is worth noting that...", "Having examined X, we now examine Y..."). Link models and mechanisms exclusively via their **Technical Delta**: state in exactly 1 direct sentence the precise mathematical bottleneck, asymptotic failure, or identification limit of the preceding model that necessitates the new model, then immediately state the corrective formulation (e.g., "Because standard Dickey-Fuller assumes serially uncorrelated residuals, the Augmented Dickey-Fuller (ADF) absorbs residual autocorrelation by parameterizing p lagged first-differences: [Formula]"). Maintain absolute economy of words: pure signal, zero introductory padding, zero rhetorical questions.
4. Uniform Analytical Caliber (Empirical & Computational Rigor): Treat empirical regression tables, diagnostic test outputs, and system metrics with the SAME formal mathematical grammar as foundational theory. Explicitly map empirical coefficients and test statistics to theoretical null hypotheses ($H_0$), critical values, structural parameter shifts, and asymptotic properties. Never degrade empirical or code sections into descriptive summaries or mere slide commentary.
5. End-to-End Methodological Continuity (Resolving Circular Dilemmas & Empirical Paradoxes):
   - Trace the causal necessity of diagnostic algorithms (e.g., sequential testing procedures, model selection criteria, lag pruning, downward testing). Explicitly formulate the **circular dilemma or structural trade-off** that mandates the procedure (e.g., testing deterministics requires knowing integration order, but testing integration order requires knowing deterministics).
   - Directly connect empirical paradoxes or edge cases (e.g., structural breaks in drift, near-unit roots, I(2) multiple roots) to the breakdown modes of the underlying estimators (e.g., how an omitted step break forces OLS to fit the jump with alpha_1 ≈ 1 or a spurious concave quadratic trend). Never leave an empirical contradiction unexplained.
6. Selective Grounded Examples: Provide a concrete empirical/numerical scenario formatted with the mandatory example pattern ONLY for complex, non-trivial models or estimation trade-offs. Never generate examples for basic terminology, administrative overviews, or syllabus lists.
7. Core Insights as Quotes: Elevate only foundational theorems, asymptotic properties, or critical identification rules into dedicated blockquotes (`>`). Maximum 1 quote per major section (`##`).
8. Boundary Conditions & Trade-offs: State exact conditions where models fail, unit roots arise, or estimators become biased/inconsistent.
9. Mathematical & Architectural Deconstruction (Complex / Detached Concepts): Whenever formulas, hardware abstractions, computational complexity claims (e.g., GEMM, attention complexity, O(N^3), memory bandwidth bottlenecks), or standalone technical tangents appear, NEVER present them as bare, isolated equations or dry bullet points. Apply systematic pedagogical grounding:
   - Physical & Domain Mapping: Ground every variable, index, and matrix dimension (e.g., m, k, n) into its concrete physical reality in the system (e.g., batch tokens, input embedding channels, output neuron projections).
   - Operational Count & Mechanics: Explicitly explain WHY the computational complexity holds by counting individual scalar multiplications and additions.
   - Hardware & Silicon Bridge: Explain why hardware (CPU vs GPU vs specialized Tensor Cores) excels or struggles with the operation (e.g., Arithmetic Intensity = FLOPs / byte transferred, Compute-Bound vs Memory-Bandwidth Bound, zero-dependency parallel execution).
   - Concrete Numerical Walkthrough: Provide a minimal 2x2 or 3x3 numeric or tabular illustration showing data flow and independent computation.
   - Boundary Conditions & Inversion: State the exact conditions where the operation breaks down or becomes suboptimal (e.g., single-token autoregressive decoding collapsing GEMM into memory-bandwidth bound GEMV).

Anti-Tautology & Symbolic Continuity: Explain each concept, parameter, or property ONCE at its primary introduction. When symbols, models, or state parameters are established, assume them as proven invariants and use them directly without re-explaining or re-defining them. Zero conversational padding, zero decorative throat-clearing, zero artificial elongation.
</task>

<formatting_rules>
- Hierarchy & Structure:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
  * Meaningful Granularity: Create `### [Emoji] Subsection Title` only when logically distinct models, estimators, or methodological stages are introduced. NEVER insert artificial subsections every few sentences or just to meet an arbitrary word target.
- Visual Separators: Add a single horizontal rule (---) before each ## section (except the first). NEVER add a horizontal rule before ### subsections. NEVER place consecutive or duplicate horizontal rules.
- High-Density Prose & Paragraph Flow:
  * Deliver explanations through focused, cohesive paragraphs of 2 to 4 sentences. Lead directly with the technical or theoretical mechanism; eliminate meta-introductions ("This course delves into...", "It is crucial to understand that...", "The motivation is multifaceted...").
  * Avoid both monolithic walls of text and vacuous, fragmented filler. Connect problem, mechanism, and economic consequence in a tight logical chain.
  * Always ensure standard punctuation spacing: exactly one space after a period (`.`), comma (`,`), colon (`:`), or semicolon (`;`).
- Grounded Examples (Selective):
  * Where a complex model or estimation scenario requires concrete anchoring, use a dedicated paragraph:
    `**Example:** *[Concise numerical or empirical application in italics detailing the exact setup, estimates, and economic interpretation.]*`
  * Keep examples dense and factual. Never re-state theoretical definitions already given in preceding paragraphs.
  * Omit examples entirely for descriptive, administrative, or introductory sections.
- Core Takeaways as Blockquotes:
  * Reserve blockquotes exclusively for pivotal laws, identification conditions, or core asymptotic theorems (max 1 per ## section):
    `> **Core Insight:** [Authoritative, mathematically grounded statement.]`
- Lists & Boundaries:
  * Restrict bullet points (`-`) to concise enumerations of 3 to 6 distinct properties, axioms, or components.
  * Once list items are stated, IMMEDIATELY terminate the list and return to standard narrative paragraphs without bullet points. Do not continue bullet points for explanatory commentary.
  * Keep lists strictly distinct: use numbered lists (`1.`, `2.`) ONLY for sequential execution steps or algorithms; use bullet points (`-`) ONLY for unordered attributes. NEVER mix numbered items and bullets within the same section.
  * Keep each item entirely on a single line.
- Emphasis: Use **bold** text strategically for key terms and newly defined variables within the narrative flow.
- Mathematics & Formulas: Extract all formal equations. Format inline math with `$` (e.g., $E=mc^2$) and display math on its own line with `$$` (e.g., $$\\hat{{y}} = \\sigma(Wx+b)$$). Never use code blocks for math.
  * Strict KaTeX Single-Backslash Formatting: Format all LaTeX equations with standard single backslashes (e.g., $\\tau_\\mu$, $\\Delta y_t$, $\\alpha_0$, $\\mathbb{{E}}$). NEVER emit escaped double backslashes (\\\\Delta, \\\\tau) inside math blocks, as KaTeX interprets '\\\\' as an internal line break and corrupts rendering.
  * Backtick Hygiene: Ensure all inline code backticks are strictly matched and closed. Never leave empty backticks (``) or unclosed backticks that inadvertently engulf text or mathematical equations into raw monospace blocks.
  * Complex Operations & Hardware Deconstructions: When introducing foundational mathematical operations, computational complexity bounds, or hardware-bridging mechanisms, format them under a dedicated subsection: `### 🧮 Mathematical & Hardware Deconstruction: [Concept Name]`, following the 5-point physical mapping, operational count, silicon bridge, numerical trace, and boundary conditions.
- Code Snippets: Format code inside fenced blocks with the language tag (e.g., ```python, ```r).
- Visual Diagrams & Figures (CRITICAL FORMATTING INVARIANT):
  * If a slide contains a critical architecture diagram, empirical plot, or structural matrix that cannot be rendered losslessly via LaTeX or Markdown tables, insert an image reference at the exact logical point of discussion.
  * MANDATORY STANDALONE BLOCK: The image reference MUST ALWAYS be placed on its own standalone line with empty lines before and after. Format:
    
    ![](figure://slide_N)
    
  * FULL-SLIDE INTEGRITY (NO ARBITRARY CROPPING): Always extract the full slide without coordinate crops (do NOT use ?crop=...). Extracting the full slide preserves all axes, labels, notes, and comparative panels (e.g. Before/After) without truncation.
  * STRICT PROHIBITION ON INLINE CITATIONS: NEVER write inline references or citations such as `(figure://slide_N)`, `(slide N)`, `(figura N)`, or `(vedi slide N)` inside sentences, headers, or bullet points. All figures must be isolated standalone image lines. Keep the prose completely clean and flowing.
  * ZERO BOILERPLATE CAPTIONS: Do NOT write generic captions like "Figura slide N" or "Slide N". Leave the figure reference clean as `![](figure://slide_N)`.
  * Only select figures that carry high theoretical or empirical signal. Zero screenshots of pure text slides or syllabus overviews.
- References: Place all citations exclusively at the end in a `### 📚 References` section. No inline citations in the body.
- Study Artifacts & Conceptual Maps (Mandatory Append Section):
  * Conclude the notes with the following three high-signal study sections:
    ---
    ## 🧠 Conceptual Architecture & Relational Graphs
    * Provide a Mermaid Conceptual Taxonomy Tree (`graph TD`) mapping the chapter's conceptual taxonomy with hierarchical pastel levels:
    ```mermaid
    graph TD
      classDef rootNode fill:#0f172a,stroke:#334155,stroke-width:2px,color:#fff;
      classDef level1 fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px,color:#1e3a8a;
      classDef level2 fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1.2px,color:#4c1d95;
      classDef level3 fill:#f0fdf4,stroke:#10b981,stroke-width:1px,color:#064e3b;

      ROOT(["Lecture Core"]):::rootNode
      P1["Theoretical Pillars"]:::level1
      P2["Empirical Channels"]:::level1
      M1["Key Model A"]:::level2
      M2["Key Model B"]:::level2
      S1["Identification Strategy"]:::level2
      S2["Estimation Mechanics"]:::level2

      ROOT --> P1
      ROOT --> P2
      P1 --> M1
      P1 --> M2
      P2 --> S1
      P2 --> S2
    ```
    * Provide a Mermaid flowchart (`graph TD`) mapping the primary causal chain, transmission mechanism, or algorithmic architecture. Follow these VISUAL & MATHEMATICAL standards:
      1. **Color Coding by Topic (NOT by Grouping/Box)**: Style nodes by their conceptual nature / topic across the entire architecture, NOT monochromatic by subgraph box. Use semantic pastel fills with distinct border strokes:
         - **Theory & Definitions**: `classDef theoryNode fill:#eff6ff,stroke:#3b82f6,color:#1e3a8a;` (definitions, theorems, axioms, principles).
         - **Compute & Architecture**: `classDef computeNode fill:#fef3c7,stroke:#f59e0b,color:#78350f;` (hardware models, engines, mathematical operations).
         - **Pipelines & Data Flow**: `classDef pipelineNode fill:#f5f3ff,stroke:#8b5cf6,color:#4c1d95;` (transformations, execution DAGs, data lifecycle).
         - **Engineering & Storage**: `classDef devopsNode fill:#f0fdf4,stroke:#10b981,color:#064e3b;` (tools, reproducibility, storage economics).
         - **Bottlenecks & Failure Modes**: `classDef bottleneckNode fill:#fff1f2,stroke:#f43f5e,color:#881337;` (physical limits, performance walls, failure conditions).
      2. **Strict Text Formatting (NO HTML)**:
         - NEVER use HTML tags (`<span>`, `<b>`, `<i>`, `<br/>`, `<br>`, etc.) inside Mermaid nodes or subgraph titles. Notion and ELK layout engines fail on HTML tags with layout null pointer exceptions.
         - For multi-line labels, separate concepts with hyphens (` - `) or concise phrases entirely wrapped in double quotes: `NodeID["Clean Descriptive Title - Secondary Detail"]`.
         - ALWAYS wrap ALL node labels in double quotes (e.g. `NodeID["Label Text"]`, `NodeID("Rounded Label")`, `NodeID{{"Condition"}}`).
         - In edge labels (`|label|`), use concise words without parentheses or angle brackets (`<`, `>`).
      3. **Formal Mathematical Notation**: In diagrams, format mathematical complexities and variables using clean Unicode math notation instead of ASCII approximations (e.g. `O(m × n × k) ≈ O(N³)` instead of `O(N^3)`, `O(log N)`, `(K₁, V₁)`, `∑`, `β̂`, `λ`, `->`).
      4. **Topology & Subgraph Rules**:
         - Connect STRICTLY node-to-node (`NodeA --> NodeB`). NEVER connect an edge to or from a subgraph container directly.
         - If using subgraphs, always specify an alphanumeric ID: `subgraph SG_ID ["Subgraph Title"]`.
         - NEVER apply `style` directly to subgraph IDs (e.g. `style SG_ID ...` is forbidden as it causes Notion layout crashes).
         - Cross-subgraph edges MUST be declared outside/after the subgraph blocks at root level, never nested inside individual subgraphs.
         - Use standard edge labels with vertical pipes: `-->|label|`, never `-- "label" -->`.
      5. **Strict Vertical Flow & Width Budget (Anti-Shrink Guarantee)**:
         - Notion constrains diagrams to a narrow column width (700-900px). Diagrams with wide horizontal sprawl or subgraphs placed side-by-side shrink proportionally, making text microscopic and unreadable.
         - STRICTLY use `graph TD` (Top-Down). NEVER use `graph LR` (Left-to-Right).
         - NEVER declare multiple subgraphs in parallel side-by-side. Stack all subgraphs sequentially in a single vertical column (`SG_1 --> SG_2 --> SG_3`).
         - Inside each subgraph, chain nodes vertically in a single sequence (`Node1 --> Node2 --> Node3`) or allow at most 2 parallel branches across the rank.
         - Keep node labels strictly compact (max 25-28 characters per node, e.g. 'Layered EA Models', 'Serving & Realisation'). Labels exceeding 30 characters cause Notion's SVG layout engine to overflow and physically clip words against the right border of the node rectangle.
    ```mermaid
    graph TD
      classDef rootNode fill:#0f172a,stroke:#334155,stroke-width:2.5px,color:#fff;
      classDef theoryNode fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px,color:#1e3a8a;
      classDef pipelineNode fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1.5px,color:#4c1d95;
      classDef bottleneckNode fill:#fff1f2,stroke:#f43f5e,stroke-width:1.5px,color:#881337;

      ROOT["Econometric Framework - Structural Overview"]:::rootNode

      subgraph SG_ID ["Causal Identification Engine"]
        Shock["Exogenous Shock (Z) - Quasi-experimental instrument"]:::theoryNode
        Channel["Transmission Channel (D) - Compliance and response"]:::pipelineNode
        Lim["Weak Instrument Limit - F-stat breakdown"]:::bottleneckNode
      end

      ROOT --> Shock
      Shock --> Channel
      Channel --> Lim
    ```
    ---
    ## 🎯 Active Recall & Examination Drills
    * Formulate 3 to 5 rigorous, examination-grade questions targeting analytical friction points:
    - **Drill 1 (Foundational):** [Core conceptual question]
      * **Rubric:** [Explicit technical criteria required for full marks]
    - **Drill 2 (Analytical Derivation):** [Question on econometric or mathematical mechanics]
      * **Rubric:** [Explicit technical criteria required for full marks]
    - **Drill 3 (Boundary & Failure Mode):** [Question on when the framework breaks down]
      * **Rubric:** [Explicit technical criteria required for full marks]
    ---
    ## ⚖️ Model Boundary Conditions
    * Provide a concise Markdown table mapping failure modes:
    | Model / Framework | Validity Domain | Failure Trigger / Invalidation | Robust Alternative |
    | :--- | :--- | :--- | :--- |
    | [Model Name] | [Core assumptions] | [Condition where estimator/model breaks] | [Methodological fix] |
- Language & Tone: British English exclusively. Direct, rigorous, academic tone. Output ONLY the finalized study notes without conversational meta-commentary or tags.
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
Deconstruct and synthesize the provided academic document (paper, book chapter, or report) on {subject} into rigorous, high-density study notes with a clear logical progression and zero fluff:
1. Research Question & Empirical Gap: Identify the fundamental market failure, theoretical limitation, or identification problem the work addresses — stated crisply without introductory padding.
2. Foundational Anchoring & Pedagogical Calibration (Target Audience Invariant):
   - Assume the target reader has solid training in classical foundational disciplines (probability, expected value, variance, OLS regression, t-test, F-test, LLN, CLT; or systems architecture and hardware memory hierarchies), but is studying the specific specialized subject for the first time.
   - For every specialized framework or model, explicitly articulate **which baseline assumption breaks down and why** before presenting the advanced tool (e.g., cross-sectional independent draws -> single time trajectory; stationary regressors -> random walk variance exploding at T^2; i.i.d. errors -> serial correlation; spherical errors -> heteroskedasticity/clustering).
   - Disclose the underlying statistical or physical intuition for transformations and distribution shifts (e.g., why OLS suffers from downward Hurwicz bias by chasing sample means, why Said-Dickey parameterization isolates long-run scalar persistence while absorbing short-run nuisance dynamics in stationary differences, why deterministic dominance collapses non-standard distributions to standard Gaussian).
   - Explicitly state why choosing the wrong transformation/model is fatal (e.g., spurious regression vs over-differencing; lock contention vs memory thrashing).
3. Direct Technical Progression (Zero-Slop Transitions): Never use conversational or formulaic transition phrases ("As previously analyzed...", "Now turning to..."). Link concepts exclusively via their **Technical Delta**: state in exactly 1 direct sentence the precise theoretical, identification, or empirical limit of the preceding model that necessitates the new framework, then immediately present the corrective formulation. Maintain absolute economy of words: pure signal, zero introductory padding.
4. Uniform Analytical Caliber (Theoretical & Empirical Parity): Maintain identical formal depth across theoretical derivations and empirical estimates. Map empirical coefficients and test statistics directly to structural parameters, identification hypotheses ($H_0$), and asymptotic failure conditions. Never degrade empirical sections into descriptive walkthroughs.
5. End-to-End Methodological Continuity (Resolving Circular Dilemmas & Empirical Paradoxes):
   - Trace the causal necessity of diagnostic algorithms and identification sequences (e.g., sequential testing procedures, model selection criteria, lag pruning, downward testing). Explicitly formulate the **circular dilemma or structural trade-off** that mandates the procedure (e.g., testing deterministics requires knowing integration order, but testing integration order requires knowing deterministics).
   - Directly connect empirical paradoxes or edge cases (e.g., structural breaks in drift, near-unit roots, I(2) multiple roots, exclusion restriction violations) to the breakdown modes of the underlying estimators (e.g., how an omitted step break forces OLS to fit the jump with alpha_1 ≈ 1 or a spurious concave quadratic trend). Never leave an empirical contradiction unexplained.
6. Theoretical Framework & Mechanics: Formulate the core thesis, formal assumptions, and model mechanics with mathematical rigor and cause-effect links.
7. Selective Grounded Examples: Anchor abstract theoretical propositions or complex models with a concrete empirical scenario formatted with the mandatory example pattern ONLY when non-trivial.
8. Core Insights as Quotes: Elevate foundational theorems, identification conditions, or core economic laws into dedicated blockquotes (`>`). Maximum 1 quote per major section (`##`).
9. Mathematical Derivations & Computational Deconstruction: Provide step-by-step derivations. Whenever complex mathematical operators, asymptotic complexity claims, or computational bottlenecks appear, ground every variable into its concrete domain reality, explain the operation count mechanics, bridge the formulation to hardware/computational dynamics (e.g., Arithmetic Intensity, memory vs compute bounds), provide concrete numerical traces when non-trivial, and detail theoretical failure modes.
10. Boundary Conditions & Identification Threats: Clarify theoretical boundary conditions, identification threats, empirical limitations, and structural trade-offs.

Anti-Tautology & Symbolic Continuity: Explain each concept, parameter, or property ONCE at its primary introduction. When symbols, models, or state parameters are established, assume them as proven invariants and use them directly without re-explaining or re-defining them. Zero conversational padding, zero decorative throat-clearing, zero artificial elongation.
</task>

<formatting_rules>
- Hierarchy & Structure:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
  * Meaningful Granularity: Create `### [Emoji] Subsection Title` only when logically distinct models, estimators, or methodological stages are introduced. NEVER insert artificial subsections every few sentences or just to meet an arbitrary word target.
- Visual Separators: Add a single horizontal rule (---) before each ## section (except the first). NEVER add a horizontal rule before ### subsections. NEVER place consecutive or duplicate horizontal rules.
- High-Density Prose & Paragraph Flow:
  * Deliver explanations through focused, cohesive paragraphs of 2 to 4 sentences. Lead directly with the technical or theoretical mechanism; eliminate meta-introductions ("This paper investigates...", "It is important to emphasize that...").
  * Avoid both monolithic walls of text and vacuous, fragmented filler. Connect motivation, mechanics, and consequences in a tight logical chain.
  * Always ensure standard punctuation spacing: exactly one space after a period (`.`), comma (`,`), colon (`:`), or semicolon (`;`).
- Grounded Examples (Selective):
  * Format concrete empirical or applied illustrations in their own dedicated paragraph using the syntax:
    `**Example:** *[Concrete empirical case, market application, or quantitative illustration in italics detailing the exact setup and findings.]*`
  * Omit examples entirely for self-evident or purely definitional sections.
- Core Takeaways as Blockquotes:
  * Highlight the single most critical theoretical insight, identification condition, or core theorem of each section using a Markdown blockquote (max 1 per ## section):
    `> **Core Insight:** [Authoritative formulation capturing the fundamental theoretical or empirical takeaway.]`
- Lists & Boundaries:
  * Restrict bullet points (`-`) to concise enumerations of 3 to 6 items maximum (e.g., formal axioms, parameter definitions, or boundary conditions).
  * Once the list items are stated, IMMEDIATELY terminate the list and return to standard narrative paragraphs without bullet points. Do not continue bullet points for explanatory commentary.
  * Keep lists strictly distinct: use numbered lists (`1.`, `2.`) ONLY for sequential methodology steps or algorithms; use bullet points (`-`) ONLY for unordered attributes or axioms. NEVER mix numbered items and bullets within the same section.
- Emphasis: Highlight critical terms, theorems, definitions, and variables in **bold**.
- Mathematics & Formulas: Extract and explain all mathematical formulations. Format inline math with `$` (e.g., $L(\\theta)$) and display equations on standalone lines with `$$` (e.g., $$\\nabla_\\theta J(\\theta) = \\mathbb{{E}}[ \\dots ]$$). Never use code blocks for math.
  * Strict KaTeX Single-Backslash Formatting: Format all LaTeX equations with standard single backslashes (e.g., $\\tau_\\mu$, $\\Delta y_t$, $\\alpha_0$, $\\mathbb{{E}}$). NEVER emit escaped double backslashes (\\\\Delta, \\\\tau) inside math blocks, as KaTeX interprets '\\\\' as an internal line break and corrupts rendering.
  * Backtick Hygiene: Ensure all inline code backticks are strictly matched and closed. Never leave empty backticks (``) or unclosed backticks that inadvertently engulf text or mathematical equations into raw monospace blocks.
  * Complex Operations & Deconstructions: When introducing foundational mathematical operations, computational complexity bounds, or algorithmic mechanisms, format them under a dedicated subsection: `### 🧮 Mathematical Deconstruction: [Concept Name]`, systematically providing physical variable mapping, step-by-step derivation, operational count, and boundary failure modes.
- Code & Algorithms: Format pseudo-code or algorithms inside fenced code blocks with language identifiers (e.g., ```python, ```r).
- Visual Diagrams & Figures (CRITICAL FORMATTING INVARIANT):
  * If the document contains a critical architecture diagram, empirical plot, or structural matrix that cannot be rendered losslessly via LaTeX or Markdown tables, insert an image reference at the exact logical point of discussion.
  * MANDATORY STANDALONE BLOCK: The image reference MUST ALWAYS be placed on its own standalone line with empty lines before and after. Format:
    
    ![](figure://slide_N)
    
  * PAGE INTEGRITY (NO ARBITRARY CROPPING): Always extract the full page without coordinate crops (do NOT use ?crop=...). Extracting the full page preserves all axes, labels, and mathematical annotations without truncation.
  * STRICT PROHIBITION ON INLINE CITATIONS: NEVER write inline references or citations such as `(figure://slide_N)`, `(slide N)`, `(figura N)`, or `(vedi slide N)` inside sentences, headers, or bullet points. All figures must be isolated standalone image lines. Keep the prose completely clean and flowing.
  * ZERO BOILERPLATE CAPTIONS: Do NOT write generic captions like "Figura slide N" or "Slide N". Leave the figure reference clean as `![](figure://slide_N)`.
  * Only select figures that carry high theoretical or empirical signal. Zero screenshots of pure text pages.
- References: Consolidate formal bibliographic citations in a final `### 📚 References` section. No inline citations in the body.
- Study Artifacts & Conceptual Maps (Mandatory Append Section):
  * Conclude the paper synthesis with the following three high-signal study sections:
    ---
    ## 🧠 Conceptual Architecture & Relational Graphs
    * Provide a Mermaid Conceptual Taxonomy Tree (`graph TD`) mapping the paper's conceptual taxonomy with hierarchical pastel levels:
    ```mermaid
    graph TD
      classDef rootNode fill:#0f172a,stroke:#334155,stroke-width:2px,color:#fff;
      classDef level1 fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px,color:#1e3a8a;
      classDef level2 fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1.2px,color:#4c1d95;
      classDef level3 fill:#f0fdf4,stroke:#10b981,stroke-width:1px,color:#064e3b;

      ROOT(["Paper Core"]):::rootNode
      P1["Theoretical Framework"]:::level1
      P2["Empirical Identification"]:::level1
      M1["Assumptions"]:::level2
      M2["Equilibrium"]:::level2
      S1["Methodology"]:::level2
      S2["Causal Mechanism"]:::level2

      ROOT --> P1
      ROOT --> P2
      P1 --> M1
      P1 --> M2
      P2 --> S1
      P2 --> S2
    ```
    * Provide a Mermaid flowchart (`graph TD`) mapping the primary causal chain or identification tree. Follow these VISUAL & MATHEMATICAL standards:
      1. **Color Coding by Topic (NOT by Grouping/Box)**: Style nodes by their conceptual nature / topic across the entire paper, NOT monochromatic by subgraph box. Use semantic pastel fills with distinct border strokes:
         - **Theory & Identification**: `classDef theoryNode fill:#eff6ff,stroke:#3b82f6,color:#1e3a8a;` (identification hypotheses, structural equations, estimators).
         - **Empirical Channels & Mechanics**: `classDef pipelineNode fill:#f5f3ff,stroke:#8b5cf6,color:#4c1d95;` (transmission channels, data variation, sample cuts).
         - **Controls & Econometric Robustness**: `classDef devopsNode fill:#f0fdf4,stroke:#10b981,color:#064e3b;` (fixed effects, clusters, balance checks).
         - **Threats to Validity & Boundary Failures**: `classDef bottleneckNode fill:#fff1f2,stroke:#f43f5e,color:#881337;` (exclusion restriction violations, weak instruments, endogeneity).
      2. **Strict Text Formatting (NO HTML)**:
         - NEVER use HTML tags (`<span>`, `<b>`, `<i>`, `<br/>`, `<br>`, etc.) inside Mermaid nodes or subgraph titles. Notion and ELK layout engines fail on HTML tags with layout null pointer exceptions.
         - For multi-line labels, separate concepts with hyphens (` - `) or concise phrases entirely wrapped in double quotes: `NodeID["Clean Descriptive Title - Secondary Detail"]`.
         - ALWAYS wrap ALL node labels in double quotes (e.g. `NodeID["Label Text"]`, `NodeID("Rounded Label")`, `NodeID{{"Condition"}}`).
         - In edge labels (`|label|`), use concise words without parentheses or angle brackets (`<`, `>`).
      3. **Formal Mathematical Notation**: In diagrams, format mathematical complexities and variables using clean Unicode math notation instead of ASCII approximations (e.g. `O(m × n × k) ≈ O(N³)` instead of `O(N^3)`, `O(log N)`, `(K₁, V₁)`, `∑`, `β̂`, `λ`, `->`).
      4. **Topology & Subgraph Rules**:
         - Connect STRICTLY node-to-node (`NodeA --> NodeB`). NEVER connect an edge to or from a subgraph container directly.
         - If using subgraphs, always specify an alphanumeric ID: `subgraph SG_ID ["Subgraph Title"]`.
         - NEVER apply `style` directly to subgraph IDs (e.g. `style SG_ID ...` is forbidden as it causes Notion layout crashes).
         - Cross-subgraph edges MUST be declared outside/after the subgraph blocks at root level, never nested inside individual subgraphs.
         - Use standard edge labels with vertical pipes: `-->|label|`, never `-- "label" -->`.
      5. **Strict Vertical Flow & Width Budget (Anti-Shrink Guarantee)**:
         - Notion constrains diagrams to a narrow column width (700-900px). Diagrams with wide horizontal sprawl or subgraphs placed side-by-side shrink proportionally, making text microscopic and unreadable.
         - STRICTLY use `graph TD` (Top-Down). NEVER use `graph LR` (Left-to-Right).
         - NEVER declare multiple subgraphs in parallel side-by-side. Stack all subgraphs sequentially in a single vertical column (`SG_1 --> SG_2 --> SG_3`).
         - Inside each subgraph, chain nodes vertically in a single sequence (`Node1 --> Node2 --> Node3`) or allow at most 2 parallel branches across the rank.
         - Keep node labels strictly compact (max 25-28 characters per node, e.g. 'Layered EA Models', 'Serving & Realisation'). Labels exceeding 30 characters cause Notion's SVG layout engine to overflow and physically clip words against the right border of the node rectangle.
    ```mermaid
    graph TD
      classDef rootNode fill:#0f172a,stroke:#334155,stroke-width:2.5px,color:#fff;
      classDef theoryNode fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px,color:#1e3a8a;
      classDef pipelineNode fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1.5px,color:#4c1d95;
      classDef bottleneckNode fill:#fff1f2,stroke:#f43f5e,stroke-width:1.5px,color:#881337;

      ROOT["Empirical Strategy - Identification Architecture"]:::rootNode

      subgraph SG_ID ["Identification Design"]
        Shock["Exogenous Variation (Z) - Instrument discontinuity"]:::theoryNode
        Channel["Transmission Channel (D) - Compliance and response"]:::pipelineNode
        Lim["Violation of Exclusion Restriction - Direct unobserved channel"]:::bottleneckNode
      end

      ROOT --> Shock
      Shock --> Channel
      Channel --> Lim
    ```
    ---
    ## 🎯 Active Recall & Examination Drills
    * Formulate 3 to 5 rigorous, examination-grade questions targeting analytical friction points:
    - **Drill 1 (Foundational):** [Core conceptual question]
      * **Rubric:** [Explicit technical criteria required for full marks]
    - **Drill 2 (Analytical Derivation):** [Question on econometric or mathematical mechanics]
      * **Rubric:** [Explicit technical criteria required for full marks]
    - **Drill 3 (Boundary & Failure Mode):** [Question on when the framework breaks down]
      * **Rubric:** [Explicit technical criteria required for full marks]
    ---
    ## ⚖️ Model Boundary Conditions
    * Provide a concise Markdown table mapping failure modes:
    | Model / Framework | Validity Domain | Failure Trigger / Invalidation | Robust Alternative |
    | :--- | :--- | :--- | :--- |
    | [Model Name] | [Core assumptions] | [Condition where estimator/model breaks] | [Methodological fix] |
- Language & Tone: British English exclusively. Direct, rigorous, academic tone. Output ONLY the finalized notes without conversational padding or tags.
</formatting_rules>

<input_data>
Please analyze and distill the following {subject} document:
</input_data>
""".strip()


# ARCHITETTURA: Template per il secondo stage (Two-Stage Decoupled Mode).
# Viene invocato unicamente quando il documento originale supera la soglia di densità
# (es. >50 slide o >40k caratteri), estraendo gli artefatti dal markdown di staging
# a costo di input token minimo senza re-ingestire il file binario originale.
TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT = """
<role>
You are an Academic Knowledge Architect and Senior Quantitative Pedagogist in {subject}.
</role>

<task>
Deconstruct the provided synthesized study notes into high-signal conceptual study artifacts:
1. Mermaid Conceptual Taxonomy Tree (`graph TD`): A clean, hierarchical taxonomy of core pillars and sub-concepts (depth 3-4) using hierarchical pastel classDef styling (`rootNode`, `level1`, `level2`, `level3`, `levelN`).
2. Mermaid Flowchart (`graph TD`): The core cause-and-effect chain, empirical transmission mechanism, or identification flowchart. Follow these visual and mathematical standards:
   - **Color Coding by Topic (NOT by Grouping/Box)**: Style nodes by their conceptual nature / topic across the entire architecture, NOT monochromatic by subgraph box. Use semantic pastel fills (theory/definitions in blue, compute/hardware in amber, pipelines/flow in purple, engineering/storage in green, bottlenecks/failure modes in coral).
   - **Strict Text Formatting (NO HTML)**: NEVER use HTML tags (`<span>`, `<b>`, `<br/>`, etc.) in node labels or subgraph titles. Wrap all labels in double quotes. For multi-line labels, use ` - ` or concise phrases.
   - **Formal Mathematical Notation**: In diagrams, format mathematical complexities and variables using clean Unicode math notation instead of ASCII approximations (e.g. `O(m × n × k) ≈ O(N³)` instead of `O(N^3)`, `O(log N)`, `(K₁, V₁)`, `∑`, `β̂`, `λ`, `->`).
   - **Topology & Subgraph Rules**: Connect STRICTLY node-to-node (`NodeA --> NodeB`). NEVER connect an edge to or from a subgraph container directly. If using subgraphs, always specify an alphanumeric ID: `subgraph SG_ID ["Subgraph Title"]`. NEVER apply `style` to subgraph IDs (`style SG_ID` is forbidden). Declare cross-subgraph edges outside subgraphs at root level. Use `-->|label|` for edge labels.
   - **Strict Vertical Flow & Width Budget (Anti-Shrink Guarantee)**: Notion renders code blocks in a narrow reading column (~700-900px). NEVER use `graph LR`. STRICTLY use `graph TD`. Never place multiple subgraphs in parallel side-by-side. Stack all subgraphs sequentially in a single vertical column (`SG_1 --> SG_2 --> SG_3`). Inside each subgraph, chain nodes vertically in a single sequence. Keep node labels strictly compact (max 25-28 characters per node). Labels exceeding 30 characters cause Notion's SVG layout engine to overflow and clip words against the right border of the rectangle.
3. Active Recall & Examination Drills: 3 to 5 examination-grade analytical questions with explicit evaluation rubrics.
4. Model Boundary Conditions: A Markdown table mapping frameworks, validity domains, breakdown triggers, and robust alternatives.

Format the output strictly as the following 3 Markdown sections:

---
## 🧠 Conceptual Architecture & Relational Graphs
```mermaid
graph TD
  classDef rootNode fill:#0f172a,stroke:#334155,stroke-width:2px,color:#fff;
  classDef level1 fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px,color:#1e3a8a;
  classDef level2 fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1.2px,color:#4c1d95;
  classDef level3 fill:#f0fdf4,stroke:#10b981,stroke-width:1px,color:#064e3b;

  ROOT(["Lecture Core"]):::rootNode
  P1["Pillar 1"]:::level1
  P2["Pillar 2"]:::level1
  ...
```

```mermaid
graph TD
  ...
```

---
## 🎯 Active Recall & Examination Drills
- **Drill 1 (Foundational):** ...
  * **Rubric:** ...
- **Drill 2 (Analytical Derivation):** ...
  * **Rubric:** ...
- **Drill 3 (Boundary & Failure Mode):** ...
  * **Rubric:** ...

---
## ⚖️ Model Boundary Conditions
| Model / Framework | Validity Domain | Failure Trigger / Invalidation | Robust Alternative |
| :--- | :--- | :--- | :--- |
| ... | ... | ... | ... |
</task>

<constraints>
- British English exclusively.
- Output ONLY the requested Markdown sections without any conversational meta-commentary.
- Formulas inside text must use standard LaTeX ($...$). In Mermaid diagrams, use Unicode math notation (e.g. `O(N³)`, `β̂`, `(K₁, V₁)`).
- In Mermaid taxonomy trees and flowcharts, connect strictly node-to-node (`NodeA --> NodeB`), never use HTML tags, never style subgraph containers (`style SG_ID` is strictly prohibited), and declare cross-subgraph edges at root level outside subgraphs.
</constraints>

<input_study_notes>
{notes_markdown}
</input_study_notes>
""".strip()


def get_prompt_template(
    doc_type_value: str,
    subject: str,
    professor_type: str,
    include_study_artifacts: bool = True
) -> str:
    """
    Ritorna il prompt compilato con materia e ruolo in base al tipo di documento.
    # TRADE-OFF: Se include_study_artifacts è False (attivato nella prima chiamata della modalità
    # Two-Stage), rimuoviamo le sezioni di append per dedicare il 100% dell'output token budget
    # alla trattazione analitica del capitolo, prevenendo troncamenti anticipati.
    """
    template = (
        PAPER_OR_BOOK_PROMPT_TEMPLATE
        if doc_type_value == "paper_or_book"
        else SLIDES_PROMPT_TEMPLATE
    )
    rendered = template.format(subject=subject, professor_type=professor_type)
    if not include_study_artifacts:
        # Rimozione selettiva della sezione append per lo Stage 1 della modalità Two-Stage
        pattern_start = "- Study Artifacts & Conceptual Maps (Mandatory Append Section):"
        if pattern_start in rendered:
            parts = rendered.split(pattern_start)
            # Ricollega le regole preservando Language & Tone finale
            end_rules = parts[1].split("- Language & Tone:")
            if len(end_rules) > 1:
                rendered = parts[0] + "- Language & Tone:" + end_rules[1]
    return rendered


def get_artifacts_extraction_prompt(subject: str, notes_markdown: str) -> str:
    """
    Ritorna il prompt per lo Stage 2 della modalità Two-Stage, compilato con materia
    e il markdown precedentemente sintetizzato in staging.
    """
    return TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT.format(
        subject=subject,
        notes_markdown=notes_markdown
    )
