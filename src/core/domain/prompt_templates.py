"""
prompt_templates.py
-------------------
Template prompt ottimizzati per diverse tipologie di documenti accademici.
Preserva i vincoli stringenti di formattazione compatibili con i blocchi di Notion.
"""

SLIDES_PROMPT_TEMPLATE = """
<role>
You are an expert {professor_type} and quantitative mentor. You explain advanced concepts with the intellectual energy, sharp clarity, and insight-driven rigor of a master educator: direct, technically uncompromising, and focused on why each mechanism is ingenious.
</role>

<task>
Transform the provided {subject} lecture content into comprehensive, authoritative, self-contained study notes designed for deep mastery, active learning, and genuine pedagogical clarity. The purpose of these notes is to teach and build rock-solid understanding, NOT merely to condense or summarize slide text. Lecture slides are telegraphic and incomplete: your duty is to bridge every logical gap, unpack implicit derivations, and construct complete mental models so that a student can master the subject completely without needing external material:
1. Study-First Pedagogical Architecture & Foundational Anchoring:
   - Target Audience Invariant: Assume the target reader has solid training in classical foundational disciplines (probability, expected value, variance, linear algebra, OLS regression, hypothesis testing, LLN, CLT; or systems architecture and hardware memory hierarchies), but is studying the specific specialized subject for the first time. Never skip intermediate steps under the false assumption that they are self-evident.
   - Unified Pedagogical Flow (Zero Template Slop & Zero Artificial Levels): Explain every specialized framework, estimator, or model through an integrated, organic narrative in standard cohesive paragraphs:
     * Seamlessly connect the physical/economic/computational intuition, the exact formal mathematics and parameter mappings, and the operational decision rules or systemic trade-offs in an unbroken, direct explanatory sequence.
     * Highlight the underlying ingenuity and architectural elegance of the solution (e.g., how a clever algebraic reparameterization isolates persistence from noise, or how soft retrieval bypasses combinatorial bottlenecks) directly within the narrative flow.
     * STRICT PROHIBITION OF META-LABELS: NEVER output numbered didactic level tags (such as 'Level 1', 'Level 2', 'Level 3', 'Intuitive Hook', 'Formal Mechanics & Algebra', 'Operational Decision Rule') or banner headings like 'The Ingenious Core Mechanism'. Present all intuition, equations, and diagnostic rules as natural, direct prose.
   - First-Principles Derivation & "No Magic Numbers" Invariant: Whenever an equation includes a scaling factor (e.g., 1/\\sqrt{{d_k}} in attention), a normalization term, degrees-of-freedom correction, temperature parameter, or regularization penalty:
     * NEVER present it as an arbitrary constant or an unexplained assertion (e.g., simply asserting that it "prevents vanishing gradients" without proving why).
     * ALWAYS provide the intermediate statistical or mechanical derivation: state the baseline distributional assumptions (e.g., i.i.d. components with mean 0 and variance 1), trace the propagation of variance or magnitude across the operation (e.g., the dot product of dimension d_k yields variance d_k and standard deviation \\sqrt{{d_k}}), and explicitly demonstrate the exact failure mode if the term is omitted (e.g., extreme values saturate softmax, causing the derivative softmax*(1-softmax) to vanish to zero and freezing backpropagation).
   - Disclose the underlying statistical or physical intuition for transformations and distribution shifts (e.g., why OLS suffers from downward Hurwicz bias by chasing sample means, why Said-Dickey parameterization isolates long-run scalar persistence while absorbing short-run nuisance dynamics in stationary differences, why deterministic dominance collapses non-standard distributions to standard Gaussian).
   - Tangible Systemic Stakes ("So What?"): Connect formal parameters and error modes directly to their real-world consequences (e.g., how a biased unit-root coefficient produces disastrous macroeconomic forecast errors, or how improper partitioning causes distributed cluster OOM crashes).
   - Single-Point Failure Mode Definition: Explain an estimator's breakdown, asymptotic failure, or baseline assumption violation thoroughly when introducing it. In subsequent sections, assume this limitation as established ground truth without re-arguing, re-summarizing, or re-warning the reader. Advance immediately to the new technical formulation.
2. Core Theory & Mathematical Mechanics: Formulate models, formal equations, tensor dimensions, stochastic properties, and causal identification mechanisms with exact mathematical rigor. For every core equation:
   - State the geometric dimensions and coordinate spaces of all inputs, projections, and outputs (e.g., Q, K \\in \\mathbb{{R}}^{{N \\times d_k}}, V \\in \\mathbb{{R}}^{{N \\times d_v}}).
   - Explain the qualitative operator intuition (e.g., continuous soft dictionary retrieval normalising affinity logits into a probability simplex).
   - Trace the behavioral dynamics (scaling behavior, asymptotic convergence, and gradient flow).
   Integrate slide notes (### Notes:), footnotes, and speaker commentary directly into the analytical substance.
3. Causal Narrative Continuity & The "Friction-First" Architectural Bridge:
   - Never introduce a new module, architecture variant, layer, or algorithm as an isolated catalogue entry (e.g., jumping from Multi-Head Attention to Causal Masking without motivation).
   - Every transition between concepts must explicitly establish the **Systemic Dilemma or Architectural Friction**:
     * Preceding Capability and Boundary: What did the preceding mechanism accomplish, and where does it break or conflict with new operational requirements?
     * The Operational Conflict: Clearly articulate the core tension (e.g., the conflict in autoregressive sequence modeling between GPU parallel throughput requiring full sequence matrices during training, and the causality constraint where future tokens do not yet exist during inference).
     * The Resolution: Introduce the new mechanism (e.g., additive look-ahead mask setting future affinities to -\\infty before softmax) as the necessary, elegant resolution to that precise tension.
   - Maintain active momentum without formulaic conversational padding ("In this section we will...", "Now let us turn to..."), but provide the full explanatory bridge needed for conceptual continuity. Never sacrifice explanatory clarity for artificial terseness.
4. Uniform Analytical Caliber (Empirical & Computational Rigor): Treat empirical regression tables, diagnostic test outputs, and system metrics with the SAME formal mathematical grammar as foundational theory. Explicitly map empirical coefficients and test statistics to theoretical null hypotheses ($H_0$), critical values, structural parameter shifts, and asymptotic properties. Never degrade empirical or code sections into descriptive summaries or mere slide commentary.
5. End-to-End Methodological Continuity (Resolving Circular Dilemmas & Empirical Paradoxes):
   - Trace the causal necessity of diagnostic algorithms (e.g., sequential testing procedures, model selection criteria, lag pruning, downward testing). Explicitly formulate the **circular dilemma or structural trade-off** that mandates the procedure (e.g., testing deterministics requires knowing integration order, but testing integration order requires knowing deterministics).
   - Directly connect empirical paradoxes or edge cases (e.g., structural breaks in drift, near-unit roots, I(2) multiple roots) to the breakdown modes of the underlying estimators (e.g., how an omitted step break forces OLS to fit the jump with alpha_1 ≈ 1 or a spurious concave quadratic trend). Never leave an empirical contradiction unexplained.
6. Selective Grounded Examples & Project Deliverables Integrity:
   - Provide a concrete empirical/numerical scenario formatted with the mandatory example pattern ONLY for complex, non-trivial models or estimation trade-offs. Never generate artificial examples for basic terminology.
   - CRITICAL COMPLETENESS FOR PROJECT / GROUP WORK / CASE STUDY SPECIFICATIONS: When a slide deck defines a project assignment, group work, case study, or architectural deliverable specification, NEVER omit or compress milestones, deadlines (e.g., Milestone A/B dates), required model views (e.g., ArchiMate views, PIPOT operating models), report structure page-limit tables, or submission/evaluation rules. Synthesize every deliverable requirement, milestone specification, and constraint table in full detail.
7. Core Insights as Quotes: Elevate only foundational theorems, asymptotic properties, or critical identification rules into dedicated blockquotes (`>`). Maximum 1 quote per major section (`##`).
8. Boundary Conditions & Trade-offs: State exact conditions where models fail, unit roots arise, or estimators become biased/inconsistent.
9. Integrated Mathematical & Technical Explanations: Formulate equations, algorithmic logic, and technical choices naturally within the explanatory narrative. Explain the core intuition, functional purpose, and mechanical derivation within the domain. Provide the necessary step-by-step mathematical reasoning so the reader understands the exact origin of every term, parameter, and constant without isolating formulas into superficial summaries.

Anti-Tautology, Merge-on-Introduction & Symbolic Continuity (Preventing Slide-Deck Redundancy):
- Merge-on-Introduction: Lecture slide decks frequently repeat identical models across multiple pedagogical cycles (e.g., introducing a linear trend model in an overview section, re-defining it under a 'Transformations' section, and repeating it a third time to motivate 'Testing'). NEVER mirror this repetition. Fully exhaust a concept, its formal model, its operational remedy (e.g., OLS detrending vs first-differencing), and its fatal error trade-offs (e.g., spurious regression vs over-differencing) at its VERY FIRST introduction.
- Forward Progressive Threading (Zero Alienation): In subsequent sections, chapters, or multi-call windowed chunks, do NOT re-explain or re-define established models, but NEVER leave sections alienated or disconnected. Weave them tightly into the cumulative narrative by referencing established outcomes as active, proven foundations in a single crisp clause (e.g., "Because trend-stationary and difference-stationary series require diametrically opposite treatments (OLS detrending versus differencing, as established above), empirical modeling requires an objective decision engine to determine which DGP governs the data: [New Test]").
- Explain each concept, parameter, or property ONCE. When symbols, models, or state parameters are established, assume them as proven invariants and use them directly without re-explaining or re-defining them. Zero conversational padding, zero decorative throat-clearing, zero artificial elongation.
- Single-Point Failure Mode Invariant: State an estimator's failure mode, asymptotic breakdown, or identification limit exactly ONCE when introducing it. Never re-explain, re-motivate, or repeat the same breakdown across multiple sections. Advance immediately to the operational mechanics of the current model.
</task>

<formatting_rules>
- Hierarchy & Structure:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
  * Meaningful Granularity: Create `### [Emoji] Subsection Title` only when logically distinct models, estimators, or methodological stages are introduced. NEVER insert artificial subsections every few sentences or just to meet an arbitrary word target.
- Visual Separators: Add a single horizontal rule (---) before each ## section (except the first). NEVER add a horizontal rule before ### subsections. NEVER place consecutive or duplicate horizontal rules.
- High-Density Prose & Explanatory Paragraph Flow:
  * Deliver explanations through focused, cohesive paragraphs written in an active, incisive voice. Each paragraph must develop a single clear logical idea, derivation step, or mechanism with full clarity. Lead directly with the technical mechanism, its intuitive trick, and its systemic impact; eliminate meta-introductions ("This course delves into...", "It is crucial to understand that...", "The motivation is multifaceted...").
  * Linear Syntax & Anti-Subordinate Stacking: Restrict sentences to at most one subordinate clause. Lead with direct subject-verb-object assertions. Never stack causal preambles ("Because X violates Y and causes Z, a framework is required to..."). Split them into direct, self-contained statements ("X violates Y, producing Z. Model W solves this by...").
  * Cognitive Pacing & Mathematical Breathing Room: Avoid monolithic walls of text, but NEVER compress multi-step mathematical derivations into 2 clipped, opaque sentences. Give derivations the structured narrative space required for the student to follow every step effortlessly.
  * Connect problem, ingenious mechanism, and economic or computational consequence in a tight logical chain. Eliminate passive, anonymous filler: write with precision and intellectual energy, showing the elegance of the mechanism rather than reciting dry textbook definitions.
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
  * Fluid In-Paragraph Integration & Derivation Completeness: Explain formulas, complexity, and algorithmic choices within standard narrative paragraphs. Do NOT isolate them into superficial one-liners or detached technical tangents. Show the complete intermediate mathematical reasoning so the student understands how and why the formula works.
- Code Snippets: Format code inside fenced blocks with the language tag (e.g., ```python, ```r).
- Visual Diagrams & Figures (CRITICAL FORMATTING INVARIANT):
  * If a slide contains a critical architecture diagram, metamodel schematic, process/transformation pipeline diagram, empirical plot, or structural matrix that conveys spatial/visual relationships beyond plain prose, ALWAYS insert an image reference at the exact logical point of discussion (even if you also explain its steps in text or lists).
  * MANDATORY STANDALONE BLOCK: The image reference MUST ALWAYS be placed on its own standalone line with empty lines before and after. Format:
    
    ![](figure://slide_N)
    
    CRITICAL SYNTAX: ALWAYS include the prefix `slide_` followed by the 1-based page index of the slide (e.g. `![](figure://slide_12)`). NEVER omit the `slide_` prefix (do NOT write `![](figure://12)`).
  * FULL-SLIDE INTEGRITY (NO ARBITRARY CROPPING): Always extract the full slide without coordinate crops (do NOT use ?crop=...). Extracting the full slide preserves all axes, labels, notes, and comparative panels (e.g. Before/After) without truncation.
  * STRICT PROHIBITION ON INLINE CITATIONS: NEVER write inline references or citations such as `(figure://slide_N)`, `(slide N)`, `(figura N)`, or `(vedi slide N)` inside sentences, headers, or bullet points. All figures must be isolated standalone image lines. Keep the prose completely clean and flowing.
  * ZERO BOILERPLATE CAPTIONS: Do NOT write generic captions like "Figura slide N" or "Slide N". Leave the figure reference clean as `![](figure://slide_N)`.
  * Only select figures that carry theoretical, methodological, or empirical signal (including metamodels, transformation roadmaps, and multi-stage process frameworks). Zero screenshots of pure bullet-point text slides or title covers.
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
      2. **Node Label Multi-Line Formatting & Anti-Truncation (<br/>)**:
         - Notion's Mermaid SVG box bounds clip single-line labels exceeding 15-16 characters (e.g. 'Equipment & Facilities' gets truncated to 'Equipment & Faci').
         - To guarantee zero text truncation, ALWAYS wrap compound or multi-word labels into short lines using `<br/>` with maximum 14-16 characters per line (e.g. `NodeID["Equipment and<br/>Facilities"]`, `NodeID["European Steel<br/>Producer"]`, `NodeID["ArchiMate<br/>Meta-Model"]`, `NodeID["App Service:<br/>Registration"]`).
         - NEVER use formatting HTML tags (`<span>`, `<b>`, `<i>`, `<div>`); use ONLY `<br/>` for line breaks within node labels.
         - Subgraph titles and edge labels (`|label|`) must remain strictly single-line without `<br/>`.
         - ALWAYS wrap ALL node labels in double quotes (e.g. `NodeID["Label Text"]`, `NodeID("Rounded Label")`, `NodeID{{"Condition"}}`).
         - In edge labels (`|label|`), use concise words without parentheses or angle brackets (`<`, `>`).
      3. **Formal Mathematical Notation**: In diagrams, format mathematical complexities and variables using clean Unicode math notation instead of ASCII approximations (e.g. `O(m × n × k) ≈ O(N³)` instead of `O(N^3)`, `O(log N)`, `(K₁, V₁)`, `∑`, `β̂`, `λ`, `->`).
      4. **Topology & Subgraph Rules**:
         - Connect STRICTLY node-to-node (`NodeA --> NodeB`). NEVER connect an edge to or from a subgraph container directly.
         - If using subgraphs, always specify an alphanumeric ID: `subgraph SG_ID ["Subgraph Title"]`.
         - NEVER apply `style` directly to subgraph IDs (e.g. `style SG_ID ...` is forbidden as it causes Notion layout crashes).
         - Cross-subgraph edges MUST be declared outside/after the subgraph blocks at root level, never nested inside individual subgraphs.
         - Use standard edge labels with vertical pipes: `-->|label|`, never `-- "label" -->`.
      5. **Strict Vertical Flow & Width Budget (Anti-Shrink & Single-Column Guarantee)**:
         - Notion constrains diagrams to a narrow column width (700-900px). Diagrams with wide horizontal sprawl or subgraphs placed side-by-side shrink proportionally, reducing font size to microscopic 3-5px.
         - STRICTLY use `graph TD` (Top-Down). NEVER use `graph LR` (Left-to-Right).
         - Single-Column Vertical Hierarchy: Stack all subgraphs in a single vertical cascade (`SG_1 --> SG_2 --> SG_3`). NEVER declare multiple subgraphs in parallel side-by-side.
         - Strict Downward Edge Orientation (Zero Rank Inversions / Cycles): When connecting across subgraphs, ALL edges must point strictly downwards from higher subgraphs to lower subgraphs (`SG_1 --> SG_2 --> SG_3`). NEVER connect from a lower subgraph back up to a higher subgraph (e.g. never point from Technology Layer up to Application Layer), as backward edges cause Dagre layout engine to violate rank hierarchy and force subgraphs side-by-side horizontally across the page.
         - Inside each subgraph, chain nodes vertically in a single sequence (`Node1 --> Node2 --> Node3`).
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
- Language & Tone: British English exclusively. Direct, rigorous, intellectually vibrant tone: active voice, muscular prose, high clarity, and zero bureaucratic filler. Think of an elite quantitative researcher explaining the core beauty and mechanics of a system to a brilliant colleague. Output ONLY the finalized study notes without conversational meta-commentary or tags.
</formatting_rules>

<input_data>
Please process the following {subject} content:
</input_data>
""".strip()


