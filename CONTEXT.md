# CONTEXT.md — PHD Prof

## Visione & Scopo del Progetto
ETL antifragile e crash-only per ingerire documenti e slide accademiche in formato PDF, sintetizzarli tramite LLM (Gemini) e archiviarli su Notion senza perdita di dati né duplicazione di token.

## Stato Attuale
- **Architettura**: Esagonale (Ports & Adapters) in `src/`.
- **Inbound Web Adapter & Cockpit UI**: Server locale FastAPI (`127.0.0.1:8000`) con streaming telemetrico SSE (`/api/events`), single-page dark tech industrial (zero-build, hotkey da tastiera, WCAG 2.2 AA).
- **Desktop Launcher**: Avvio rapido con un clic da `Avvia_PHD_Prof.bat` (target del collegamento desktop `PHD Prof.lnk`) con apertura automatica del browser predefinito.
- **Modello LLM**: Gemini 2.5 Flash con rate limiting, retry esponenziale e fallback automatico a 2.0/1.5 Flash.
- **Ingestione Multimodale PPTX**: Dual-Payload (rendering vettoriale PDF via PowerPoint COM + note a piè di pagina via python-pptx).
- **Persistent Course Profiles**: Invarianti di corso (materia, ruolo professorale, doc type, cartella locale, target Notion) memorizzati in `course_profiles.json` per avvio one-click a latenza zero.
- **Bilingual Interaction (EN default vs IT)**: Modulo `I18n` disaccoppiato nell'inbound adapter per visualizzazione bilingue terminale (default: `EN`, opzionale: `IT`).
- **Windowed Slide Chunker (Character-Driven & Volume-Balanced)**: Controllo preventivo prioritario sul volume di caratteri effettivi (`SPLIT_THRESHOLD_CHARS=25000`) invece del mero conteggio delle slide. Le slide vengono raggruppate in tranche bilanciate pesate sulla massa di caratteri per slide (`_partition_slides_by_character_budget`), allocando un budget di output dedicato di 8.192 token per ciascun blocco.
- **Test Suite**: 157 unit test offline con mock completi (100% passati, 0 regressioni).
- **Standard Documentale README (Invariante)**: Il file `README.md` DEVE essere SEMPRE ed ESCLUSIVAMENTE in lingua inglese. Ogni futura modifica deve preservare la massima chiarezza operativa per l'utilizzatore finale: setup di Python da zero (PATH), creazione API key Gemini, autorizzazioni e gerarchia del database Notion (Root Page -> Course Page -> Database con rilevamento automatico della property di tipo Title), tassonomia completa dei file di runtime/stato e funzionamento utilitaristico della Web Cockpit.

## Prossimi Passi (Futuro / Manutenzione)
- **Supporto Modelli Aggiuntivi**: Eventuale configurazione UI per modelli LLM alternativi oltre a Gemini.
- **Osservabilità Avanzata**: Ulteriori metriche di latenza e token profiling.

## Log delle Sessioni
### 2026-10-20 (PPTX Vector Visual Extraction, Recursive GroupShape Reader & Syllabus/Project Completeness)
- **Diagnosi delle 4 Root Causes (Immagini Errate/Bianche, Sezioni Tagliate e Clipping Mermaid)**:
  1. *Immagini .pptx Errate o Bianche (PyMuPdfVisualExtractor.extract_figure)*: MuPDF (fitz.open) eseguiva un reflow testuale del .pptx grezzo su 13 pagine verticali prive di grafica e con clamping silenzioso sull ultima pagina (min(page_number - 1, len(doc) - 1)), producendo 20 PNG identici/bianchi per EA2627-04-W5.pptx e EA2627-05-W5.pptx.
  2. *Omissione di Testo Annidato nei .pptx (pptx_extractor.py & text_pdf_reader.py)*: L iterazione flat su slide.shapes ignorava i GroupShape (shape_type == 6) e le tabelle annidate in modalita fallback testuale.
  3. *Soppressione Indebita di Deliverable, Milestone e Limiti di Pagina (prompt_templates.py)*: La regola di esclusione delle sezioni logistiche in SLIDES_PROMPT_TEMPLATE induceva Gemini a scartare le specifiche operative dei progetti d esame (Milestone A/B, tabella limiti di pagina A4, viste ArchiMate).
  4. *Mancato Sync Git del Wrapping Mermaid (notion_block_builder.py)*: Le modifiche wrap_mermaid_label (wrapping multilinea a 16-18 caratteri) erano rimaste uncommitted sulla macchina principale.
- **Risoluzione Deterministica nel Core & Adapters**:
  - src/adapters/outbound/pymupdf_visual_extractor.py: Implementato _resolve_renderable_pdf_path() per risolvere obbligatoriamente il PDF vettoriale staging/{file_hash}_slides.pdf (o conversione on-demand) per i file .pptx, e introdotta validazione rigorosa dei limiti 1..len(doc) (ValueError su fuori range).
  - src/adapters/outbound/document_readers/pptx_extractor.py, text_pdf_reader.py & process_document.py: Implementato _iter_shapes_recursive(shapes) per attraversare ricorsivamente GroupShape e tabelle.
  - src/core/domain/prompt_templates.py: Aggiornato SLIDES_PROMPT_TEMPLATE per preservare integralmente deliverable, milestone, limiti di pagina e diagrammi di processo/roadmap.
