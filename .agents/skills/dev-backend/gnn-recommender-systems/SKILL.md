---
name: gnn-recommender-systems
description: >
  MUST USE THIS SKILL whenever designing, building, or training Graph Neural Networks (GNN) for recommender systems or link prediction on user-item graphs.
  Attiva per keyword o intenti concreti: "raccomandazioni GNN", "graph neural network", "sistema di raccomandazione a grafo", "link prediction", "PyTorch Geometric", "DGL", "grafo utenti prodotti", "node embedding grafo", "LightGCN".
  NON attivare per semplici filtri collaborativi matriciali (SVD) o raccomandazioni euristiche basate su regole.
tags: [dev-backend]
---

> ℹ️ **Skill in esecuzione**: `gnn-recommender-systems`
> *Questa skill si è attivata per guidare la progettazione e l'implementazione di sistemi di raccomandazione basati su Graph Neural Networks.*

**REGOLA DI OUTPUT OBBLIGATORIA**: Quando questa skill è attiva, includi SEMPRE all'inizio della tua risposta il blocco di callout soprastante.

# Graph Neural Network Recommender Systems

## Il problema che questa skill risolve
I sistemi di raccomandazione classici (collaborative filtering matriciale) faticano a incorporare relazioni multi-hop, attributi di nodi eterogenei e grafi bipartiti complessi utente-articolo. Questa skill guida l'agente nella progettazione di architetture GNN (come LightGCN, GraphSAGE o GAT) utilizzando PyTorch Geometric (PyG) o DGL per link prediction, massimizzando recall@K e NDCG@K.

---

## 1. Pipeline di Implementazione

1. **Costruzione del Grafo Bipartito (`torch_geometric.data.HeteroData`)**:
   - Mappa ID utente e ID item in indici continui `[0, N-1]`.
   - Crea il tensore di adiacenza `edge_index` per le interazioni (es. click, purchase) con archi bidirezionali o pesati.
2. **Scelta dell'Architettura GNN**:
   - **LightGCN**: default raccomandato per collaborative filtering puro (elimina trasformazioni non lineari e matrici di peso pesanti, mantenendo solo la propagazione di vicinato).
   - **GraphSAGE / GAT**: se sono presenti feature ricche sui nodi (metadati prodotto, profili utente) o grafi eterogenei.
3. **Loss Function e Negative Sampling**:
   - Usa la **BPR Loss** (Bayesian Personalized Ranking) con campionamento negativo uniforme o hard negative mining.
4. **Valutazione Offline Rigorosa**:
   - Separazione temporale train/test (evita data leakage da split randomico).
   - Calcolo metriche di ranking: `Recall@K`, `NDCG@K`, `MRR`.

---

## Checklist di Conformità

- [ ] I grafi bipartiti sono stati indicizzati correttamente senza overlap tra nodi utente e nodi item?
- [ ] Il campionamento negativo è isolato dal test set?
- [ ] La propagazione dei messaggi è implementata in modo idiomatico (PyG/DGL) senza cicli Python lenti?
- [ ] La valutazione è condotta su metriche di ranking (Recall@K / NDCG@K) e non su semplice accuracy?

