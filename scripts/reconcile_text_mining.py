"""
reconcile_text_mining.py
------------------------
Utility script to backfill cryptographic SHA-256 state tracking for 'Text Mining and Search'
course files already synced to Notion prior to the hexagonal crash-only architecture refactoring.

Maps local files to their corresponding Notion page IDs and records them as SYNCED in sync_state.json
without triggering redundant LLM inference or creating duplicate Notion pages.
"""
import os
import sys
import json
import hashlib
from pathlib import Path

# Ensure root directory is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Verified mapping between local file names and Notion page IDs / titles
RECONCILIATION_MAPPING = {
    # Lab 1
    "Lab_1.pdf": {
        "page_id": "3b2b63e8-59c8-8199-99b7-cd627ac3084f",
        "title": "Lab_1",
        "subpath": "Lab 1 material-20260510/Lab_1.pdf",
    },
    "TMS - Lab 1p1 and 1p2- DOCUMENT MODELING HERE.pdf": {
        "page_id": "3b2b63e8-59c8-81b0-92ab-c8f18f06e90e",
        "title": "DOCUMENT MODELING",
        "subpath": "Lab 1 material-20260510/TMS - Lab 1p1 and 1p2- DOCUMENT MODELING HERE.pdf",
    },

    # Main Slides
    "TEXT MINING AND SEARCH 2025-26 ON DATA STRUCTURES FOR SEARCH.pdf": {
        "page_id": "35eb63e8-59c8-81ec-808a-fd5755c18825",
        "title": "Data Structures for Search",
    },
    "TEXT MINING AND SEARCH - STATISTICAL LANGUAGE MODELS 2025.pdf": {
        "page_id": "35eb63e8-59c8-818c-bf47-c18150790fee",
        "title": "Statistical Language Models",
    },
    "TEXT MINING AND SEARCH - PART OF SPEECH TAGGING 2025.pdf": {
        "page_id": "35eb63e8-59c8-816b-8fc3-eff66e3544c8",
        "title": "Part of Speech Tagging",
    },
    "TEXT MINING AND SEARCH - 5 NLP 2025.pdf": {
        "page_id": "35eb63e8-59c8-81bc-ad99-fd5310e32a76",
        "title": "NLP",
    },
    "TEXT MINING AND SEARCH - 4 NER 2025.pdf": {
        "page_id": "35db63e8-59c8-8158-b8ee-eec4b4a110a3",
        "title": "NER - Named Entity Recognition",
    },
    "TEXT MINING AND SEARCH - 3 TEXT REPRESENTATION.pdf": {
        "page_id": "35db63e8-59c8-8176-b497-ef05ff84ae3d",
        "title": "Text Representation",
    },
    "TEXT MINING AND SEARCH - 2 TEXT PROCESSING 2024-2025.pdf": {
        "page_id": "35db63e8-59c8-8178-972c-c64f085f42c4",
        "title": "Text Processing",
    },
    "TEXT MINING AND SEARCH - 1 INTRODUCTION 25-26.pdf": {
        "page_id": "35db63e8-59c8-81b5-ba89-d593672a9074",
        "title": "Introduction to Text Mining",
    },
    "POS TAGGING AND NER.pdf": {
        "page_id": "35db63e8-59c8-8112-861d-c61e73602b53",
        "title": "POS TAGGING AND NER",
    },

    # MV Series
    "MV09. TMS - RAG (2025-26).pdf": {
        "page_id": "35db63e8-59c8-8142-8f07-e3ecbaf8a13e",
        "title": "RAG (2025-26)",
    },
    "MV08. TMS - Information Retrieval (2025-26).pdf": {
        "page_id": "35db63e8-59c8-8174-b2bb-c814141a0b4e",
        "title": "Information Retrieval (2025-26)",
    },
    "MV07. TMS - Text summarization (2025-26) (1).pdf": {
        "page_id": "35db63e8-59c8-81a2-b9ee-e9d3a3b982bd",
        "title": "Text summarization (2025-26)",
    },
    "MV06. TMS - Topic Modeling (2025-26).pdf": {
        "page_id": "35db63e8-59c8-81b4-a2ee-d2089c907bc5",
        "title": "Topic Modeling (2025-26)",
    },
    "MV05. TMS - Text Clustering (2025-26).pdf": {
        "page_id": "35db63e8-59c8-81c1-8435-ff6c551306f2",
        "title": "Text Clustering (2025-26)",
    },
    "MV04. TMS - Text Classification (2025-26).pdf": {
        "page_id": "35db63e8-59c8-81f1-b5cf-ec2ffbf58cfa",
        "title": "Text Classification (2025-26)",
    },
    "MV03. TMS  - Word Embedding (Basics on Contextualized Word Embedding) (2025-26).pdf": {
        "page_id": "35db63e8-59c8-8156-9048-cabedf27d611",
        "title": "Contextualized Word Embedding (2025-26)",
    },
    "MV02. TMS  - Word Embedding (GloVe and word2vec) (2025-26).pdf": {
        "page_id": "35db63e8-59c8-8115-afa0-c5114b01eac9",
        "title": "Word Embedding - GloVe and word2vec (2025-26)",
    },
    "MV01. TMS  - Word Embedding (Vector semantics) (2025-26).pdf": {
        "page_id": "35db63e8-59c8-8134-ad6f-fa2d07390d28",
        "title": "Word Embedding - Vector semantics (2025-26)",
    },
    "MV00. TMS - Project instructions (2025-26).pdf": {
        "page_id": "35db63e8-59c8-81a0-88a7-ea05146fc289",
        "title": "Project instructions (2025-26)",
    },

    # Academic Research Papers
    "oneata.pdf": {
        "page_id": "35db63e8-59c8-810e-90d9-d753de7bc9dc",
        "title": "Probabilistic Latent Semantic Analysis (PLSA)",
    },
    "blei03a.pdf": {
        "page_id": "35db63e8-59c8-81ec-93ca-f7d2c62b458d",
        "title": "Latent Dirichlet Allocation (LDA)",
    },
    "2203.05794v1.pdf": {
        "page_id": "35cb63e8-59c8-814f-ac17-ca811eaa2c93",
        "title": "BERTopic: Neural Topic Modeling with a Class-Based TF-IDF Procedure",
    },
    "3731445.pdf": {
        "page_id": "35db63e8-59c8-81ec-b3f7-f95277794484",
        "title": "A Systematic Survey of Text Summarization",
    },
    "978-1-4614-3223-4_3.pdf": {
        "page_id": "35db63e8-59c8-8150-ba9b-eb257fcfad78",
        "title": "A Survey of Text Summarization Techniques",
    },
    "6.pdf": {
        "page_id": "35db63e8-59c8-81a5-b601-f08835c563d2",
        "title": "Vector Semantics and Embeddings",
    },
    "978-3-030-88389-8_16.pdf": {
        "page_id": "35db63e8-59c8-8172-90e5-d17575c97d50",
        "title": "Text Representations and Word Embeddings",
    },
    "information-10-00150-v2.pdf": {
        "page_id": "35db63e8-59c8-810b-bf37-e6a14a278118",
        "title": "Text Classification Algorithms: A Survey",
    },
    "3495162.pdf": {
        "page_id": "35db63e8-59c8-81ee-835e-d61a7da33de7",
        "title": "Text Mining and Search: A Comprehensive Survey",
    },
}

