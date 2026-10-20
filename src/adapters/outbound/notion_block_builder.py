import re
from typing import List, Dict, Any, Tuple, Optional

NOTION_MAX_BLOCK_CHARS = 1900

# Notion-supported languages for code blocks
NOTION_SUPPORTED_LANGUAGES = {
    "abap", "arduino", "bash", "basic", "c", "clojure", "coffeescript", "c++", "c#",
    "css", "dart", "diff", "docker", "elixir", "elm", "erlang", "flow", "fortran",
    "f#", "gherkin", "glsl", "go", "graphql", "groovy", "haskell", "html", "java",
    "javascript", "json", "julia", "kotlin", "latex", "less", "lisp", "livescript",
    "lua", "makefile", "markdown", "markup", "matlab", "mermaid", "nix", "objective-c",
    "ocaml", "pascal", "perl", "php", "plain text", "powershell", "prolog", "protobuf",
    "python", "r", "reason", "ruby", "rust", "sass", "scala", "scheme", "scss",
    "shell", "sql", "swift", "typescript", "vb.net", "verilog", "vhdl", "visual basic",
    "webassembly", "xml", "yaml", "java/c/c++/c#"
}

def normalize_sentence_spacing(text: str) -> str:
    """
    Ensures a single space exists after sentence-ending punctuation
    when followed immediately by a letter (e.g. 'concept.Next' -> 'concept. Next').
    Avoids altering numbers ('3.14') or valid LaTeX.
    """
    text = re.sub(r'([a-zA-Z0-9\)])\.([A-Z])', r'\1. \2', text)
    text = re.sub(r'([a-zA-Z0-9\)]):([A-Za-z])', r'\1: \2', text)
    text = re.sub(r'([a-zA-Z0-9\)]),([A-Za-z])', r'\1, \2', text)
    text = re.sub(r'([a-zA-Z0-9\)]);([A-Za-z])', r'\1; \2', text)
    return text

def parse_rich_text(line: str, annotations: Dict[str, bool] = None) -> List[Dict[str, Any]]:
    """
    Converts a Markdown line into Notion rich_text objects.
    Recursively handles nested formatting:
      - `code` -> rich_text with code annotation
      - $$formula$$ / $formula$ -> inline equation object (even inside bold or italic)
      - ***bold italic*** -> rich_text with bold and italic annotations (recursive)
      - **bold** -> rich_text with bold annotation (recursive)
      - *italic* -> rich_text with italic annotation (recursive)
      - plain text -> text object
    Normalizes punctuation spacing and truncates individual segments to NOTION_MAX_BLOCK_CHARS.
    """
    if annotations is None:
        # ARCHITETTURA: In Markdown (in particolare nelle celle di tabelle GFM), i ritorni a capo
        # e le liste puntate interne sono codificati come tag HTML (<br>, <br/>, <br />).
        # Notion non esegue il rendering dei tag HTML nativi e li visualizzerebbe come testo grezzo.
        # TRADE-OFF: Convertiamo deterministicamente qualsiasi variante di <br> in newline nativo '\n',
        # supportato nativamente dall'engine di layout di Notion sia nelle celle che nei blocchi di testo.
        line = re.sub(r'[ \t]*</?br\s*/?>[ \t]*', '\n', line, flags=re.IGNORECASE).strip('\n')
        line = line.replace('&nbsp;', ' ')
        line = normalize_sentence_spacing(line)
        annotations = {}

    parts: List[Dict[str, Any]] = []
    pattern = re.compile(
        r'(`([^`]+)`)'
        r'|(\$\$([^\$]+)\$\$)'
        r'|(\$(?!\$)([^\$]+?)(?<!\$)\$)'
        r'|(\*\*\*(.+?)\*\*\*)'
        r'|(\*\*(.+?)\*\*)'
        r'|((?<!\*)\*(?!\s|\*)(.+?)(?<!\s|\*)\*(?!\*))'
        r'|(\[([^\]]+)\]\((https?://[^\s\)]+)\))'
    )
    cursor = 0

    for m in pattern.finditer(line):
        if m.start() > cursor:
            seg = line[cursor:m.start()][:NOTION_MAX_BLOCK_CHARS]
            if seg:
                item: Dict[str, Any] = {"type": "text", "text": {"content": seg}}
                if annotations:
                    item["annotations"] = dict(annotations)
                parts.append(item)

        # 1: Code `...` -> Group 2
        if m.group(2) is not None:
            seg = m.group(2)[:NOTION_MAX_BLOCK_CHARS]
            code_ann = dict(annotations)
            code_ann["code"] = True
            parts.append({
                "type": "text",
                "text": {"content": seg},
                "annotations": code_ann,
            })
        # 2: $$...$$ -> Group 4
        elif m.group(4) is not None:
            expr = m.group(4).strip()[:NOTION_MAX_BLOCK_CHARS]
            eq_item: Dict[str, Any] = {"type": "equation", "equation": {"expression": expr}}
            if annotations:
                eq_item["annotations"] = dict(annotations)
            parts.append(eq_item)
        # 3: $...$ -> Group 6
        elif m.group(6) is not None:
            expr = m.group(6).strip()[:NOTION_MAX_BLOCK_CHARS]
            eq_item = {"type": "equation", "equation": {"expression": expr}}
            if annotations:
                eq_item["annotations"] = dict(annotations)
            parts.append(eq_item)
        # 4: ***...*** -> Group 8
        elif m.group(8) is not None:
            sub_ann = dict(annotations)
            sub_ann["bold"] = True
            sub_ann["italic"] = True
            parts.extend(parse_rich_text(m.group(8), sub_ann))
        # 5: **...** -> Group 10
        elif m.group(10) is not None:
            sub_ann = dict(annotations)
            sub_ann["bold"] = True
            parts.extend(parse_rich_text(m.group(10), sub_ann))
        # 6: *...* -> Group 12
        elif m.group(12) is not None:
            sub_ann = dict(annotations)
            sub_ann["italic"] = True
            parts.extend(parse_rich_text(m.group(12), sub_ann))
        # 7: [text](url) -> Group 13
        elif m.group(13) is not None:
            link_text = m.group(14)[:NOTION_MAX_BLOCK_CHARS]
            link_url = m.group(15)
            link_item: Dict[str, Any] = {
                "type": "text",
                "text": {"content": link_text, "link": {"url": link_url}},
            }
            if annotations:
                link_item["annotations"] = dict(annotations)
            parts.append(link_item)

        cursor = m.end()

    if cursor < len(line):
        seg = line[cursor:][:NOTION_MAX_BLOCK_CHARS]
        if seg:
            item = {"type": "text", "text": {"content": seg}}
            if annotations:
                item["annotations"] = dict(annotations)
            parts.append(item)

    return parts or [{"type": "text", "text": {"content": ""}}]


