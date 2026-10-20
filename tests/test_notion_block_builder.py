import pytest
from src.adapters.outbound.notion_block_builder import (
    parse_rich_text,
    build_notion_blocks,
    NOTION_MAX_BLOCK_CHARS,
    normalize_sentence_spacing,
    sanitize_mermaid_mindmap,
    sanitize_mermaid_flowchart,
    convert_mindmap_to_flowchart,
    wrap_mermaid_label,
)


def test_parse_rich_text_plain():
    parts = parse_rich_text("Hello world")
    assert len(parts) == 1
    assert parts[0]["type"] == "text"
    assert parts[0]["text"]["content"] == "Hello world"

def test_parse_rich_text_bold():
    parts = parse_rich_text("This is **critical** concept.")
    assert len(parts) == 3
    assert parts[0]["text"]["content"] == "This is "
    assert parts[1]["text"]["content"] == "critical"
    assert parts[1]["annotations"]["bold"] is True
    assert parts[2]["text"]["content"] == " concept."

def test_parse_rich_text_inline_math():
    parts = parse_rich_text("Given the formula $E=mc^2$, we deduce...")
    assert len(parts) == 3
    assert parts[0]["text"]["content"] == "Given the formula "
    assert parts[1]["type"] == "equation"
    assert parts[1]["equation"]["expression"] == "E=mc^2"
    assert parts[2]["text"]["content"] == ", we deduce..."

def test_parse_rich_text_truncation():
    long_str = "a" * (NOTION_MAX_BLOCK_CHARS + 500)
    parts = parse_rich_text(long_str)
    assert len(parts[0]["text"]["content"]) <= NOTION_MAX_BLOCK_CHARS

def test_build_notion_blocks_headings_and_dividers():
    md = "# Main Title\nSome introduction.\n## Section Title\nDetailed analysis."
    blocks = build_notion_blocks(md)
    # H1 is first -> no divider before it
    assert blocks[0]["type"] == "heading_1"
    assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Main Title"
    # Paragraph
    assert blocks[1]["type"] == "paragraph"
    # Divider before H2
    assert blocks[2]["type"] == "divider"
    assert blocks[3]["type"] == "heading_2"
    assert blocks[3]["heading_2"]["rich_text"][0]["text"]["content"] == "Section Title"

def test_build_notion_blocks_code_block():
    md = "Here is the implementation:\n```python\ndef solve():\n    return 42\n```\nDone."
    blocks = build_notion_blocks(md)
    code_blocks = [b for b in blocks if b["type"] == "code"]
    assert len(code_blocks) == 1
    assert code_blocks[0]["code"]["language"] == "python"
    assert "def solve():" in code_blocks[0]["code"]["rich_text"][0]["text"]["content"]

def test_build_notion_blocks_display_math():
    md = "$$\n\\hat{y} = \\sigma(Wx + b)\n$$\n$$E = mc^2$$"
    blocks = build_notion_blocks(md)
    eq_blocks = [b for b in blocks if b["type"] == "equation"]
    assert len(eq_blocks) == 2
    assert "\\hat{y} = \\sigma(Wx + b)" in eq_blocks[0]["equation"]["expression"]
    assert eq_blocks[1]["equation"]["expression"] == "E = mc^2"

def test_build_notion_blocks_blockquote():
    md = "> Important theorem statement"
    blocks = build_notion_blocks(md)
    assert blocks[0]["type"] == "quote"
    assert blocks[0]["quote"]["rich_text"][0]["text"]["content"] == "Important theorem statement"

def test_build_notion_blocks_h4_fallback():
    md = "#### Sub-sub heading"
    blocks = build_notion_blocks(md)
    # Notion does not support H4; downgraded to heading_3
    assert blocks[0]["type"] == "heading_3"

