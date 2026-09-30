# CONTEXT.md — PHD Prof

## Visione & Scopo del Progetto
ETL antifragile e crash-only per ingerire documenti e slide accademiche in formato PDF, sintetizzarli tramite LLM (Gemini) e archiviarli su Notion senza perdita di dati né duplicazione di token.

## Stato Attuale
- **Architettura**: Esagonale (Ports & Adapters) in src/.
- **Modello LLM**: Gemini 2.5 Flash con rate limiting, retry esponenziale e fallback automatico a 2.0/1.5 Flash.
- **Ingestione Multimodale PPTX**: Dual-Payload (rendering vettoriale PDF via PowerPoint COM + note a piè di pagina via python-pptx).
- **Persistent Course Profiles**: Invarianti di corso (materia, ruolo professorale, doc type, cartella locale, target Notion) memorizzati in `course_profiles.json` per avvio one-click a latenza zero.
- **Bilingual Interaction (IT vs EN)**: Modulo `I18n` disaccoppiato nell'inbound adapter per visualizzazione bilingue terminale senza impatto sul core.
- **Test**: 74 unit test offline con mock completi (100% passati).

## Prossimi Passi
- Monitorare l'esecuzione batch in produzione su corsi reali Notion.
- Valutare eventuale caching vettoriale locale se la libreria di PDF cresce ulteriormente.

## Log delle Sessioni

