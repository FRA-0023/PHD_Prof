# 📄 PHD Prof: The Antifragile Document ETL Pipeline

[![Language](https://img.shields.io/badge/Language-Python%203.10+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-Google%20Gemini%20API-4285F4?logo=google)](https://ai.google.dev/)
[![Destination](https://img.shields.io/badge/Destination-Notion%20API-000000?logo=notion)](https://www.notion.so/)
[![Architecture](https://img.shields.io/badge/Architecture-Crash--Only%20ETL-green)](#)

> A crash-only, zero-data-loss document processing pipeline: ingesting academic PDFs, synthesizing core findings via LLM, and persisting structured intelligence to Notion with cryptographic state tracking.

---

## 📌 Executive Summary

Manually extracting findings from academic papers wastes cognitive bandwidth, but fragile automation scripts are worse. Basic scripts work on a single PDF, but crumble at scale: an API rate limit (HTTP 429) or gateway timeout (HTTP 502) crashes the process, leaving databases corrupted with orphaned records while burning expensive inference tokens.

**PHD Prof** is engineered as a relentless, **Crash-Only ETL pipeline**:
- Ingests complex academic PDFs autonomously.
- Enforces **cryptographic state tracking** via SHA-256 file fingerprints: renames are ignored, and extraction triggers strictly on mutated data.
- Protects API budgets: if Notion endpoints fail, atomic checkpointing guarantees zero lost inference and zero duplicate pages upon restart.

---

## 🔍 Architectural Safeguards

### 1. Cryptographic Fingerprinting (Zero Duplicates)
Standard scripts rely on file names or filesystem modification timestamps. PHD Prof calculates the **SHA-256 hash** of incoming PDF content. Redundant runs over existing files cost exactly 0 inference tokens.

### 2. Crash-Only Persistence & Exponential Backoff
All pipeline stages are decoupled. If the Notion API throttles requests or experiences network instability:
- State is preserved locally before external dispatch.
- Exponential backoff automatically handles transient 429 and 502 errors.
- On script restart, already processed papers are skipped instantaneously.

---

## 🛠️ Reproduction & Setup

```bash
# 1. Clone repository
git clone https://github.com/FRA-0023/PHD_Prof.git
cd PHD_Prof

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables (.env)
GEMINI_API_KEY=your_gemini_key
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id

# 4. Run pipeline
python pdf_to_notion.py
```

---

**Author:** Francesco Colombini  
[GitHub Profile](https://github.com/FRA-0023) · [LinkedIn](https://www.linkedin.com/in/francescocolombini/)