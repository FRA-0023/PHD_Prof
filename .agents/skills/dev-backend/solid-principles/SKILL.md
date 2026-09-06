---
name: solid-principles
description: >
  MUST USE THIS SKILL whenever designing, refactoring, decoupling, or organizing classes, functions, and module interfaces in software projects.
  Attiva per keyword o intenti concreti: "solid", "principi solid", "clean code", "object oriented", "oop", "design pattern", "architettura software", "refactor", "disaccoppia", "interfacce", "adapter pattern", "dependency injection", "dipendenze", "modularità", "single responsibility".
  NON attivare per script monolitici usa-e-getta di poche righe.
tags: [dev-backend]
---

> ℹ️ **Skill in esecuzione**: `solid-principles`

> *Questa skill si è attivata per guidare l'operazione corrente.*



**REGOLA DI OUTPUT OBBLIGATORIA**: Quando questa skill è attiva, includi SEMPRE all'inizio della tua risposta il blocco di callout soprastante.



# SOLID Principles



## Come usare questa skill



Leggi le regole, poi applica la checklist finale prima di consegnare il codice.

Non devi seguirle tutte alla perfezione ogni volta — ma devi sapere quando le stai violando.



---

## S



**La regola**: Ogni funzione o classe fa UNA cosa sola.



**Come riconoscere la violazione**:

- La funzione si chiama `carica_e_processa_e_salva()`

- La funzione è più lunga di 20-25 righe

- Il docstring usa la parola "e" più di una volta



**Come correggere**:

Dividi in funzioni separate, ognuna con un nome che descrive UNA azione.



```python

# ❌ Viola SRP

def processa_dati(filepath):

    data = pd.read_csv(filepath)          # carica

    data = data.dropna()                  # pulisce

    data.to_csv('output.csv')            # salva

    return data



# ✅ Rispetta SRP

def carica_dati(filepath: str) -> pd.DataFrame:

    return pd.read_csv(filepath)



def pulisci_dati(data: pd.DataFrame) -> pd.DataFrame:

    return data.dropna()



def salva_dati(data: pd.DataFrame, filepath: str) -> None:

    data.to_csv(filepath, index=False)

```



---

## O



**La regola**: Aggiungi funzionalità creando nuovo codice, non modificando quello che funziona.



**Come riconoscere la violazione**:

- Hai una serie di `if model_type == 'A': ... elif model_type == 'B': ...`

- Ogni volta che aggiungi un caso nuovo, modifichi una funzione esistente



**Come correggere**:

Usa classi con un metodo comune. Aggiungi nuovi casi come nuove classi.



```python

# ❌ Viola OCP

def allena_modello(data, tipo):

    if tipo == 'random_forest':

        model = RandomForestClassifier()

    elif tipo == 'logistic':

        model = LogisticRegression()

    # Per aggiungere un nuovo tipo, devi toccare questo codice

    model.fit(data['X'], data['y'])

    return model



# ✅ Rispetta OCP

from abc import ABC, abstractmethod



class Modello(ABC):

    @abstractmethod

    def allena(self, X, y):

        pass



class RandomForestModello(Modello):

    def allena(self, X, y):

        model = RandomForestClassifier()

        model.fit(X, y)

        return model



class LogisticModello(Modello):

    def allena(self, X, y):

        model = LogisticRegression()

        model.fit(X, y)

        return model



# Per aggiungere SVM: crei SVM Modello. Non tocchi nient'altro.

```



---

## L



**La regola**: Se B eredita da A, B deve poter essere usato ovunque si usa A senza sorprese.



**Come riconoscere la violazione**:

- Una sottoclasse ha un metodo che lancia `NotImplementedError`

- Una sottoclasse restituisce un tipo diverso rispetto alla classe madre



**Come correggere**:

Assicurati che ogni sottoclasse rispetti esattamente il contratto della classe madre.