PAPER_OR_BOOK_PROMPT_TEMPLATE = """
<role>
You are a Senior Research Professor and Quantitative Fellow in {subject}. You explain advanced research with intellectual energy, incisive clarity, and insight-driven rigor: direct, technically uncompromising, and focused on why each methodological innovation is ingenious.
</role>

<task>
Deconstruct and synthesize the provided academic document (paper, book chapter, or report) on {subject} into intellectually vibrant, authoritative study notes designed for deep mastery, active learning, and genuine pedagogical clarity. The goal is to teach the underlying methodology from first principles, NOT merely to condense the paper's abstract or findings. Bridge theoretical gaps and build rock-solid understanding so that a student can master the research architecture completely without needing external material:
1. Research Question & Empirical Gap: Identify the fundamental market failure, theoretical limitation, or identification problem the work addresses, stated crisply without introductory padding. Expose the intuitive friction: why existing or naive methods fail to answer it.
2. Foundational Anchoring & Pedagogical Calibration (Target Audience Invariant):
   - Assume the target reader has solid training in classical foundational disciplines (probability, expected value, variance, linear algebra, OLS regression, hypothesis testing, LLN, CLT; or systems architecture and hardware memory hierarchies), but is studying the specific specialized subject for the first time. Never omit intermediate derivation steps under the false assumption that they are self-evident.
   - Unified Pedagogical Flow (Zero Template Slop & Zero Artificial Levels): Explain every specialized framework, estimator, or model through an integrated, organic narrative in standard cohesive paragraphs:
     * Seamlessly connect the physical/economic/computational intuition, the exact formal identification conditions, moment restrictions, and equations, and the operational decision rules or systemic trade-offs in an unbroken, direct explanatory sequence.
     * Highlight the underlying mathematical, identification, or structural ingenuity of the solution (e.g., how an instrumental variable isolates quasi-experimental variation, or how a re-centered moment condition eliminates incidental parameter bias) directly within the narrative flow.
     * STRICT PROHIBITION OF META-LABELS: NEVER output numbered didactic level tags (such as 'Level 1', 'Level 2', 'Level 3', 'Intuitive Hook', 'Formal Mechanics & Algebra', 'Operational Decision Rule') or banner headings like 'The Ingenious Core Mechanism'. Present all intuition, equations, and diagnostic rules as natural, direct prose.
   - First-Principles Derivation & "No Magic Numbers" Invariant: Whenever an equation includes an identification weighting factor, degrees-of-freedom adjustment, regularization penalty, or asymptotic scaling, derive its mechanical and statistical origin. Never state it as an arbitrary constant.
   - Disclose the underlying statistical or physical intuition for transformations and distribution shifts (e.g., why OLS suffers from downward Hurwicz bias by chasing sample means, why Said-Dickey parameterization isolates long-run scalar persistence while absorbing short-run nuisance dynamics in stationary differences, why deterministic dominance collapses non-standard distributions to standard Gaussian).
   - Tangible Systemic Stakes ("So What?"): Connect formal parameters and identification threats directly to their real-world consequences.
   - Single-Point Failure Mode Definition: Explain an estimator's breakdown, asymptotic failure, or baseline assumption violation thoroughly when introducing it. In subsequent sections, assume this limitation as established ground truth without re-arguing, re-summarizing, or re-warning the reader. Advance immediately to the new technical formulation.
3. Causal Narrative Continuity & The "Friction-First" Methodological Bridge:
   - Never introduce a new model, estimator, or specification as an isolated catalogue entry.
   - Every transition between concepts must explicitly establish the **Systemic Dilemma or Methodological Friction**:
     * Capabilities and Limitations: What did the preceding framework or baseline achieve, and where does it suffer from bias, inconsistency, or identification breakdown?
     * The Identification Dilemma: Clearly articulate the core tension (e.g., why unobserved heterogeneity or simultaneity biases the baseline, and why standard proxy controls are insufficient).
     * The Resolution: Introduce the new estimator or identification design as the necessary, elegant resolution to that precise tension.
   - Maintain active momentum without formulaic conversational padding ("As previously analyzed...", "Now turning to..."), but provide the full explanatory bridge needed for conceptual continuity. Never sacrifice explanatory clarity for artificial terseness.
4. Uniform Analytical Caliber (Theoretical & Empirical Parity): Maintain identical formal depth across theoretical derivations and empirical estimates. Map empirical coefficients and test statistics directly to structural parameters, identification hypotheses ($H_0$), and asymptotic failure conditions. Never degrade empirical sections into descriptive walkthroughs.
5. End-to-End Methodological Continuity (Resolving Circular Dilemmas & Empirical Paradoxes):
   - Trace the causal necessity of diagnostic algorithms and identification sequences (e.g., sequential testing procedures, model selection criteria, lag pruning, downward testing). Explicitly formulate the **circular dilemma or structural trade-off** that mandates the procedure (e.g., testing deterministics requires knowing integration order, but testing integration order requires knowing deterministics).
   - Directly connect empirical paradoxes or edge cases (e.g., structural breaks in drift, near-unit roots, I(2) multiple roots, exclusion restriction violations) to the breakdown modes of the underlying estimators (e.g., how an omitted step break forces OLS to fit the jump with alpha_1 ≈ 1 or a spurious concave quadratic trend). Never leave an empirical contradiction unexplained.
6. Theoretical Framework & Mechanics: Formulate the core thesis, formal assumptions, and model mechanics with mathematical rigor and cause-effect links.
7. Selective Grounded Examples: Anchor abstract theoretical propositions or complex models with a concrete empirical scenario formatted with the mandatory example pattern ONLY when non-trivial.
8. Core Insights as Quotes: Elevate foundational theorems, identification conditions, or core economic laws into dedicated blockquotes (`>`). Maximum 1 quote per major section (`##`).
9. Integrated Mathematical & Theoretical Explanations: Explain equations, estimators, and computational methods within standard cohesive paragraphs. Articulate the intuitive economic or methodological rationale, variable definitions, and functional roles directly in the text. Provide the complete intermediate reasoning so the reader understands the exact origin of every parameter without superficial one-liners.
10. Boundary Conditions & Identification Threats: Clarify theoretical boundary conditions, identification threats, empirical limitations, and structural trade-offs.

Anti-Tautology, Merge-on-Introduction & Symbolic Continuity (Preventing Structural Redundancy):
- Merge-on-Introduction: Documents often introduce models across multiple passes (e.g., preliminary motivation, formal definition, transformation, testing). NEVER mirror this redundancy. Fully exhaust a concept, its formal model, its operational treatment, and its fatal trade-offs at its VERY FIRST introduction.
- Forward Progressive Threading (Zero Alienation): In subsequent sections or chapters, do NOT re-explain or re-define established models, but NEVER leave sections alienated or disconnected. Weave them tightly into the cumulative narrative by referencing established outcomes as active, proven foundations in a single crisp clause, advancing directly to the new technical delta.
- Explain each concept, parameter, or property ONCE. When symbols, models, or state parameters are established, assume them as proven invariants and use them directly without re-explaining or re-defining them. Zero conversational padding, zero decorative throat-clearing, zero artificial elongation.
- Single-Point Failure Mode Invariant: State an estimator's failure mode, asymptotic breakdown, or identification limit exactly ONCE when introducing it. Never re-explain, re-motivate, or repeat the same breakdown across multiple sections. Advance immediately to the operational mechanics of the current model.
</task>

<formatting_rules>
- Hierarchy & Structure:
  # Main Title (no emoji)
  ## [Emoji] Section Title
  ### [Emoji] Subsection Title
  Maximum heading depth is 3 (###). Never use ####; use bold text within paragraphs if deeper nesting is needed.
  * Meaningful Granularity: Create `### [Emoji] Subsection Title` only when logically distinct models, estimators, or methodological stages are introduced. NEVER insert artificial subsections every few sentences or just to meet an arbitrary word target.
- Visual Separators: Add a single horizontal rule (---) before each ## section (except the first). NEVER add a horizontal rule before ### subsections. NEVER place consecutive or duplicate horizontal rules.
- High-Density Prose & Explanatory Paragraph Flow:
  * Deliver explanations through focused, cohesive paragraphs written in an active, incisive voice. Each paragraph must develop a single clear logical idea, derivation step, or identification mechanism with full clarity. Lead directly with the technical mechanism, its intuitive trick, and its substantive impact; eliminate meta-introductions ("This paper investigates...", "It is important to emphasize that...").
  * Linear Syntax & Anti-Subordinate Stacking: Restrict sentences to at most one subordinate clause. Lead with direct subject-verb-object assertions. Never stack causal preambles ("Because X violates Y and causes Z, a framework is required to..."). Split them into direct, self-contained statements ("X violates Y, producing Z. Model W solves this by...").
  * Cognitive Pacing & Mathematical Breathing Room: Avoid monolithic walls of text, but NEVER compress multi-step mathematical derivations or identification arguments into 2 clipped, opaque sentences. Give derivations the structured narrative space required for the student to follow every step effortlessly.
  * Connect motivation, ingenious mechanics, and consequences in a tight logical chain. Eliminate passive, anonymous filler: write with precision and intellectual energy, showing the elegance of the mechanism rather than reciting dry textbook definitions.
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
  * Fluid In-Paragraph Integration & Derivation Completeness: Explain formulas, estimators, and computational mechanisms within standard narrative paragraphs. Do NOT isolate them into superficial one-liners or detached technical tangents. Show the complete intermediate mathematical reasoning so the student understands how and why the formula works.
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
      2. **Node Label Multi-Line Formatting & Anti-Truncation (<br/>)**:
         - Notion's Mermaid SVG box bounds clip single-line labels exceeding 15-16 characters (e.g. 'Equipment & Facilities' gets truncated to 'Equipment & Faci').
         - To guarantee zero text truncation, ALWAYS wrap compound or multi-word labels into short lines using `<br/>` with maximum 14-16 characters per line (e.g. `NodeID["Equipment and<br/>Facilities"]`, `NodeID["European Steel<br/>Producer"]`, `NodeID["ArchiMate<br/>Meta-Model"]`, `NodeID["App Service:<br/>Registration"]`).
         - NEVER use formatting HTML tags (`<span>`, `<b>`, `<i>`, `<div>`); use ONLY `<br/>` for line breaks within node labels.
         - Subgraph titles and edge labels (`|label|`) must remain strictly single-line without `<br/>`.
         - ALWAYS wrap ALL node labels in double quotes (e.g. `NodeID["Label Text"]`, `NodeID("Rounded Label")`, `NodeID{{"Condition"}}`).
         - In edge labels (`|label|`), use concise words without parentheses or angle brackets (`<`, `>`).
      3. **Formal Mathematical Notation**: In diagrams, format mathematical complexities and variables using clean Unicode math notation instead of ASCII approximations (e.g. `O(m × n × k) ≈ O(N³)` instead of `O(N^3)`, `O(log N)`, `(K₁, V₁)`, `∑`, `β̂`, `λ`, `->`).
      4. **Topology & Subgraph Rules**:
         - Connect STRICTLY node-to-node (`NodeA --> NodeB`). NEVER connect an edge to or from a subgraph container directly.
         - If using subgraphs, always specify an alphanumeric ID: `subgraph SG_ID ["Subgraph Title"]`.
         - NEVER apply `style` directly to subgraph IDs (e.g. `style SG_ID ...` is forbidden as it causes Notion layout crashes).
         - Cross-subgraph edges MUST be declared outside/after the subgraph blocks at root level, never nested inside individual subgraphs.
         - Use standard edge labels with vertical pipes: `-->|label|`, never `-- "label" -->`.
      5. **Strict Vertical Flow & Width Budget (Anti-Shrink & Single-Column Guarantee)**:
         - Notion constrains diagrams to a narrow column width (700-900px). Diagrams with wide horizontal sprawl or subgraphs placed side-by-side shrink proportionally, reducing font size to microscopic 3-5px.
         - STRICTLY use `graph TD` (Top-Down). NEVER use `graph LR` (Left-to-Right).
         - Single-Column Vertical Hierarchy: Stack all subgraphs in a single vertical cascade (`SG_1 --> SG_2 --> SG_3`). NEVER declare multiple subgraphs in parallel side-by-side.
         - Strict Downward Edge Orientation (Zero Rank Inversions / Cycles): When connecting across subgraphs, ALL edges must point strictly downwards from higher subgraphs to lower subgraphs (`SG_1 --> SG_2 --> SG_3`). NEVER connect from a lower subgraph back up to a higher subgraph (e.g. never point from Technology Layer up to Application Layer), as backward edges cause Dagre layout engine to violate rank hierarchy and force subgraphs side-by-side horizontally across the page.
         - Inside each subgraph, chain nodes vertically in a single sequence (`Node1 --> Node2 --> Node3`).
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
- Language & Tone: British English exclusively. Direct, rigorous, intellectually vibrant tone: active voice, muscular prose, high clarity, and zero bureaucratic filler. Think of an elite quantitative researcher explaining the core beauty and mechanics of a system to a brilliant colleague. Output ONLY the finalized notes without conversational padding or tags.
</formatting_rules>

<input_data>
Please analyze and distill the following {subject} document:
</input_data>
""".strip()


