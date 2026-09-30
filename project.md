# Project Status

## Current Phase
Phase 5 - Frontend Web UI Architecture & Local Browser Launcher

## Objective
Progettare e sviluppare un frontend web locale di livello eccellente (modalità Operate, standard Impeccable Design e Frontend UX Excellence) che sostituisca la pura console CMD. L'applicazione deve consentire gestione profili, selezione corso, avvio batch con progresso in tempo reale e preview note, lanciabile con un clic da desktop sul browser senza alterare la logica esagonale esistente.

## Next Actions
1. Disegnare i documenti di verità visiva (PRODUCT.md e DESIGN.md) specificando la modalità Operate, token semantici, griglia 8pt e contrasto WCAG 2.2 AA.
2. Implementare un adapter inbound HTTP/Web leggero (FastAPI/Uvicorn) che esponga i casi d'uso core (ProcessDocumentUseCase, JsonCourseProfileRepository, IStateRepository) tramite endpoint REST e WebSocket/SSE per lo streaming del batch.
3. Costruire il frontend UI ad alta scansionabilità e densità cognitiva (selezione corso one-click, selettore file, progresso live, log di sincronizzazione, monitor quota LLM).
4. Aggiornare Avvia_PHD_Prof.bat per avviare il server in background e aprire immediatamente il browser predefinito a http://localhost:8000.

## Open Decisions
- Stack frontend locale: HTML5/CSS moderno con design token e Vanilla JS reattivo (zero build step, massima portabilità, avvio istantaneo) vs React/Vite con compilazione statica servita da FastAPI.

## Blockers
- None

## Definition of Done
Il collegamento desktop PHD Prof apre l'interfaccia nel browser; l'utente può avviare ed esaminare l'ETL su Notion con feedback in tempo reale e gestione profili; l'intera suite di 74 test unitari backend rimane verde al 100%.