def test_normalize_sentence_spacing():
    assert normalize_sentence_spacing("concept.Next") == "concept. Next"
    assert normalize_sentence_spacing("value:Key") == "value: Key"
    assert normalize_sentence_spacing("first,second") == "first, second"
    assert normalize_sentence_spacing("clause;another") == "clause; another"
    assert normalize_sentence_spacing("pi is 3.14 approx") == "pi is 3.14 approx"
    assert normalize_sentence_spacing("already separated. Words.") == "already separated. Words."

def test_no_duplicate_dividers():
    md = "### Previous H3\nSome text\n---\n## Next Section\nMore text"
    blocks = build_notion_blocks(md)
    # Filter only divider blocks
    dividers = [b for b in blocks if b["type"] == "divider"]
    assert len(dividers) == 1

def test_no_divider_before_h3():
    md = "# Main Title\nIntroductory text\n## Section\nSome text\n### Subsection\nMore text"
    blocks = build_notion_blocks(md)
    # Divider before H2, but NO divider before H3
    dividers = [b for b in blocks if b["type"] == "divider"]
    assert len(dividers) == 1
    # Check types sequence: heading_1, paragraph, divider, heading_2, paragraph, heading_3, paragraph
    types = [b["type"] for b in blocks]
    assert types == ["heading_1", "paragraph", "divider", "heading_2", "paragraph", "heading_3", "paragraph"]

def test_parse_rich_text_italic():
    parts = parse_rich_text("This is *italicized* thought.")
    assert len(parts) == 3
    assert parts[1]["text"]["content"] == "italicized"
    assert parts[1]["annotations"]["italic"] is True

def test_parse_rich_text_bold_italic():
    parts = parse_rich_text("This is ***crucial premise*** here.")
    assert len(parts) == 3
    assert parts[1]["text"]["content"] == "crucial premise"
    assert parts[1]["annotations"]["bold"] is True
    assert parts[1]["annotations"]["italic"] is True

def test_parse_rich_text_code():
    parts = parse_rich_text("Call the `evaluate()` function.")
    assert len(parts) == 3
    assert parts[1]["text"]["content"] == "evaluate()"
    assert parts[1]["annotations"]["code"] is True

def test_parse_rich_text_example_pattern():
    parts = parse_rich_text("**Example:** *In banking monoliths, decoupling starts with strangler fig.*")
    assert parts[0]["text"]["content"] == "Example:"
    assert parts[0]["annotations"]["bold"] is True
    assert parts[1]["text"]["content"] == " "
    assert "banking monoliths" in parts[2]["text"]["content"]
    assert parts[2]["annotations"]["italic"] is True

def test_build_notion_blocks_blockquote_with_formatting():
    md = "> **Core Insight:** Loose coupling minimizes systemic fragility."
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "quote"
    rich_text = blocks[0]["quote"]["rich_text"]
    assert rich_text[0]["text"]["content"] == "Core Insight:"
    assert rich_text[0]["annotations"]["bold"] is True
    assert "Loose coupling" in rich_text[1]["text"]["content"]

def test_parse_rich_text_italic_with_nested_bold():
    line = "**Example:** *Consider a **stationary series** before shock.*"
    parts = parse_rich_text(line)
    # Check Example: is bold
    assert parts[0]["text"]["content"] == "Example:"
    assert parts[0]["annotations"]["bold"] is True
    # Check italic prefix
    italic_prefix = next(p for p in parts if "Consider a " in p["text"]["content"])
    assert italic_prefix["annotations"]["italic"] is True
    # Check bold+italic nested text
    nested_bold = next(p for p in parts if p["text"]["content"] == "stationary series")
    assert nested_bold["annotations"]["bold"] is True
    assert nested_bold["annotations"]["italic"] is True

def test_parse_rich_text_formula_inside_bold():
    line = "**Sample size ($T=100$):** critical baseline."
    parts = parse_rich_text(line)
    eq_parts = [p for p in parts if p.get("type") == "equation"]
    assert len(eq_parts) == 1
    assert eq_parts[0]["equation"]["expression"] == "T=100"
    assert eq_parts[0]["annotations"]["bold"] is True

