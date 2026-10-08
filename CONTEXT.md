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
- **Test Suite**: 99 unit test offline con mock completi (100% passati, 0 regressioni).
- **Standard Documentale README (Invariante)**: Il file `README.md` DEVE essere SEMPRE ed ESCLUSIVAMENTE in lingua inglese. Ogni futura modifica deve preservare la massima chiarezza operativa per l'utilizzatore finale: setup di Python da zero (PATH), creazione API key Gemini, autorizzazioni e gerarchia del database Notion (Root Page -> Course Page -> Database con rilevamento automatico della property di tipo Title), tassonomia completa dei file di runtime/stato e funzionamento utilitaristico della Web Cockpit.

## Prossimi Passi
- Monitorare l'esperienza d'uso reale del cockpit web durante sessioni di studio continuative.
- Esplorare l'estensione della riconciliazione automatica per cartelle nested o esportazioni Moodle complesse (es. Big Data).

## Log delle Sessioni

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
  - Aggiornato .agents/profile.json montando le skill specialistiche rontend-ux-excellence, impeccable-design, design-taste-frontend e rchitecture-design in .agents/skills/ tramite Skills_Orchestrator/main.py.
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
- **Fix Upload Gemini File API**: Corretto il parametro da ile=... a path=... in GeminiFileReader per piena conformità con google-genai SDK v0.6.0.
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
- **Test Suite**: 107/107 unit test passati con successo.

