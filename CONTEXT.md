# CONTEXT.md — PHD Prof

## Visione & Scopo del Progetto
ETL antifragile e crash-only per ingerire documenti e slide accademiche in formato PDF, sintetizzarli tramite LLM (Gemini) e archiviarli su Notion senza perdita di dati né duplicazione di token.

## Stato Attuale
- **Architettura**: Esagonale (Ports & Adapters) in src/.
- **Modello LLM**: Gemini 2.5 Flash con rate limiting e retry esponenziale.
- **Test**: 24 unit test offline con mock completi.

## Prossimi Passi
- Monitorare l'esecuzione batch in produzione su corsi reali Notion.
- Valutare eventuale caching vettoriale locale se la libreria di PDF cresce ulteriormente.

## Log delle Sessioni

### 2026-09-23 (Prompt & Block Builder: Airy Layout, Frequent H3, Italic Examples, Quotes)
- **Struttura Paragrafi Rilassati & Granularita H3**:
  - Aggiornati SLIDES_PROMPT_TEMPLATE e PAPER_OR_BOOK_PROMPT_TEMPLATE per imporre paragrafi ariosi (2-3 frasi max) che danno respiro ai concetti.
  - Vietati blocchi H2 massivi da 400-500 parole: imposto l'uso sistematico di sottosezioni ### [Emoji] (ogni ~120-180 parole o a cambi di layer/modello) per scandire visivamente la gerarchia.
- **Esempi Visivamente Distinti**:
  - Standardizzato il formato degli esempi in un paragrafo dedicato: **Example:** *[Scenario applicato in corsivo...]*.
  - Aggiornato parse_rich_text in notion_block_builder.py con supporto completo a *italic*, ***bold italic***, e code per convertire correttamente il corsivo nelle annotazioni Notion rich text.
- **Parti Salienti come Quote**:
  - Istruito il modello a racchiudere le massime teoriche, gli assiomi fondamentali e i trade-off critici in blocchi quote Markdown (> **Core Insight:** ...), resi su Notion come callout con barra verticale.
- **Test Suite**: Aggiunti 5 nuovi test di parsing rich text e formattazione blockquote in tests/test_notion_block_builder.py (24/24 test passati).

### 2026-09-22 (Prompt Enhancement: Fluid Narrative Flow & Grounded Examples)
- **Superamento del Formato Piatto**:
  - Aggiornato <task> in prompt_templates.py per imporre un arco narrativo logico e progressivo (percorso logico sensato), vietando esposizioni frammentate in soli bullet points o grassetti surrogati di titoli.
  - Introdotto lo stadio Grounded Examples: obbligo di ancorare modelli, framework e trade-off complessi a esempi concreti e realistici (es. migrazione legacy, disaccoppiamento API, cascate di errori) quando il concetto rischia di apparire astratto.
- **Narrative Flow & Delimitazione Bullet**:
  - In <formatting_rules>, la prosa in paragrafi coesi (2-4 frasi) diventa il veicolo principale di spiegazione; i bullet points sono rigorosamente confinati a inventari mirati di 3-6 elementi (proprieta, assiomi, componenti distinti).

### 2026-09-22 (Fix Formatting Inconsistencies & Divider Deduplication)
- **Deduplicazione Divider & H3**:
  - Aggiornato notion_block_builder.py per prevenire doppi divisori consecutivi (---).
  - Rimosso l'inserimento automatico del divisore prima dei sottotitoli H3 (###), garantendo continuita visiva con la sezione genitore H2.
- **Terminazione e Delimitazione Liste**:
  - Esplicitata nei prompt (prompt_templates.py) la regola di chiusura immediata delle liste (max 3-6 elementi) e ritorno ai paragrafi discorsivi senza bullet points persistenti.
- **Separazione Semantica Elenchi**:
  - Vietato il mix disordinato tra liste numerate e bullet points: numeri (1., 2.) riservati a sequenze cronologiche/step operativi, bullet (-) per insiemi non ordinati.
- **Spaziatura Punteggiatura & Paragrafi**:
  - Introdotta la funzione normalize_sentence_spacing in notion_block_builder.py per garantire lo spazio dopo la punteggiatura (., ,, :, ;).
  - Vincolato il prompt a raggruppare i periodi in paragrafi coesi di 2-4 frasi con spaziatura corretta.
- **Test Suite**: Aggiunti 3 nuovi test in tests/test_notion_block_builder.py per convalidare spaziatura, assenza di divisori duplicati e assenza di divisori prima di H3 (19/19 test superati).

