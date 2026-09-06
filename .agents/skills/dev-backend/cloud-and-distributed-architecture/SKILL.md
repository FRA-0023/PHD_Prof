---
name: cloud-and-distributed-architecture
description: >
  MUST USE THIS SKILL whenever designing, analyzing, or implementing cloud infrastructure, distributed systems, event-driven architectures (Kafka, RabbitMQ), distributed transactions (Saga, Transactional Outbox), idempotency, or Lakehouse storage (Delta Lake, Apache Iceberg).
  Attiva per keyword o intenti concreti: "architettura distribuita", "cloud architecture", "sistemi distribuiti", "microservizi", "event driven", "kafka", "saga pattern", "transactional outbox", "idempotenza", "lakehouse", "delta lake", "iceberg", "airflow", "dagster", "orchestrazione pipeline", "coordinamento nodi", "partizionamento kafka".
  NON attivare per semplici script locali single-process o CRUD sincroni senza architettura distribuita (usa solid-principles o master-hexagonal-architecture).
tags: [dev-backend]
---

> ℹ️ **Skill in esecuzione**: `cloud-and-distributed-architecture`
> *Questa skill si è attivata per guidare l'operazione corrente.*

**REGOLA DI OUTPUT OBBLIGATORIA**: Quando questa skill è attiva, includi SEMPRE all'inizio della tua risposta il blocco di callout soprastante.

# Cloud & Distributed System Architecture

## Il problema che questa skill risolve
I sistemi distribuiti falliscono silenziosamente quando si tenta di trattarli come monoliti locali: problemi di doppia scrittura (dual-write problem), perdita di messaggi durante disconnessioni di rete, transazioni distribuite bloccanti, disallineamento dello stato e corruzione dei dati su object storage non transazionali. Questa skill fornisce i pattern di resilienza, coerenza eventuale e storage distribuito necessari per costruire architetture cloud robuste.

---

## 1. Transazioni Distribuite e Coerenza Eventuale

Nei sistemi distribuiti, l'illusione delle transazioni ACID globali (2PC - Two-Phase Commit) introduce blocchi distribuiti, elevata latenza e fragilità sistemica. Adottare modelli di coerenza eventuale (*BASE*):

### 1.1 Il Problema della Doppia Scrittura (Dual-Write)
- **Scenario Critico**: Un servizio aggiorna il database relazionale (es. salva un ordine) e contemporaneamente pubblica un evento su Kafka/RabbitMQ. Se il broker fallisce dopo la scrittura su DB (o viceversa), il sistema entra in uno stato incoerente irreversibile.
- **Soluzione Obbligatoria: Transactional Outbox Pattern**
  1. Il servizio scrive la modifica applicativa E l'evento di notifica nella stessa transazione ACID locale su una tabella `outbox_events`.
  2. Un processo asincrono (CDC via **Debezium** o poller con `SELECT ... FOR UPDATE SKIP LOCKED`) legge gli eventi non pubblicati e li trasmette al message broker.
  3. Una volta confermato l'ack dal broker, il record outbox viene marcato come pubblicato o cancellato.

```sql
-- Schema Outbox Pattern (PostgreSQL)
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_outbox_unprocessed ON outbox_events (created_at) WHERE published_at IS NULL;
```

### 1.2 Saga Pattern: Orchestrazione vs Coreografia
Per workflow di business che attraversano più microservizi indipendenti:
- **Coreografia (Event-Driven Reattiva)**: I servizi reagiscono direttamente agli eventi di dominio altrui.
  - *Trade-off*: Disaccoppiamento elevato, ma rischio di dipendenze cicliche invisibili e difficoltà di monitoraggio dello stato globale per workflow lunghi (>4 step).
- **Orchestrazione (State Machine Centralizzata)**: Un orchestratore (es. Temporal, AWS Step Functions o servizio dedicato) coordina i singoli step ed emette le transazioni compensative in caso di fallimento.
  - *Regola*: Per ogni operazione progressiva $T_i$ che muta lo stato, deve esistere una corrispondente azione di compensazione semantica $C_i$ idempotente (es. *Effettua Pagamento* $\rightarrow$ *Storna Pagamento*).

### 1.3 Idempotenza e Deduplicazione
La semantica di consegna standard nei broker moderni è **At-Least-Once**. I consumatori riceveranno duplicati in caso di ritrasmissioni:
- **Idempotency Key**: Ogni richiesta o messaggio deve contenere un identificatore deterministico univoco (`idempotency_key` o `message_id`).
- **Consumer Guard**: Prima di processare il messaggio, il consumatore verifica su Redis o DB relazionale con operazione atomica (es. `INSERT ... ON CONFLICT DO NOTHING` o Redis `SETNX` con TTL). Se la chiave esiste già, l'elaborazione viene ignorata o viene restituito il risultato salvato in precedenza.

---

## 2. Streaming Dati e Partizionamento (Kafka & Event Brokers)