def split_table_row(line: str) -> List[str]:
    """
    Estrae le singole celle da una riga di tabella Markdown delimitata da pipe.
    Gestisce pipe escapati (\\|) per evitare split incorretti su formule matematiche.
    """
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|"):
        content = content[:-1]

    # PERFORMANCE: Preserviamo i pipe escapati tramite placeholder temporaneo
    placeholder = "___ESCAPED_PIPE___"
    content = content.replace(r"\|", placeholder)
    return [c.replace(placeholder, "|").strip() for c in content.split("|")]

def is_table_separator(line: str) -> bool:
    """
    Verifica se una riga corrisponde alla riga separatore della tabella Markdown GFM
    (composta da caratteri '-', ':', spazi e delimitatori pipe).
    """
    cells = split_table_row(line)
    if not cells:
        return False
    return all(
        ("-" in c) and (set(c.strip()) <= {"-", ":", " "})
        for c in cells
    )


def wrap_mermaid_label(text: str, max_chars_per_line: int = 16) -> str:
    """
    Spezza deterministicamente etichette Mermaid lunghe su più righe tramite tag <br/> a confine di parola.
    # ARCHITETTURA: Nei blocchi Mermaid di Notion, il renderer calcola le bounding box SVG
    # con font standard, mentre il CSS del client desktop impone 'Segoe UI 14px'.
    # Su una singola riga continua, parole o stringhe superiori a 16 caratteri oltrepassano la larghezza
    # del box SVG e subiscono il troncamento visivo (overflow: hidden / clipPath).
    # Suddividendo le etichette con <br/> in righe da massimo 14-16 caratteri, il testo rimane
    # perfettamente centrato, la bounding box si espande in altezza e non si verifica alcun troncamento.
    # TRADE-OFF: L'uso di <br/> è l'unico meccanismo nativo supportato dall'engine Dagre di Mermaid
    # per forzare il multi-line rendering all'interno dei nodi senza ricorrere a costrutti HTML complessi.
    """
    if not text:
        return text
    parts = re.split(r'<br\s*/?>', text, flags=re.IGNORECASE)
    wrapped_lines = []
    for part in parts:
        part = part.strip()
        if not part or len(part) <= max_chars_per_line:
            if part:
                wrapped_lines.append(part)
            continue
        words = part.split()
        cur_line = []
        cur_len = 0
        for w in words:
            w_len = len(w)
            add_len = w_len if not cur_line else w_len + 1
            if cur_len + add_len <= max_chars_per_line:
                cur_line.append(w)
                cur_len += add_len
            else:
                if cur_line:
                    wrapped_lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = w_len
        if cur_line:
            wrapped_lines.append(" ".join(cur_line))
    return "<br/>".join(wrapped_lines) if wrapped_lines else text


def _clean_mermaid_label(inner_text: str, preserve_br: bool = True) -> str:
    """
    Rimuove tag HTML, backticks e normalizza virgolette, parentesi e simboli di confronto
    per la compatibilità con Notion, Mermaid ed ELK/Dagre.
    # ARCHITETTURA: Notion e i renderer web sanitizzano o isolano i nodi SVG; la presenza di tag
    # inline o caratteri XML non escapati manda in crash l'engine di layout.
    # TRADE-OFF: Preserviamo i tag <br/> (proteggendoli temporaneamente con un token placeholder)
    # per consentire il multi-line wrapping essenziale a prevenire il text clipping SVG a ~16 caratteri.
    """
    # 1. Protezione o rimozione tag <br/>
    br_placeholder = "___MERMAID_BR_TAG___"
    if preserve_br:
        inner_text = re.sub(r'<br\s*/?>', br_placeholder, inner_text, flags=re.IGNORECASE)
    else:
        inner_text = re.sub(r'<br\s*/?>', ' - ', inner_text, flags=re.IGNORECASE)

    # 2. Rimozione tag HTML specifici senza corrompere disuguaglianze matematiche
    inner_text = re.sub(r'<span[^>]*>', '', inner_text, flags=re.IGNORECASE)
    inner_text = re.sub(r'</span>', '', inner_text, flags=re.IGNORECASE)
    inner_text = re.sub(r'</?[bi]>', '', inner_text, flags=re.IGNORECASE)
    inner_text = re.sub(r'</?[a-zA-Z][a-zA-Z0-9]*(?:\s+[^>]*)?>', '', inner_text)

    # 3. Rimozione backticks
    inner_text = inner_text.replace('`', "'")

    # 4. Rimozione delimitatori di forma e virgolette esterne
    inner_text = inner_text.strip()
    while (inner_text.startswith('"') and inner_text.endswith('"')) or (inner_text.startswith("'") and inner_text.endswith("'")):
        inner_text = inner_text[1:-1].strip()

    if inner_text.startswith('((') and inner_text.endswith('))'):
        inner_text = inner_text[2:-2].strip()
    if (inner_text.startswith('["') and inner_text.endswith('"]')) or (inner_text.startswith('("') and inner_text.endswith('")')):
        inner_text = inner_text[2:-2].strip()
    if (inner_text.startswith('[') and inner_text.endswith(']')) or (inner_text.startswith('(') and inner_text.endswith(')')):
        inner_text = inner_text[1:-1].strip()

    while (inner_text.startswith('"') and inner_text.endswith('"')) or (inner_text.startswith("'") and inner_text.endswith("'")):
        inner_text = inner_text[1:-1].strip()

    # 5. Eliminazione virgolette doppie interne e normalizzazione apici singoli
    inner_text = inner_text.replace('"', "")
    inner_text = re.sub(r"(^'|'$|(?<=[\s,])'|'(?=[\s,]))", "", inner_text)

    # 6. Normalizzazione operatori matematici e caratteri XML problematici in Mermaid
    inner_text = inner_text.replace('&', ' and ')
    inner_text = inner_text.replace('<=', '≤').replace('>=', '≥')
    inner_text = inner_text.replace('<>', '≠')
    inner_text = inner_text.replace('<', 'lt ').replace('>', 'gt ')

    # 7. Conversione quadre e graffe annidate a parentesi tonde
    inner_text = re.sub(r'\[([^\]]*)\]', r'(\1)', inner_text)
    inner_text = re.sub(r'\{([^\}]*)\}', r'(\1)', inner_text)

    # 8. Conversione frecce interne a trattino
    inner_text = re.sub(r'\s*(?:->|—)\s*', ' - ', inner_text)

    # 9. Ripristino del tag <br/> se protetto
    if preserve_br:
        inner_text = inner_text.replace(br_placeholder, '<br/>')

    # 10. Normalizzazione whitespace
    inner_text = re.sub(r'[ \t]+', ' ', inner_text).strip()
    return inner_text