- **Bonifica Asset su Cloudflare R2 & Live Patch Notion**:
  - Rigenerate a 300 DPI dai PDF vettoriali (staging/*_slides.pdf) e ricaricate su Cloudflare R2 tutte le 21 figure di EA2627-04-W5.pptx e EA2627-05-W5.pptx piu le 6 slide diagrammatiche di Group_work_EA_2026-2027.pptx (Slide 3-8).
  - Patchate live via Notion API le pagine Group work Enterprise Architecture 2026-2027 (3ffb63e8-59c8-81cd-a6b6-c9cfda651f57) e Group_work_EA_2026-2027 (3ffb63e8-59c8-81b8-a966-e3f5a1cb4899): iniettate le 6 figure vettoriali, integrati i 20 blocchi delle sezioni mancanti (Milestone A/B, viste ArchiMate, tabella budget 15 pagine A4, governance) e aggiornati tutti i 4 blocchi Mermaid con sanitize_mermaid_flowchart().
- **Autonomous Verification Gate**:
  - Aggiunti 4 nuovi test unitari in tests/test_visual_extractor.py e tests/test_text_pdf_reader.py. Suite completa: **157/157 unit test passati (100% green)**.
### 2026-10-16 (Unit Root Testing In-Place Pedagogical Harmonization & KaTeX Normalization)
- **Diagnosi della Disconnessione e Frattura Concettuale**:
  - *Problema Utente*: La nota Notion *Unit Root Testing* presentava una qualità analitica elevata a livello locale, ma mancava di un filo logico unitario ed era ostica per uno studente con basi solide in statistica classica ($E[X], \text{Var}(X)$, OLS, $t$-test, $F$-test, LLN/CLT) che affronta le serie storiche per la prima volta.
  - *Root Cause Formattazione*: Un backtick non chiuso nel blocco 189 mandava in crash il parser LaTeX Notion (trasformando l'intero blocco in codice grezzo con `code: true`); formule e tabelle da blocco 235 a 324 presentavano doppi backslash (`\\`) che KaTeX interpretava come comandi di a capo invece che simboli matematici.
- **Armonizzazione Chirurgica In-Place (52 Blocchi Chiave Patched)**:
  - *Sezione 1 (Stationarity vs Non-Stationarity, blocchi 1, 5, 7, 11, 17, 20, 24, 44)*: Ancorata la debolezza inferenziale al fatto che nelle serie storiche si osserva una **singola traiettoria temporale** $\{y_t\}$; spiegato il collasso di LLN e CLT e definita la stazionarietà in covarianza come condizione di regolarità minima. Distinzione netta tra non-stazionarietà deterministica (shock transitori, mean-reverting) e stocastica (shock permanenti a memoria infinita via radice unitaria).
  - *Sezione 2 (Transformations to Stationary Series, blocchi 52, 55, 58, 60, 62)*: Esplicitata l'inefficienza che motiva il test: detrending lineare su serie stocastica lascia la non-stazionarietà nei residui (spurious regression), mentre differenziare una serie trend-stazionaria induce una radice unitaria non-invertibile nel MA (over-differencing).
  - *Sezione 3 (Dickey-Fuller Test & ADF, blocchi 67, 69, 74, 79, 87, 88, 90, 93, 98, 99, 101, 110, 115, 121, 132, 133, 134, 137, 139, 140, 149, 150, 151)*:
    - *Spiegazione della Distribuzione DF e Hurwicz Bias*: Chiarito perché sotto $H_0: \gamma=0$ OLS sottostima sistematicamente $\alpha_1$ ($\hat{\gamma} < 0$, regressione che insegue la media campionaria della passeggiata aleatoria), spostando $\tau$ a sinistra (valori critici più negativi, $-1.95$). Spiegato perché aggiungere intercetta e trend sposta la soglia ancora più a sinistra ($-2.88 \to -3.43$).
    - *Spiegazione Statistiche $\phi_1, \phi_2, \phi_3$*: Identificate come esatti test $F$ congiunti su $q$ restrizioni lineari, ma valutati su tavole simulate DF poiché il denominatore contiene regressori non-stazionari.
    - *Decomposizione di Said-Dickey*: Spiegata la separazione ortogonale: la memoria di lungo periodo è isolata nel singolo coefficiente scalare $\gamma = \sum \alpha_j - 1$, mentre la correlazione seriale a breve termine è assorbita dai lag differenziati $\Delta y_{t-i} \sim I(0)$ su cui valgono $t$-test standard.
    - *Biforcazione Gaussiana*: Chiarito il *Deterministic Dominance Effect* (in random walk con drift, la crescita deterministica cresce ad ordine $O(t)$ dominando la componente stocastica $O(t^{1/2})$, per cui $\tau_\mu \xrightarrow{d} \mathcal{N}(0, 1)$), e spiegato perché usiamo comunque le tabelle DF per prudenza econometrica.
  - *Sezioni 4 & 5 (Model Selection, Enders & Pitfalls, blocchi 157, 159, 171, 174, 175, 176, 187, 189, 204, 206, 209, 213, 216, 221, 224, 233)*:
    - Risolto il dilemma circolare tramite la procedura sequenziale di Enders.
    - Fissato il backtick errato nel blocco 189 e rimossi backtick vuoti / caratteri spuri.
    - Collegati i 3 pitfall strutturali (bassa potenza vs radici vicine $\to$ KPSS; rotture strutturali omese $\to$ Perron; radici multiple $I(2) \to$ Dickey-Pantula) direttamente alla Sezione 6 (casi empirici CPI Belgio e PIL Austria).
- **Normalizzazione KaTeX & Sincronizzazione**:
  - Script `scripts/harmonize_unit_root_notion.py` eseguito con successo: 52 blocchi modificati in-place, 45+ espressioni LaTeX e tutte le celle della tabella normalizzate a singolo backslash.
  - File di staging locale `staging/83a7b4017cfc38140920d829b29610228ac79aff81e663841c4711576e5eb162.md` sincronizzato a 57.321 caratteri.
  - Suite di test: **151/151 unit test passati (100% green)**.
- **Codifica Permanente per le Prossime Generazioni (Prompt Hardening & Chunker Engine)**:
  - *Hardening Prompt Template (`src/core/domain/prompt_templates.py`)*:
    - Integrata la regola tassativa di **Foundational Anchoring & Pedagogical Calibration**: il target reader possiede solide basi di statistica/computer science classica, ma approccia la materia per la prima volta. Per ogni formalismo avanzato, il modello DEVE esplicitare quale assunzione di base collassa e perché prima di introdurre lo strumento correttivo, fornendo l'intuizione fisica/statistica dei parametri (es. Hurwicz bias, decomposizione Said-Dickey, dominanza deterministica) e spiegando perché la scelta errata è fatale (spurious regression vs over-differencing).
    - Integrata la regola di **Merge-on-Introduction (Soppressione Cicli Didattici Slide)**: esaurire modello, definizione, trattamento operativo (es. detrending vs differencing) e trade-off fatali fin dalla prima comparsa. Divieto di rispecchiare i cicli delle slide (es. definire il trend, poi rispiegarlo sotto "trasformazioni", poi ripeterlo per motivare i test).
    - Integrata la regola di **Progressive Narrative Threading (Zero Alienazione tra Sezioni e Chunk)**: evitare sezioni staccate o aliene. Collegare saldamente ogni nuova sezione o chunk richiamando le conclusioni della precedente come premesse dimostrate in una singola proposizione tagliente, avanzando immediatamente al Delta Tecnico senza duplicazioni.
    - Integrata la regola di **End-to-End Methodological Continuity**: esplicitare il dilemma circolare o trade-off strutturale che motiva algoritmi diagnostici sequenziali e collegare direttamente paradossi o edge case empirici (rotture nel drift) ai failure modes degli stimatori.
    - Introdotti i vincoli negativi vincolanti di **KaTeX Single-Backslash Formatting** (divieto assoluto di doppie barre rovesciate dentro le formule KaTeX) e **Backtick Hygiene** (chiusura e bilanciamento rigoroso di ogni backtick per evitare wrapping accidentale in monospace).
  - *Rinforzo del Chunker Multi-Call (`src/core/usecases/process_document.py`)*:
    - Estesa la `continuity_directive` iniettata nei prompt dei chunk $k > 1$, ordinando a Gemini sia di consolidare senza duplicazioni sia di applicare la **Progressive Narrative Threading**, prevenendo sezioni aliene e garantendo un filo narrativo compatto e ininterrotto lungo tutta la presentazione.
- **Diagnosi della Frattura Concettuale tra Chunk Multi-Call**:
  - *Sintomo*: Note generate su presentazioni massive (3 chiamate LLM) con ottima qualità locale ma percepite come frammentate e scollegate.
  - *Root Cause*: Isolamento a finestra cieca (stateless chunking) in cui le chiamate 2 e 3 non avevano visibilità sulle definizioni/notazioni introdotte nella chiamata 1, portando a notational drift, rispiegazioni ridondanti o salti bruschi di registro.
  - *Vincolo Utente*: Coerenza e continuità reale senza aumentare lo slop, senza formule di transizione retoriche ("Come abbiamo visto...", "Passiamo ora a...") e senza allungare inutilmente il testo ("brodo lungo e poco saporito").
- **Implementazione della Staffetta Simbolica e Transizione per Delta Tecnico**:
  - `src/core/domain/prompt_templates.py`:
    - Rinforzati `SLIDES_PROMPT_TEMPLATE` e `PAPER_OR_BOOK_PROMPT_TEMPLATE` con la regola di *Direct Technical Progression (Zero-Slop Transitions)*: divieto assoluto di formule transizionali discorsive; obbligo di legare i concetti esclusivamente tramite il loro *Delta Tecnico* (1 sola proposizione diretta sul limite o fallimento matematico del modello precedente che motiva la nuova formulazione).
    - Introdotto il vincolo di *Uniform Analytical Caliber (Empirical & Computational Rigor)*: la stessa grammatica formale (ipotesi $H_0$, parametri strutturali, statistiche test) applicata sia alla teoria che alle regressioni empiriche e codice.
    - Aggiornato *Anti-Tautology & Symbolic Continuity*: i simboli e modelli già formalizzati sono invarianti provati da usare direttamente senza rispiegazioni.
  - `src/core/usecases/process_document.py`:
    - Implementato `_extract_chunk_symbolic_anchor(notes_markdown)`: estrazione vettoriale (<1ms) dei modelli H2/H3 e delle formulazioni formali ($$...$$) stabiliti nel chunk precedente.
    - Iniezione deterministica nel prompt del Chunk $k$ del blocco vincolante `ACTIVE NOTATIONAL & CONCEPTUAL STATE` che ordina a Gemini di assumere notazione e proprietà come invarianti noti, avanzando unicamente per delta tecnici.
- **Autonomous Verification Gate**:
  - Aggiunti 2 test unitari dedicati in `tests/test_process_document_adaptive.py` (`test_extract_chunk_symbolic_anchor` e verifica della direttiva di continuità passata al Chunk 2).
  - Suite completa: **151/151 unit test passati al 100% (0 regressioni)**.
### 2026-10-15 (Unit Root Testing Complete Audit & Live Empirical Enrichment)
- **Diagnosi Root Cause della Pagina 'Unit Root Testing' (3fab63e8-59c8-8140-9c6d-f7514f7ce955)**:
  - *Origine Temporale*: La pagina segnalata dall'utente era stata generata alle 08:43 AM, ovvero prima dello sviluppo e del deploy del Windowed Slide Chunker.
  - *Meccanismo di Troncamento*: Il file sorgente (2 Unit Root Testing.pdf, 131 slide, 60.792 caratteri) era stato inviato a Gemini in una singola chiamata monolitica. L'output aveva saturato il ceiling di 8.192 token alla slide 111, tagliando interamente le slide 112–131 (casi empirici su CPI belga e PIL reale austriaco con rotture strutturali nel drift).
  - *Validazione della Nuova Architettura Chunker*: Con il nuovo *Character-First Chunker* attivo (soglia 25.000 caratteri), lo stesso identico PDF viene ripartito automaticamente in **3 blocchi bilanciati** (~20.000 caratteri ciascuno), allocando  \times 8.192 = 24.576$ token di output complessivi (più del triplo del budget) ed eliminando strutturalmente ogni omissione per i test futuri.
- **Live Enrichment Accademico & Bonifica Blocchi Notion**:
  - *Asset Visivi su Cloudflare R2*: Estratte ad alta definizione (300 DPI) tramite PyMuPDF e caricate su R2 le 12 figure e tabelle di regressione empiriche mancanti (slide 114–130).
  - *Bonifica Strutturale*: Archiviati (eliminati) tramite DELETE API Notion i 36 blocchi orfani e duplicati a fondo pagina (da indice 232 a 267).
  - *Iniezione 93 Nuovi Blocchi Accademici*:
    1. **Belgian Price Level Dynamics: Inflation Drift Collapse vs Spurious Stationarity** (Slide 113–120): Conflitto tra procedura univariata (drop trend) e multivariata (keep trend), fallacia della stazionarietà attorno alla media nel modello con drift ($\tau_\mu = -3.88$), artefatto del trend quadratico concavo ( = -2.95$), e risoluzione definitiva con rottura strutturale nel drift al 1985:Q1 ( = -2.08, \tau = -1.27$, random walk con breaking drift).
    2. **Austrian Macroeconomic Output: Growth Deceleration vs Spurious Mean Reversion** (Slide 121–130): Stazionarietà della crescita $\Delta \ln Y_t \sim I(0)$ ($\tau_\mu = -4.95$), fallacia dell'output stazionario a media costante ($\tau_\mu = -3.55$), rottura strutturale nella crescita trimestrale al 1975:Q1 (dall'1.1% allo 0.5%,  = -3.38$), e risoluzione con breaking drift ($\tau = -1.54$, random walk con breaking drift).
    3. **Protocollo Metodologico & Decision Engine**: Flowchart di diagnosi contro l'applicazione meccanica dei test di radice unitaria.
    4. **Bibliografia Accademica Rigorosa**: 7 paper canonici (Dickey-Fuller 1979/1981, Dickey-Pantula 1987, KPSS 1992, Perron 1989, Said-Dickey 1984, Zivot-Andrews 1992).
    5. **Artefatti Didattici**: Diagrammi Mermaid, 5 Active Recall Drills di livello avanzato e Model Boundary Conditions Table.
  - *Verifica Live*: Pagina Notion portata a 325 blocchi, totale coerenza concettuale e zero metadati tecnici o riferimenti numerici alle slide nei titoli.
  - *Sincronizzazione Staging*: Aggiornato con codifica UTF-8 il file locale staging/83a7b4017cfc38140920d829b29610228ac79aff81e663841c4711576e5eb162.md.

### 2026-10-15 (Notion Table <br> HTML Tag Normalization & Output Budget Diagnosis)
- **Normalizzazione Deterministica HTML <br> nei Blocchi Notion**:
  - *Diagnosi Root Cause*: Le tabelle Markdown GFM usano convenzionalmente tag HTML <br>/<br/> per formattare punti elenco o a capo dentro le singole celle (dove i newline fisici \n romperebbero la riga GFM). Notion API non renderizza tag HTML nativi e li visualizzava come testo grezzo <br>- ...<br>-.
  - *Fix Deterministico*: Aggiornato src/adapters/outbound/notion_block_builder.py in parse_rich_text(), normalizzando regex [ \t]*</?br\s*/?>[ \t]* in newline nativi \n (pienamente supportati da Notion nei 
ich_text per celle e paragrafi) e convertendo &nbsp; in spazio ordinario.
  - *Verifica Suite*: Aggiunti 2 test di regressione dedicati in 	ests/test_notion_block_builder.py. Suite completa superata con 147/147 test passati (0 regressioni).
  - *Live Patch Notion*: Aggiornate via API Notion le righe della tabella sulla pagina *Big Data Engineering & Distributed Systems 2* (3fab63e8-59c8-8157-89b9-dcc46a0daaf5), azzerando i blocchi residui con <br>.
- **Diagnosi Omissione Slide 30–37 (Saturazione Output Token Budget)**:
  - Isolata la causa del salto delle slide su presentazioni dense: non è memoria di input (contesto 1M+ di Gemini 2.5 Flash), ma la saturazione dell'output token envelope (max 8.192 token di generazione).
  - Il markdown sintetizzato per la Sessione 2 contava esattamente 42.528 caratteri (~8.100 token), spingendo il planner dell'LLM a comprimere/saltare le slide 30–37 (Spark SQL, viste temporanee, query parametrizzate Spark 3.4+).
  - Generata e validata la sezione mancante (17.378 caratteri di analisi dettagliata salvati in scratch/missing_section_30_37.md).
  - Formulato piano architetturale per *Windowed Slide Chunking* (splitting a soglia slide > 35) per garantire 8k token dedicati a ciascuna porzione.
- **Live Injection Sezione Spark SQL (Slide 30–37)**:
  - Generata sintesi accademica esaustiva delle slide 30–37 (ciclo di vita della modellazione predittiva, PySpark 3.4 parameter injection, viste temporanee Spark SQL e matrice di trade-off DataFrame vs SQL).
  - Convertita in 42 blocchi Notion nativi via `build_notion_blocks()` e iniettata tramite Notion API con puntamento esatto immediatamente prima del blocco *"🧩 Spark Data Structures: RDDs, DataFrames, and Datasets"* sulla pagina Notion `3fab63e8-59c8-8157-89b9-dcc46a0daaf5`. Rimosso il vecchio blocco segnaposto ridondante.
- **Implementazione Windowed Slide Chunker**:
  - `src/core/usecases/process_document.py`: Aggiunti metodi `_count_slides()`, `_slice_pdf_pages()` (con PyMuPDF / fitz) e `_process_windowed_slides()` orchestrati in `execute()` tramite la condizione `should_chunk_slides = (total_slides > split_threshold_slides and pre_density >= 15000)`. Ciascun chunk riceve una chiamata LLM dedicata con 8k token di output, le note vengono ricomposte linearmente e lo Stage 2 genera gli artefatti concettuali (Mermaid, Mindmap, OPML) sul corpus unificato.
  - `pdf_to_notion.py`: Parametro `split_threshold_slides` (default: 35) configurabile da variabile d'ambiente `SPLIT_THRESHOLD_SLIDES`.
  - `.env.example` & `README.md`: Documentate le variabili `SPLIT_THRESHOLD_CHARS` e `SPLIT_THRESHOLD_SLIDES`.
  - `tests/test_process_document_adaptive.py`: Aggiunto test unitario `test_process_document_windowed_slide_chunking` a copertura completa della suddivisione e fusione degli output. Suite totale: 148/148 passati.
- **Audit Sistematico & Risoluzione Sezioni Mancanti (Slide 53, 54, 58, 60)**:
  - *Diagnosi Integrale Presentazione (67 Slide)*: Eseguito audit microscopico slide-by-slide del file `BigData_Session_2_2026_2027.pdf` confrontando il corpus di ciascuna slide con la pagina Notion remota (`3fab63e8-59c8-8157-89b9-dcc46a0daaf5`). Rilevate omissioni critiche causate dal budget token nella seconda metà del documento:
    1. **Slide 53**: Matrice di codice eseguibile per Inner, Left, Right e Full Outer Join su tabelle `t_a` e `t_b` con output ASCII espliciti.
    2. **Slide 54**: Modello esecutivo Non-Distributed vs Distributed Systems, comunicazione/network shuffle, determinanti di costo (cardinalità chiavi, data skew, località di partizionamento su nodo/macchina), rischi OOM (JVM heap exhaustion e disk spill thrashing), e regola aurea: *"TIP: Filter before joining to avoid using unnecessary computing power"*.
    3. **Slide 58 & 60**: Modalità di registrazione UDF (SQL Catalog `spark.udf.register()` vs wrapper DataFrame `udf()`) e matrice di compatibilità runtime Pandas 2.0+ (richiede Spark $\ge 3.4$) / Pandas 3.0+ (`FutureWarning`).
  - *Live Injection & Staging Sync*: Generati 35 blocchi Notion nativi addizionali (25 per Joins Slide 53-54, 10 per UDF Slide 58-60) e iniettati via PATCH API con coordinate esatte sulla pagina Notion remota (portando i blocchi totali da 214 a 249). Sincronizzato parallelamente il file di staging markdown locale `staging/743fd4a784268b4ea4895760d595985fe21ae0e44e3859b5453d0fffb86bea33.md`.
- **Refactoring Character-First per Slide Chunker**:
  - *Razionale Sistemico*: Il numero grezzo di slide è un proxy ingannevole (80 slide sparse con poche parole = 7.000 caratteri, mentre 25 slide dense di codice/formule = 35.000 caratteri). L'attivazione e il partizionamento devono essere determinati dal volume di caratteri reali per prevenire saturazioni dell'envelope di output senza generare chiamate API superflue per mazzi visivi leggeri.
  - *Implementazione Use Case (`src/core/usecases/process_document.py`)*:
    1. `_get_slide_character_counts(document)`: Estrazione vettoriale rapida (<20ms) del conteggio caratteri per singola slide tramite PyMuPDF.
    2. `_partition_slides_by_character_budget(counts, budget)`: Algoritmo di raggruppamento delle slide in tranche bilanciate che minimizza la varianza del carico informativo per chunk.
    3. Trigger `should_chunk_slides`: Attivato prioritariamente da `total_chars > split_threshold_chars` (default: 25.000 caratteri), con fallback sul conteggio slide solo per mazzi puramente grafici o scansionati privi di testo vettoriale.
  - *Allineamento Configurazione*: Aggiornati `pdf_to_notion.py` (default: 25.000 caratteri), `.env.example` e `README.md`.
  - *Suite di Test Estesa*: Aggiunti 2 test unitari dedicati in `tests/test_process_document_adaptive.py` (`test_partition_slides_by_character_budget_skewed` e `test_slide_chunking_triggered_by_characters_not_slide_count`). Suite totale: 150/150 passati (100% green).

### 2026-10-14 (Resilient Visual Extraction, Inline Figure Lifting & Notion Block Captioning)
- **Diagnosi & Root Causes Isolate**:
  1. *Disallineamento Sintassi LLM (Inline Citations vs Standalone Image Blocks)*:
     - Nelle slide con grafici o tabelle, Gemini generava riferimenti discorsivi parentetici (es. `(figure://slide_6)`, `(figure://slide_8?crop=100,0,700,500)`) all'interno di frasi o bullet point accademici anziché blocchi immagine Markdown dedicati (`![caption](figure://slide_N)`).
  2. *Regex Rigida in `ProcessDocumentUseCase._process_figures`*:
     - La regex preesistente cercava unicamente `!\[([^\]]*)\]\(figure://slide_(\d+)...\)`. I riferimenti privi di punto esclamativo o alt text venivano completamente ignorati, bypassando l'estrazione grafica con PyMuPDF e l'upload su Cloudflare R2, lasciando stringhe testuali grezze `(figure://slide_X)` nel corpo dei blocchi Notion.
  3. *Incompatibilità con il Block Model di Notion*:
     - In Notion le immagini non possono esistere come frammenti inline dentro un blocco `rich_text` (paragrafo o bullet point). Sono obbligatoriamente blocchi autonomi di primo livello (`type: "image"`). Qualsiasi immagine annidata inline dentro una riga veniva degradata a testo letterale.
- **Risoluzione Deterministica nel Core & Block Builder**:
  - `ProcessDocumentUseCase._process_figures`:
    - Introdotta regex universale con named groups che cattura sia blocchi standalone (`![Alt](figure://...)`), sia citazioni parentetiche (`(figure://slide_N...)`) che riferimenti testuali grezzi (`figure://slide_N...`).
    - *Inline Figure Lifting*: quando un riferimento visivo si trova all'interno di una riga di testo, la frase viene bonificata con un'annotazione pulita `*(Slide N)*` e l'immagine estratta/caricata su R2 viene sollevata come blocco Markdown autonomo (`\n\n![Alt](url)\n\n`) posizionato immediatamente sotto il blocco genitore.
    - Preservato il graceful fallback con callout `> 📷 ...` o testo discorsivo in assenza di credenziali R2 o in caso di errore.
  - `notion_block_builder.py`:
    - Supporto esplicito per le didascalie native Notion (`caption`) nei blocchi `image` generate dall'alt text Markdown.
    - Esteso `parse_rich_text` con il parsing nativo dei link Markdown `[testo](url)` serializzati come oggetti `text` con attributo `link: {url: ...}`.
  - `prompt_templates.py`:
    - Rinforzati `SLIDES_PROMPT_TEMPLATE` e `PAPER_OR_BOOK_PROMPT_TEMPLATE` con un vincolo vincolante negativo esplicito: divieto assoluto di referenziare figure in formato parentetico inline; obbligo di emissione come riga autonoma isolata da newline vuoti.
- **Autonomous Verification Gate**:
  - 144/144 unit test superati al 100% su pytest (0 regressioni). Aggiunti 5 test unitari dedicati per estrazione inline, lifting su blocchi multipli, fallback senza R2, caption immagini e link Markdown.
### 2026-10-13 (Cross-Platform Mac/Win Hardening, Fault Isolation & Recursive Engine)
- **Diagnosi & Root Causes Isolate**:
  1. *Perdita di Fault Isolation tra CLI e Web Cockpit*: Nella CLI, se un profilo conteneva una cartella inesistente sul nuovo PC (`C:\Documenti\UNIMIB\...` vs nuova macchina), la scansione isolava il singolo corso stampando "Cartella non trovata", consentendo di utilizzare gli altri domini corretti. Nel Web Cockpit (`/api/profiles`), qualsiasi eccezione `OSError` o `PermissionError` durante `scan_documents` o `is_dir()` faceva collassare l'intero endpoint con HTTP 500, facendo sollevare a `app.js` l'errore bloccante: `Impossibile caricare i profili: Errore recupero profili`.
  2. *DNS Wildcard Hijacking su Host Locale (`phdprof.test`)*: In `pdf_to_notion.py`, `socket.gethostbyname(web_domain)` considerava valida qualsiasi risoluzione DNS. Su un PC nuovo connesso a reti con DNS hijacking (che rispondono con IP pubblici per qualsiasi dominio inesistente come `.test`), il sistema apriva il browser su un host remoto invece di fare il fallback su `127.0.0.1`.
  3. *Cartelle e File Fantasma su macOS (TCC, Tilde `~`, `._*`)*:
     - Accesso a `~/Documents` su macOS protetto da framework TCC (richiede autorizzazione in Privacy & Sicurezza).
     - Deserializzazione profili `Path(raw_folder)` priva di `expanduser()` (la tilde `~` cercava directory letterali `~`).
     - File fantasma AppleDouble (`._*.pdf` / `._*.pptx`) inclusi erroneamente nella coda batch.
     - Scansione strettamente flat (`iterdir()`): corsi con materiali organizzati in sottocartelle (`Lezione 1/`, `Slide/`) mostravano 0 file.
     - Parità funzionale PPTX: su macOS assenza di PowerPoint COM per esportazione visiva vettoriale.
- **Risoluzione Deterministica nel Core, Backend & Frontend**:
  - `web_adapter.py` & `cli_adapter.py`: Scansione documentale ricorsiva (`scan_documents(recursive=True)`), esclusione automatica di directory di runtime (`.git`, `.venv`, `staging`, `node_modules`, `__pycache__`) e scarto deterministico di file fantasma macOS (`._*`, `.DS_Store`, file nascosti).
  - `models.py` (`CourseProfile.from_dict`) & `web_adapter.py` (`save_profile`): Normalizzazione automatica tilde `~` (`expanduser()`) e ripristino leading slash per percorsi UNIX (`Users/...` -> `/Users/...`).
  - `gemini_file_reader.py`: Hook per conversione vettoriale PPTX via **LibreOffice CLI** (`soffice --headless --convert-to pdf`) in fallback su macOS/Linux quando PowerPoint COM non è disponibile.
  - `pdf_to_notion.py`: Risoluzione locale vincolata rigorosamente a IP loopback (`127.0.0.1`, `::1`, `0.0.0.0`), con fallback automatico e trasparente su `127.0.0.1` in caso di DNS esterno.
  - `app.js` & `app.css`: Badge visivo arancione/rosso `Cartella assente` per i profili orfani nella sidebar, con warning esplicito nel log di sistema che guida l'utente a cliccare "Modifica" senza bloccare la selezione degli altri corsi.
- **Autonomous Verification Gate**:
  - 139/139 unit test superati al 100% su pytest (0 regressioni). Aggiunti test dedicati per scansione ricorsiva, filtraggio file fantasma AppleDouble e fallback LibreOffice CLI.

### 2026-10-11 (Notion Mermaid Truncation & Dark Mode White-on-White Contrast Resolution)
- **Diagnosi Empirica & Root Causes Isolate**:
  1. *Troncamento Forzato di Parole a Metà (`...` nel Grafo 1 / Blocco 77)*:
     - `convert_mindmap_to_flowchart()` eseguiva uno slicing arbitrario `full_label[:52] + "..."` ogni volta che la stringa superava 55 caratteri.
     - Questo tranciava brutalmente le parole a metà (es. `Reali...`, `Orga...`, `Customer St...`, `Formal A...`), distruggendo la leggibilità concettuale.
  2. *Titoli Invisibili Bianco su Chiaro in Notion Dark Mode (Grafo 2 / Blocco 78)*:
     - Nei diagrammi Mermaid con direttive `style <NodeId> fill:<pastelHex>`, l'attributo `color:` era assente.
     - Quando Notion è impostato su tema scuro (Dark Mode), applica il colore font ereditato predefinito del tema (`#ffffff`, bianco).
     - Il rendering di testo bianco su sfondi pastello chiari (`#add8e6`, `#c8e6c9`, `#ffd7a0`, `#f9f7f7`) produce un contrast ratio di appena ~1.2:1, rendendo tutti i titoli completamente illeggibili e invisibili.
- **Risoluzione Deterministica nel Core & Block Builder (`notion_block_builder.py`)**:
  - `convert_mindmap_to_flowchart()`:
    - Rimosso lo slicing a caratteri grezzi.
    - Introdotta logica word-safe: il titolo del concetto viene sempre preservato per intero; i dettagli aggiuntivi vengono inseriti solo se rientrano nel budget di 55 caratteri; eventuali accorciamenti avvengono rigorosamente ai confini di parola (`rsplit(' ', 1)`), con zero parole troncate a metà.
  - `is_light_hex(hex_str)`:
    - Calcolo deterministico della luminanza WCAG (soglia > 140) per classificare colori di riempimento chiari vs scuri.
  - `sanitize_mermaid_flowchart()`:
    - Nelle direttive `style`, se `color:` è omesso e `fill` è un colore chiaro, viene iniettato deterministicamente `color:#0f172a` (ardesia scuro ad altissimo contrasto). Se lo sfondo è scuro, viene iniettato `color:#ffffff`.
    - Normalizzazione automatica `graph LR` -> `graph TD` per preservare il layout verticale compatto.
- **Hardening dei Prompt Template (`prompt_templates.py`)**:
  - Aggiornati `SLIDES_PROMPT_TEMPLATE`, `PAPER_OR_BOOK_PROMPT_TEMPLATE` e `TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT`:
    - Obbligo esplicito di abbinamento contrasto: ogni nodo con sfondo pastello deve definire esplicitamente `color:#0f172a` per garantire leggibilità incondizionata sia in Light che in Dark Mode.
    - Limite stringente sulle etichette a 45-50 caratteri interi senza troncature.
- **Diagnosi Visiva Definitiva (Text Clipping sul Bordo Destro dei Rettangoli SVG)**:
  - Il difetto percepito come "parole/frasi troncate" non era un troncamento semantico nel testo sorgente con puntini di sospensione, bensì un **clipping geometrico del motore di rendering SVG di Notion**:
  - Quando un'etichetta Mermaid su singola riga supera i 35-40 caratteri (nel grafo precedente erano 50-60 caratteri come `Layered EA Models: Serving, Realisation and Grouping`), Mermaid calcola le dimensioni della bounding box con metriche font generiche.
  - Notion, renderizzando l'SVG all'interno del proprio contenitore web/desktop con il font di sistema locale (Inter/Segoe UI) e padding fisso della colonna, fa straripare il testo (`<text>`) oltre il margine destro del rettangolo (`<rect>`) e del subgraph.
  - Le ultime parole di ogni nodo venivano quindi fisicamente tagliate dal tratto del rettangolo e dal bordo del container (`overflow: hidden`).
- **Risoluzione a Budget Stretto & Zero-Overflow**:
  - `notion_block_builder.py` e `prompt_templates.py`: ridotto il budget massimo per nodo a **25-28 caratteri**, spezzando i concetti complessi in nodi atomici concatenati verticalmente (es. `Layered EA Models` -> `Serving & Realisation`) anziché stringhe monolitiche su singola riga.
  - Aggiornati live via Notion API i blocchi 77 e 78 con il layout compatto a colonna singola: larghezza box ridotta a ~200px con ampi margini di sicurezza su entrambi i lati, garantendo zero clipping e leggibilità immediata.
- **Autonomous Verification Gate & Test Suite**:
  - 133/133 unit test superati al 100% su pytest (0 regressioni).

### 2026-10-11 (Notion Mermaid Single-Column Vertical Layout & Anti-Shrink Enforcement)
- **Diagnosi Empirica & Root Cause del Rimpicciolimento Font**:
  - *Sprawl Orizzontale & Scaling Ratio in Notion*: I blocchi Notion renderizzano gli SVG di Mermaid dentro un contenitore a larghezza fissa (700-900px).
  - Quando un diagramma ha più subgraph/cluster disposti in parallelo dal nodo radice (`ROOT --> SG_1`, `ROOT --> SG_2`, `ROOT --> SG_3`) e nodi interni non connessi verticalmente, l'SVG risultante raggiunge oltre 2100px di larghezza (`viewBox: 4 4 2110 396`).
  - Per far entrare 2110px dentro 800px, Notion applica un fattore di scala proporzionale di **0.379 (38%)**, rimpicciolendo i font da 14px a **5.3px**, rendendo il testo illegibile.
- **Risoluzione Deterministica nel Core & Block Builder (`notion_block_builder.py`)**:
  - `convert_mindmap_to_flowchart()`: Riprogettata la topologia del grafo:
    1. *Catena top-down interna*: I nodi appartenenti allo stesso subgraph sono ora concatenati sequenzialmente in verticale (`N1 --> N2 --> N3`).
    2. *Impilamento sequenziale dei cluster*: I subgraph sono ora concatenati in cascata progressiva a colonna singola (`ROOT --> first(SG_1)`, `last(SG_1) --> first(SG_2)`, `last(SG_2) --> first(SG_3)`).
    3. *Budget larghezza label*: Accorciato il tetto massimo delle etichette a 55 caratteri.
    4. Risultato misurato via Playwright: larghezza SVG ridotta da **2110px a 216px**, scale factor **1.0 (100%)**, font nitidi e perfettamente leggibili.
  - `sanitize_mermaid_flowchart()`: Normalizzazione automatica da `graph LR` / `flowchart LR` a `graph TD` / `flowchart TD` per impedire esplosioni in larghezza.
- **Hardening dei Prompt Accademici (`prompt_templates.py`)**:
  - Aggiornati `SLIDES_PROMPT_TEMPLATE`, `PAPER_OR_BOOK_PROMPT_TEMPLATE` e `TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT`.
  - Introdotti vincoli vincolanti negativi e positivi:
    - Divieto assoluto di `graph LR` (solo `graph TD`).
    - Divieto assoluto di subgraph disposti in parallelo side-by-side.
    - Obbligo di impilamento sequenziale verticale dei cluster (`SG_1 --> SG_2 --> SG_3`).
    - Obbligo di catena top-down dei nodi interni o massimo 2 nodi in parallelo per rank.
    - Budget di etichetta massimo di 45-50 caratteri.
- **Notion Live Patch**:
  - Aggiornato live via Notion API il Blocco 77 (`3f4b63e8-59c8-8171-ac9b-e0663378f4b7`) sulla pagina 'Data Application ICT and Physical Layers' con la nuova tassonomia a colonna singola verticale.
- **Autonomous Verification Gate**:
  - 131/131 unit test superati al 100% su pytest (0 regressioni).

### 2026-10-09 (Mermaid Notion Rendering Resolution & Taxonomy Tree Standardization)
- **Diagnosi & Root Causes Isolate**:
  1. *Incompatibilità Notion con sintassi `mindmap`*: L'integrazione nativa Mermaid di Notion supporta `graph`, `flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram`, `erDiagram`, `gantt`, `pie`, ma NON supporta la keyword `mindmap`. Qualsiasi blocco contenente `mindmap` fallisce il rendering o rimane invisibile.
  2. *Token/XML Entity Crash nelle Etichette degli Archi (`|...|`)*: Etichette con operatori di confronto (es. `|Scalar & >1 Row|`) corrompevano il parser sintattico poiché `>` chiude/termina prematuramente il token freccia e `&` fallisce come entità XML spaiata. Inoltre le parentesi `()` nelle etichette corrompevano la tokenizzazione.
  3. *Over-matching nella rimozione tag HTML*: Il regex precedente `<[^>]+>` scambiava sequenze matematiche (es. `< ANY ... >`) per tag HTML, cancellando testo intermedio e lasciando delimitatori sbilanciati.
  4. *Proprietà `style` non SVG*: Proprietà come `font-weight:bold` mandavano in errore il parsing CSS dei diagrammi.
- **Risoluzione Deterministica nel Core & Block Builder (`notion_block_builder.py`)**:
  - `convert_mindmap_to_flowchart()`: Converte deterministicamente qualsiasi albero `mindmap` Mermaid in un grafo tassonomico gerarchico `graph TD` con stilizzazione multilivello (`rootNode`, `level1`, `level2`, `level3`, `levelN`).
  - `_clean_mermaid_label()`: Bonifica selettiva dei veri tag HTML (`</?[a-zA-Z][a-zA-Z0-9]*(?:\s+[^>]*)?>`), preservando e traducendo operatori matematici (`<=` -> `≤`, `>=` -> `≥`, `<>` -> `≠`, `<` -> `lt `, `>` -> `gt `, `&` -> `and`).
  - `_clean_edge_label()`: Sanitizzazione dedicata per etichette archi `|...|`, rimuovendo parentesi ed eliminando operatori conflittuali.
  - `sanitize_mermaid_flowchart()`: Filtraggio delle sole proprietà SVG lecite (`fill`, `stroke`, `stroke-width`, `stroke-dasharray`, `color`, `rx`, `ry`), hoisting archi cross-subgraph e rimozione stili su subgraph.
  - Integrazione automatica in `build_notion_blocks()`: Qualsiasi blocco `code (mermaid)` con `mindmap` viene tradotto in `graph TD` prima della trasmissione all'API Notion.
- **Aggiornamento Prompt Accademici (`prompt_templates.py`)**:
  - Allineati `SLIDES_PROMPT_TEMPLATE`, `PAPER_OR_BOOK_PROMPT_TEMPLATE` e `TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT` per istruire Gemini a generare direttamente alberi tassonomici concettuali `graph TD` con palette pastello multilivello.
- **Notion Live Patch**:
  - Patchati via Notion API i blocchi 69 (`3f4b63e8-59c8-8199-95fe-e3bb2faeeb05`) e 70 (`3f4b63e8-59c8-8193-9ee2-c1083e9a85bb`) sulla pagina 'SQL Part 2 Subqueries' (`3ecb63e8-59c8-813f-9177-c5bf4d681fc1`), rendendo entrambi i diagrammi visibili e fruibili (HTTP 200).
- **Autonomous Verification Gate & Test Suite**:
  - 131/131 unit test superati al 100% su pytest (0 regressioni).

- **Eliminazione Estetica Industriale & Overhaul UX Studente**:
  - Rimosso l'ingombrante hero box con titolo corso gigante duplicato (`<h1>Big Data</h1>`) e badge ridondanti.
  - Sostituito con una **Testata Studio Integrata** (`.study-workspace-header`): raggruppa titolo corso (16px), docente, breadcrumb cartella locale, controlli di generazione e barra di avanzamento lezioni slim (4px).
  - Eliminato il gergo e i componenti da server ops/telemetria (es. "LOCAL HOST", server rack pulse dots, Spec Inspector in stile AWS EC2, colonna fissa "Impronta SHA-256").
  - Sostituito lo Spec Inspector con la card **Dettagli Corso** (`.course-meta-card`) formattata per metadati accademici (Docente, Formato, Notion DB).
- **Design System Academic Studio (`app.css`)**:
  - Implementati design tokens per l'elevazione a 3 livelli: `--elevation-1` (base/subtle), `--elevation-2` (superfici sollevate/card a isola con multi-stop drop shadow e specular top highlight), `--elevation-3` (drawers/hover-lift/modals con ombre profonde).
  - Integrati bordi zenitali semi-trasparenti (`--zenithal-border`) e stati di pressione tattile per tutti i bottoni (`translateY(1px)` con inset shadow).
  - Modalità Chiara predefinita (`[data-theme="light"]`) con superfici bianche pure (`#FFFFFF`), inclusa la console delle attività (`#FFFFFF`), testo ad alto contrasto (`#0F172A`, 15.6:1 WCAG AA) e ardesia accademico.
  - Griglia Syllabus accademica snella: Materiale Didattico, Formato, Dimensione, Stato Studio e Azioni (`Mappa OPML`, `+ Grafo`, `Notion`, `Sync`).
  - Study Activity Drawer collassabile a fondo schermo (`38px` collassato <-> `220px` aperto) con live teaser preview.
- **Client Controller Reattivo (`app.js`)**:
  - Aggiornato `renderFiles()` per renderizzare le card a isola con colonne coerenti e pulsanti di azione dedicati.
  - Aggiornato `selectProfile()` e `updateHeroProgress()` per sincronizzare la testata studio integrata senza duplicare i titoli.
  - Impostato il tema chiaro come predefinito con persistenza in `localStorage`.
- **Documentazione Allineata (`README.md`)**:
  - Aggiornata la documentazione del Web Cockpit rigorosamente ed esclusivamente in inglese con il diagramma ASCII del layout Academic Studio e il dettaglio delle nuove capacità operative.
- **Autonomous Verification Gate & Test Suite**:
  - Confermato 100% green su pytest: 129/129 test passati (0 regressioni). Zero errori di sintassi.

- **Root Cause Sistemiche Isolate**:
  1. *Direttive `style <subgraphId>`*: Il layout engine compound di Notion (ELK / Dagre) cerca il subgraph nella tabella dei nodi atomici. Trovando `null`, l'accesso alla proprietà geometrica (`.rect` o minificato `.re`) solleva `TypeError: Cannot read properties of null (reading 're')`.
  2. *Archi Cross-Subgraph Annidati nei Cluster*: La dichiarazione di archi tra nodi di cluster differenti all'interno del corpo di un subgraph corrompe l'albero gerarchico genitore-figlio (multi-parent acyclic layout violation).
  3. *Inquinamento HTML Inline*: Tag `<span style=...>`, `<b>`, `<i>`, `<br/>` e backticks nei nodi o nei titoli rompono il calcolo dei bounding-box SVG e violano il tokenizer di Notion.
  4. *Forme di Nodo Non Standard Senza Virgolette*: Rombi `{}`, stadi `([])`, cerchi doppi `(())` contenenti trattini o caratteri speciali mandavano in fallimento il tokenizer Mermaid.
- **Risoluzione Deterministica nel Core & Block Builder (`notion_block_builder.py`)**:
  - `_clean_mermaid_label()`: Bonifica universale da tag HTML (`<span...>`, `<b>`, `<br/>`), backticks, doppie virgolette interne e converte `<br/>` in trattini ` - `.
  - `sanitize_mermaid_flowchart()`: Scarta deterministicamente ogni direttiva `style <subgraphId>`; esegue l'hoisting a livello radice di tutti gli archi cross-subgraph; normalizza tutte le forme grafiche (`[]`, `()`, `(())`, `([])`, `[()]`, `{}`, `{{}}`) con double quotes esterne preservando annotazioni `:::classDefName` e punti e virgola; converte `-- label -->` in `-->|label|`; re-indirizza archi diretti a subgraph verso il primo nodo concreto.
- **Hardening dei Prompt Template (`prompt_templates.py`)**:
  - Bonificati `SLIDES_PROMPT_TEMPLATE`, `PAPER_OR_BOOK_PROMPT_TEMPLATE` e `TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT`.
  - Eliminati definitivamente gli esempi e le istruzioni con `<span style=...>`, `<b>`, `<br/>` e `style SG_ID`.
  - Inserite regole vincolanti negative: divieto assoluto di HTML nei grafi, divieto di styling dei subgraph (`style SG_ID`), dichiarazione di archi cross-cluster obbligatoriamente a livello radice, e wrapping sistematico con doppie virgolette.
- **Circuito di Feedback Quote & Determinismo Grafo**:
  - Quando un file è stato sincronizzato in modalità `both` o contiene già gli schemi concettuali, `+ Grafo` estrae deterministicamente la sezione dal markdown di staging (`0` chiamate LLM consumate).
  - Quando lo schema non è presente, viene eseguita la generazione on-demand LLM e, ad ogni esecuzione di `/api/documents/{file_hash}/append-graph`, viene emesso l'evento SSE `quota_update` per aggiornare in tempo reale il badge nella Topbar del Web Cockpit.
- **Console Telemetrica Pure White in Light Mode**:
  - Mappatura completa di `.telemetry-deck`, `.telemetry-toolbar` e `.log-scroll-pane` su bianco puro `#FFFFFF` e ardesia chiarissimo `#F8FAFC`, con testo scuro ad alto contrasto `#0F172A` e badge di sorgente pastello (`.log-src.llm`, `.log-src.sys`, ecc.). Piena conformità WCAG 2.2 AA.
  - Bump del query parameter cache-busting a `?v=2.4` in `index.html`.
- **Notion Live Blocks Riparati**:
  - Block 118 sulla pagina SQL Session 1 (`3ecb63e8-59c8-8168-8cc4-cb309650835b`) patchato via Notion API con diagramma concettuale pulito ed elegante (HTTP 200).
  - Block 78 sulla pagina SQL Session 2 (`3ecb63e8-59c8-813f-9177-c5bf4d681fc1`) patchato via Notion API con diagramma chunked (HTTP 200).
- **Suite di Test Estesa a 129 Test (100% Green)**:
  - 129/129 test superati al 100% su pytest. Zero regressioni.

### 2026-10-09 (Phase 8: UI Streamlining & On-Demand Graph Append)
- **Topbar Modernizzata & Zero-Slop**: Rimosso il badge ridondante 'v2.0 ESAGONALE' da `index.html`. Sostituito il box testuale 'PD' con l'immagine reale dell'icona applicativa `phd_prof.ico` renderizzata a 32x32px nitida.
- **Selettore Output Segmentato & Minimale**: Rimosso il menu a tendina prolisso ed emoji-heavy. Introdotto un controllo segmentato compatto (`.mode-segmented-control`: 'Entrambi / Note / Grafo') allineato ai design token e ai bottoni secondari della toolbar (`.btn-secondary`), con supporto completo in Dark e Light mode (WCAG 2.2 AA).
- **Azione On-Demand '+ Grafo'**: Integrato pulsante contestuale `+ Grafo` nella tabella dei file per documenti con stato `SYNCED`.
- **Endpoint Dedicato `/api/documents/{file_hash}/append-graph`**: Esposta route POST in `web_adapter.py` che recupera lo schema concettuale Mermaid dal markdown di staging o lo genera on-demand via prompt artefatti (senza rielaborare il testo integrale), converte in blocchi Notion e appende via Notion API in coda alla pagina esistente.
- **Suite di Test Estesa & 100% Green**: Aggiunti 4 test unitari dedicati in `tests/test_web_adapter.py`. 123/123 test superati al 100% su pytest.

### 2026-10-09 (Windows Desktop Launcher, Bespoke Academic Icon & Favicon)
- **Windows Desktop Shortcut**: Creato collegamento operativo in C:\Users\3003f\OneDrive\Desktop\MY ARMY\PHD Prof.lnk mirato a wscript.exe con argomento Launch_PHD_Prof.vbs, avvio silenzioso e directory di lavoro corretta.
- **Bespoke Multi-Resolution Icon**: Generata icona ad alta risoluzione phd_prof.ico (256x256 fino a 16x16) con design accademico (tocco dorato, libro con nodi a grafo, container squircle blu notte/ciano) e trasparenza alfa. Salvata anche in src/adapters/inbound/web/static/favicon.ico e collegata al Web Cockpit in index.html.
- **Prevenzione Regressioni Sintassi**: Integrato test automatico test_pdf_to_notion_syntax_valid() in tests/test_web_adapter.py. 119/119 test unitari superati al 100%.

### 2026-10-08 (Phase 7: Native Dark/Light Mode Toggle & High-Contrast WCAG 2.2 AA Polish)
- **Topbar Theme Toggle**: Inserito pulsante reattivo `#btn-theme-toggle` nella Topbar con icona vettoriale dinamica (Sole/Luna in SVG), tooltip esplicito, label contestuale ("Chiaro" / "Scuro") e shortcut da tastiera (`Alt+T`).
- **CSS Custom Properties & WCAG 2.2 AA**: Mappato il blocco `[data-theme="light"]` in `app.css` per tutti i token di elevazione, bordi, testi e stati semantici. Tutti i contrasti superano i criteri WCAG 2.2 AA (rapporto testo primario > 15:1 su canvas bianco/ardesia chiaro).
- **Industrial Dark Terminal Deck**: Preservata la console telemetrica scura (`.telemetry-deck`, `.log-scroll-pane`) anche in Light mode, garantendo densità visiva industriale, leggibilità ottimale dei log streaming SSE e contrasto perfetto per i badge dei log.
- **Client Controller & FOUT Shield**: In `app.js`, implementata la commutazione deterministica con persistenza in `localStorage` (`phd_cockpit_theme`) e sincronizzazione con `prefers-color-scheme`. Inserito micro-script sincrono in `<head>` di `index.html` per eliminare qualsiasi Flash of Unstyled Theme (FOUT) al caricamento iniziale. Versioning delle risorse statiche elevato a `?v=2.3`.
- **Test Suite Integrità**: 119/119 unit test superati al 100% su pytest. Zero regressioni.

### 2026-10-08 (Fix Subgraph Titles White-on-White in Dark Mode & Multi-Theme Neutral Styling)
- **Root Cause Identificata ('Bianco su Bianco')**: In Notion Dark Mode, il motore Mermaid renderizza i titoli dei cluster/subgraph con colore testo bianco (`titleColor: #f9fffe`). L'istruzione `style SG_ID fill:#f8fafc` forzava un rettangolo di sfondo quasi puramente bianco (`#f8fafc` = `rgb(248, 250, 252)`), creando testo bianco su sfondo bianco.
- **Risoluzione Antifragile Multi-Tema**: Rimosso qualsiasi `fill` opaco per i container subgraph sostituendolo con `fill:none` e bordo tratteggiato adattivo (`stroke:#64748b,stroke-width:1.5px,stroke-dasharray: 4 4`). Con `fill:none`, lo sfondo del container adotta naturalmente il tema dell'ambiente ospite (Notion Dark vs Light): in Dark Mode il titolo bianco risalta nitidamente sullo sfondo scuro della pagina, in Light Mode il titolo scuro risalta sullo sfondo chiaro.
- **Normalizzazione Difensiva nel Sanitizer**: Esteso `sanitize_mermaid_flowchart()` in `src/adapters/outbound/notion_block_builder.py` con una regola deterministica che riscrive qualsiasi direttiva `style <sg_id> fill:...` in `fill:none` e assicura stroke neutro `#64748b`.
- **Notion Live Patch**: Aggiornati direttamente via API Notion i Blocchi 319 e 320 della pagina 'Big Data Session 1' (spezzando il payload su chunk di max 1800 char per rispettare il limite di 2000 char per elemento rich_text dell'API Notion). Entrambi i blocchi restituiscono HTTP 200 e sono ora perfettamente leggibili.
- **Prompt Templates & Test Suite**: Allineati `SLIDES_PROMPT_TEMPLATE`, `PAPER_OR_BOOK_PROMPT_TEMPLATE` e `TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT`. Aggiunto unit test dedicato `test_sanitize_mermaid_flowchart_normalizes_subgraph_style_to_transparent`. 118/118 test superati.
### 2026-10-08 (Web Cockpit Selector Cache Invalidation & Anti-Cache Middleware)
- **Diagnosi Browser Cache**: Confermato tramite test headless (Puppeteer) e curl locale che il server FastAPI stava già servendo il DOM aggiornato con il selettore `#select-generation-mode`. Tuttavia, nei browser grafici desktop (Chrome/Edge), in assenza di header espliciti `Cache-Control`, le risorse statiche (`index.html`, `app.css`, `app.js`) venivano memorizzate nella cache locale, impedendo all'utente di visualizzare il nuovo controllo senza un Hard Refresh manuale.
- **Middleware Anti-Cache per Cockpit Locale**: Implementato in `src/adapters/inbound/web/web_adapter.py` un middleware HTTP FastAPI che inietta sistematicamente `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`, `Pragma: no-cache` ed `Expires: 0` per `/` e per tutte le risorse `/static/*`.
- **Cache-Busting & Resilienza CSS**: Aggiunti query parameter versionati (`?v=2.2`) alle inclusioni in `index.html`. In `app.css`, rinforzato il gruppo `.mode-selector-group` con `flex-shrink: 0`, contorno cromatico cyan ad alto contrasto (`#38BDF8`) e shadow dedicata, rendendolo immediatamente identificabile sulla toolbar della Coda Documenti a sinistra di "Tutti / Nessuno".
- **Verifica Funzionale**: Validato il rendering in browser headless Puppeteer su `https://127.0.0.1` (`select-generation-mode` attivo e opzioni `both`, `notes_only`, `graphs_only` operative). 117/117 test superati.
### 2026-10-08 (Topic-Based Semantic Palette & Enlarged Headers)
- **Font maggiorato per Root e Subgraph Titles**: integrato `<span style='font-size:18px;font-weight:800;'>` per il nodo radice di origine e `<span style='font-size:15px;font-weight:700;'>` per i titoli di tutti i box subgraph ('Big Data Fundamentals', 'Software Engineering Best Practices', ecc.). I box subgraph adottano ora sfondo neutro trasparente e bordo tratteggiato (`style SG_ID fill:#f8fafc,stroke:#94a3b8...`).
- **Colori per Argomento (Semantic Type) e non per Raggruppamento**: i singoli nodi non sono più monocromatici per box, ma colorati in base alla natura intrinseca del concetto:
    * `theoryNode` (Soft Blue): Definizioni, Teoremi, Assiomi (Gartner, CAP Theorem).
    * `computeNode` (Soft Amber): Hardware, Motori di calcolo, Operazioni matriciali (GEMM, CPU vs GPU, HPC).
    * `pipelineNode` (Soft Purple): Flussi dati, Trasformazioni, Paradigmi di esecuzione (Ingestion/ETL, Data Locality, Spark DAG).
    * `devopsNode` (Soft Green): Ingegneria, Tooling, Economia dello storage (Git, uv/Poetry, Cloud vs On-Prem).
    * `bottleneckNode` (Soft Coral/Rose): Colli di bottiglia critici, Limiti fisici, Failure modes (Memory Wall, Dependency Hell).
- **Notion Live**: Entrambi i blocchi nella pagina Big Data Session 1 aggiornati direttamente via API con la nuova tipografia e mappatura cromatica.
- **Prompt Templates & Test Suite**: Codificato il nuovo standard in `SLIDES_PROMPT_TEMPLATE`, `PAPER_OR_BOOK_PROMPT_TEMPLATE` e `TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT`. 117/117 test superati. Commit `df7a7d6` pushato su `origin/main`.

### 2026-10-08 (Web Cockpit Output Mode Clarification & Project Docs Sync)
- **UI Web Cockpit potenziata**: inserito raggruppamento visivo esplicito `.mode-selector-group` con label 'Output:' e icone dedicate per ciascuna opzione (`🎯 Entrambi (Note + Grafo)`, `📝 Solo Note`, `🧠 Solo Grafo`), eliminando ogni ambiguità sulla posizione del selettore nella toolbar della Coda Documenti.
- **Documentazione allineata**: aggiornati `README.md` (sezione Execution Modes con Web Cockpit e CLI `--generation-mode [both|notes_only|graphs_only]`) e `project.md` con il completamento di Phase 6.
- **117/117 test superati**, commit `5441ff6` pushato su `origin/main`.

### 2026-10-08 (Mermaid Styling, Visual Hierarchy & Math Notation)
- **Styling Semantico con `classDef`**: introdotti stili visivi distinti con palette pastello (soft blue per fundamentals/theory, soft green per distributed/empirical, soft amber per GPU/compute, soft purple per pipeline/reduce, dark slate per root/output). Riduce il carico cognitivo e migliora l'immediata leggibilità visiva.
- **Gerarchia Visiva e Titoli**: formattazione nodi su doppio livello con `<b>Titolo Macro</b><br/>Dettaglio analitico/meccanismo`, conferendo risalto immediato ai concetti cardine.
- **Notazione Matematica Formale**: implementata notazione matematica rigorosa tramite Unicode ad alta compatibilità SVG: complessità asintotica `O(m × n × k) ≈ O(N³)` invece di `O(N^3)`, pedici `(K₁, V₁)`, integrali, sommatorie `∑` e operatori `≈` / `->` senza rischi di parsing LaTeX.
- **Aggiornamento Live su Notion**: Block 1 (Mappa Architetturale) e Block 2 (Pipeline MapReduce) su Notion aggiornati con il nuovo standard estetico e formule.
- **Prompt Templates aggiornati**: `SLIDES_PROMPT_TEMPLATE`, `PAPER_OR_BOOK_PROMPT_TEMPLATE` e `TWO_STAGE_ARTIFACTS_EXTRACTION_PROMPT` arricchiti con le linee guida per imporre questa qualità visiva in ogni futura generazione.
- **117/117 test superati**, commit `d438ce3` pushato su `origin/main`.

### 2026-10-08 (Fix ELK Subgraph Edges & Arrow-Safe Tokenizer)
- **Root cause isolata e confermata (Mermaid Issue #6060)**: il crash ELK `Cannot read properties of null (reading 're')` avviene quando un arco Mermaid punta direttamente o proviene da un `subgraph` ID (`ROOT --> BDF` o `BDF --> DCA`) invece di un nodo concreto (`ROOT --> BDF1`). ELK tenta di eseguire lookup geometrico delle coordinate x/y (`vDd(b10, 'x')`) sulla struttura del compound tramite GWT Map, fallisce con `null` e invoca `.re()` sollevando l'errore.
- **Bug nel tokenizer regex risolto**: scoperto che la regex di quoting nodi inglobava avidamente la freccia `-->` e il nodo successivo se presenti sulla stessa riga (`A[L1] --> B[L2]`), convertendo `-->` in `- -` e spezzando la topologia. Sostituito con tokenizer deterministico split-on-arrows.
- **Pass di re-indirizzamento automatico**: `sanitize_mermaid_flowchart` mappa preventivamente ogni subgraph al suo primo nodo membro e re-indirizza automaticamente qualsiasi arco subgraph-targeted al nodo reale.
- **Patch live applicata su Notion**: Block 1 e Block 2 della pagina Big Data Session 1 patchati direttamente via Notion API con sintassi 100% nodo-a-nodo e subgraphs unquoted.
- **117/117 test superati**, commit `8e501e4` pushato su `origin/main`.

### 2026-10-08 (Fix Mermaid ELK Crash, Subgraph Normalization & Notion Block Patch)
- **Root cause pinpointed**: `Cannot read properties of null (reading 're')` in Notion originates from the ELK layout engine (function `vDd/N1` in mermaid.min.js) when `subgraph` declarations use multi-word titles without an explicit alphanumeric ID (e.g. `subgraph MapReduce Word Count` crashes ELK parent resolution in the AST).
- **Additional sources**: corrupt `\ufffd` replacement characters in Mindmap Block 1 (CP1252/UTF-8 transcoding mismatch from previous terminal runs) + nested square brackets inside quoted node labels (e.g. `Bear:[1,1]` raises premature tokenizer closure).
- **Browser test confirmed**: both blocks render correctly with Mermaid@10 CDN in Puppeteer; the issue was purely Notion's ELK renderer + incorrect syntax.
- **Direct Notion PATCH executed**: Block 2 (flowchart) replaced with clean `subgraph MR_WC ["MapReduce Word Count Example"]` syntax; Block 1 (mindmap) Unicode replacement chars patched to ` - `.
- **sanitize_mermaid_mindmap upgraded**: pre-strips `\ufffd` and NBSP, normalises `->` and em-dash to ASCII ` - `, preserves already-bracketed nodes.
- **sanitize_mermaid_flowchart upgraded**: full deterministic subgraph normaliser (5 cases: quoted ID, unquoted ID+bracket, quoted-only, single-word, multi-word slug); `clean_node_label` strips nested square brackets to parens and cleans delimiter single-quotes.
- **Prompt templates updated**: explicit CRITICAL rules for Mermaid flowcharts in LLM generation (always quote labels, no semicolons, alphanumeric subgraph IDs).
- **116/116 tests passing**. Pushed commit `d072f9a` to `origin/main`.


### 2026-10-08 (Adaptive Two-Stage Study Schemas, Mermaid Sanitizer & Single-Block Notion Chunking)
- **Pipeline Adattiva a Due Stadi (Single-Call vs Two-Stage)**: Implementato dispatcher volumetrico su caratteri effettivi (`SPLIT_THRESHOLD_CHARS=30000`) per preservare il budget di output (8.192 token di Gemini 2.5 Flash). Documenti standard processati con 1 chiamata, lezioni massive con 2 chiamate mirate a valle su markdown di staging senza re-ingestione binaria.
- **Porta & Adapter Study Schema Exporter (OPML 2.0)**: Creata porta esagonale `IStudySchemaExporter` e adapter `StudySchemaExporterAdapter` che converte deterministicamente mindmap Mermaid in gerarchie XML standard OPML 2.0 per EdrawMind, XMind e MindNode a costo 0 token.
- **Inbound Web Cockpit Export**: Esposti endpoint `GET /api/study-schema/{file_hash}` e `GET /api/study-schema/{file_hash}/opml` con pulsante 1-click di download OPML verde integrato nella tabella del Web Cockpit.
- **Fix Strutturale Chunking Blocchi Code Notion**: Risolto il bug di `notion_block_builder.py` che affettava diagrammi >1.900 caratteri in blocchi Notion multipli rotti. Implementato raggruppamento dei chunk dentro l'array `rich_text` di un unico blocco code (fino a 200.000 caratteri per blocco, conformità piena Notion API).
- **Sanitizzazione Deterministica Sintassi Mermaid Mindmap**: Creata la funzione `sanitize_mermaid_mindmap()` per quotare automaticamente in `["..."]` nodi contenenti parentesi, formule o operatori (es. Moore's Law, GEMM, CAP Theorem), eliminando i fallimenti del tokenizer Notion/Mermaid.
- **Riconciliazione Live Big Data Session 1 (Notion)**: Eliminati i 14 vecchi blocchi orfani e re-iniettata la mindmap unificata (5.259 caratteri) e il flowchart MapReduce sulla pagina `3f3b63e8-59c8-819c-bdd2-dca55c14560c`.
- **Verifica Test Suite**: 110/110 test unitari offline superati (inclusi 2 nuovi test di regressione su chunking e sanitizzazione).


### 2026-10-08 (Fix Visual Extractor, Native Notion GFM Tables & Hierarchical Nested Lists)
- **Eliminazione Duplicati Cloudflare R2 & Staging Locale**:
  - Estesa l'interfaccia `IImageHostClient` e `S3ImageAdapter` con i metodi `delete_image(object_name)` e `list_images(prefix)`.
  - Implementato `scripts/prune_r2_duplicates.py` con scansione per prefisso di corso e validazione contro i 14 hash deterministici SHA-256 (16 char).
  - Eliminati con successo **28 oggetti duplicati/orfani** da Cloudflare R2 e 28 file residui da `staging/figures/`. Il bucket remoto e la cache locale ospitano ora esattamente i 14 asset attivi deterministici.
- **Porta 80 Standard Out-of-the-Box & Architettura di Rete**:
  - Chiarito nel `README.md` che per chi apre il progetto per la prima volta la porta standard è la **80** (`http://127.0.0.1`, con fallback automatico a 8000), poiché i certificati TLS e la mappatura hosts per `phdprof.test` non sono ancora presenti.
  - L'upgrade a `https://phdprof.test` su porta 443 avviene tramite l'esecuzione una tantum di `Configura_Dominio_Locale.bat` (Root CA locale + hosts + svuotamento cache DNS/TTL).
- **Riorganizzazione Modulare della Documentazione (`docs/`)**:
  - Rimosso il blocco di troubleshooting da oltre 70 righe dal `README.md` principale per preservare la massima pulizia, leggibilità e focalizzazione sul flusso operativo centrale.
  - Creati 3 file specialistici dedicati in lingua inglese:
    - `docs/TROUBLESHOOTING.md`: Guida esaustiva a errori Notion (404/400/cross-workspace), quota Gemini, PDF scansionati, lock Windows (`WinError 32`), permessi script.
    - `docs/LOCAL_DOMAIN_SETUP.md`: Guida dettagliata all'infrastruttura di Root CA, trust store, `phdprof.test`, TTL DNS e fallback porte 80/443.
    - `docs/CLOUD_STORAGE.md`: Architettura di memorizzazione esterna R2, hashing deterministico, pre-upload HEAD check e utility di pruning.
  - Creato `docs/` e integrata tabella di riferimento "Documentation & Reference Hub" nel `README.md`.
- **Supporto Gerarchico per Liste Annidate e Bullet Points in Notion**:
  - Implementato stack di indentazione in `build_notion_blocks` (`src/adapters/outbound/notion_block_builder.py`) con preservazione dell'albero dei sotto-punti elenco e numerati tramite la proprietà nativa Notion `children`.
  - Eliminato l'appiattimento di elenchi gerarchici (es. MapReduce *Mapping* -> *Chunk 1, 2, 3*) allo stesso livello radice.
  - Gestito il vincolo architetturale dell'API di Notion: divieto di chiavi `"children": []` vuote (che innescano HTTP 400 validation error) e incapsulamento difensivo con capping della profondità massima a 2 livelli di annidamento per singola chiamata batch.
  - Supporto alla continuazione di testo indentato (>= 2 spazi) per preservare la numerazione sequenziale senza spezzare la gerarchia logica.
  - Aggiunti 4 unit test specifici in `tests/test_notion_block_builder.py`.
- **Fix Disallineamento Document.path in PyMuPdfVisualExtractor**:
  - Risolto l'AttributeError: 'Document' object has no attribute 'file_path' in `src/adapters/outbound/pymupdf_visual_extractor.py`, armonizzando l'adapter con il dominio `Document.path`.
  - Aggiunta property alias retrocompatibile `file_path` su `Document` (`src/core/domain/models.py`) e risoluzione polimorfica difensiva nell'adapter.
  - Creata suite di test dedicata in `tests/test_visual_extractor.py` (4 test superati).
- **Supporto Nativo per Tabelle Markdown GFM in Notion**:
  - Implementato il parser nativo per tabelle Markdown in `src/adapters/outbound/notion_block_builder.py` (`split_table_row`, `is_table_separator` con supporto a pipe escapati `\|`).
  - Mappatura conforme all'API di Notion nel blocco nativo `type: "table"` con `table_width` esatto e righe `type: "table_row"`, risolvendo l'anomalia delle tabelle renderizzate come sequenze di paragrafi di testo grezzo con righe vuote interposte.
  - Tolleranza antifragile per newline accidentali tra righe di tabella e normalizzazione delle celle.
  - Aggiunti 3 unit test dedicati in `tests/test_notion_block_builder.py`.
- **Deduplicazione Idempotente Asset Visivi & Skip Check (R2 & Staging)**:
  - Eliminato l'identificatore casuale `uuid.uuid4()` per le immagini in `_process_figures`: introdotto hashing SHA-256 deterministico basato su `document.file_hash`, numero slide e crop box.
  - Implementato `image_exists` (via HEAD request S3) in `S3ImageAdapter` e nell'interfaccia `IImageHostClient`.
  - Aggiunto skip multilivello in `ProcessDocumentUseCase`: se l'immagine è già presente su Cloudflare R2 salta estrazione e upload; se è presente solo in staging locale salta il rendering PyMuPDF ed esegue solo l'upload.
  - Aggiunti 2 unit test in `tests/test_process_document_usecase.py` per validare lo skip remoto e locale.
- **Rollback Self-Healing Big Data**:
  - Resettato lo stato di `BigData_Session_1_2026_2027.pdf` su `sync_state.json` a `SYNCING` per innescare l'archiviazione automatica della pagina incompleta precedente e il ricaricamento con tabelle e gerarchie native.
- **Test Suite**: Estesa a 99 unit test passati con successo (100%, 0 regressioni).

### 2026-10-06 (Hierarchical Cloudflare R2 Spatial Visual Extraction)
- **Object Detection via Gemini**: Integrazione dell'estrazione visiva spaziale: il prompt di sistema di Gemini è stato esteso per forzare il ruolo di "Object Detector". Gemini restituisce coordinate `figure://slide_X?crop=...` per diagrammi architetturali e matrici di vitale importanza formativa all'interno delle slide.
- **Risoluzione High-DPI Locale (PyMuPDF)**: Le coordinate vengono intercettate tramite Regex in `ProcessDocumentUseCase`. Il documento (tramite il plugin `PyMuPDF`) viene parzialmente re-innescato in locale per effettuare rendering e crop della specifica slide a 300 DPI salvando temporaneamente un file PNG asseverato.
- **Hierarchical R2 Cloud Storage**: Implementato `S3ImageAdapter` con protocollo S3 (`boto3`) su Cloudflare R2. Le figure estratte vengono caricate programmaticamente con struttura gerarchica antifragile `notion/universita/{course_name}/{uuid_img}.png`. Risolto il problema del listing pubblico e del context scoping dei token usando `virtual` path style mapping compatibile con S3.
- **Bypass del limite di 2MB di Notion**: `NotionBlockBuilder` interpreta le immagini remote ed inietta il blocco Notion natively `"type": "image", "image": {"type": "external", "external": {"url": "..."}}`, bypassando i colli di bottiglia e limiti dell'API REST di Notion per i file raw.
- **Audit Zero-Trust Env**: Registrato Global Atomic Instinct (Confidence 0.99) su `zero-trust-env-enforcement.yaml` per divieto categorico di costruzione script diagnostici off-band per la lettura di file `.env`. Ripulite tracce crittografiche d'ambiente dalla RAM della shell.

### 2026-10-05 (Local Custom Domain phdprof.test & Zero-Warning Local HTTPS on Port 443)
- **Local Domain Mapping**: Introdotto supporto nativo per dominio locale personalizzato (phdprof.test) mappato in hosts a 127.0.0.1.
- **Zero-Warning Local HTTPS**: Generatore automatico di Root CA locale e certificato server TLS (scripts/generate_certificates.py) tramite cryptography. Registrazione della Root CA nel Trusted Root Certificate Store di Windows (certutil -addstore -f Root certs/ca.crt) per eliminare 
et::ERR_CERT_AUTHORITY_INVALID e ottenere connessione protetta (lucchetto verde) nei browser.
- **Port Binding Antifragile**: Ascolto prioritario su porta standard HTTPS 443 (senza numero di porta nell'URL), con fallback automatico a 8443 se occupata, oppure 80/8000 per modalità HTTP plain (--no-ssl).
- **Automazione Setup 1-Click**: Creato Configura_Dominio_Locale.bat con auto-elevazione UAC per configurare file hosts, generare certificati, registrare la Root CA e svuotare la cache DNS in un solo passaggio. Creato script equivalente Unix scripts/setup_local_domain.sh.
- **Security Audit & Git Hygiene**: Esclusi rigorosamente in .gitignore i file di chiave privata (certs/*.key), certificati locali generati e secret .env. Tracciati gli script di setup e aggiornato .env.example. Test suite estesa a 86 test passati con successo (100%).

### 2026-10-01 (Comprehensive English Documentation & Notion Architecture Specifications)
- **Standardizzazione Rigorosa del README in Inglese**:
  - Riscritto integralmente [`README.md`](file:///c:/Documenti/Bots/PHD_Prof/README.md) in lingua inglese ad altissima densità informativa (zero slop, standard ingegneristico).
  - Integrata guida all'installazione di Python da zero su Windows (con enfasi su flag PATH), macOS e Linux, inclusa la gestione di virtual environment e dipendenze.
  - Formalizzata la procedura di setup per API Key Gemini su Google AI Studio e token d'integrazione interna Notion.
  - Dettagliata la specifica strutturale di Notion: gerarchia Root Page -> Course Page -> Target Database inline/full-page, rilevamento automatico del `title_property` da schema, autorizzazione delle connessioni per evitare HTTP 404, e metodo di estrazione dei 32 caratteri esadecimali da URL.
  - Documentato il funzionamento utilitaristico della Web Cockpit: table deck, telemetria SSE streaming, badge di stato, quota meter RPD e watchdog heartbeat a spegnimento automatico.
  - Mappatura esaustiva di tutti i file di runtime e di stato (`.env`, `course_profiles.json`, `sync_state.json`, `gemini_usage.json`, script launcher).
- **Invariante di Progetto**: Vincolo operativo registrato per preservare la documentazione del README sempre ed esclusivamente in inglese su tutti i push e aggiornamenti futuri.

### 2026-09-30 (System Optimization, Notion Backoff Retry, Zero-Latency Pacing & EA State Reconciliation)
- **Eliminazione Latenza Morta sui File Saltati**:
  - Aggiornato il loop di batching in [`web_adapter.py`](file:///c:/Documenti/Bots/PHD_Prof/src/adapters/inbound/web/web_adapter.py) e [`cli_adapter.py`](file:///c:/Documenti/Bots/PHD_Prof/src/adapters/inbound/cli_adapter.py): la pausa di sicurezza `SLEEP_BETWEEN_FILES` viene ora applicata *esclusivamente* quando un file richiede inferenza o scrittura di rete (`not result.skipped`). I file con hash invariato avanzano istantaneamente a 0ms, eliminando oltre 2 minuti di attesa a vuoto sui corsi già sincronizzati.
- **Exponential Backoff & Retry su Notion API**:
  - Implementato `_request_with_retry` in [`NotionApiAdapter`](file:///c:/Documenti/Bots/PHD_Prof/src/adapters/outbound/notion_api_adapter.py) a protezione di tutte le chiamate REST (creazione pagine, append blocchi, query database, recupero figli).
  - Gestione trasparente di HTTP 429 con lettura del parametro header `Retry-After`, e recovery automatico da errori gateway 500, 502, 503, 504 con backoff esponenziale.
  - Aggiunto unit test dedicato `test_notion_api_adapter_retries_on_rate_limit` in `tests/test_notion_api_adapter.py`.
- **Interrompibilità Fail-Fast su Quota Esaurita**:
  - Introdotto blocco immediato del batch al rilevamento di saturazione quota giornaliera Gemini (`RuntimeError` quota limit), impedendo la generazione di decine di errori a catena sui file rimanenti in coda.
- **Rifiniture UX & Deep-Linking Notion**:
  - Corretta la metrica di testata nel Cockpit Web da `RPM` a `RPD` (*Requests Per Day*) in conformità con la quota giornaliera di 20 chiamate tracciata in `gemini_usage.json`.
  - Aggiunto deep-link diretto "Notion" nelle righe file con stato `SYNCED`, consentendo di aprire con un solo clic la pagina Notion corrispondente (`https://www.notion.so/<page_id>`).
- **Riconciliazione Storica EA2627-02-W2.pptx**:
  - Censito e collegato il file `EA2627-02-W2.pptx` (hash `650811237420501ee9e250243e113eb9645ddf21a06ca78a5c0326d46a0f5050`) alla corrispondente pagina Notion già esistente `Business Architecture with ArchiMate` (`3e8b63e8-59c8-81c1-99e6-e795ddf4c976`), sanando lo stato nel Cockpit da `IDLE` a `SYNCED`.
- **Test Suite**: 84/84 unit test passati con successo (0 regressioni).

### 2026-09-30 (Text Mining and Search Cryptographic State Reconciliation)
- **Riconciliazione Idempotente di Stato Storico**:
  - Risolto il disallineamento sul corso "Text Mining and Search": le 30 pagine pre-esistenti su Notion (caricate prima dell'introduzione del tracking crittografico a stati) sono state censite e mappate biunivocamente 1-to-1 sui rispettivi 30 file PDF locali.
  - Implementato lo script di riconciliazione atomica [`scripts/reconcile_text_mining.py`](file:///c:/Documenti/Bots/PHD_Prof/scripts/reconcile_text_mining.py): ha calcolato l'impronta crittografica SHA-256 dei PDF e iniettato le voci con stato `SYNCED` e i rispettivi `page_id` Notion in `sync_state.json`.
  - Zero token LLM consumati, zero chiamate di riscrittura Notion, zero pagine duplicate.
  - Creata copia di sicurezza automatica preventiva `sync_state.json.bak` e aggiornato `.gitignore` con pattern `sync_state.json*` e `*.bak`.
  - Cockpit Web verificato: tutti i 28 file scansionati nella root del corso mostrano ora lo stato nominale verde `SYNCED`.
- **Test Suite**: 83/83 unit test verificati con successo (0 regressioni).

### 2026-09-30 (Local Web Frontend Cockpit, Inbound Web Adapter & Desktop Launcher Integration)
- **Documenti di Verità Visiva (PRODUCT.md & DESIGN.md)**:
  - Redatti `PRODUCT.md` e `DESIGN.md` secondo i framework Impeccable Design (Modalità Operate), Frontend UX Excellence e Design Taste Frontend.
  - Definiti token semantici Dark Tech Industriale, contrasto verificato WCAG 2.2 AA (>= 4.5:1), modular scale (Minor Third), griglia spaziale a multipli di 8pt e contratti a 9 stati per ciascun controllo.
- **Inbound Web Adapter, Telemetria & Heartbeat Watchdog**:
  - Implementato `WebAdapter` (`src/adapters/inbound/web/web_adapter.py`) con endpoint REST per profili corso, esplorazione file locale e quota Gemini.
  - Implementato `TelemetryStreamer` (`telemetry_streamer.py`) con duplicazione dello stdout per trasmettere in tempo reale i log interni della pipeline ETL via Server-Sent Events (`/api/events`).
  - Introdotto sistema Heartbeat/Keepalive (`/api/heartbeat`, `/api/unload`) con watchdog a 10s: quando l'utente chiude la finestra del browser, il processo Python in background si arresta automaticamente senza processi orfani.
- **Raffinamento Tipografico (Anti-Mechanical Polish)**:
  - Eliminato l'uso pervasivo e asettico del font monospace su etichette, badge, percorsi e tabelle.
  - Introdotto **Plus Jakarta Sans** come tipografia primaria (sans-serif geometrico-umanista ad alta densità e calore visivo).
  - Confinato il font monospace (`JetBrains Mono`) strettamente agli hash crittografici SHA-256 e alla console telemetrica.
- **Silent Launcher Desktop Unificato (Zero-CMD Flash)**:
  - Creato `Avvia_PHD_Prof.vbs` per lanciare il server Python in background con finestra CMD completamente invisibile (`WindowStyle = 0`).
  - Aggiornato `Avvia_PHD_Prof.bat` per delegare allo script VBS ed uscire istantaneamente.
  - Riconfigurato il collegamento desktop `PHD Prof.lnk` per puntare direttamente ad `Avvia_PHD_Prof.vbs`, aprendo il browser con un doppio clic a zero attrito e zero finestre di terminale residue.
- **Test Suite**:
  - Suite estesa con test su endpoint `/api/heartbeat` e `/api/unload` in `tests/test_web_adapter.py`.
  - Suite complessiva: 83/83 passati in 2.84s (0 regressioni).

### 2026-09-30 (Course Profiles Local Seeding, UTF-8 Console & Web Design Skills Setup)
- **Materializzazione Profili su Disco (course_profiles.json)**:
  - Creato e popolato course_profiles.json su disco con le coordinate operative reali di 4 corsi UNIMIB (Enterprise Architectures, Text Mining and Search, Big Data, Time Series Analysis), associando ciascuno al rispettivo database Notion 'Notes' e cartella locale.
  - Implementato in pdf_to_notion.py il fallback di auto-seeding da course_profiles.example.json (tracciato su Git) per evitare regressioni o avvii con lista profili vuota.
- **Console UTF-8 Resilience**:
  - Configurato chcp 65001 > nul in Avvia_PHD_Prof.bat e forzato sys.stdout.reconfigure(encoding='utf-8') in pdf_to_notion.py per garantire resa impeccabile di caratteri accentati nei prompt su Windows.
- **Orchestrazione Competenze Web Design**:
  - Aggiornato .agents/profile.json montando le skill specialistiche 
rontend-ux-excellence, impeccable-design, design-taste-frontend e rchitecture-design in .agents/skills/ tramite Skills_Orchestrator/main.py.
- **Test Suite**: 74/74 unit test verificati con successo.

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
- **Fix Upload Gemini File API**: Corretto il parametro da 
ile=... a path=... in GeminiFileReader per piena conformità con google-genai SDK v0.6.0.
- **Supporto Nativo PPTX**: Estesa la scansione in CLIAdapter e il parsing in TextPdfReader (tramite MarkItDown) per supportare presentazioni PowerPoint (.pptx), estraendo sia il contenuto delle slide sia le note del relatore.
- **Test Suite**: Aggiunto 	est_process_document_pptx_routing, 16/16 test superati con successo.


### 2026-09-22 — Refactoring Esagonale, Dual PDF Reader & Anti-Overengineering Gate
- **Architettura Esagonale & SOLID**: Rifattorizzato il monolite pdf_to_notion.py in src/ disaccoppiando Core Domain, Use Cases (ProcessDocumentUseCase), Ports e Adapters (IDocumentReader, ILlmClient, INotionClient, IStateRepository, IStagingStorage).
- **Dual PDF Reading**: Supporto per SLIDES (upload multimodale Gemini File API per espansione pedagogica di grafici e layout) e PAPER_OR_BOOK (estrazione testuale/markdown locale con MarkItDown/PyMuPDF per paper densi e teoremi).
- **Ottimizzazione Blocchi Notion**: Parser Markdown -> Blocchi Notion potenziato con supporto per code blocks evidenziati, LaTeX math ($ e ), blockquotes, divisori e safe chunking a 1900 caratteri.
- **Testing Strategy**: Suite di 15 unit test (	ests/) con mock offline per tutte le porte, 100% superata in 0.23s.
- **Anti-Overengineering Gate**: Aggiornata la skill master-hexagonal-architecture con soglia minima esplicita e stop conditions per prevenire complessità prematura.


### 2026-10-08 (Standardizzazione Lingua Inglese, Launchers & Docs Hub)
- **Standardizzazione 100% Lingua Inglese**: Rimosso ogni riferimento o file in lingua italiana (Configura_Dominio_Locale.bat e Avvia_PHD_Prof.*) a favore dei launcher universali in inglese (Configure_Local_Domain.bat, Launch_PHD_Prof.bat, Launch_PHD_Prof.vbs, Launch_PHD_Prof.command, Launch_PHD_Prof.sh).
- **Traduzione Script di Manutenzione & Utility**: Tradotti integralmente in inglese docstring, argomenti CLI e output a terminale di scripts/prune_r2_duplicates.py, scripts/setup_local_domain.ps1, scripts/generate_certificates.py e notifiche CLI in pdf_to_notion.py.
- **Modularizzazione Documentale in docs/**: Snellite 70+ righe di troubleshooting e dettagli infra da README.md, creando guide dedicate in docs/ (TROUBLESHOOTING.md, LOCAL_DOMAIN_SETUP.md, CLOUD_STORAGE.md) collegate tramite un hub centrale.
- **Pulizia Cloudflare R2 & Staging**: Pruning di 28 asset duplicati/orfani legacy (UUID casuali) e mantenimento dei soli 14 asset deterministici SHA-256 (300 DPI) per il corso Big Data.
- **Verifica Test Suite**: 99/99 test unitari superati con successo in locale.


### 2026-10-08 (Cloudflare R2 Beginner Guide & UI Walkthrough)
- **Guida Step-by-Step Cloudflare R2 per Principianti**: Espanso integralmente docs/CLOUD_STORAGE.md con un walkthrough visuale dettagliato per utenti senza esperienza di Cloudflare: creazione bucket (R2_BUCKET_NAME), estrazione Account ID ed endpoint S3 (R2_ENDPOINT_URL), generazione API Token con permessi *Object Read & Write* (R2_ACCESS_KEY, R2_SECRET_KEY) e attivazione accesso pubblico tramite sottodominio 
2.dev (R2_PUBLIC_DOMAIN).
- **Tabella Mappatura UI -> .env**: Aggiunto cheat-sheet comparativo e tabella diagnostica con le cause radice dei codici di errore S3/R2 (403 Forbidden, 404 NoSuchBucket, broken icons in Notion).
- **Allineamento .env.example**: Tradotti i commenti e aggiornati i placeholder per puntare direttamente alla guida in docs/CLOUD_STORAGE.md.


### 2026-10-08 (Guida Approfondita Dominio Locale, Porte & Certificati TLS)
- **Espansione docs/LOCAL_DOMAIN_SETUP.md per Principianti**: Ristrutturato il documento con modelli mentali chiari su TLD riservati (.test per RFC 2606), porte standard HTTP (80) vs HTTPS (443) e porte di fallback (8000, 8443).
- **Walkthrough 1-Click ed Elevazione UAC**: Istruzioni passo-passo per l'esecuzione di Configure_Local_Domain.bat su Windows con spiegazione del prompt di controllo account utente e procedura analoga per macOS e Linux (setup_local_domain.sh).
- **Architettura Root CA Locale & Browser Trust**: Chiarito perché Let's Encrypt non è applicabile a domini privati locali e come la private Root CA consenta la connessione HTTPS nativa con lucchetto verde e zero avvisi di sicurezza.
- **Risoluzione Problemi DNS TTL & Cache dei Browser**: Dettagliate le cause del caching negativo NXDOMAIN e i passaggi esatti per il flush DNS a livello di sistema operativo (ipconfig /flushdns) e nei motori Chromium (chrome://net-internals/#dns / edge://net-internals/#dns).
- **Matrice Conflitti Porte & Diagnostica**: Censiti i servizi comuni che occupano la porta 80 (IIS, Skype, Apache, Docker) o 443 (VMware) e spiegato il meccanismo di fallback automatico trasparente.


### 2026-10-08 (Elevazione Value Proposition & ROI in README e GitHub)
- **Tagline e Descrizione Repository GitHub**: Allineata la descrizione pubblica GitHub (gh repo edit) e il blocco quote iniziale del README per rendere immediatamente tangibile il ROI (trasformazione di oltre 100 slide in capitoli completi Notion in 30 secondi con zero token sprecati).
- **Ristrutturazione Sezione Valore (README.md)**: Introdotto schema di flusso ASCII che contrappone il costo del metodo manuale (4-6 ore a lezione di fatica clericale) con la pipeline PHD Prof (30 secondi).
- **Tabella Pilastri di Vantaggio & Metriche Quantitative**: Formalizzati i 6 pilastri di valore (10x Time Recovery, Zero Information Loss su speaker notes, Sintesi Notion di livello textbook, Figure vettoriali a 300 DPI, Idempotenza crittografica SHA-256 e architettura a costo zero).
- **Matrice Comparativa di Vantaggio Asimmetrico**: Aggiunta tabella di confronto tra Studio Manuale, Chatbot AI Generici (ChatGPT/Claude) e Pipeline Industriale ETL PHD Prof su 7 dimensioni operative.


### 2026-10-08 (Handoff Nuova Sessione: Generazione Schemi di Studio & Mappe Concettuali)
- **Fase 6 Iniziata (Study Schemas & Concept Maps)**: Aggiornato project.md per impostare l'obiettivo della nuova sessione: implementazione di un modulo per la generazione di schemi concettuali e mappe di studio (ispirato a Google NotebookLM e compatibile con EdrawMind/Mermaid/OPML) basato sulle note sintetizzate.
- **Preparazione Handoff XML Structured**: Strutturato prompt di passaggio ad alta densità informativa secondo le regole di master-context-engineering e prompt-engineering per migrazione in nuova chat.


### 2026-10-08 (Decostruzione Pedagogica GEMM & Standard Prompt Deconstructions)
- **Aggiornamento Live Pagina Notion (Big Data)**: Rimosso il blocco GEMM sintetico (5 blocchi) e iniettati 36 blocchi Notion arricchiti con decostruzione fisica delle dimensioni (m, k, n), derivazione operativa della complessità O(N^3), proprietà di intensità aritmetica, parallelismo massivo dei Tensor Cores, trace numerico 2x2 e boundary condition del decoding autoregressivo (GEMV memory-bound).
- **Hardening dei Prompt Template (prompt_templates.py)**: Esteso lo standard di decostruzione matematica in SLIDES_PROMPT_TEMPLATE e PAPER_OR_BOOK_PROMPT_TEMPLATE. Per ogni concetto astratto o complessità computazionale distaccata, il prompt impone ora la derivazione in 5 punti (mapping fisico, conteggio operazioni, ponte hardware/silicio, micro-esempio numerico e boundary conditions).
- **Test Suite**: 116/116 unit test passati con successo.


### 2026-10-08 (Fix Mermaid AST Layout Error & Modalità di Generazione Multi-Artefatto)
- **Diagnosi & Risoluzione Bug Mermaid ELK (`Cannot read properties of null (reading 're')`)**:
  * Identificato errore di layout engine (ELK/dagre) dovuto a nodi Mermaid AST nulli causati da label non quotate con parentesi/quadre annidate (es. MapReduce `K[Shuffle & Sort: Bear:[1,1], Car:[1,1,1]]`).
  * Implementato e integrato `sanitize_mermaid_flowchart()` in `notion_block_builder.py` per racchiudere automaticamente in `["..."]` o `{"..."}` i nodi con parentesi e due punti.
  * Aggiornati via PATCH Notion API i blocchi Mindmap e Flowchart sulla pagina Notion `3f3b63e8-59c8-819c-bdd2-dca55c14560c` (Big Data Session 1), ripristinando il rendering grafico immediato a zero errori.
- **Supporto Modalità di Generazione (`GenerationMode`: both, notes_only, graphs_only)**:
  * Domain Model: Introdotto enum `GenerationMode` (`BOTH = "both"`, `NOTES_ONLY = "notes_only"`, `GRAPHS_ONLY = "graphs_only"`).
  * Use Case (`ProcessDocumentUseCase`): Aggiunto `_split_notes_and_artifacts()` per isolare deterministicamente sintesi e grafi concettuali. In `NOTES_ONLY`, lo Stage 2 LLM e l'export OPML vengono disattivati (risparmio token); in `GRAPHS_ONLY`, si riutilizza lo staging a costo 0 token e si caricano solo gli schemi. Aggiunto supporto a `force=True` per ri-sincronizzazione pulita con archiviazione vecchie pagine.
  * Inbound CLI (`CLIAdapter` & `pdf_to_notion.py`): Aggiunto argomento `--generation-mode` (`--gen-mode`) e prompt interattivo con selezione rapida [1], [2], [3].
  * Inbound Web (`WebAdapter`, `index.html`, `app.js`, `app.css`): Aggiunto campo `mode` in `BatchStartRequest`, selettore visuale dropdown (`.select-mode`) nel toolbar della coda documenti e logging telemetrico della modalità attiva.
- **Verifica Test Suite**: Eseguiti 116 unit test offline con mock completi (116/116 passati con successo).


### 2026-10-14 (Fix Pipeline Rendering Figure & Patch Live Pagina Notion 'Data Visualization')
- **Diagnosi Root Cause**:
  * LLM Gemini produceva marker figura inline in formato genitore `(figure://slide_N)` anziché la sintassi standard `![alt](figure://slide_N)`.
  * La regex precedente in `ProcessDocumentUseCase._process_figures()` matchava unicamente immagini Markdown standalone, lasciando intatti i marker testuali `figure://` e impedendo l'estrazione visiva.
  * Il blocco di codice locale era stato corretto ma la pagina Notion remota non era stata aggiornata, mostrando i vecchi blocchi non renderizzati.
- **Hardening Multi-Livello Codebase**:
  * `src/core/usecases/process_document.py`: Introdotta universal figure regex `(?:!\[(?P<alt_img>[^\]]*)\]\((?P<uri_img>figure://[^\s\)]+)\)|\((?P<uri_paren>figure://[^\s\)]+)\)|(?P<uri_bare>figure://[^\s\)]+))`. Implementato il pattern *Inline Figure Lifting*: trasforma il testo inline in `*(Slide N)*` e solleva la figura in un blocco immagine Markdown standalone adiacente.
  * `src/adapters/outbound/notion_block_builder.py`: Aggiunto supporto a `caption` nativa su blocchi immagine esterni Notion ed esteso `parse_rich_text` con supporto a link Markdown standard `[testo](url)`.
  * `src/core/domain/prompt_templates.py`: Aggiunti vincoli negativi rigorosi in `SLIDES_PROMPT_TEMPLATE` e `PAPER_OR_BOOK_PROMPT_TEMPLATE` vietando marker inline e imponendo blocchi standalone vuoti prima e dopo.
- **Esecuzione Patch Live & Sincronizzazione**:
  * Creata utility `scripts/patch_data_visualization_page.py`.
  * Estratte 11 figure a 300 DPI dal file ufficiale del corso `C:\Documenti\UNIMIB\Data science for Economics\Class_4_Theory_4_Data_Science_in_Economics_Data_Visualization_Coding_Activity.pdf` (SHA-256 `5a597c6221d39590...`), caricate su Cloudflare R2 con percorso gerarchico (`notion/universita/data_science_in_economics/`).
  * Sostituiti integralmente i blocchi sulla pagina Notion `3f9b63e8-59c8-811e-b88b-cc0f883162fa` con 105 blocchi strutturati e 11 blocchi immagine nativi.
  * Sincronizzato staging `staging/5a597c6221d39590f17c2ab752bb510f02f88a2867fd5eb15ba60bb27934f7cc.md` e aggiornato `sync_state.json`.
- **Verifica Test Suite**: 144/144 unit test passati con successo (100% green).

