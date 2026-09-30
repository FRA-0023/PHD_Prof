# PRODUCT.md — PHD Prof (Durable Product Truth)

> Documento di verità invariante del prodotto software PHD Prof. Registra vincoli operativi, audience, valore core e principi di sistema. Non varia durante iterazioni di stile.

---

## 1. Audience & Operating Context
- **Target User**: Dottorando / Ricercatore quantitativo e ingegnere dell'informazione che elabora moli consistenti di materiale didattico (slide `.pptx`/`.pdf`, paper, testi accademici) per archiviarle sistematicamente nei database di corso su Notion.
- **Ambiente d'Uso**: Workstation locale Windows 11, postazione di studio/ricerca a doppio monitor o laptop, contesto a concentrazione elevata. Spesso eseguito in multitasking con lettori PDF, appunti e finestre browser aperte.
- **Frequenza d'Uso**: Settimanale o bisettimanale in concomitanza con lezioni universitarie e rilasci di materiale di corso.
- **Mental Model**: Strumento di controllo e osservabilità "Cockpit Industriale" — l'utente richiede controllo deterministico sul batch, visibilità immediata sullo stato di sincronizzazione crittografica (SHA-256), trasparenza sulle quote di inferenza LLM residue e certezza assoluta di non perdere dati né duplicare record.

---

## 2. Core Value Proposition
- **Problema Risolto**: Trasformazione manuale lenta, incompleta e frammentata di complesse presentazioni accademiche (diagrammi, grafici di sistema, note dell'oratore) e paper in dispense iper-strutturate per Notion.
- **Soluzione PHD Prof**: Pipeline ETL crash-only, idempotente e bilingue ad Architettura Esagonale. Ingestione multimodale (Gemini File API + PowerPoint COM bridge per slide, MarkItDown per paper), sintesi pedagogica avanzata (framework Tutor-Universale) e caricamento a blocchi ricchi su Notion.
- **Metrica di Successo**:
  1. *Zero Attrito d'Avvio*: Tempo dall'apertura del desktop shortcut all'avvio del batch $< 5$ secondi.
  2. *Idempotenza Crittografica*: $0\%$ caricamenti duplicati o orfani in caso di interruzione forzata.
  3. *Zero-Jank UX*: Feedback visivo percepito entro $100\text{ ms}$, aggiornamento progressivo log via streaming senza freeze dell'interfaccia.

---

## 3. Modalità Visiva (Visitor Mode)
- **Modalità Eletta**: **`Operate`** (Impeccable Design Framework).
- **Priorità Architetturali di Modalità**:
  - Massima densità visiva e scansionabilità per monitorare code di file, hash SHA-256 e quote API.
  - Zero decorazioni superflue, zero gradienti sfumati "lilla AI", zero illustrazioni decorative prive di contenuto.
  - Focus da tastiera integrale (`Tab`, `Enter`, `Space`, `Esc`, shortcut numerici).
  - Stati operativi espliciti: Idle, Scanning, Streaming/Processing, Success, Error, Empty.

---

## 4. Invariant Constraints (Vincoli Non Negoziabili)
1. **Architettura Esagonale Rigida**: Il frontend web opera unicamente come Inbound Adapter (`WebAdapter`). Core domain (`models.py`), casi d'uso (`ProcessDocumentUseCase`) e porte outbound rimangono disaccoppiate e prive di dipendenze verso framework HTTP o browser.
2. **Zero-Trust Secrets**: Divieto assoluto di esporre chiavi API (`GEMINI_API_KEY`, `NOTION_TOKEN`) nel frontend, nelle risposte HTTP o nei file statici. L'autenticazione verso i provider esterni avviene unicamente lato server.
3. **Local-First & Offline-First Asset Packaging**: Il server gira su `127.0.0.1:8000`. Nessun CDN esterno obbligatorio per il rendering; il software deve essere avviabile istantaneamente senza connessione Internet attiva per la UI.
4. **Desktop Launcher & Lifecycle Watchdog**: Il collegamento desktop avvia il server in background in modo invisibile (`Avvia_PHD_Prof.vbs`) e apre il browser a latenza zero; un watchdog heartbeat spegne automaticamente il processo Python alla chiusura del browser.
5. **Standard di Accessibilità WCAG 2.2 AA**:
   - Contrasto minimo testo/sfondo $\ge 4.5:1$.
   - Contrasto controlli interattivi e icone informative $\ge 3.0:1$.
   - Focus ring visibile su tutti gli elementi interattivi.
   - Rispetto stringente di `prefers-reduced-motion`.
6. **Griglia Spaziale a Multipli di 8pt**: Padding, margin, gap e altezze confinati a 4, 8, 12, 16, 24, 32, 48, 64px.

---

## 5. Tone & Voice
- **Registro**: Freddo, tecnico, autoritario, ad alta precisione ingegneristica.
- **Micro-Copy**: Diretto e informativo. Niente messaggi melensi, emoji infantili o frasi rassicuranti da SaaS consumer. Termini esatti: "SHA-256", "Inference RPM", "Notion Blocks", "Idempotent Skip".