def _clean_edge_label(edge_label: str) -> str:
    """
    Pulisce specificamente le etichette degli archi Mermaid (|label|),
    rimuovendo parentesi, operatori di confronto e caratteri che corrompono il lexer.
    # ARCHITETTURA: Le etichette degli archi devono rimanere rigidamente su una singola riga
    # senza tag <br/> per non rompere il calcolo delle spline in Dagre.
    """
    lbl = _clean_mermaid_label(edge_label, preserve_br=False)
    # Rimuove parentesi tonde che mandano in crash il parser delle etichette degli archi
    lbl = lbl.replace('(', '- ').replace(')', '')
    lbl = lbl.replace('|', '/')
    lbl = re.sub(r'\s+', ' ', lbl).strip()
    return lbl


def is_light_hex(hex_str: str) -> bool:
    """
    Determina se un valore di colore rappresenta uno sfondo chiaro,
    richiedendo testo scuro (color:#0f172a) per garantire il contrasto WCAG AA sia in Light che in Dark Mode.
    """
    clean_hex = hex_str.strip().lstrip('#')
    if len(clean_hex) == 3:
        clean_hex = ''.join([c * 2 for c in clean_hex])
    if len(clean_hex) == 6:
        try:
            r = int(clean_hex[0:2], 16)
            g = int(clean_hex[2:4], 16)
            b = int(clean_hex[4:6], 16)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            return lum > 140
        except ValueError:
            pass
    dark_names = {'black', 'navy', 'darkblue', 'maroon', 'indigo', 'midnightblue', 'darkslategray', 'darkslategrey'}
    if hex_str.strip().lower() in dark_names:
        return False
    return True


