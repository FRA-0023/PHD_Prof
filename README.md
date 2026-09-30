# 📄 PHD Prof: The Antifragile Document ETL Pipeline

[![Language](https://img.shields.io/badge/Language-Python%203.10+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-Google%20Gemini%20API-4285F4?logo=google)](https://ai.google.dev/)
[![Destination](https://img.shields.io/badge/Destination-Notion%20API-000000?logo=notion)](https://www.notion.so/)
[![Architecture](https://img.shields.io/badge/Architecture-Crash--Only%20ETL-green)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> A crash-only, zero-data-loss document processing pipeline: ingesting academic PDFs, synthesizing core findings via LLM, and persisting structured intelligence to Notion with cryptographic state tracking.

---

## 📌 Executive Summary

Manually extracting findings from academic papers wastes cognitive bandwidth, but fragile automation scripts are worse. Basic scripts work on a single PDF, but crumble at scale: an API rate limit (HTTP 429) or gateway timeout (HTTP 502) crashes the process, leaving databases corrupted with orphaned records while burning expensive inference tokens.

**PHD Prof** is engineered as a relentless, **Crash-Only ETL pipeline**:
- Ingests complex academic PDFs autonomously.
- Enforces **cryptographic state tracking** via SHA-256 file fingerprints: renames are ignored, and extraction triggers strictly on mutated data.
- Protects API budgets: if Notion endpoints fail, atomic checkpointing guarantees zero lost inference and zero duplicate pages upon restart.
---

## 🏗️ Core Capabilities

### 1. Hexagonal Architecture (Ports & Adapters)
The codebase is structured into a modular Ports & Adapters architecture (`src/`). The core domain and use cases (`ProcessDocumentUseCase`) are fully decoupled from external APIs and interface layers. It features interchangeable inbound adapters:
- **CLI Adapter** (`src/adapters/inbound/cli_adapter.py`): Interactive terminal console with bilingual support (`IT`/`EN`).
- **Web Cockpit Adapter** (`src/adapters/inbound/web/`): Local FastAPI server delivering a high-density, keyboard-driven single-page cockpit with real-time Server-Sent Events (SSE) telemetry, Plus Jakarta Sans typography, and automatic lifecycle management.

### 2. Multimodal Reading Strategies & Dual-Payload PPTX Engine
Academic materials are not uniform. PHD Prof supports two dedicated ingestion modes:
- **Visual / Slides Mode (`SLIDES`) for PDF & PPTX**:
  - *PDFs*: Directly ingested via Google Gemini File API for multimodal spatial awareness.
  - *PPTX Decks*: Employs a **Dual-Payload Multimodal Architecture**. On Windows, converts PPTX slides into a vector PDF via headless PowerPoint COM (`win32com`) while simultaneously extracting speaker notes and footer commentary via `MarkItDown`/`python-pptx`. Gemini simultaneously cross-references visual diagrams (ADM cycles, metamodels, architecture blueprints) with detailed speaker commentary. Gracefully falls back to structured text extraction if COM is unavailable.
- **Academic Paper / Book Mode (`PAPER_OR_BOOK`)**: Uses local text and Markdown extraction (via MarkItDown and PyMuPDF) to ingest dense multi-column academic papers, textbook chapters, and technical reports, distilling rigorous mathematical proofs, theorems, and empirical methodologies.

### 3. Persistent Course Profiles (Zero-Friction Execution)
Course parameters (subject, professor persona, document type, local folder, and resolved Notion database ID) are invariant within an academic semester. PHD Prof persists these configurations in an atomic, gitignored `course_profiles.json` repository:
- **Instant Execution**: Launching either the Web Cockpit or CLI lists registered course profiles with live file counts and cryptographic sync statuses.
- **Interactive Override & Auto-Learning**: Configure or adjust course parameters on the fly; upon completion, the system automatically registers the profile for future one-click runs.

### 4. Enhanced Notion Block Engine
- **Fenced Code Blocks**: Native syntax-highlighted Notion code blocks (Python, R, SQL, Shell, etc.).
- **LaTeX Math Support**: Inline equations (`$formula$`) and standalone equation blocks (`$$...$$`).
- **Blockquotes & Dividers**: Quotes (`>`) and horizontal dividers (`---`) for structured readability.
- **1900-Character Safe Chunking**: Prevents Notion API 2000-character payload rejection.

---

## 🔍 Architectural Safeguards

### 1. Cryptographic Fingerprinting (Zero Duplicates)
Standard scripts rely on file names or filesystem modification timestamps. PHD Prof calculates the **SHA-256 hash** of incoming PDF content. Redundant runs over existing files cost exactly 0 inference tokens.

### 2. Crash-Only Persistence & Exponential Backoff
All pipeline stages are decoupled. If the Notion API throttles requests or experiences network instability:
- State is preserved locally before external dispatch.
- Exponential backoff automatically handles transient 429 and 502 errors.
- On script restart, already processed papers are skipped instantaneously.

### 3. Silent Cross-Platform Desktop Launchers & Lifecycle Watchdog
- **Windowless Windows Launcher (`Avvia_PHD_Prof.vbs`)**: Executes the local FastAPI service invisibly (`WindowStyle = 0`) and opens the default browser directly to `http://localhost:8000`.
- **One-Click macOS Launcher (`Avvia_PHD_Prof.command` / `Avvia_PHD_Prof.sh`)**: Double-clickable in Finder. Resolves Python 3 across virtual environments, Homebrew (Apple Silicon / Intel), or system paths, executes detached in the background via `nohup`, auto-closes the launching Terminal window, and surfaces the browser cockpit.
- **Automatic Process Termination**: The browser cockpit continuously emits heartbeats. When the browser tab is closed, a beacon terminates the background server with zero dangling processes. During active batch extraction, the watchdog is automatically frozen to ensure uninterrupted processing even if the tab is placed in the background.

### 4. Comprehensive Test Suite
Fully decoupled unit testing via `pytest` and offline mocks covering all ports, use cases, and adapters:
- **84/84 unit tests passing** in under 3 seconds.

---

## 🛠️ Reproduction & Setup

```bash
# 1. Clone repository
git clone https://github.com/FRA-0023/PHD_Prof.git
cd PHD_Prof

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables (.env)
copy .env.example .env     # Windows
# cp .env.example .env      # Linux/macOS

# Edit .env with your credentials:
# GEMINI_API_KEY=your_gemini_key
# NOTION_TOKEN=your_notion_token
# NOTION_ROOT_PAGE_ID=your_courses_page_or_database_id
# CLI_LANGUAGE=IT  # Optional: IT (Italian, default) or EN (English)

# 4. Launching the Application
# Option A: One-click Web Cockpit
wscript Avvia_PHD_Prof.vbs          # Windows (or double-click Avvia_PHD_Prof.bat)
./Avvia_PHD_Prof.command            # macOS (or double-click in Finder)
./Avvia_PHD_Prof.sh                 # Linux / POSIX shell

# Option B: Interactive Terminal CLI
python pdf_to_notion.py --mode cli
python pdf_to_notion.py --mode cli --lang EN
```

---

**Author:** Francesco Colombini  
[GitHub Profile](https://github.com/FRA-0023) · [LinkedIn](https://www.linkedin.com/in/francescocolombini/)