```python

# ❌ Viola LSP

class Modello(ABC):

    @abstractmethod

    def predict(self, X) -> list:

        pass



    @abstractmethod

    def explain(self, X) -> dict:

        pass



class SimpleModello(Modello):

    def predict(self, X) -> list:

        return [1, 0, 1]



    def explain(self, X) -> dict:

        raise NotImplementedError("SimpleModello non supporta explain")

        # Chi usa Modello si aspetta explain()



# ✅ Rispetta LSP

class Modello(ABC):

    @abstractmethod

    def predict(self, X) -> list:

        pass



class ModelloSpiegabile(Modello):

    @abstractmethod

    def explain(self, X) -> dict:

        pass



class SimpleModello(Modello):

    def predict(self, X) -> list:

        return [1, 0, 1]

    # Non implementa explain perché non è ModelloSpiegabile



class XGBoostModello(ModelloSpiegabile):

    def predict(self, X) -> list:

        return [...]



    def explain(self, X) -> dict:

        return {"feature_importance": [...]}

```



---

## I



**La regola**: Non forzare una classe a implementare metodi che non usa.



**Come riconoscere la violazione**:

- Hai una classe base con 8+ metodi astratti

- Alcune sottoclassi implementano metodi con `pass` o `raise NotImplementedError`



**Come correggere**:

Dividi l'interfaccia grande in interfacce piccole. Le classi implementano solo quelle che servono.



```python

# ❌ Viola ISP

class AnalizzatoreCompleto(ABC):

    @abstractmethod

    def carica(self): pass

    @abstractmethod

    def pulisci(self): pass

    @abstractmethod

    def analizza(self): pass

    @abstractmethod

    def visualizza(self): pass    # Non tutti gli analizzatori visualizzano

    @abstractmethod

    def esporta_pdf(self): pass   # Non tutti esportano in PDF



# ✅ Rispetta ISP

class Caricatore(ABC):

    @abstractmethod

    def carica(self): pass



class Pulitore(ABC):

    @abstractmethod

    def pulisci(self): pass



class Visualizzatore(ABC):

    @abstractmethod

    def visualizza(self): pass



# Ora ogni classe implementa solo quello che fa davvero

class AnalizzatoreBase(Caricatore, Pulitore):

    def carica(self): ...

    def pulisci(self): ...



class AnalizzatoreVisivo(Caricatore, Pulitore, Visualizzatore):

    def carica(self): ...

    def pulisci(self): ...

    def visualizza(self): ...

```



---

## D



**La regola**: Le classi non devono creare le loro dipendenze internamente.

Le dipendenze vengono passate dall'esterno (Dependency Injection).



**Come riconoscere la violazione**:

- Una classe crea connessioni al database nel suo `__init__`

- Una classe fa `import requests` e chiama direttamente un'API esterna

- Cambiare il database richiede modificare la classe



**Come correggere**:

Passa la dipendenza come parametro al costruttore. La classe riceve

un'astrazione (ABC), non un'implementazione concreta.



```python

# ❌ Viola DIP

class ServizioAnalisi:

    def __init__(self):

        # Hard-coded a PostgreSQL

        self.db = psycopg2.connect("host=localhost dbname=mydb")



    def analizza(self, dataset_id):

        data = self.db.execute(f"SELECT * FROM datasets WHERE id={dataset_id}")

        return processa(data)



# ✅ Rispetta DIP

class ServizioAnalisi:

    def __init__(self, repository: Repository):  # Riceve il contratto, non l'implementazione

        self.repository = repository



    def analizza(self, dataset_id):

        data = self.repository.carica(dataset_id)  # Usa il contratto

        return processa(data)



# In main.py scegli l'implementazione:

repo = PostgresRepository(connection_string="...")

# oppure domani:

repo = CSVRepository(base_path="data/")



servizio = ServizioAnalisi(repository=repo)  # Inietta

```



---

## Checklist pre-consegna



Prima di consegnare qualsiasi codice, verifica:



- [ ] Ogni funzione fa UNA cosa sola? (SRP)

- [ ] Per aggiungere un nuovo caso basta creare una nuova classe? (OCP)

- [ ] Ogni sottoclasse può sostituire la classe madre senza sorprese? (LSP)

- [ ] Nessuna classe implementa metodi con `pass` o `raise NotImplementedError`? (ISP)

- [ ] Le dipendenze esterne sono iniettate nel costruttore, non create internamente? (DIP)

- [ ] Nessuna funzione supera le 25 righe?

- [ ] Tutte le funzioni pubbliche hanno type annotations e docstring?