def test_parse_rich_text_formula_inside_italic():
    line = "**Example:** *Simulated white noise with $T=100$ observations.*"
    parts = parse_rich_text(line)
    eq_parts = [p for p in parts if p.get("type") == "equation"]
    assert len(eq_parts) == 1
    assert eq_parts[0]["equation"]["expression"] == "T=100"
    assert eq_parts[0]["annotations"]["italic"] is True

def test_build_notion_blocks_bullet_with_equation():
    md = "- $$n_i = |F_i|$$"
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "bulleted_list_item"
    rich_text = blocks[0]["bulleted_list_item"]["rich_text"]
    assert any(r.get("type") == "equation" and r["equation"]["expression"] == "n_i = |F_i|" for r in rich_text)


def test_build_notion_blocks_standard_table():
    md = (
        "| Feature | CPU | GPU |\n"
        "| :--- | :--- | :--- |\n"
        "| **Role** | Expert | Workers |\n"
        "| **Cores** | 4-128 | 10,000+ |"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    assert table["table_width"] == 3
    assert table["has_column_header"] is True
    assert len(table["children"]) == 3  # 1 header + 2 rows

    # Header verification
    header_row = table["children"][0]["table_row"]["cells"]
    assert len(header_row) == 3
    assert header_row[0][0]["text"]["content"] == "Feature"
    assert header_row[1][0]["text"]["content"] == "CPU"
    assert header_row[2][0]["text"]["content"] == "GPU"

    # Data row with formatting
    row1 = table["children"][1]["table_row"]["cells"]
    assert row1[0][0]["text"]["content"] == "Role"
    assert row1[0][0]["annotations"]["bold"] is True
    assert row1[1][0]["text"]["content"] == "Expert"


def test_build_notion_blocks_table_with_blank_lines():
    # Tollera righe vuote accidentali tra le righe della tabella
    md = (
        "| Feature | CPU | GPU |\n\n"
        "| :--- | :--- | :--- |\n\n"
        "| **Role** | Expert | Workers |\n\n"
        "| **Cores** | 4-128 | 10,000+ |\n"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    assert table["table_width"] == 3
    assert len(table["children"]) == 3


def test_build_notion_blocks_table_with_escaped_pipe():
    md = (
        "| Expression | Meaning |\n"
        "| :--- | :--- |\n"
        "| $P(A \\| B)$ | Conditional probability |"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    assert table["table_width"] == 2
    assert len(table["children"]) == 2


def test_parse_rich_text_html_br_tags():
    # ARCHITETTURA: Verifica che le varianti di tag HTML <br> siano normalizzate in newline nativi
    # senza lasciare residui di sintassi HTML o spazi spurii.
    raw = "<br>- Point 1<br/>- Point 2<br />- Point 3</br>- Point 4<BR>- Point 5<br>"
    parts = parse_rich_text(raw)
    content = "".join(p["text"]["content"] for p in parts)
    assert "<br" not in content.lower()
    assert "</br" not in content.lower()
    assert content == "- Point 1\n- Point 2\n- Point 3\n- Point 4\n- Point 5"


def test_build_notion_blocks_table_with_html_br():
    # ARCHITETTURA: Verifica che le celle delle tabelle Markdown con elenchi o a capo <br>
    # vengano convertite in blocchi Notion table nativi con soft-break \n puliti.
    md = (
        "| Data Structure | Characteristics |\n"
        "| :--- | :--- |\n"
        "| DataFrame | - Data organised into named columns.<br>- Immutable distributed collection of data.<br>- Allows imposition of structure. |"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    row_cells = table["children"][1]["table_row"]["cells"]
    cell_text = "".join(item["text"]["content"] for item in row_cells[1])
    assert "<br" not in cell_text.lower()
    assert cell_text == "- Data organised into named columns.\n- Immutable distributed collection of data.\n- Allows imposition of structure."


def test_build_notion_blocks_nested_bullet_points():
    md = (
        "* **Mapping (List(K2, V2)):** Each chunk is processed by a map function.\n"
        "    * Chunk 1: (Deer, 1)\n"
        "    * Chunk 2: (Car, 1)\n"
        "* **Shuffling (K2, List(V2)):** All pairs grouped by word."
    )
    blocks = build_notion_blocks(md)
    # Only 2 root blocks: Mapping and Shuffling
    assert len(blocks) == 2
    assert blocks[0]["type"] == "bulleted_list_item"
    assert blocks[1]["type"] == "bulleted_list_item"

    # Mapping must contain 2 nested children
    mapping_payload = blocks[0]["bulleted_list_item"]
    assert "children" in mapping_payload
    assert len(mapping_payload["children"]) == 2
    assert mapping_payload["children"][0]["type"] == "bulleted_list_item"
    assert mapping_payload["children"][1]["type"] == "bulleted_list_item"
    assert "Chunk 1" in mapping_payload["children"][0]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
    assert "Chunk 2" in mapping_payload["children"][1]["bulleted_list_item"]["rich_text"][0]["text"]["content"]

    # Leaf children must NEVER contain an empty 'children' key (Notion API rejects empty children with 400)
    assert "children" not in mapping_payload["children"][0]["bulleted_list_item"]
    assert "children" not in mapping_payload["children"][1]["bulleted_list_item"]

    # Shuffling has no children -> no 'children' key
    assert "children" not in blocks[1]["bulleted_list_item"]


def test_build_notion_blocks_mixed_nested_lists():
    md = (
        "1. Primary Phase\n"
        "    - Sub-bullet A\n"
        "    - Sub-bullet B\n"
        "2. Secondary Phase"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 2
    assert blocks[0]["type"] == "numbered_list_item"
    assert blocks[1]["type"] == "numbered_list_item"

    p1 = blocks[0]["numbered_list_item"]
    assert "children" in p1
    assert len(p1["children"]) == 2
    assert p1["children"][0]["type"] == "bulleted_list_item"
    assert p1["children"][1]["type"] == "bulleted_list_item"


def test_build_notion_blocks_list_continuation():
    md = (
        "1. **Training MSE:** For this specific model, residuals are zero.\n"
        "    Consequently, the training MSE will be exactly 0.\n"
        "2. **Test MSE:** High variance expected."
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 2
    assert blocks[0]["type"] == "numbered_list_item"
    assert blocks[1]["type"] == "numbered_list_item"

    # Continuation text is merged into the first item's rich_text
    full_text = " ".join(
        t["text"]["content"] for t in blocks[0]["numbered_list_item"]["rich_text"] if "text" in t
    )
    assert "residuals are zero" in full_text
    assert "Consequently, the training MSE will be exactly 0" in full_text


def test_build_notion_blocks_max_depth_safety():
    # Notion API limits nesting to 2 levels in batch append
    md = (
        "- Level 0\n"
        "    - Level 1\n"
        "        - Level 2\n"
        "            - Level 3 (should be capped at level 2 without error)"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    lvl0 = blocks[0]["bulleted_list_item"]
    assert len(lvl0["children"]) == 1
    lvl1 = lvl0["children"][0]["bulleted_list_item"]
    assert len(lvl1["children"]) == 2  # Level 2 and Level 3 both placed under Level 1 as siblings
    lvl2 = lvl1["children"][0]["bulleted_list_item"]
    assert "children" not in lvl2  # Not deeply nested beyond level 2


def test_sanitize_mermaid_mindmap_escapes_parentheses_and_operators():
    raw_mermaid = (
        "mindmap\n"
        "  root((Big Data Systems))\n"
        "    Architecture\n"
        "      Scale (KB to YB)\n"
        "      Moore's Law((N_T(t) proportional to 2^(t/tau)))\n"
        "      Consistency (C)\n"
        "      LLM Wall (m=1) -> Bandwidth Bound\n"
        "      Clean Leaf Node\n"
        '      ["Already Quoted Node"]\n'
    )
    sanitized = sanitize_mermaid_mindmap(raw_mermaid)
    assert "graph TD" in sanitized
    assert "htmlLabels" in sanitized
    assert 'ROOT["Big Data Systems"]:::rootNode' in sanitized
    assert 'subgraph SG_1 ["1. Architecture"]' in sanitized
    assert 'N3["Scale (KB to YB)"]:::theoryNode' in sanitized
    assert "ROOT --> N3" in sanitized


def test_sanitize_mermaid_flowchart_escapes_nested_brackets_and_colons():
    raw_flowchart = (
        "graph TD\n"
        "  A[Input Data (K1, V1)] --> B{Data Partitioning: Step 1};\n"
        "  B --> C[Map Function (per chunk)];\n"
        "  subgraph MapReduce Word Count\n"
        "    I[\"'Deer Bear River', 'Car Car River'\"] --> J[Map: (Deer,1), (Bear,1)];\n"
        "    K[Shuffle & Sort: Bear:[1,1], Car:[1,1,1]];\n"
        "    L[Reduce: Bear:2, Car:3];\n"
        "  end"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert 'A["Input Data (K1,<br/>V1)"]' in sanitized
    assert 'B{"Data Partitioning:<br/>Step 1"}' in sanitized
    assert 'C["Map Function (per<br/>chunk)"]' in sanitized
    assert 'subgraph sg_MapReduce_Word_Count ["MapReduce Word Count"]' in sanitized
    assert "Deer Bear River" in sanitized
    assert "Shuffle and Sort:" in sanitized
    assert 'L["Reduce: Bear:2,<br/>Car:3"]' in sanitized


def test_sanitize_mermaid_flowchart_redirects_edges_to_subgraph_members():
    raw_flowchart = (
        "graph LR\n"
        "  ROOT[System Root] --> CLUSTER;\n"
        "  subgraph CLUSTER [Compute Engine]\n"
        "    NODE1[Executor 1] --> NODE2[Executor 2];\n"
        "  end\n"
        "  CLUSTER --> SINK[Storage Sink];\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert 'ROOT["System Root"] --> NODE1' in sanitized
    assert 'NODE1 --> SINK["Storage Sink"]' in sanitized


def test_build_notion_blocks_sanitizes_flowchart_in_code_block():
    md = (
        "```mermaid\n"
        "graph TD\n"
        "  K[Shuffle & Sort: Bear:[1,1], Car:[1,1,1]];\n"
        "```"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"
    content = blocks[0]["code"]["rich_text"][0]["text"]["content"]
    assert "Shuffle and Sort:" in content
    assert "Bear:(1,1)" in content


def test_build_notion_blocks_large_code_block_preserves_single_block_integrity():
    # Code block larger than NOTION_MAX_BLOCK_CHARS (e.g. 4500 chars)
    # Must NOT be sliced into multiple code blocks, but kept in 1 block with multiple rich_text chunks
    long_code = "print('hello world')\n" * 250  # ~5250 chars
    md = f"```python\n{long_code}```"

    blocks = build_notion_blocks(md)
    code_blocks = [b for b in blocks if b["type"] == "code"]

    # Critical invariant: 1 block only!
    assert len(code_blocks) == 1
    assert code_blocks[0]["code"]["language"] == "python"

    rich_text = code_blocks[0]["code"]["rich_text"]
    assert len(rich_text) > 1  # multiple chunks
    total_reconstructed = "".join(chunk["text"]["content"] for chunk in rich_text)
    assert total_reconstructed == long_code.strip()


def test_sanitize_mermaid_flowchart_drops_subgraph_style_to_prevent_elk_crash():
    # ARCHITETTURA: Previene il crash ELK/Dagre in Notion 'Cannot read properties of null (reading re)'.
    # Le direttive `style <subgraphId>` su cluster causano lookup null nella tabella nodi atomici.
    # Devono essere scartate deterministicamente.
    raw_flowchart = (
        "graph TD\n"
        "  subgraph BDF [Big Data Fundamentals]\n"
        "    BDF1[Node 1]\n"
        "  end\n"
        "  style BDF fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,stroke-dasharray: 3 3\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert "style BDF" not in sanitized
    assert 'subgraph BDF ["Big Data Fundamentals"]' in sanitized
    assert 'BDF1["Node 1"]' in sanitized


def test_sanitize_mermaid_flowchart_strips_html_tags_and_spans():
    # ARCHITETTURA: Tag HTML inline (<span style=...>, <b>, <br/>) rompono il calcolo
    # delle bounding-box SVG in Notion ed ELK.
    raw_flowchart = (
        "graph TD\n"
        "  ROOT[\"<span style='font-size:18px;font-weight:800;'>Big Data Architecture</span><br/><span style='font-size:12px;'>Core</span>\"]:::rootNode\n"
        "  subgraph SG1 [\"<span style='font-size:15px;'>Ingestion Layer</span>\"]\n"
        "    A[\"<b>Kafka Broker</b><br/>Partitioned topic\"] --> B[\"<i>Flink Worker</i>\"]\n"
        "  end\n"
        "  ROOT --> A\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert "<span" not in sanitized
    assert "</span>" not in sanitized
    assert "<b>" not in sanitized
    assert "</b>" not in sanitized
    assert "<i>" not in sanitized
    assert "</i>" not in sanitized
    assert "<br/>" in sanitized
    assert 'ROOT["Big Data<br/>Architecture<br/>Core"]:::rootNode' in sanitized
    assert 'subgraph SG1 ["Ingestion Layer"]' in sanitized
    assert 'A["Kafka Broker<br/>Partitioned topic"]' in sanitized
    assert 'B["Flink Worker"]' in sanitized


def test_sanitize_mermaid_flowchart_hoists_cross_subgraph_edges():
    # ARCHITETTURA: Dichiarare archi con nodi esterni dentro un subgraph causa
    # duplicazione del nodo in più cluster (multi-parent) mandando in crash l'engine di layout.
    raw_flowchart = (
        "graph TD\n"
        "  subgraph SG1 [Layer 1]\n"
        "    A[Producer]\n"
        "  end\n"
        "  subgraph SG2 [Layer 2]\n"
        "    B[Consumer]\n"
        "    A --> B\n"
        "  end\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    lines = sanitized.splitlines()

    sg2_body = []
    in_sg2 = False
    for line in lines:
        if "subgraph SG2" in line:
            in_sg2 = True
            continue
        if in_sg2 and "end" in line:
            in_sg2 = False
            continue
        if in_sg2:
            sg2_body.append(line.strip())

    assert "A --> B" not in sg2_body
    assert any("A --> B" in line for line in lines)
    assert "%% Cross-subgraph edges hoisted" in sanitized


def test_sanitize_mermaid_flowchart_normalizes_all_node_shapes_and_quotes():
    # ARCHITETTURA: Tutte le forme grafiche (tonde, doppie tonde, rombi, stadi, esagoni)
    # devono avere il contenuto quotato con double quotes per proteggere formule e trattini.
    raw_flowchart = (
        "graph TD\n"
        "  N1(Rounded Node: 10ms)\n"
        "  N2((Double Circle: Target))\n"
        "  N3([Stadium Shape: Batch processing])\n"
        "  N4{Rhombus Condition: x > 0}\n"
        "  N5{{Hexagon Prep: init()}}\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert 'N1("Rounded Node: 10ms")' in sanitized
    assert 'N2(("Double Circle:<br/>Target"))' in sanitized
    assert 'N3(["Stadium Shape:<br/>Batch processing"])' in sanitized
    assert 'N4{"Rhombus Condition:<br/>x gt 0"}' in sanitized
    assert 'N5{"Hexagon Prep:<br/>init()"}' in sanitized


def test_sanitize_mermaid_flowchart_normalizes_edge_labels():
    # ARCHITETTURA: Sintassi non standard come `A -- "label" --> B` o `A -- label --> B`
    # devono essere tradotte nel formato universale Mermaid `A -->|label| B`.
    raw_flowchart = (
        "graph TD\n"
        '  A -- "HTTP Post (JSON)" --> B\n'
        "  B -- Event Stream --> C\n"
        "  C -.->|Standard Label| D\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert "A -->|HTTP Post - JSON| B" in sanitized
    assert "B -->|Event Stream| C" in sanitized
    assert "C -.->|Standard Label| D" in sanitized


def test_sanitize_mermaid_mindmap_converts_to_flowchart_taxonomy():
    # ARCHITETTURA: Notion non supporta la sintassi mindmap di Mermaid;
    # essa viene convertita deterministicamente in un albero tassonomico 'graph TD' con classi di stile.
    raw_mindmap = (
        "mindmap\n"
        "  root((<b>Academic Core</b><br/>Syllabus))\n"
        "    Pillars\n"
        "      <span style='color:red;'>Optimization Problem (min f(x))</span>\n"
        '      ["`Complex Feature` (O(N^2))"]\n'
    )
    sanitized = sanitize_mermaid_mindmap(raw_mindmap)
    assert "graph TD" in sanitized
    assert "htmlLabels" in sanitized
    assert "<b>" not in sanitized
    assert "</b>" not in sanitized
    assert "<span" not in sanitized
    assert "`" not in sanitized
    assert 'ROOT["Academic Core<br/>Syllabus"]:::rootNode' in sanitized
    assert 'subgraph SG_1 ["1. Pillars"]' in sanitized
    assert 'N3["Optimization<br/>Problem (min<br/>f(x))"]:::theoryNode' in sanitized
    assert 'N4["Complex Feature<br/>(O(N^2))"]:::theoryNode' in sanitized
    assert "ROOT --> N3" in sanitized


def test_sanitize_mermaid_flowchart_filters_invalid_style_props():
    # ARCHITETTURA: Proprietà CSS non valide per SVG in Mermaid (es. font-weight:bold)
    # vengono rimosse per evitare errori di parsing in Notion.
    raw_flowchart = (
        "graph TD\n"
        "  ROOT[SQL Execution Flow]\n"
        "  style ROOT fill:#DA70D6,stroke:#333,stroke-width:2px,font-weight:bold\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert "style ROOT fill:#DA70D6,stroke:#333,stroke-width:2px" in sanitized
    assert "font-weight:bold" not in sanitized


def test_sanitize_mermaid_flowchart_escapes_problematic_edge_labels():
    # ARCHITETTURA: Caratteri come `&`, `>`, parentesi in etichette arco (|...|)
    # causano crash del tokenizer Mermaid e vengono sanitizzati.
    raw_flowchart = (
        "graph TD\n"
        "  A[Start] -->|Scalar & >1 Row| B[Error]\n"
        "  A -->|Yes (Scalar)| C[Process]\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert 'A["Start"] -->|Scalar and gt 1 Row| B["Error"]' in sanitized
    assert 'A -->|Yes - Scalar| C["Process"]' in sanitized


def test_sanitize_mermaid_flowchart_injects_dark_mode_contrast_color():
    # ARCHITETTURA: Se una direttiva 'style' definisce uno sfondo chiaro ma omette 'color:',
    # viene iniettato 'color:#0f172a' per evitare testo bianco invisibile in Notion Dark Mode.
    raw_flowchart = (
        "graph TD\n"
        "  BA[Customer Actor]\n"
        "  style BA fill:#add8e6,stroke:#336699,stroke-width:1.5px\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert "color:#0f172a" in sanitized


def test_convert_mindmap_to_flowchart_preserves_whole_words_without_truncation():
    # ARCHITETTURA: Previene troncamenti distruttivi con '...' a metà parola (es. 'Reali...', 'Orga...')
    raw_mindmap = (
        "mindmap\n"
        "  root((Enterprise Architecture))\n"
        "    Core Concepts\n"
        "      Layered Models\n"
        "        Serving Relationships\n"
    )
    sanitized = convert_mindmap_to_flowchart(raw_mindmap)
    assert "..." not in sanitized
    assert "Serving<br/>Relationships" in sanitized


def test_build_notion_blocks_image_with_caption():
    # ARCHITETTURA: Verifica che blocchi immagine con alt text popolino correttamente il campo caption di Notion
    md = "![Architecture Diagram](https://cdn.example.com/notion/universita/ea/arch.png)"
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "image"
    assert blocks[0]["image"]["type"] == "external"
    assert blocks[0]["image"]["external"]["url"] == "https://cdn.example.com/notion/universita/ea/arch.png"
    assert "caption" in blocks[0]["image"]
    assert blocks[0]["image"]["caption"][0]["text"]["content"] == "Architecture Diagram"


def test_build_notion_blocks_markdown_link_in_rich_text():
    # ARCHITETTURA: Verifica che link Markdown [testo](url) vengano serializzati con il campo link nativo
    md = "Consulenza e documentazione su [Notion Docs](https://developers.notion.com) ufficiale."
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    rich_text = blocks[0]["paragraph"]["rich_text"]
    link_parts = [p for p in rich_text if p.get("text", {}).get("link") is not None]
    assert len(link_parts) == 1
    assert link_parts[0]["text"]["content"] == "Notion Docs"
    assert link_parts[0]["text"]["link"]["url"] == "https://developers.notion.com"


def test_build_notion_blocks_suppress_boilerplate_figure_caption():
    # ARCHITETTURA: Verifica che didascalie boilerplate ('Figura slide N', 'Slide N') vengano omesse
    md = "![Figura slide 8](https://cdn.example.com/notion/universita/ea/slide8.png)"
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "image"
    assert "caption" not in blocks[0]["image"]

    # Immagine senza alt text
    md_empty = "![](https://cdn.example.com/notion/universita/ea/clean.png)"
    blocks_empty = build_notion_blocks(md_empty)
    assert len(blocks_empty) == 1
    assert "caption" not in blocks_empty[0]["image"]


def test_wrap_mermaid_label_prevents_notion_word_clipping():
    # ARCHITETTURA: Verifica che stringhe composite superiori a 16 caratteri vengano
    # spezzate con tag <br/> a confine di parola, evitando il troncamento visivo a ~16 caratteri in Notion Desktop.
    labels_to_test = [
        "Equipment and Facilities",
        "European Steel Producer",
        "ArchiMate Meta-Model",
        "App Service: Registration",
        "Layered EA Models",
        "Customer Retention CRM",
    ]
    for label in labels_to_test:
        wrapped = wrap_mermaid_label(label, max_chars_per_line=16)
        assert "<br/>" in wrapped, f"Expected <br/> in wrapped label for '{label}', got '{wrapped}'"
        for line in wrapped.split("<br/>"):
            assert len(line) <= 18, f"Line '{line}' in '{wrapped}' exceeds character threshold"


def test_sanitize_mermaid_flowchart_wraps_long_labels_with_br():
    # ARCHITETTURA: Verifica che sanitize_mermaid_flowchart applichi deterministicamente
    # wrap_mermaid_label su nodi definiti con etichette lunghe, preservando la leggibilità in Notion.
    raw_flowchart = (
        "graph TD\n"
        '  N10["Equipment and Facilities"]\n'
        '  N11["European Steel Producer"]\n'
        '  N3["ArchiMate Meta-Model"]\n'
        '  AS_OR["App Service: Registration"]\n'
        "  N10 --> N11 --> N3 --> AS_OR\n"
    )
    sanitized = sanitize_mermaid_flowchart(raw_flowchart)
    assert 'N10["Equipment and<br/>Facilities"]' in sanitized
    assert 'N11["European Steel<br/>Producer"]' in sanitized
    assert 'N3["ArchiMate<br/>Meta-Model"]' in sanitized
    assert 'AS_OR["App Service:<br/>Registration"]' in sanitized