# Template per il secondo stage (Two-Stage Decoupled Mode).
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
   - **Node Label Multi-Line Formatting & Anti-Truncation (<br/>)**: Notion clips single-line labels exceeding 15-16 characters. ALWAYS wrap compound or multi-word labels into short lines using `<br/>` with maximum 14-16 characters per line (e.g. `NodeID["Equipment and<br/>Facilities"]`, `NodeID["ArchiMate<br/>Meta-Model"]`). Wrap all labels in double quotes. Subgraph titles and edge labels must remain single-line without `<br/>`.
   - **Formal Mathematical Notation**: In diagrams, format mathematical complexities and variables using clean Unicode math notation instead of ASCII approximations (e.g. `O(m × n × k) ≈ O(N³)` instead of `O(N^3)`, `O(log N)`, `(K₁, V₁)`, `∑`, `β̂`, `λ`, `->`).
   - **Topology & Subgraph Rules**: Connect STRICTLY node-to-node (`NodeA --> NodeB`). NEVER connect an edge to or from a subgraph container directly. If using subgraphs, always specify an alphanumeric ID: `subgraph SG_ID ["Subgraph Title"]`. NEVER apply `style` to subgraph IDs (`style SG_ID` is forbidden). Declare cross-subgraph edges outside subgraphs at root level. Use `-->|label|` for edge labels.
   - **Strict Vertical Flow & Width Budget (Anti-Shrink & Single-Column Guarantee)**: Notion renders code blocks in a narrow reading column (~700-900px). NEVER use `graph LR`. STRICTLY use `graph TD`. Never place multiple subgraphs in parallel side-by-side. Stack all subgraphs sequentially in a single vertical column (`SG_1 --> SG_2 --> SG_3`). All cross-subgraph edges must point strictly downwards (zero cycles / rank inversions). Inside each subgraph, chain nodes vertically in a single sequence.
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
- In Mermaid taxonomy trees and flowcharts, connect strictly node-to-node (`NodeA --> NodeB`), use ONLY `<br/>` for line breaks within node labels to prevent clipping, never style subgraph containers (`style SG_ID` is strictly prohibited), and declare cross-subgraph edges at root level outside subgraphs.
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
    # Se include_study_artifacts è False (attivato nella prima chiamata della modalità
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
