---
name: docker-compose-patterns
description: >
  MUST USE THIS SKILL whenever creating, configuring, containerizing, or debugging Dockerfiles and docker-compose.yml files.
  Attiva per keyword o intenti concreti: "crea dockerfile", "docker-compose", "containerizza applicazione", "docker container", "volumi docker", "rete docker", "build docker", "multi stage build", "env file docker".
  NON attivare per deploy bare-metal senza container o semplici script locali.
tags: [dev-backend]
---

> ℹ️ **Skill in esecuzione**: `docker-compose-patterns`

> *Questa skill si è attivata per guidare l'operazione corrente.*



**REGOLA DI OUTPUT OBBLIGATORIA**: Quando questa skill è attiva, includi SEMPRE all'inizio della tua risposta il blocco di callout soprastante.



# Docker Compose Patterns



Guida alla configurazione sicura, isolata ed efficiente di architetture multi-container con Docker Compose (sviluppo locale, home lab e Raspberry Pi).



---

## 1. Struttura del Progetto Multi-Container



```

progetto/

├── docker-compose.yml             # Definizione dei servizi principali (committato)

├── docker-compose.override.yml    # Override locale/dev (opzionale, in .gitignore se contiene percorsi locali)

├── .env.example                    # Template delle variabili d'ambiente (committato)

├── .env                            # Variabili d'ambiente reali (MAI committato, in .gitignore)

├── Dockerfile                      # Build immagine custom per l'applicazione principale

├── .dockerignore                   # Esclusione venv, cache, .git, logs

└── services/                       # Moduli di servizio dedicati

    ├── api/

    ├── worker/

    └── db/

```



> **Regola Tassativa**: `.env` va **SEMPRE** inserito in `.gitignore`. Solo `.env.example` con valori fittizi viene committato nel repository.



---

## 2. Template Base



```yaml

services:

  api:

    build:

      context: .

      dockerfile: Dockerfile

    container_name: nome-progetto-api

    restart: unless-stopped

    env_file:

      - .env

    ports:

      - "8000:8000"

    depends_on:

      db:

        condition: service_healthy

    healthcheck:

      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

      interval: 30s

      timeout: 5s

      retries: 3

      start_period: 10s

    networks:

      - backend

    logging:

      driver: json-file

      options:

        max-size: "10m"

        max-file: "3"



networks:

  backend:

    driver: bridge



volumes:

  db-data:

```



### Perché ogni parametro è fondamentale:

- `depends_on -> condition: service_healthy`: Attende che il database o la dipendenza sia **effettivamente pronta a ricevere connessioni**, non solo che il container sia nello stato "started".

- `logging.options`: Impedisce che i file di log saturino il disco fisso (critico per installazioni su SD Card / Raspberry Pi).

- `networks: backend`: Mantiene i container isolati su una rete privata riservata, evitando collisioni di nomi/porte con altri progetti sulla stessa macchina.



---

## 3. Database con Healthcheck Reale



```yaml

services:

  db:

    image: postgres:16-alpine

    container_name: nome-progetto-db

    restart: unless-stopped

    env_file:

      - .env

    volumes:

      - db-data:/var/lib/postgresql/data

    healthcheck:

      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]

      interval: 10s

      timeout: 5s

      retries: 5

    networks:

      - backend

```



- ❌ `test: ["CMD", "echo", "ok"]` → Healthcheck finto che non verifica la reale disponibilità del servizio.

- ✅ Usa comandi nativi del DB: `pg_isready` per Postgres, `redis-cli ping` per Redis, `mysqladmin ping` per MySQL.



---

## 4. Gestione Sicura dei Secrets e delle Variabili d'Ambiente



```yaml

# .env.example (Template committato)

POSTGRES_USER=app_user

POSTGRES_PASSWORD=changeme_secret

DATABASE_URL=postgresql://app_user:changeme_secret@db:5432/app_db

```



- ❌ `environment: - API_KEY=sk-abc123secret` scritto in chiaro nel compose → rischio di leak su Git.

- ✅ `env_file: [.env]` caricato esternamente con `.env` escluso da Git.



---

## 5. Home Lab & Raspberry Pi



Sui sistemi con risorse limitate (Raspberry Pi, mini-PC), applica sempre vincoli di piattaforma e limiti hardware:



```yaml

services:

  worker:

    build:

      context: .

      platforms:

        - "linux/arm64"

    deploy:

      resources:

        limits:

          cpus: "1.0"

          memory: 512M

```



- **Verifica Architettura**: Assicurati che le immagini base utilizzate supportino `arm64` (`python:3.10-slim`, `postgres:alpine`).

- **Limiti di Risorse**: Imposta `memory` e `cpus` per evitare che un memory leak blocchi l'intero sistema operativo host o l'accesso SSH.



---

## 6. Servizi Opzionali e Debug (`profiles`)



Stacca gli strumenti di debug/amministrazione dal container principale usando i profili Compose:



```yaml

services:

  pgadmin:

    image: dpage/pgadmin4

    profiles: ["dev"]

    ports:

      - "5050:80"

    networks:

      - backend

```



- **Avvio di produzione**: `docker compose up -d` (il servizio `pgadmin` rimane spento).

- **Avvio in sviluppo**: `docker compose --profile dev up -d` (attiva anche gli strumenti di debug).



---

## 7. Pattern Scraper & Job Periodici (Batch Job)



Gli scraper e i task batch **non sono servizi long-running**:



```yaml

services:

  scraper:

    build: .

    container_name: nome-progetto-scraper

    env_file:

      - .env

    restart: "no"  # Trattato come job one-shot, non si riavvia in caso di uscita

    networks:

      - backend

```



- ❌ Scraper con `restart: always` → rischia di andare in loop infinito di crash e causare il ban dell'IP dalla fonte di scraping.

- ✅ Esegui lo scraper tramite cron host o scheduler dedicato: `docker compose run --rm scraper`.



---

## Checklist di Qualità Pre-Commit (Docker Compose)



- [ ] `.env` è inserito in `.gitignore` ed esiste `.env.example` con dati fittizi?

- [ ] Le dipendenze dei servizi usano `depends_on` con `condition: service_healthy`?

- [ ] I comandi di `healthcheck` eseguono verifiche reali (`pg_isready`, `curl /health`, `redis-cli ping`)?

- [ ] La rotazione dei log (`logging.options`) è configurata (`max-size: 10m`, `max-file: 3`)?

- [ ] I servizi sono isolati in una rete custom (`networks: backend`) invece della rete default?

- [ ] I tool di debug o amministrazione (pgadmin, mailpit) sono isolati con `profiles: ["dev"]`?

- [ ] Le risorse hardware (`cpus`, `memory`) sono limitate per i container a carico variabile?