def convert_mindmap_to_flowchart(content: str) -> str:

    """
    Converte deterministicamente un diagramma Mermaid 'mindmap' in un albero tassonomico 'graph TD'
    ad alta leggibilità e densità concettuale ottimale per Notion.
    # ARCHITETTURA: Un mindmap non strutturato può contenere decine di micro-nodi a 4-5 livelli di
    # profondità che, renderizzati in un unico grafo piatto, espandono l'SVG oltre 3000px di larghezza.
    # Scalato da Notion al container di lettura (700-900px), il testo si rimpicciolisce a 2-3px risultando illeggibile.
    # Raggruppiamo i rami di livello 1 in 'subgraph' modulari e limitiamo la profondità dei nodi atomici
    # a massimo 2 livelli, condensando i micro-dettagli di livello 3+ nei nodi padre per garantire font grandi e nitidi.
    """
    lines = content.splitlines()

    classes = [
        'classDef rootNode fill:#0f172a,stroke:#334155,stroke-width:2px,color:#fff;',
        'classDef theoryNode fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px,color:#1e3a8a;',
        'classDef pipelineNode fill:#f5f3ff,stroke:#8b5cf6,stroke-width:1.5px,color:#4c1d95;',
        'classDef computeNode fill:#fef3c7,stroke:#f59e0b,stroke-width:1.5px,color:#78350f;',
        'classDef devopsNode fill:#f0fdf4,stroke:#10b981,stroke-width:1.5px,color:#064e3b;',
    ]
    color_cycle = ['theoryNode', 'pipelineNode', 'computeNode', 'devopsNode']

    raw_items = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.lower() == 'mindmap':
            continue
        indent = len(line) - len(line.lstrip(" "))
        raw_text = stripped
        if raw_text.startswith('root((') and raw_text.endswith('))'):
            raw_text = raw_text[6:-2]
        elif (raw_text.startswith('["') and raw_text.endswith('"]')) or (raw_text.startswith('("') and raw_text.endswith('")')):
            raw_text = raw_text[2:-2]
        elif (raw_text.startswith('[') and raw_text.endswith(']')) or (raw_text.startswith('(') and raw_text.endswith(')')):
            raw_text = raw_text[1:-1]
        label = _clean_mermaid_label(raw_text)
        if label:
            raw_items.append((indent, label))

    if not raw_items:
        return "graph TD\n  N1[\"Empty Concept\"]\n"

    # Ricostruzione albero logico con livelli
    tree_nodes = []
    stack = []
    for idx, (indent, label) in enumerate(raw_items):
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent_idx = stack[-1][1] if stack else None
        level = 0 if not stack else tree_nodes[parent_idx]['level'] + 1
        node_info = {
            'id': f"N{idx+1}",
            'label': label,
            'level': level,
            'parent_idx': parent_idx,
            'children': [],
        }
        tree_nodes.append(node_info)
        if parent_idx is not None:
            tree_nodes[parent_idx]['children'].append(idx)
        stack.append((indent, idx))

    root = tree_nodes[0]
    root_label = wrap_mermaid_label(_clean_mermaid_label(root['label'], preserve_br=True), max_chars_per_line=16)

    result = [
        "%%{init: {'flowchart': {'htmlLabels': false}}}%%",
        "graph TD"
    ]
    result.extend([f"  {c}" for c in classes])
    result.append("")
    result.append(f'  ROOT["{root_label}"]:::rootNode')
    result.append("")

    lvl1_indices = root['children']
    root_links = []
    inter_sg_links = []
    prev_sg_last_node = None

    for p_i, p_idx in enumerate(lvl1_indices):
        pillar = tree_nodes[p_idx]
        cls = color_cycle[p_i % len(color_cycle)]
        sg_slug = f"SG_{p_i+1}"
        p_label = _clean_mermaid_label(pillar['label'], preserve_br=False)
        sg_title = f"{p_i+1}. {p_label}"

        result.append(f'  subgraph {sg_slug} ["{sg_title}"]')

        l2_indices = pillar['children']
        sg_nodes = []
        if not l2_indices:
            nid = pillar['id']
            p_wrapped = wrap_mermaid_label(_clean_mermaid_label(p_label, preserve_br=True), max_chars_per_line=16)
            result.append(f'    {nid}["{p_wrapped}"]:::{cls}')
            sg_nodes.append(nid)
        else:
            for c_idx in l2_indices:
                child = tree_nodes[c_idx]
                cid = child['id']
                sg_nodes.append(cid)

                # ARCHITETTURA: Prevenzione del text-clipping SVG nei box a larghezza fissa di Notion.
                # Nei blocchi Notion, etichette superiori a 16-18 caratteri su singola riga causano lo straripamento
                # (overflow) del testo rispetto al rettangolo SVG calcolato, con troncamento visivo delle ultime parole.
                # Suddividiamo deterministicamente con wrap_mermaid_label a confine di parola intera con <br/>.
                clean_child = child['label'].strip()
                detail_strs = [tree_nodes[sub_idx]['label'].strip() for sub_idx in child['children']]
                if detail_strs and len(clean_child) <= 25:
                    first_det = detail_strs[0]
                    candidate = f"{clean_child} - {first_det}"
                    if len(candidate) <= 40:
                        full_label = candidate
                    else:
                        full_label = clean_child
                else:
                    full_label = clean_child

                # Se supera 40 caratteri, tronca a confine di parola intera senza '...'
                if len(full_label) > 40:
                    words = full_label.split()
                    kept = []
                    cur = 0
                    for w in words:
                        if cur + len(w) + (1 if kept else 0) > 38:
                            break
                        kept.append(w)
                        cur += len(w) + (1 if len(kept) > 1 else 0)
                    full_label = " ".join(kept) if kept else clean_child[:38]

                full_wrapped = wrap_mermaid_label(_clean_mermaid_label(full_label, preserve_br=True), max_chars_per_line=16)
                result.append(f'    {cid}["{full_wrapped}"]:::{cls}')


            # PERFORMANCE/LAYOUT: Catena sequenziale top-down dei nodi interni per evitare
            # allineamento orizzontale su un'unica riga larga migliaia di pixel.
            if len(sg_nodes) > 1:
                result.append(f"    {' --> '.join(sg_nodes)}")

        result.append("  end\n")

        # ARCHITETTURA: Impilamento rigorosamente verticale (Top-Down) a colonna singola.
        # Notion inserisce i grafi SVG in una colonna a larghezza fissa (700-900px).
        # Se i subgraph sono disposti in parallelo dal ROOT ('l'uno accanto all'altro'),
        # l'SVG complessivo supera i 2000px e viene scalato del 60-70%, rendendo i caratteri microscopici.
        # Concatenando i cluster in cascata verticale progressiva (ROOT -> SG1 -> SG2 -> SG3),
        # la larghezza massima resta ≤ 400px e i font vengono renderizzati a dimensione nativa (100% leggibile).
        first_node = sg_nodes[0] if sg_nodes else None
        last_node = sg_nodes[-1] if sg_nodes else None

        if p_i == 0:
            if first_node:
                root_links.append(('ROOT', first_node))
        else:
            if prev_sg_last_node and first_node:
                inter_sg_links.append((prev_sg_last_node, first_node))

        if last_node:
            prev_sg_last_node = last_node

    for r_from, r_to in root_links:
        result.append(f"  {r_from} --> {r_to}")
    for s_from, s_to in inter_sg_links:
        result.append(f"  {s_from} --> {s_to}")

    return "\n".join(result)


def sanitize_mermaid_mindmap(content: str) -> str:
    """
    Funzione retrocompatibile per sanitizzare diagrammi mindmap Mermaid.
    Delega direttamente a convert_mindmap_to_flowchart per garantire il rendering in Notion.
    """
    return convert_mindmap_to_flowchart(content)