### 2026-09-30 (Bilingual Interaction Flag IT vs EN & Useful-Comments Audit)
- **Visualizzazione Bilingue Terminale (IT vs EN)**:
  - Introdotto il modulo di presentazione `I18n` ([i18n.py](file:///c:/Documenti/Bots/PHD_Prof/src/adapters/inbound/i18n.py)) che incapsula tutte le stringhe di visualizzazione CLI in italiano e inglese.
  - Risoluzione del flag a doppio livello: priorità al parametro CLI `--lang IT|EN`, con fallback sulla variabile d'ambiente `CLI_LANGUAGE=IT` in `.env`.
  - Zero impatto sui processi interni: il core domain, le use case, l'estrazione documenti e i prompt di sintesi didattica rimangono inalterati.
  - Parser di conferma bilingue: accetta indistintamente input affermativi (`s`, `si`, `y`, `yes`) e negativi (`n`, `no`).
- **Code Audit & Useful Comments**:
  - Applicata la skill `useful-comments` sull'intera codebase: eliminati commenti parafrasativi o banali, documentando il *perché* architetturale (scrittura atomica con swap `.tmp` per prevenire corruzione da crash, decontaminazione byte nulli `\x00` per stabilità gRPC, cascading waterfall resilient dei modelli LLM, disaccoppiamento visivo/testuale PPTX).
- **Test Suite**: Aggiunti 4 nuovi test in `tests/test_i18n.py`. Test suite complessiva: 74/74 passati in 2.27s.

### 2026-09-30 (Persistent Course Profiles & Fast CLI Selection)
- **Eliminazione Attrito Operativo & Discovery Overhead**:
  - Rimossa la necessità di re-inserire a ogni run materia, tipo di professore, doc type, cartella locale e navigazione ricorsiva delle API Notion.
  - Introdotto il domain model `CourseProfile` ([models.py](file:///c:/Documenti/Bots/PHD_Prof/src/core/domain/models.py)) che incapsula la tupla invariante di corso.
  - Creata la porta outbound `ICourseProfileRepository` e l'adapter `JsonCourseProfileRepository` ([json_course_profile_repository.py](file:///c:/Documenti/Bots/PHD_Prof/src/adapters/outbound/json_course_profile_repository.py)) per persistenza atomica su file locale `course_profiles.json` (aggiunto in `.gitignore`).
  - Aggiornato `CLIAdapter` ([cli_adapter.py](file:///c:/Documenti/Bots/PHD_Prof/src/adapters/inbound/cli_adapter.py)):
    - All'avvio elenca i corsi memorizzati con conteggio immediato dei file disponibili.
    - Selezione immediata (invio/numero) a zero latenza e zero chiamate di rete.
    - Supporto per override rapido (`m`), configurazione nuovo corso (`+`) e salvataggio automatico/richiesto al primo setup.
- **Testing**: Aggiunti 7 nuovi unit test in `tests/test_course_profile_repository.py` e `tests/test_cli_adapter_profiles.py`. Test suite complessiva: 70/70 passati in 2.9s.

### 2026-09-30 (Dual-Payload Multimodal Ingestion per Slide PPTX)
- **Risoluzione Visual Blindness su PPTX**:
  - Eliminato il collo di bottiglia che riduceva le presentazioni `.pptx` a puro testo Markdown, privando il modello della vista su diagrammi, grafici di sistema e schemi concettuali.
  - Implementato in `GeminiFileReader` il bridge di rendering PowerPoint COM (`win32com.client.Dispatch("PowerPoint.Application")`), con salvataggio vettoriale del PDF in cache locale (`staging/{file_hash}_slides.pdf`).
  - Mantenuta l'estrazione esaustiva delle note a piè di pagina e note dell'oratore tramite `extract_pptx_to_markdown`.
  - Inviato a Gemini un payload composito `[notes_text, uploaded_pdf]` che unisce simultaneamente percezione visiva delle forme e contesto testuale delle note.
- **Resilienza, Fallback & Idempotenza**:
  - *Caching locale*: se il PDF prerenderizzato è già presente in `staging/`, la conversione COM viene saltata.
  - *Fallback trasparente*: se PowerPoint COM non è disponibile (es. runtime non Windows o assenza di Office), la pipeline arretra automaticamente alla sola estrazione testuale senza interruzioni.
  - *Cleanup sicuro*: `GeminiFileReader.cleanup` itera su payload compositi eliminando ogni `genai_types.File` remoto al termine dell'inferenza.
  - *Sanitizzazione input*: `GeminiLlmAdapter` ripulisce da null byte ogni stringa presente in payload compositi.
- **Test Suite**: Aggiunti 6 nuovi test unitari in `tests/test_gemini_file_reader.py` e `tests/test_gemini_llm_adapter.py`. 63/63 test superati in 2.3s.

### 2026-09-29 (ArchiMate 3.2 Selective Reading Pipeline & Notion Sync)
- **Estrazione Selettiva Manuale ArchiMate 3.2**:
  - Estratte con precisione vettoriale le sezioni richieste per la lezione successiva: Ch 3 (3.3-3.4, 3.7-3.9), Ch 4 (4.5), Ch 5 (5.1-5.5 inclusa intro/connectors), Ch 8 (8.1-8.6).
  - Pagine complessive estratte: 38 (31-33, 35-36, 43-60, 82-96).
  - Generato PDF unico con albero segnalibri/TOC gerarchico completo (56 voci): [ArchiMate - Selected Sections (Ch 3, 4, 5, 8).pdf](file:///C:/Documenti/UNIMIB/Enterprise%20Architecture/ArchiMate_Selected_Sections/ArchiMate%20-%20Selected%20Sections%20(Ch%203,%204,%205,%208).pdf).
  - File salvato in ArchiMate_Selected_Sections/ e duplicato nella root del corso per consultazione diretta.
- **Esecuzione Pipeline Multimodale PHD_Prof**:
  - Ingestione multimodale via Gemini File API (6.3 MB) per preservare layout visivo, sintassi grafica, forme, frecce e diagrammi del metamodello.
  - Sintesi didattico-pedagogica ad alta densita con framework Tutor-Universale e modello PhD Professor in Enterprise Architecture (35.294 caratteri).
  - Markdown archiviato in cache staging locale ([staging/2538841248a46aa73362432fac733b6c4e8a439ba50b5ad2d706b8224c35870b.md](file:///c:/Documenti/Bots/PHD_Prof/staging/2538841248a46aa73362432fac733b6c4e8a439ba50b5ad2d706b8224c35870b.md)).
  - Creata nuova pagina Notion nel database Notes di Enterprise Architecture (3eab63e8-59c8-810d-88dd-de0dbd0f217d) con 211 blocchi ricchi (formule KaTeX, elenchi, callout, citazioni e blocchi di codice).
  - Registrato stato crittografico SYNCED in sync_state.json.

### 2026-09-29 (In-Place Notion Page Enhancement & Anti-Overengineering Decision)
- **Elaborazione Remota Note Manuali**:
  - Applicato il framework cognitivo `PHD_Prof` (Tutor-Universale, systems thinking, formalizzazione Enterprise Architecture) a una pagina Notion preesistente con appunti da conferenza senza slide di Jonas Van Riel (*Leading with Capabilities*).
  - Inserito il link profilo di Jonas Van Riel e aggiornato il contenuto remoto direttamente tramite MCP Notion API Markdown.
  - Decisione architetturale: mantenuta la separazione del core `src/` (nessuna complessità prematura introdotta per rari casi d'uso ad-hoc).
  - Salvato backup in [staging/jonas_van_riel_leading_with_capabilities.md](file:///c:/Documenti/Bots/PHD_Prof/staging/jonas_van_riel_leading_with_capabilities.md).

### 2026-09-25 (Prompt Engineering: Anti-Tautology, Pruning & High Density)
- **Eliminazione Inflazione & Ridondanze**:
  - Rimosso l'obbligo forzato di sottosezioni `###` ogni 120-180 parole che frammentava il testo e costringeva il modello a generare formule di raccordo e preamboli ad ogni micro-blocco.
  - Introdotta la regola tassativa di **Anti-Tautologia & Anti-Ripetizione**: ogni concetto, proprietà o parametro viene spiegato una sola volta alla prima introduzione sostanziale; nelle sezioni successive si fa riferimento diretto al termine senza ridefinizioni circolari.
  - Circoscritti gli esempi `**Example:**` esclusivamente a modelli o scenari di stima econometrici complessi e non banali, eliminando esempi superflui su panoramiche di syllabus e definizioni terminologiche di base.
  - Limitati i callout quote (`> **Core Insight:**`) a massimo 1 per sezione principale `##`, riservandoli a teoremi o leggi di identificazione cardine.
  - Sostituito il comando "airy relaxed paragraphs" con "dense, focused paragraphs" eliminando meta-introduzioni decorative e padding accademico ("delves into the intricate world", "it is vital to understand that").

### 2026-09-24 (Recursive Notion Block Parsing: KaTeX Equations & Nested Styles)
- **Parser Rich-Text Ricorsivo**:
  - Risolto il bug delle formule inline `$T=100$` e `$\delta$` visibili come testo grezzo: implementato un tokenizer ricorsivo in `parse_rich_text` che estrae equazioni KaTeX anche se annidate all'interno di grassetti (`**...**`) o corsivi (`*...*`).
  - Aggiunto supporto a equazioni display su elenchi puntati (`- $$...$$`).
  - Risolto il `TypeError: 'NoneType' object is not subscriptable` su delimitatori annidati.
  - Suite unit test estesa a 28/28 test superati con successo.

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