### 2026-09-22 (Tutor-Universale Pedagogical Framework Integration)
- **Framework Didattico Evoluto**: Integrati nel prompt (prompt_templates.py) i 4 stadi cardine di 	utor-universale:
  1. *Inefficienza Risolta*: Esplicitare il problema originario, attrito o collo di bottiglia che il modello/teoria è nato per superare.
  2. *Modello Mentale & Meccanica*: Spiegare la struttura sistemica e le relazioni di causa-effetto, integrando organicamente slide notes (### Notes:) e piè di pagina.
  3. *Boundary Conditions (Inversione)*: Chiarire trade-off occulti e limiti operativi dove il concetto fallisce.
  4. *Decostruzione Formule/Parametri*: Spiegare analiticamente ogni variabile e coefficiente anziché presentare equazioni monolitiche.


### 2026-09-22 (PPTX Footnotes & Speaker Notes Integration)
- **Verifica Estrazione Note PPTX**: Confermato che MarkItDown estrae sia i piè di pagina delle slide sia le note del relatore (### Notes:) — rilevati 44 blocchi di note in EA2627-00-W1.pptx e 24 in EA2627-01-W1.pptx.
- **Istruzione Esplicita nel Prompt**: Aggiunta in SLIDES_PROMPT_TEMPLATE la direttiva per Gemini di integrare attivamente i dettagli esplicativi, le letture consigliate e gli insight presenti nelle note a piè di pagina e del relatore.


### 2026-09-22 (Prompt Engineering) — Ottimizzazione XML & Token-Efficiency
- **Ristrutturazione XML**: Applicata la skill prompt-engineering a prompt_templates.py, strutturando il prompt con tag semantici (<role>, <task>, <formatting_rules>, <input_data>).
- **Eliminazione Token Fluff**: Rimossi preamboli ridondanti ('Master in Science Communication', 'Previous ideal notes') e preservate al 100% tutte le regole operative: elenchi puntati a riga singola (-/*/1.), prefissi emoji su ##/###, formule LaTeX ($ e $$), code blocks, separatori --- e assenza di righe vuote.


### 2026-09-22 (Prompt Calibration) — Rimozione Moltiplicatore Fisso x1.3
- **Calibrazione Espansione Cognitiva**: Rimosso il vincolo arbitrario di espansione a 1.3x. L'espansione è ora vincolata rigorosamente al valore cognitivo e alla complessità intrinseca dei concetti, vietando padding o allungamenti forzati del testo.


### 2026-09-22 (Prompt Restore) — Ripristino Elenchi Puntati, Emoji e Dettaglio Pedagogico
- **Ripristino Prompt Ideale**: Rimosso il divieto assoluto di elenchi puntati (STRICTLY FORBIDDEN from using bullet points) in prompt_templates.py.
- **Formattazione Rich Notion**: Reinserite le regole originali per elenchi puntati standard (* e -), liste numerate (1.), prefisso emoji su ## e ###, separatori visuali ---, espansione a 1.3x con spiegazioni pedagogiche approfondite ed estrazione di tutte le formule matematiche ($ e ).


### 2026-09-22 (Hotfix) — Supporto PPTX & Correzione Parametro Upload Gemini
- **Fix Upload Gemini File API**: Corretto il parametro da ile=... a path=... in GeminiFileReader per piena conformità con google-genai SDK v0.6.0.
- **Supporto Nativo PPTX**: Estesa la scansione in CLIAdapter e il parsing in TextPdfReader (tramite MarkItDown) per supportare presentazioni PowerPoint (.pptx), estraendo sia il contenuto delle slide sia le note del relatore.
- **Test Suite**: Aggiunto 	est_process_document_pptx_routing, 16/16 test superati con successo.


### 2026-09-22 — Refactoring Esagonale, Dual PDF Reader & Anti-Overengineering Gate
- **Architettura Esagonale & SOLID**: Rifattorizzato il monolite pdf_to_notion.py in src/ disaccoppiando Core Domain, Use Cases (ProcessDocumentUseCase), Ports e Adapters (IDocumentReader, ILlmClient, INotionClient, IStateRepository, IStagingStorage).
- **Dual PDF Reading**: Supporto per SLIDES (upload multimodale Gemini File API per espansione pedagogica di grafici e layout) e PAPER_OR_BOOK (estrazione testuale/markdown locale con MarkItDown/PyMuPDF per paper densi e teoremi).
- **Ottimizzazione Blocchi Notion**: Parser Markdown -> Blocchi Notion potenziato con supporto per code blocks evidenziati, LaTeX math ($ e ), blockquotes, divisori e safe chunking a 1900 caratteri.
- **Testing Strategy**: Suite di 15 unit test (	ests/) con mock offline per tutte le porte, 100% superata in 0.23s.
- **Anti-Overengineering Gate**: Aggiornata la skill master-hexagonal-architecture con soglia minima esplicita e stop conditions per prevenire complessità prematura.

