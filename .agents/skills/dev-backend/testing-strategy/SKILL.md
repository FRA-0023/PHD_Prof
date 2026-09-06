---
name: testing-strategy
description: >
  MUST USE THIS SKILL whenever writing, running, designing, or repairing tests (unit test, integration test, pytest, mocks) to verify code correctness.
  Attiva per keyword o intenti concreti: "scrivi test", "esegui test", "unit test", "pytest", "strategia di test", "test coverage", "integrazione test", "tdd", "verifica codice", "valida modifiche", "mock client", "test suite", "fix test falliti".
  NON attivare se non è richiesto testare o verificare il funzionamento del software.
tags: [dev-backend]
---

> ℹ️ **Skill in esecuzione**: `testing-strategy`

> *Questa skill si è attivata per guidare l'operazione corrente.*



**REGOLA DI OUTPUT OBBLIGATORIA**: Quando questa skill è attiva, includi SEMPRE all'inizio della tua risposta il blocco di callout soprastante.



# Testing Strategy



Guida strategica per scrivere test ad altissima efficienza: massima copertura dei rischi di business, zero spreco di token per boilerplate.



---

## 1. Principio Guida: Priorità del Testing



Il coverage non è un obiettivo, ma un segnale diagnostico. Testare getter/setter o dataclass senza logica è spreco di tempo; non testare un algoritmo di calcolo ROI o regole di branching business è un rischio critico.



### Regola di Priorità (dalla più alta alla più bassa)



1. **Logica di calcolo / trasformazione dati** (es. mROI, RFM scoring, kpis, algoritmi algebrici)

2. **Decisioni condizionali di business** (branching su soglie, regole di validazione)

3. **Parsing e validazione input/output** (pydantic schemas, API payload parsing)

4. **Contratti tra moduli** (interazione Ports ↔ Adapters)

5. **Codice I/O puro o boilerplate** → Non testare direttamente la libreria esterna; testare il confine tramite mock.



---

## 2. Struttura del Progetto Test



Organizza la directory `tests/` rispecchiando la struttura del codice sorgente:



```

project/

├── src/

│   └── domain/

│       └── roi_calculator.py

└── tests/

    ├── conftest.py          # Fixture globali e configurazioni condivise

    ├── unit/

    │   └── test_roi_calculator.py

    └── integration/

        └── test_pipeline_integration.py

```



**Convenzione di Naming**: `test_<funzione_o_modulo>_<scenario>_<risultato_atteso>`  

*Esempio*: `test_calculate_mroi_when_spend_is_zero_returns_none`



---

## 3. Pattern AAA (Arrange - Act - Assert)



Struttura ogni test unitario in 3 fasi chiare e separate:



```python

import pytest

from core.domain.entities import Channel

from core.usecases.roi_calculator import calculate_roi



def test_calculate_roi_with_saturated_channel() -> None:

    # 1. Arrange (Preparazione dello stato e degli input)

    spend = 10_000.0

    revenue = 5_000.0

    channel = Channel(name="GOOGLE_DISPLAY", saturated=True)



    # 2. Act (Esecuzione dell'unità sotto test)

    result = calculate_roi(spend, revenue, channel)



    # 3. Assert (Verifica del risultato)

    assert result.roi == pytest.approx(0.5, rel=1e-3)

    assert result.is_saturated is True

```



---

## 4. Fixture Efficienti (`conftest.py`)



Usa le fixture per creare oggetti di dominio complessi o stati riutilizzabili.



```python

# tests/conftest.py

import pytest

from core.domain.entities import ModelConfig



@pytest.fixture

def sample_model_config() -> ModelConfig:

    return ModelConfig(

        channels=["META_OTHER", "GOOGLE_DISPLAY"],

        learning_rate=0.01,

        max_iterations=100,

    )

```



- Scope di default: `function` (isolamento totale tra i test).

- Scope `session` o `module`: Usare esclusivamente per setup I/O costosi (es. DB container in test d'integrazione).



---

## 5. Mocking al Confine del Sistema



Mocka **solo** I/O ed enti esterni. Non mockare mai la logica di dominio pura.



| Da Mockare (Boundary I/O) | Da NON Mockare (Pure Logic) |

|---|---|

| Chiamate HTTP / API esterne (requests/httpx) | Funzioni di calcolo pure e matematiche |

| Connessioni Database / Query reali | Trasformazioni dati in memoria |

| Filesystem I/O / S3 Buckets | Regole di decisione ed entità di dominio |

| Orologio di sistema / Random (per determinismo) | Dataclasses e modelli Pydantic |



```python

# Mocking con pytest-mock (mocker fixture)

def test_fetch_oecd_data_falls_back_on_http_error(mocker) -> None:

    # Patch dell'adapter esterno

    mocker.patch("adapters.oecd_client.fetch_data", side_effect=RuntimeError("500 Server Error"))

    mock_fallback = mocker.patch("adapters.fallback_client.fetch_data", return_value={"status": "ok"})



    result = fetch_data_with_fallback(indicator="GDP")



    mock_fallback.assert_called_once()

    assert result == {"status": "ok"}

```



---

## 6. Test Parametrizzati (`@pytest.mark.parametrize`)



Evita test duplicati per variazioni di input. Usa `@pytest.mark.parametrize` includendo **sempre** edge cases (zero, valori negativi, None, liste vuote).



```python

@pytest.mark.parametrize(

    "spend,revenue,expected_roi",

    [

        (1000.0, 2000.0, 2.0),

        (1000.0, 0.0, 0.0),

        (0.0, 1000.0, None),  # Edge case: divisione per zero

    ],

)

def test_calculate_roi_scenarios(spend: float, revenue: float, expected_roi: float | None) -> None:

    assert calculate_roi(spend, revenue) == expected_roi

```



---

## 7. Retrofit su Codice Legacy (Characterization Tests)



Quando si lavora su codice esistente privo di test:



1. **Non rifattorizzare alla cieca**: Identifica prima la logica di calcolo/dominio.

2. **Characterization Test**: Scrivi test basati sul comportamento *attuale osservato* (anche se sospetti sia un bug), per congelare lo stato.

3. **Refactoring guidato**: Procedi al refactoring (usando `python-standards` e `src-hexagonal`) mantenendo i test verdi.



---

## 8. Diagnostica Coverage



Esegui il report con:

```bash

pytest --cov=src --cov-report=term-missing

```



- Insegui il 100% di coverage solo sulle classi di **Dominio/Core**.

- Righe scoperte in file DTO, wrapper o script di avvio sono accettabili se la logica interna è coperta.



---

## Checklist di Qualità Pre-Commit (per i Test)



- [ ] Ogni funzione di calcolo/decisione ha almeno un test happy-path e uno per gli edge case?

- [ ] I mock sono applicati unicamente ai confini di I/O (API, DB, file system)?

- [ ] Il pattern Arrange-Act-Assert è visibile e rispettato?

- [ ] Tutti i test sono deterministici e indipendenti dall'ordine di esecuzione?

- [ ] I test per il codice legacy sono stati scritti *prima* di ogni refactoring?