def sanitize_mermaid_flowchart(content: str) -> str:
    """
    Sanitizza diagrammi di flusso Mermaid (graph TD / flowchart TD) per Notion e renderer web.
    # ARCHITETTURA: Nei flowchart Mermaid elaborati con motore ELK (Eclipse Layout Kernel) o Dagre
    # in Notion, si verificano crash sistematici 'TypeError: Cannot read properties of null (reading \'re\')':
    # 1. Direttive `style <subgraphId>` su cluster/subgraph: ELK cerca la shape nella tabella nodi atomici,
    #    restituisce null e manda in crash il layout engine. Esse vengono scartate deterministicamente.
    # 2. Tag HTML inline (<span style=...>, <br/>, <b>): rompono il calcolo geometrico delle bounding box SVG.
    # 3. Archi cross-subgraph dichiarati all'interno di un subgraph: causano conflitti di gerarchia ad albero
    #    multi-genitore in Dagre/ELK; vengono estratti e spostati (hoisted) a livello radice.
    # 4. Forme di nodo non standard (tonde, doppie tonde, rombi, stadi) non quotate: vengono normalizzate.
    # 5. Sintassi frecce con etichetta non standard (`-- "label" -->`): normalizzate a `-->|label|`.
    # 6. Archi puntati a ID di subgraph: re-indirizzati al primo nodo concreto del subgraph.
    # 7. Pulizia proprietà style: rimozione proprietà non SVG (es. font-weight) che causano parse error.
    """
    content = content.replace("\ufffd", " - ").replace("\u00a0", " ")
    lines = content.splitlines()

    # Pass 1: Identificazione preventiva di tutti i subgraph e dei rispettivi nodi membri
    subgraph_map: Dict[str, Optional[str]] = {}
    subgraph_nodes: Dict[str, set] = {}
    all_declared_nodes = set()
    current_sg: Optional[str] = None

    for line in lines:
        stripped = line.strip()
        m_sub = re.match(r'^subgraph\s+([A-Za-z0-9_]+)', stripped, re.IGNORECASE)
        if m_sub:
            current_sg = m_sub.group(1)
            if current_sg not in subgraph_map:
                subgraph_map[current_sg] = None
                subgraph_nodes[current_sg] = set()
            continue
        if stripped.lower() == 'end':
            current_sg = None
            continue
        if current_sg:
            m_node = re.search(r'\b([A-Za-z0-9_]+)\s*(\[|\(|\{|\(\(|\[\(|\{\{)', stripped)
            if m_node and m_node.group(1).lower() not in ('style', 'subgraph', 'end', 'direction', 'classdef', 'class'):
                nid = m_node.group(1)
                subgraph_nodes[current_sg].add(nid)
                all_declared_nodes.add(nid)
                if subgraph_map[current_sg] is None:
                    subgraph_map[current_sg] = nid

    sanitized_lines = []
    cross_sg_edges = []
    in_subgraph = False
    current_sg_id = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sanitized_lines.append(line)
            continue

        indent = len(line) - len(line.lstrip(" "))
        indent_str = " " * indent

        # Rimuove punto e virgola finale ridondante a fine riga
        line_clean = re.sub(r';\s*$', '', stripped)

        # ARCHITETTURA: Normalizzazione layout orizzontale in Top-Down verticale.
        # Grafi 'graph LR' o 'flowchart LR' esplodono in larghezza e causano il downscaling
        # aggressivo dell'SVG in Notion, rendendo i caratteri microscopici.
        if re.match(r'^(graph|flowchart)\s+LR\b', line_clean, re.IGNORECASE):
            line_clean = re.sub(r'^(graph|flowchart)\s+LR\b', r'\1 TD', line_clean, flags=re.IGNORECASE)

        # 1. Normalizzazione Subgraph Header

        m_sub = re.match(r'^subgraph\s+(.+)$', line_clean, re.IGNORECASE)
        if m_sub:
            in_subgraph = True
            sub_body = m_sub.group(1).strip()
            # Caso a: ID con titolo tra parentesi quadre
            m_id_bracket = re.match(r'^([A-Za-z0-9_]+)\s*\[(.*)\]$', sub_body)
            if m_id_bracket:
                sid = m_id_bracket.group(1)
                stitle = _clean_mermaid_label(m_id_bracket.group(2), preserve_br=False)
                current_sg_id = sid
                sanitized_lines.append(f'{indent_str}subgraph {sid} ["{stitle}"]')
                continue
            # Caso b: solo titolo tra virgolette senza ID
            m_quoted_only = re.match(r'^"([^"]+)"$', sub_body)
            if m_quoted_only:
                stitle = _clean_mermaid_label(m_quoted_only.group(1), preserve_br=False)
                slug = "sg_" + re.sub(r'[^A-Za-z0-9_]+', '_', stitle).strip('_')
                current_sg_id = slug
                sanitized_lines.append(f'{indent_str}subgraph {slug} ["{stitle}"]')
                continue
            # Caso c: singolo identificatore alfanumerico
            if re.match(r'^[A-Za-z0-9_]+$', sub_body):
                current_sg_id = sub_body
                sanitized_lines.append(f"{indent_str}subgraph {sub_body}")
                continue
            # Caso d: titolo con parole multiple non quotato
            stitle = _clean_mermaid_label(sub_body, preserve_br=False)
            slug = "sg_" + re.sub(r'[^A-Za-z0-9_]+', '_', stitle).strip('_')
            current_sg_id = slug
            sanitized_lines.append(f'{indent_str}subgraph {slug} ["{stitle}"]')
            continue

        if stripped.lower() == 'end':
            in_subgraph = False
            current_sg_id = None
            sanitized_lines.append(f"{indent_str}end")
            continue

        # 2. Direttiva style: sanitizza le proprietà SVG valide e scarta style sui subgraph
        m_style = re.match(r'^style\s+([A-Za-z0-9_]+)\s+(.+)$', line_clean, re.IGNORECASE)
        if m_style:
            target_id = m_style.group(1)
            if target_id in subgraph_map:
                continue
            raw_props = m_style.group(2).strip()
            valid_props = []
            has_color = False
            fill_val = None
            for p in raw_props.split(','):
                p = p.strip()
                if not p:
                    continue
                k = p.split(':')[0].strip().lower() if ':' in p else ''
                v = p.split(':')[1].strip() if ':' in p else ''
                if k == 'color':
                    has_color = True
                if k == 'fill':
                    fill_val = v
                if k in ('fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'color', 'rx', 'ry'):
                    valid_props.append(p)

            # ARCHITETTURA: Risoluzione del contrasto per Notion Dark Mode.
            # Se la direttiva 'style' definisce uno sfondo 'fill' ma omette 'color:',
            # Notion Dark Mode applica il font bianco (#ffffff) di default del tema scuro,
            # rendendo il testo invisibile su sfondi pastello chiari (#add8e6, #c8e6c9, etc.).
            # Iniettiamo deterministicamente color:#0f172a per sfondi chiari e color:#ffffff per sfondi scuri.
            if fill_val and not has_color and fill_val.lower() not in ('none', 'transparent'):
                if is_light_hex(fill_val):
                    valid_props.append("color:#0f172a")
                else:
                    valid_props.append("color:#ffffff")

            if valid_props:
                sanitized_lines.append(f"{indent_str}style {target_id} {','.join(valid_props)}")
            continue


        # 3. Normalizzazione frecce con label:
        # Trasforma `A -- "label" --> B` o `A -- label --> B` in standard universale `A -->|label| B`
        def _normalize_edge_labels(l: str) -> str:
            p_labeled = r'--\s*(?:\||"|)?(.*?)(?:\||"|)?\s*(-->|---|-.->|==>)'
            def rep_edge(m):
                lbl = _clean_edge_label(m.group(1))
                arr = m.group(2)
                return f'{arr}|{lbl}|'
            return re.sub(p_labeled, rep_edge, l)

        line_clean = _normalize_edge_labels(line_clean)

        # 4. Riconoscimento e sanitizzazione dei nodi in tutte le forme grafiche
        arrow_pattern = r'(\s*(?:-->|---|-.->|-.-|==>|==)(?:\|[^|\n]+\|)?\s*)'
        parts = re.split(arrow_pattern, line_clean)
        cleaned_parts = []
        is_edge_line = len(parts) > 1

        for part in parts:
            if re.match(r'^\s*(?:-->|---|-.->|-.-|==>|==)', part):
                m_edge_lbl = re.match(r'^(\s*(?:-->|---|-.->|-.-|==>|==)\|)([^|\n]+)(\|\s*)$', part)
                if m_edge_lbl:
                    clean_elbl = _clean_edge_label(m_edge_lbl.group(2))
                    part = f'{m_edge_lbl.group(1)}{clean_elbl}{m_edge_lbl.group(3)}'
                cleaned_parts.append(part)
                continue

            semicolon = ";" if part.rstrip().endswith(";") else ""
            clean_part = re.sub(r';\s*$', '', part).strip()
            if not clean_part:
                cleaned_parts.append(part)
                continue

            # ARCHITETTURA: Estrazione preventiva di annotazioni di stile di classe (:::className)
            # per consentire il parsing pulito della shape del nodo e ri-agganciarla all'uscita.
            class_suffix = ""
            m_cls = re.search(r':::([A-Za-z0-9_]+)$', clean_part)
            if m_cls:
                class_suffix = f":::{m_cls.group(1)}"
                clean_part = clean_part[:m_cls.start()].strip()

            # a) Double circle (( ... ))
            m_dcircle = re.match(r'^([A-Za-z0-9_]+)\s*\(\((.*)\)\)$', clean_part)
            # b) Stadium ([ ... ])
            m_stadium = re.match(r'^([A-Za-z0-9_]+)\s*\(\[(.*)\]\)$', clean_part)
            # c) Cylinder [( ... )]
            m_cylinder = re.match(r'^([A-Za-z0-9_]+)\s*\[\((.*)\)\]$', clean_part)
            # d) Hexagon {{ ... }}
            m_hex = re.match(r'^([A-Za-z0-9_]+)\s*\{\{(.*)\}\}$', clean_part)
            # e) Rhombus { ... }
            m_rhombus = re.match(r'^([A-Za-z0-9_]+)\s*\{(.*)\}$', clean_part)
            # f) Circle / Rounded ( ... )
            m_round = re.match(r'^([A-Za-z0-9_]+)\s*\((.*)\)$', clean_part)
            # g) Square [ ... ]
            m_bracket = re.match(r'^([A-Za-z0-9_]+)\s*\[(.*)\]$', clean_part)

            if m_dcircle:
                nid, text = m_dcircle.group(1), wrap_mermaid_label(_clean_mermaid_label(m_dcircle.group(2), preserve_br=True), max_chars_per_line=18)
                part = f'{nid}(("{text}")){class_suffix}{semicolon}'
            elif m_stadium:
                nid, text = m_stadium.group(1), wrap_mermaid_label(_clean_mermaid_label(m_stadium.group(2), preserve_br=True), max_chars_per_line=18)
                part = f'{nid}(["{text}"]){class_suffix}{semicolon}'
            elif m_cylinder:
                nid, text = m_cylinder.group(1), wrap_mermaid_label(_clean_mermaid_label(m_cylinder.group(2), preserve_br=True), max_chars_per_line=18)
                part = f'{nid}[("{text}")]{class_suffix}{semicolon}'
            elif m_hex:
                nid, text = m_hex.group(1), wrap_mermaid_label(_clean_mermaid_label(m_hex.group(2), preserve_br=True), max_chars_per_line=18)
                part = f'{nid}{{"{text}"}}{class_suffix}{semicolon}'
            elif m_rhombus:
                nid, text = m_rhombus.group(1), wrap_mermaid_label(_clean_mermaid_label(m_rhombus.group(2), preserve_br=True), max_chars_per_line=18)
                part = f'{nid}{{"{text}"}}{class_suffix}{semicolon}'
            elif m_round:
                nid, text = m_round.group(1), wrap_mermaid_label(_clean_mermaid_label(m_round.group(2), preserve_br=True), max_chars_per_line=18)
                part = f'{nid}("{text}"){class_suffix}{semicolon}'
            elif m_bracket:
                nid, text = m_bracket.group(1), wrap_mermaid_label(_clean_mermaid_label(m_bracket.group(2), preserve_br=True), max_chars_per_line=18)
                part = f'{nid}["{text}"]{class_suffix}{semicolon}'

            cleaned_parts.append(part)

        line_clean = "".join(cleaned_parts)

        # 5. Re-indirizzamento archi che puntano a subgraph ID invece che a nodi concreti
        for sg_id, first_node in subgraph_map.items():
            if first_node:
                line_clean = re.sub(rf'\b{sg_id}\s*(-->|---|-.->|==>)\s*', f'{first_node} \\1 ', line_clean)
                line_clean = re.sub(rf'\s*(-->|---|-.->|==>)\s*{sg_id}\b', f' \\1 {first_node}', line_clean)

        # 6. Hoisting degli archi cross-subgraph:
        # Se un arco dichiarato dentro un subgraph fa riferimento a un nodo dichiarato altrove,
        # estrailo fuori dal cluster per non inquinare la gerarchia compound in Dagre/ELK
        if in_subgraph and is_edge_line and current_sg_id:
            edge_nodes = re.findall(r'\b([A-Za-z0-9_]+)\b', line_clean)
            has_external_node = False
            for en in edge_nodes:
                if en in all_declared_nodes and en not in subgraph_nodes.get(current_sg_id, set()):
                    has_external_node = True
                    break
            if has_external_node:
                cross_sg_edges.append(line_clean.strip())
                continue

        sanitized_lines.append(f"{indent_str}{line_clean}")

    # Aggiungi in coda eventuali archi cross-subgraph hoisted
    if cross_sg_edges:
        sanitized_lines.append("")
        sanitized_lines.append("  %% Cross-subgraph edges hoisted for ELK/Dagre hierarchy stability")
        for edge in cross_sg_edges:
            sanitized_lines.append(f"  {edge}")

    res = "\n".join(sanitized_lines)
    # ARCHITETTURA: Risoluzione del clipping del testo in Notion (SVG foreignObject bug).
    # Disabilitando htmlLabels, Mermaid genera elementi nativi SVG <text> e <tspan>
    # anziché box <foreignObject> a larghezza fissa che tagliano le parole a ~16 caratteri.
    if not res.strip().startswith("%%{init:"):
        res = f"%%{{init: {{'flowchart': {{'htmlLabels': false}}}}}}%%\n{res}"
    return res


def build_notion_blocks(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Parses full Markdown text into a list of Notion-compliant block dictionaries.
    Supports:
      - Multiline and single-line LaTeX display equations ($$...$$)
      - Fenced code blocks (```lang ... ```)
      - GFM Tables (| header | ... |) rendered to native Notion table blocks
      - Blockquotes (> ...)
      - Headings (H1, H2, H3) with automatic dividers
      - Bulleted and numbered lists
      - Horizontal dividers (---)
      - Standard paragraphs with rich_text formatting
    """
    blocks: List[Dict[str, Any]] = []
    lines = markdown_text.splitlines()

    in_display_math = False
    display_math_buf: List[str] = []

    in_code_block = False
    code_block_lang = "plain text"
    code_block_buf: List[str] = []

    table_buf: List[str] = []

    # ARCHITETTURA: Stack di indentazione per preservare la gerarchia ad albero dei bullet points
    # e delle liste numerate verso Notion. Notion accetta 'children' annidati all'interno del blocco genitore.
    list_root_blocks: List[Dict[str, Any]] = []
    list_stack: List[Dict[str, Any]] = [
        {"indent": -1, "type": "root", "payload": None, "children": list_root_blocks}
    ]

    def flush_list() -> None:
        nonlocal list_root_blocks, list_stack
        if list_root_blocks:
            blocks.extend(list_root_blocks)
            list_root_blocks = []
        list_stack = [
            {"indent": -1, "type": "root", "payload": None, "children": list_root_blocks}
        ]

    def flush_table() -> None:
        nonlocal table_buf
        if not table_buf:
            return

        # ARCHITETTURA: Conformità alle specifiche Notion API per il blocco 'table'.
        # Richiede table_width costante e ogni riga table_row con lista di celle corrispondente.
        if len(table_buf) >= 2 and is_table_separator(table_buf[1]):
            headers = split_table_row(table_buf[0])
            table_width = len(headers)
            if table_width > 0:
                header_cells = [parse_rich_text(c) if c else [] for c in headers]
                row_children = [
                    {
                        "type": "table_row",
                        "table_row": {"cells": header_cells}
                    }
                ]
                for row_line in table_buf[2:]:
                    if is_table_separator(row_line):
                        continue
                    cells = split_table_row(row_line)
                    # TRADE-OFF: Normalizzazione difensiva della larghezza per prevenire
                    # HTTP 400 da Notion API in caso di righe con colonne disallineate.
                    if len(cells) < table_width:
                        cells.extend([""] * (table_width - len(cells)))
                    else:
                        cells = cells[:table_width]
                    row_cells = [parse_rich_text(c) if c else [] for c in cells]
                    row_children.append({
                        "type": "table_row",
                        "table_row": {"cells": row_cells}
                    })

                blocks.append({
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": table_width,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": row_children
                    }
                })
                table_buf = []
                return

        # TRADE-OFF: Se la struttura non è una tabella GFM valida, degrada a paragrafi
        # individuali preservando l'integrità del testo originale senza scartare contenuti.
        for raw_line in table_buf:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": parse_rich_text(raw_line)},
            })
        table_buf = []

    for line_idx, line in enumerate(lines):
        s = line.strip()

        # ── Code Block Handling ──────────────────────────────────────────────
        if s.startswith("```"):
            flush_table()
            flush_list()
            if in_code_block:
                # Close code block
                full_code = "\n".join(code_block_buf)
                if code_block_lang == "mermaid":
                    if "mindmap" in full_code:
                        full_code = sanitize_mermaid_mindmap(full_code)
                    elif "graph" in full_code or "flowchart" in full_code:
                        full_code = sanitize_mermaid_flowchart(full_code)

                # ARCHITETTURA: Notion API supporta fino a 100 elementi rich_text (ciascuno max 2000 chars)
                # all'interno dello STESSO blocco code (capienza complessiva fino a 200.000 caratteri).
                # Chunkare su blocchi multipli spezza irrimediabilmente la continuità di script e diagrammi Mermaid.
                # Raggruppiamo i chunk nella lista rich_text di un singolo blocco code.
                rich_text_chunks: List[Dict[str, Any]] = []
                while full_code:
                    chunk = full_code[:NOTION_MAX_BLOCK_CHARS]
                    full_code = full_code[NOTION_MAX_BLOCK_CHARS:]
                    rich_text_chunks.append({"type": "text", "text": {"content": chunk}})
                    if len(rich_text_chunks) == 100:
                        blocks.append({
                            "object": "block",
                            "type": "code",
                            "code": {
                                "language": code_block_lang,
                                "rich_text": rich_text_chunks,
                            },
                        })
                        rich_text_chunks = []

                if rich_text_chunks:
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": code_block_lang,
                            "rich_text": rich_text_chunks,
                        },
                    })

                code_block_buf = []
                in_code_block = False
                continue
            else:
                # Open code block
                raw_lang = s[3:].strip().lower()
                code_block_lang = raw_lang if raw_lang in NOTION_SUPPORTED_LANGUAGES else "plain text"
                if raw_lang == "py":
                    code_block_lang = "python"
                elif raw_lang in ("sh", "zsh"):
                    code_block_lang = "shell"
                in_code_block = True
                code_block_buf = []
                continue

        if in_code_block:
            code_block_buf.append(line)  # Preserve original indentation
            continue

        # ── Display Math ($$...$$) ──────────────────────────────────────────
        if s == "$$":
            flush_table()
            flush_list()
            if in_display_math:
                expr = "\n".join(display_math_buf).strip()
                blocks.append({
                    "object": "block",
                    "type": "equation",
                    "equation": {"expression": expr[:NOTION_MAX_BLOCK_CHARS]},
                })
                display_math_buf = []
                in_display_math = False
            else:
                in_display_math = True
            continue

        if in_display_math:
            display_math_buf.append(s)
            continue

        # Single line $$equation$$
        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            flush_table()
            flush_list()
            expr = s[2:-2].strip()
            blocks.append({
                "object": "block",
                "type": "equation",
                "equation": {"expression": expr[:NOTION_MAX_BLOCK_CHARS]},
            })
            continue

        # ── Blank Line Handling ──────────────────────────────────────────────
        if not s or s.isspace():
            if table_buf:
                # TOLERANCE: Se stiamo parsando una tabella, controlliamo se la prossima
                # riga non vuota è ancora parte della tabella (es. newline accidentali tra righe).
                next_non_empty = None
                for peek_line in lines[line_idx + 1:]:
                    peek_s = peek_line.strip()
                    if peek_s:
                        next_non_empty = peek_s
                        break
                if next_non_empty and next_non_empty.startswith("|") and "|" in next_non_empty[1:]:
                    continue
                else:
                    flush_table()
            continue

        # ── Markdown Table Lines (| ... |) ───────────────────────────────────
        if s.startswith("|") and "|" in s[1:]:
            flush_list()
            table_buf.append(s)
            continue
        else:
            flush_table()

        # ── Horizontal Divider ──────────────────────────────────────────────
        if s == "---":
            flush_list()
            if blocks and blocks[-1]["type"] != "divider":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue

        # ── Blockquote ──────────────────────────────────────────────────────
        if s.startswith(">"):
            flush_list()
            content = s[1:].strip()
            if content:
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": parse_rich_text(content)},
                })
            continue

        # ── Headings with Dividers ──────────────────────────────────────────
        if s.startswith("# ") and not s.startswith("## "):
            flush_list()
            if blocks and blocks[-1]["type"] != "divider":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            content = s[2:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        if s.startswith("## ") and not s.startswith("### "):
            flush_list()
            if blocks and blocks[-1]["type"] != "divider":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            content = s[3:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        if s.startswith("### "):
            flush_list()
            content = s[4:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # Fallback for H4 (Notion does not have heading_4; downgrade to heading_3)
        if s.startswith("#### "):
            flush_list()
            content = s[5:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # ── Lists & Indented Hierarchy ──────────────────────────────────────
        expanded = line.expandtabs(4)
        l_stripped = expanded.lstrip(" ")
        indent = len(expanded) - len(l_stripped)

        bullet_match = re.match(r"^[-*+]\s+(.*)$", l_stripped)
        num_match = re.match(r"^(\d+[.)])\s+(.*)$", l_stripped)

        if bullet_match or num_match:
            flush_table()
            item_type = "bulleted_list_item" if bullet_match else "numbered_list_item"
            content = bullet_match.group(1).strip() if bullet_match else num_match.group(2).strip()
            new_block = {
                "object": "block",
                "type": item_type,
                item_type: {
                    "rich_text": parse_rich_text(content)
                }
            }

            # ARCHITETTURA: Gestione della gerarchia ad albero tramite stack di indentazione.
            # Riavvolge lo stack finché l'indentazione dell'elemento in cima è strettamente minore
            # di quella della riga corrente, identificando il corretto nodo genitore.
            while len(list_stack) > 1 and indent <= list_stack[-1]["indent"]:
                list_stack.pop()

            parent = list_stack[-1]
            if parent["payload"] is not None and "children" not in parent["payload"]:
                parent["payload"]["children"] = parent["children"]

            parent["children"].append(new_block)

            # TRADE-OFF: Notion API impone un vincolo rigido di massimo 2 livelli di nidificazione
            # all'interno di una singola chiamata 'append block children' (radice -> figli -> nipoti).
            # Limitando la profondità dello stack a 2 (len(list_stack) < 3), qualsiasi ulteriore sotto-livello
            # viene posizionato come elemento affine evitando errori HTTP 400 (validation_error).
            if len(list_stack) < 3:
                list_stack.append({
                    "indent": indent,
                    "type": item_type,
                    "payload": new_block[item_type],
                    "children": []
                })
            continue

        # ── List Continuation Handling ──────────────────────────────────────
        # Se una riga di testo è indentata (>= 2 spazi) e segue un elemento di lista attivo,
        # la accorpiamo all'elemento corrente per preservare la numerazione e il flusso logico.
        if len(list_stack) > 1 and indent >= 2 and not s.startswith(("#", "```", "$$", ">", "|", "---", "![")):
            parent = list_stack[-1]
            if parent["payload"] is not None:
                parent["payload"]["rich_text"].append({"type": "text", "text": {"content": " "}})
                parent["payload"]["rich_text"].extend(parse_rich_text(s))
                continue

        # ── Images ──────────────────────────────────────────────────────────
        # ARCHITETTURA: Riconoscimento del blocco immagine nativo Notion.
        # Supporta URL esterni con schema http/https e preserva la didascalia (alt text)
        # come rich_text dedicato nel payload del blocco image.
        img_match = re.match(r'^!\[([^\]]*)\]\((https?://[^\s\)]+)\)\.?$', s)
        if img_match:
            flush_list()
            img_url = img_match.group(2)
            img_block: Dict[str, Any] = {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": img_url}
                }
            }
            if img_match.group(1):
                caption_text = img_match.group(1).strip()
                # ARCHITETTURA: Soppressione didascalie boilerplate/generiche (es. 'Figura slide 8', 'Slide 8')
                is_boilerplate = bool(
                    re.match(r'^(figura|figure)?\s*(slide\s*)?\d+$', caption_text, re.IGNORECASE)
                    or re.match(r'^brief technical caption$', caption_text, re.IGNORECASE)
                )
                if caption_text and not is_boilerplate:
                    img_block["image"]["caption"] = parse_rich_text(caption_text)
            blocks.append(img_block)
            continue

        # ── Paragraph ───────────────────────────────────────────────────────
        flush_list()
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": parse_rich_text(s)},
        })

    flush_table()
    flush_list()
    return blocks