def compute_sha256(path: Path) -> str:
    """Computes SHA-256 fingerprint of file content on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def reconcile():
    state_file = PROJECT_ROOT / "sync_state.json"
    folder = Path(r"C:\Documenti\UNIMIB\Text Mining")

    if not folder.is_dir():
        print(f"[Error] Course folder not found: {folder}")
        sys.exit(1)

    # 1. Load current state
    current_state = {}
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            current_state = json.load(f)
    print(f"[State] Current entries in sync_state.json: {len(current_state)}")

    # 2. Iterate and hash files
    reconciled_count = 0
    skipped_count = 0

    print(f"[Scan] Processing {len(RECONCILIATION_MAPPING)} documents for Text Mining...")

    for fname, meta in RECONCILIATION_MAPPING.items():
        if "subpath" in meta:
            fpath = folder / meta["subpath"]
        else:
            fpath = folder / fname

        if not fpath.exists():
            print(f"  [MISSING] {fname} not found at {fpath}")
            continue

        file_hash = compute_sha256(fpath)
        existing = current_state.get(file_hash)

        if existing and existing.get("status") == "SYNCED":
            skipped_count += 1
            continue

        current_state[file_hash] = {
            "status": "SYNCED",
            "page_id": meta["page_id"],
            "last_updated": "2026-05-12T18:00:00.000000+00:00"
        }
        reconciled_count += 1
        print(f"  [RECONCILED] {fname[:38]:<38} -> Hash: {file_hash[:12]}... -> Page: {meta['page_id'][:12]}...")

    # 3. Atomic write with temporary file swap
    tmp_file = state_file.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(current_state, f, indent=2)
    tmp_file.replace(state_file)

    print("\n========================================================")
    print(f"  RECONCILIATION COMPLETE")
    print(f"  Newly Reconciled : {reconciled_count}")
    print(f"  Already Synced   : {skipped_count}")
    print(f"  Total in State   : {len(current_state)}")
    print("========================================================")

if __name__ == "__main__":
    reconcile()
