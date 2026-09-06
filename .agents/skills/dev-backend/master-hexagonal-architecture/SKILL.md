---
name: master-hexagonal-architecture
description: >
  MUST USE THIS SKILL whenever structuring, scaffolding, or refactoring application architecture into Ports & Adapters (Hexagonal) or Domain-Driven Design (DDD).
  Attiva per keyword o intenti concreti: "architettura esagonale", "ports and adapters", "struttura progetto python", "clean architecture", "domain driven design", "ddd", "hexagonal", "scaffolding cartelle", "core domain", "interfacce ports", "adapters storage", "dependency injection container".
  NON attivare per script di analisi dati singoli o modifiche a una sola funzione isolata.
tags: [dev-backend]
---

> ℹ️ **Skill in esecuzione**: `master-hexagonal-architecture`

> *Questa skill si è attivata per guidare l'operazione corrente.*



**REGOLA DI OUTPUT OBBLIGATORIA**: Quando questa skill è attiva, includi SEMPRE all'inizio della tua risposta il blocco di callout soprastante.



# Master Hexagonal Architecture (Ports & Adapters)



## Regole Architetturali Inviolabili

1. **Il Core è isolato**: La cartella `core/` non importa MAI da `adapters/` o librerie esterne (SQLAlchemy, FastAPI, ecc.).

2. **Ports**: Le dipendenze esterne sono definite come interfacce astratte (`ABC` in Python) dentro il `core/ports/`.

3. **Adapters**: Le implementazioni concrete (es. DB, API) vivono in `adapters/` e dipendono dal core, mai il contrario.

4. **Dependency Injection**: Il `main.py` costruisce gli adapter e li inietta negli Use Case.



## Scaffolding Standard

Quando crei un progetto, genera SEMPRE questa struttura e un `ARCHITECTURE.md`:

- `core/domain/` (Entities e Exceptions)

- `core/ports/` (Interfacce astratte)

- `core/usecases/` (Logica applicativa)

- `adapters/inbound/` (Routes, Controllers)

- `adapters/outbound/` (Database, API esterne)

---

## Pattern Esagonale per LLM Multi-Provider & Local-First (Outbound Port)

Nei sistemi moderni guidati da AI, accoppiare il dominio centrale o i casi d'uso all'SDK proprietario di un singolo provider cloud (`openai`, `anthropic`, `mistral`) viola il principio di isolamento del Core. L'interazione con l'LLM deve essere modellata rigorosamente come una **Outbound Port**.

### 1. Definizione della Porta (`core/ports/llm_port.py`)
Il dominio espone un'interfaccia astratta indipendente dall'infrastruttura di rete e dai formati dei vendor:

```python
from abc import ABC, abstractmethod

class LLMPort(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Esegue il completamento testuale disaccoppiato dall'infrastruttura."""
        pass
```

### 2. Adapter Unificato Multi-Provider (`adapters/outbound/unified_llm_adapter.py`)
L'adapter concreto gestisce la risoluzione gerarchica delle configurazioni e il fallback trasparente tra provider cloud e runtime locali offline (Ollama, vLLM, LM Studio):

- **Risoluzione Gerarchica delle Variabili**:
  - `LLM_BASE_URL`: devia le chiamate a un endpoint OpenAI-compatibile locale (es. `http://localhost:11434/v1`).
  - `LLM_MODEL`: definisce il modello target indipendentemente dal vendor (es. `llama3.1`, `mistral-large`, `gpt-4o`).
  - `LLM_API_KEY`: risolve la chiave di autenticazione.
- **Local-First Fallback per Chiavi**:
  Se `LLM_BASE_URL` punta a localhost o a un runtime on-premise privo di autenticazione e `LLM_API_KEY` non è presente nell'ambiente, l'adapter assegna automaticamente una chiave dummy (es. `"ollama"`), impedendo crash di validazione dei client SDK OpenAI-compatibili.
- **Testability Deterministica (`DryRunLLMAdapter`)**:
  Separando l'interfaccia, i test automatici e le pipeline CI/CD possono iniettare un `DryRunLLMAdapter` deterministico che restituisce payload fittizi o risposte simulate a zero costo e senza alcuna dipendenza dalla rete internet.

---

## Checklist Conformità Architettura Esagonale

- [ ] La cartella `core/` è priva di qualsiasi import verso librerie esterne di framework o SDK proprietari?
- [ ] Le chiamate a modelli linguistici (LLM) transitano unicamente attraverso un'interfaccia astratta (`LLMPort`)?
- [ ] L'adapter LLM supporta runtime locali e provider cloud tramite risoluzione gerarchica di Base URL, Model e API Key?
- [ ] La suite di test può eseguire senza chiavi API e offline tramite mock o adapter `dry-run`?
