# CONTEXT.md — PHD Prof

## Visione & Scopo del Progetto
ETL antifragile e crash-only per ingerire documenti e slide accademiche in formato PDF, sintetizzarli tramite LLM (Gemini) e archiviarli su Notion senza perdita di dati né duplicazione di token.

## Stato Attuale
- **Architettura**: Esagonale (Ports & Adapters) in src/.
- **Modello LLM**: Gemini 2.5 Flash con rate limiting e retry esponenziale.
- **Test**: 15 unit test offline con mock completi.

## Prossimi Passi
- Monitorare l'esecuzione batch in produzione su corsi reali Notion.
- Valutare eventuale caching vettoriale locale se la libreria di PDF cresce ulteriormente.

## Log delle Sessioni

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