### 2.1 Garanzie di Ordinamento e Routing
- Kafka garantisce l'ordinamento dei messaggi **unicamente all'interno della medesima partizione**.
- Per aggregati coerenti (es. transazioni dello stesso `user_id` o `order_id`), usare sempre l'ID dell'aggregato come **Partition Key**.
- **Data Skew**: Se un'entità dominante (es. account aziendale globale) produce l'80% dei volumi, la sua partizione diventerà il collo di bottiglia dell'intero cluster. Applicare tecniche di *Salting* (`user_id + "_" + (hash % num_sub_partitions)`).

### 2.2 Gestione Errori e Dead-Letter Queue (DLQ)
- **Retry Esponenziale con Jitter**: Evitare ritentativi immediati simultanei che innescano un "thundering herd" sui servizi a valle.
- **Dead-Letter Topic (DLQ)**: Se un messaggio fallisce per motivi non transitori (deserializzazione, violazione schema, errore di business), inviarlo a un topic DLQ dedicato senza bloccare l'avanzamento dell'offset della partizione.

---

## 3. Lakehouse Architecture & Storage Distribuito (Delta Lake & Apache Iceberg)

Quando si gestiscono grandi moli di dati su Object Storage (AWS S3, MinIO, GCS), i formati raw (CSV, JSON, Parquet semplice) soffrono di letture sporche, file orfani e assenza di transazionalità.

### 3.1 Tabular Formats Transazionali
- Utilizzare **Delta Lake** o **Apache Iceberg**:
  - **ACID Transactions**: Snapshot isolation su storage ad oggetti tramite log transazionali JSON/Avro.
  - **Time Travel**: Possibilità di riprodurre query a timestamp o versioni storiche esatte (`VERSION AS OF` / `TIMESTAMP AS OF`).
  - **Schema Enforcement & Evolution**: Rifiuto automatico di colonne spurie con supporto controllato per aggiunta campi senza rescansione del dataset.

### 3.2 Ottimizzazione Storage e Compaction (Anti-Small Files)
- **Il problema dei file minuscoli**: Ingestion continua in streaming genera milioni di file parquet da pochi KB, degradando drasticamente le query di scansione.
- **Compaction Regolare**: Eseguire periodicamente routine di compattazione (es. `OPTIMIZE table COMPACT` su Delta Lake, target file size $128\text{ MB} - 512\text{ MB}$).
- **Z-Ordering & Partitioning**: Partizionare unicamente su variabili a bassa cardinalità (es. `anno`, `mese`, `regione`). Per filtri continui ad alta cardinalità, applicare Z-Ordering / Min-Max file pruning.

---

## 4. Orchestrazione di Pipeline Dati (Airflow vs Dagster)

- **Dagster (Software-Defined Assets)**: Raccomandato quando l'orchestrazione modella tabelle, feature store e modelli ML dove l'unità logica è il dato prodotto e la sua lineage, non il task computazionale. Garantisce testabilità nativa in-memory.
- **Apache Airflow (Task-Based DAG)**: Raccomandato per workflow eterogenei che coordinano servizi cloud esterni, container Spark/Kubernetes e job legacy basati su sequenze temporali rigide.

---

## 5. Anti-Pattern Architetturali da Rifiutare

- ❌ **Monolite Distribuito**: Microservizi che condividono lo stesso schema di database o si invocano a catena in modo sincrono via HTTP per ogni operazione (se un servizio va giù, l'intera catena collassa).
- ❌ **2PC su HTTP**: Coordinare transazioni distribuite bloccanti tramite REST calls senza compensazioni.
- ❌ **Eventi Privi di Schema**: Inviare JSON arbitrari non validati senza un catalogo formale (es. Avro o Protobuf con Confluent/Apicurio Schema Registry).
- ❌ **Shared State via Global Storage**: Utilizzare un bucket S3 come punto di sincronizzazione concorrente senza un layer transazionale (Delta/Iceberg).

---

## 6. Checklist di Conformità Architetturale

- [ ] **Dual-Write Eliminato**: Le scritture su DB e le emissioni di eventi usano il Transactional Outbox Pattern o CDC?
- [ ] **Saga & Compensazioni**: Ogni operazione distribuita ha una procedura di rollback/compensazione semantica idempotente?
- [ ] **Idempotency Guard**: I consumer verificano l'idempotency key prima di processare i messaggi at-least-once?
- [ ] **Partizionamento Bilanciato**: Le chiavi di partizione di Kafka evitano hotspot e garantiscono l'ordinamento degli eventi correlati?
- [ ] **DLQ Attiva**: Gli errori fatali dei consumer vengono instradati a una Dead-Letter Queue senza bloccare il processing lag?
- [ ] **Lakehouse Storage**: I dataset su object storage usano formati transazionali (Delta/Iceberg) con compaction pianificata?
- [ ] **Nessun Accoppiamento Sincrono Critico**: Le dipendenze a catena sono asincrone e resilienti ai fallimenti transitori dei nodi?
