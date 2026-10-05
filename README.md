# 📄 PHD Prof: Antifragile Document ETL Pipeline for Notion

[![Language](https://img.shields.io/badge/Language-Python%203.10+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-Google%20Gemini%20API-4285F4?logo=google)](https://ai.google.dev/)
[![Destination](https://img.shields.io/badge/Destination-Notion%20API-000000?logo=notion)](https://www.notion.so/)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal%20Ports%20%26%20Adapters-green)](#)
[![Reliability](https://img.shields.io/badge/Reliability-Crash--Only%20ETL-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> A crash-only, zero-data-loss document processing pipeline: ingesting academic slide decks (PDF, PPTX with speaker notes) and dense research papers, synthesizing rigorous pedagogical lecture notes via Google Gemini, and persisting structured intelligence to Notion with cryptographic state tracking.

---

## 📌 Table of Contents

1. [Utilitarian Value: What Bottleneck PHD Prof Solves](#-utilitarian-value-what-bottleneck-phd-prof-solves)
2. [The Web Cockpit (Industrial Local Dashboard)](#-the-web-cockpit-industrial-local-dashboard)
3. [Requirements & Prerequisites](#-requirements--prerequisites)
   - [1. Python 3.10+ (Windows & macOS Installation)](#1-python-310-windows--macos-installation)
   - [2. Notion Account & Database Setup](#2-notion-account--database-setup)
   - [3. Google Gemini API Key Setup](#3-google-gemini-api-key-setup)
   - [4. Environment Setup & Dependency Installation](#4-environment-setup--dependency-installation)
   - [5. Environment Variables Configuration (.env)](#5-environment-variables-configuration-env)
4. [Project File Taxonomy & Runtime State Map](#-project-file-taxonomy--runtime-state-map)
5. [Execution Modes: Web Cockpit vs Terminal CLI](#-execution-modes-web-cockpit-vs-terminal-cli)
6. [Technical Architecture & Verification Test Suite](#-technical-architecture--verification-test-suite)
7. [Troubleshooting & Diagnostic Guide](#-troubleshooting--diagnostic-guide)

---

## 🎯 Utilitarian Value: What Bottleneck PHD Prof Solves

Graduate students, doctoral researchers, and quantitative practitioners handle hundreds of complex academic documents per semester: multi-deck slide presentations (`.pptx`, `.pdf`), dense two-column academic preprints, and textbook chapters.

### The Failure of Conventional Approaches
- **Manual Transcription**: Manually summarizing slide architectures, transcribing speaker notes, and copying mathematical proofs into Notion drains hours of high-cognitive focus on low-leverage formatting tasks. Crucial context hidden in PPTX speaker notes and slide footers is frequently lost.
- **Naive Automation Scripts**: Basic Python automation scripts fail under production conditions. An HTTP 429 (API rate limit) or HTTP 502 (gateway timeout) crashes the process mid-run. This leaves Notion databases polluted with half-written duplicate records, burns expensive LLM inference tokens, and requires painful manual cleanup.

### The PHD Prof Engineering Solution
PHD Prof operates as a **Crash-Only, Idempotent Document ETL Pipeline**:

1. **Dual-Payload Multimodal Reading Strategies**:
   - **Slide Decks (`SLIDES` Mode)**: Directly submits PDFs to the Google Gemini File API for spatial visual awareness of system diagrams, architecture blueprints, and metamodels. On Windows, PPTX decks leverage a **Dual-Payload Multimodal Architecture**: converts slides to vector PDF via headless PowerPoint COM (`win32com`) while simultaneously extracting slide notes and footer commentary via `MarkItDown` / `python-pptx`. Gemini synthesizes both streams concurrently, correlating visual figures with oral explanations.
   - **Research Papers & Books (`PAPER_OR_BOOK` Mode)**: Uses local parsing engines (`MarkItDown`, `PyMuPDF`) to ingest dense text, mathematical proofs, theorems, and empirical methodologies.
2. **Cryptographic Idempotence (Zero Token Waste)**:
   - Before dispatching any external call, the pipeline computes the **SHA-256** hash of the document content.
   - If an identical hash exists in `sync_state.json` with status `SYNCED`, the file is skipped instantly ($0\text{ ms}$ latency, **exactly 0 LLM tokens burned**).
   - Renaming or moving a file within the monitored directory never causes redundant uploads or duplicate database records.
3. **Structured Notion Pedagogical Output**:
   - Compiles output into native Notion blocks: inline LaTeX equations (`$formula$`), standalone display equations (`$$...$$`), syntax-highlighted code blocks (Python, R, SQL, Shell), analytical callouts, executive summaries, and rigorous exam preparation questions.
   - Enforces **1900-character safe chunking** to eliminate HTTP 400 payload rejections caused by Notion's strict 2000-character limit per rich text block.

---

## 🖥️ The Web Cockpit (Industrial Local Dashboard)

PHD Prof features a zero-build, local-first single-page cockpit accessible securely at `https://phdprof.test` (or `http://127.0.0.1`), running on standard HTTPS port `443` (with automatic fallback to port `8443` or `80/8000`). Built according to the *Operate* visitor mode and WCAG 2.2 AA accessibility standards:

```
+---------------------------------------------------------------------------------------+
| TOPBAR : PHD Prof Cockpit | LOCAL HOST | GEMINI QUOTA: [ 18 RPD ]                    |
+------------------------------------+--------------------------------------------------+
| CONTROL RAIL (Sidebar 320px)       | WORKSPACE VIEWPORT                               |
|                                    |                                                  |
| Registered Course Profiles:        | Document Queue: C:\Courses\Enterprise Arch       |
|  [1] Enterprise Architectures      | [All / None] [Refresh] [Sync Selected (3)]       |
|  [2] Machine Learning              |                                                  |
|  [3] Text Mining and Search        | Document Data Table:                             |
|  [+ New Course Profile]            |  [x] Week_01_Intro.pdf | 4.2 MB | SYNCED [Notion]|
|                                    |  [x] Week_02_Arch.pptx | 8.6 MB | IDLE           |
| Active Course Specification:       |  [ ] Paper_KDD.pdf     | 2.1 MB | IDLE           |
|  - DocType: Slides                 |                                                  |
|  - Role: PhD Professor in EA       | Real-Time Streaming Telemetry Console:           |
|  - Notion DB: Notes                |  [14:10:02] SHA-256: 65081123... (Computed)      |
|                                    |  [14:10:05] Gemini File API: Upload OK           |
|                                    |  [14:10:12] Notion: Writing 184 blocks...        |
+------------------------------------+--------------------------------------------------+
```

### Dashboard Operational Capabilities
- **Control Rail (Course Profile Selector)**: Displays all courses saved in `course_profiles.json`. Switch courses instantly via keyboard shortcuts (`1` to `9`) or mouse click. Inspects subject, professor persona prompt, document ingestion mode, and target Notion database ID. Click `+ New` to open the configuration modal and register a new course on the fly.
- **Document Queue Table**: Scans the configured local directory in real time. Shows:
  - Checkbox selection for granular batch execution.
  - File name, extension, and file size.
  - Content SHA-256 hash (truncated with one-click copy).
  - Status badges: `SYNCED` (emerald green, verified on Notion), `IDLE` (slate gray, pending extraction), `SYNCING` (pulsing blue, active pipeline), `FAILED` (red, diagnostic error).
  - **Direct Notion Deep-Link**: Synced documents display an inline `[Notion]` button opening the generated page directly inside your Notion workspace.
- **Batch Controls**:
  - `All / None`: Toggles table selection.
  - `Refresh`: Re-scans disk for newly dropped files.
  - `Sync Selected` (or `Ctrl + Enter`): Executes the ETL pipeline over selected documents.
  - `Stop` (or `Esc`): Appears during execution to gracefully stop the batch after completing the active document without state corruption.
- **Real-Time Telemetry Console (SSE Streaming)**: Live console duplicating internal server logs over Server-Sent Events (`/api/events`). Emits step-by-step progress: hashing, headless PPTX rendering, Gemini File API upload, pedagogical synthesis, 1900-character chunking, and Notion block writes. Features `Auto-scroll` toggle, `Copy Log`, and `Clear`.
- **Topbar LLM Quota Meter**: Tracks remaining daily requests (RPD - *Requests Per Day*) persisted in `gemini_usage.json`. If the daily quota reaches zero, batch execution halts fast before triggering consecutive API errors.
- **Automatic Lifecycle Watchdog**: Client tabs emit a heartbeat every 3 seconds and an unload beacon. When the browser tab or window is closed, a background daemon terminates the Python server after 10 seconds. No dangling Python processes, terminal windows, or occupied ports remain. The watchdog automatically freezes during active batch runs to prevent accidental interrupts.

---

## 📋 Requirements & Prerequisites

To run PHD Prof, your system must satisfy three fundamental external prerequisites:

| Requirement | Purpose | Direct Provider / Setup Link |
|---|---|:---:|
| **Python 3.10+** | Local runtime environment (Windows, macOS, Linux) | [python.org/downloads](https://www.python.org/downloads/) |
| **Notion Account & Database** | Destination storage for structured lecture intelligence | [notion.so](https://www.notion.so/) · [notion.so/profile/integrations](https://www.notion.so/profile/integrations) |
| **Google Gemini API Key** | Multimodal slide inspection & synthesis engine | [Google AI Studio](https://aistudio.google.com/) |

---

### 1. Python 3.10+ (Windows & macOS Installation)

Python is not pre-installed on all operating systems, or may exist as an outdated runtime. PHD Prof strictly requires **Python 3.10 or newer** (recommended: **Python 3.11** or **3.12**).

#### A. Installing on Windows

**Option 1: Terminal Installation (Fastest via PowerShell)**
Open PowerShell (press `Win + X` -> select *Terminal* or *PowerShell*) and run:
```powershell
# Install Python 3.11 via Windows Package Manager
winget install Python.Python.3.11

# Alternatively, if you use Chocolatey or Scoop:
# choco install python --version=3.11
# scoop install python
```
> [!IMPORTANT]
> After running `winget`, close and restart your PowerShell terminal window to reload the updated system `PATH` variables.

**Option 2: GUI Installer (.exe)**
1. Download the official installer from [python.org/downloads/windows](https://www.python.org/downloads/windows/) (select *Windows installer 64-bit* for Python 3.11 or 3.12).
2. Launch the downloaded `.exe` installer.
3. > [!IMPORTANT]
   > On the very first setup screen, check the box at the bottom:  
   > ☑ **Add python.exe to PATH** (or *Add Python to environment variables*).  
   > *If this checkbox is omitted, Windows will fail to recognize `python` or `pip` from the terminal, and launcher scripts (`.bat` and `.vbs`) will not work.*
4. Click **Install Now**.
5. Once installation finishes, click **"Disable path length limit"** if prompted (prevents errors with deep directory trees).

**Verification Commands (Windows PowerShell)**:
```powershell
python --version   # Expected output: Python 3.11.x (or >= 3.10)
pip --version      # Expected output: pip 24.x from ...
```

*(Optional Windows Requirement)*: For optimal PPTX dual-payload rendering (slides to vector PDF with embedded speaker notes), Microsoft PowerPoint should be installed. If PowerPoint is not present, PHD Prof gracefully falls back to structured text extraction via `python-pptx`.

#### B. Installing on macOS

**Option 1: Terminal Installation via Homebrew (Recommended)**
Open Terminal.app (`Cmd + Space` -> type *Terminal*) and run:
```bash
# 1. Install Python 3.11 via Homebrew
brew install python@3.11

# 2. Ensure Python 3.11 is prioritized in your PATH (Zsh default on macOS)
echo 'export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```
*(On Intel Macs, Homebrew uses `/usr/local/opt/python@3.11/bin` instead of `/opt/homebrew`).*

**Option 2: GUI Installer (.pkg)**
Download and run the macOS universal installer package from [python.org/downloads/macos](https://www.python.org/downloads/macos/).

**Verification Commands (macOS Terminal)**:
```bash
python3 --version  # Expected output: Python 3.11.x (or >= 3.10)
pip3 --version     # Expected output: pip 24.x from ...
```

#### C. Installing on Linux (Debian / Ubuntu)
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 --version
```

---

### 2. Notion Account & Database Setup

PHD Prof requires an active Notion account ([notion.so](https://www.notion.so/)) to host and organize your synthesized course knowledge base.

#### Architectural Specification: How PHD Prof Manages Academic Workflows

The pipeline models university knowledge in a **3-tier hierarchical structure**:

```
[Level 1: Academic Hub / Root Page]
  │  (NOTION_ROOT_PAGE_ID)
  │  Example: "University 2026/2027" or "PhD Studies"
  │
  ├── [Level 2: Course Container Page]
  │     │  (course_id)
  │     │  Example: "Enterprise Architectures"
  │     │
  │     └── [Level 3: Target Notes Database]
  │           │  (database_id)
  │           │  Inline or Full-page database titled "Notes" (or "Lectures" / "Dispense")
  │           │
  │           ├── [Generated Row / Page 1] Lecture 01: Introduction & Principles
  │           │     ├── [Callout Block] Core Axioms & Scope
  │           │     ├── [LaTeX Block] Formal Mathematical Definitions
  │           │     ├── [Code Block] Algorithms & Data Structures
  │           │     └── [Review Callout] Critical Exam Questions
  │           │
  │           ├── [Generated Row / Page 2] Lecture 02: ArchiMate & Business Layer
  │           └── [Generated Row / Page 3] Lecture 03: TOGAF ADM Cycles & Metamodels
  │
  └── [Level 2: Course Container Page] "Machine Learning"
        └── [Level 3: Target Notes Database] "Notes"
              ├── [Generated Row / Page 1] Week 01: Empirical Risk Minimization
              └── [Generated Row / Page 2] Week 02: Support Vector Machines
```

#### How the Pipeline Executes the Work
1. **Hierarchical Course Discovery**:
   - When configuring or launching a course in the Web Cockpit or CLI, PHD Prof queries the root entity (`NOTION_ROOT_PAGE_ID`).
   - It enumerates all Course Container Pages (Level 2) and recursively inspects the chosen course to locate its inner `Notes` database (Level 3).
   - Once resolved, the exact `database_id` is cached in `course_profiles.json`, eliminating discovery roundtrips on future runs.
2. **Cryptographic Idempotence Check**:
   - For every document in your local course folder (e.g. `EA_Lecture_03_ArchiMate.pptx`), the pipeline computes its SHA-256 hash.
   - It checks `sync_state.json`: if already marked `SYNCED`, the file is skipped instantly ($0\text{ ms}$, 0 tokens consumed).
3. **Structured Page Creation & Native Block Appending**:
   - If new or modified, PHD Prof makes an atomic API call to create a **new page/row** within the course's target database.
   - It sets the page's **Title property** to the synthesized lecture title.
   - It then appends native Notion blocks in safe batches of 100:
     - **Executive Summary Callouts**: Core theoretical principles, definitions, and theorems.
     - **Native LaTeX Math**: Standalone display equations (`$$...$$`) and inline math (`$formula$`).
     - **Syntax-Highlighted Code**: Multi-language blocks (Python, R, SQL, Shell, etc.).
     - **Speaker Notes Correlation**: For `.pptx` decks, slide diagrams are explicitly synthesized alongside instructor commentary.
     - **Exam Review Checkpoints**: Socratic oral exam questions and edge-case verifications.
4. **Deep-Link Persistence**:
   - The resulting Notion Page ID is permanently recorded in `sync_state.json`. In the Web Cockpit, the document turns green (`SYNCED`) and gains an inline `[Notion]` button opening that exact lecture page in your browser.

#### Step 1: Create an Internal Integration Token (`NOTION_TOKEN`)
1. Log in to your Notion account at [notion.so](https://www.notion.so/).
2. Open the Notion Integrations portal: [notion.so/profile/integrations](https://www.notion.so/profile/integrations).
3. Click **"+ New integration"**.
4. Configure integration settings:
   - **Name**: Enter an identifiable name (e.g., `PHD Prof`).
   - **Associated workspace**: Select the workspace hosting your academic notes.
   - **Type**: Select **Internal**.
5. Under the **Capabilities** tab, verify the following are enabled:
   - ☑ **Read content**
   - ☑ **Update content**
   - ☑ **Insert content**
6. Click **Save** at the bottom.
7. Under **Internal Integration Secret**, click **Show** and **Copy** (the secret begins with `secret_` or `ntn_`). Keep this value for your `.env` file.

#### Step 2: Creating the Course Page and Database in Notion
1. **Create the Course Page**: Inside your root page (e.g., "University"), create a regular page named after the course (e.g., "Enterprise Architectures").
2. **Create the Target Database**:
   - Inside the Course Page, click into the page body, type `/database`, and select **"Database - Inline"** (or **"Database - Full page"**).
   - Set the title of the database to `Notes` (or `Lectures`, `Papers`, etc.).
3. **Database Schema & Properties**:
   - **Mandatory Property**: The default **Title property** (named `Name` or `Title` by default). PHD Prof automatically inspects the database schema and detects whichever property has `type: "title"`. You can rename it in Notion freely without breaking the pipeline.
   - **Optional Properties**: You can add any custom properties (`Tags`, `Date`, `Status`, `Week`) for personal organization. PHD Prof creates each lecture as a new row in this database with the document title and writes all synthesized content (LaTeX math, code blocks, callouts) as child blocks inside that row's page.

#### Step 3: Authorize the Integration on Notion (Critical Step!)
> [!CAUTION]
> Notion operates under a strict zero-trust sandbox: **integrations have zero visibility into any page or database until explicitly invited**. Skipping this authorization step will cause all page creation calls to fail.

> [!WARNING]
> **Diagnostic Symptom: `Error on <file>: 404 Client Error: Not found for url: https://api.notion.com/v1/pages`**  
> In Notion's REST API architecture, querying or modifying an unauthorized resource deliberately returns **`HTTP 404 Object Not Found`** instead of `403 Forbidden` (to prevent resource enumeration). If you see this error when synchronizing documents, your integration token is valid but **has not been connected to the specific course page or database**, or your `database_id` is invalid.

##### How to Authorize Access:
- **Approach A (Direct Course/Database Connection — Recommended & Bulletproof)**:
  1. In Notion, navigate directly to your specific **Course Page** (e.g., "Econometrics") or open the inner target **Notes Database** as a full page.
  2. Click the three dots icon (**`...`**) in the top right corner of the window.
  3. Scroll down to **"Connections"** (or **"Connect to"**).
  4. Search for your integration name (e.g., `PHD Prof`) and confirm.
  5. The integration now possesses direct read, write, and page creation permissions inside that database.
- **Approach B (Recursive Root Connection)**:
  1. In Notion, navigate to your root parent page (e.g., "University" specified in `NOTION_ROOT_PAGE_ID`).
  2. Click `...` -> **"Connections"** -> **"Connect to"** -> select `PHD Prof`.
  3. *Note*: If your course page or database was created outside this root tree, or if page permissions are set to private/custom, inheritance will not apply. When in doubt, always apply **Approach A** directly on the Course Page or the target database.

#### Step 4: Extracting NOTION_ROOT_PAGE_ID and Course Database IDs
1. **Root Page ID (`NOTION_ROOT_PAGE_ID`)**:
   - Open your top-level root page in Notion.
   - Click `...` -> **"Copy link"** (or copy the URL from your browser address bar).
   - Notion URLs look like: `https://www.notion.so/workspace/University-3a8b2c4d5e6f708192a3b4c5d6e7f890`
   - The ID is the **32-character hexadecimal string** at the end of the URL slug.
2. **Course Database ID (`database_id`)**:
   - Open the target "Notes" database as a full page (hover over the header -> "Open as page", or click `...` on the database block) and click **"Copy link"**.
   - Notion URLs follow the structure: `https://www.notion.so/{workspace}/<DATABASE_ID>?v=<VIEW_ID>`.
   - **Database ID vs. View ID**: Use strictly the **32-character hexadecimal string before `?v=`** (`<DATABASE_ID>`). The string *after* `?v=` is only the UI View ID; passing the View ID will trigger an API `404 Object Not Found`.
   - > [!IMPORTANT]
   - > - **Database ID vs View ID**: Extract only the token preceding `?v=`. The `?v=...` suffix belongs to the view and must be omitted.
   - > - **Replace Template Placeholders**: Never leave the template placeholder (`"your_notion_notes_database_id_here"` from `course_profiles.example.json`). It will immediately cause a 404 error.
   - > - **Must Be a Database (Not a Plain Page)**: The target must be an inline or full-page Notion **Database** (with columns/properties), not a plain text page. Supplying a Page ID in `database_id` causes `POST /v1/pages` to fail with `404 Object Not Found`.

---

### 3. Google Gemini API Key Setup

PHD Prof relies on Google Gemini Flash for visual slide inspection and structured text distillation.

1. Navigate directly to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your standard Google account.
3. In the left navigation menu, click **"Get API key"**.
4. Click **"Create API key"**.
5. Choose **"Create API key in new project"** (or link to an existing Google Cloud project).
6. Copy the generated key string (typically starts with `AIzaSy...`).
7. Paste this string into your `.env` file as `GEMINI_API_KEY`.

> [!NOTE]
> Google AI Studio provides a free tier with generous daily request quotas (RPD) sufficient to process regular university coursework without charges.

---

### 4. Environment Setup & Dependency Installation

Isolate the project dependencies inside a local Python virtual environment:

#### Windows (PowerShell):
```powershell
# 1. Clone repository and navigate to root directory
git clone https://github.com/FRA-0023/PHD_Prof.git
cd PHD_Prof

# 2. Create isolated virtual environment (.venv)
python -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1
# If PowerShell policy prevents execution, run once:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Install required libraries
pip install -r requirements.txt
```

#### macOS / Linux (Terminal):
```bash
# 1. Clone repository and navigate to root directory
git clone https://github.com/FRA-0023/PHD_Prof.git
cd PHD_Prof

# 2. Create isolated virtual environment (.venv)
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

### 5. Environment Variables Configuration (.env)

Initialize your `.env` file from the provided [.env.example](file:///.env.example):

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in an editor and populate your credentials:

```env
# Google Gemini API
GEMINI_API_KEY=AIzaSyYourGeneratedGeminiKeyHere

# Notion Integration
NOTION_TOKEN=secret_YourNotionInternalSecretTokenHere
NOTION_ROOT_PAGE_ID=3a8b2c4d5e6f708192a3b4c5d6e7f890

# Optional Configurations
GEMINI_TIMEOUT_SECONDS=300
GEMINI_MODEL=gemini-2.5-flash
CLI_LANGUAGE=EN
```

#### Configuration Variables Reference

| Variable | Required | Description | Default |
|---|:---:|---|---|
| `GEMINI_API_KEY` | **Yes** | Google Gemini API key obtained from [Google AI Studio](https://aistudio.google.com/) | *None* |
| `NOTION_TOKEN` | **Yes** | Notion Internal Integration secret token (`secret_...` / `ntn_...`) | *None* |
| `NOTION_ROOT_PAGE_ID` | **Yes** | 32-character ID of root Notion page or master course database | *None* |
| `GEMINI_MODEL` | No | Gemini model identifier (supports automatic fallbacks) | `gemini-2.5-flash` |
| `GEMINI_TIMEOUT_SECONDS` | No | Timeout in seconds for large file uploads and inference | `300` |
| `CLI_LANGUAGE` | No | CLI interface language (`EN` or `IT`) | `EN` |

---

## 📂 Project File Taxonomy & Runtime State Map

| File / Folder | Role and Functionality | Tracked in Git? |
|---|---|:---:|
| [`.env.example`](file:///.env.example) | Public configuration template with annotated placeholders. | **Yes** |
| `.env` | Local operational secrets. **Never committed to Git**. | **No** (in `.gitignore`) |
| [`course_profiles.example.json`](file:///course_profiles.example.json) | Example course specification template. | **Yes** |
| `course_profiles.json` | Stores registered academic courses (subject, persona prompt, local path, Notion target). Auto-seeded on first run. | **No** (in `.gitignore`) |
| `sync_state.json` | **Cryptographic State Ledger**: stores content SHA-256 hashes, timestamps, token counts, and Notion page IDs. Enforces idempotence across restarts. | **No** (in `.gitignore`) |
| `gemini_usage.json` | Rolling 24-hour sliding window log of Gemini API calls for quota tracking. | **No** (in `.gitignore`) |
| `staging/` | Ephemeral scratch directory for PPTX-to-PDF vector renderings and temporary chunk slices. Cleaned automatically. | **No** (in `.gitignore`) |
| [`Avvia_PHD_Prof.bat`](file:///Avvia_PHD_Prof.bat) | Windows shortcut launcher triggering the hidden VBS process. | **Yes** |
| [`Avvia_PHD_Prof.vbs`](file:///Avvia_PHD_Prof.vbs) | Windowless Windows launcher (`WindowStyle = 0`) launching FastAPI and opening default browser without CMD popups. | **Yes** |
| [`Avvia_PHD_Prof.command`](file:///Avvia_PHD_Prof.command) | One-click double-clickable launcher for macOS Finder with environment autodetection. | **Yes** |
| [`Avvia_PHD_Prof.sh`](file:///Avvia_PHD_Prof.sh) | POSIX-compliant shell entrypoint for Linux and Unix workstations. | **Yes** |
| [`requirements.txt`](file:///requirements.txt) | Explicit runtime and testing Python dependencies. | **Yes** |
| [`pdf_to_notion.py`](file:///pdf_to_notion.py) | Application entrypoint wiring ports and adapters (`--mode web` / `--mode cli`). | **Yes** |

---

### Structure of `course_profiles.json`
`course_profiles.json` persists invariant course metadata, eliminating repetitive configuration:

```json
{
  "enterprise_architectures": {
    "subject": "Enterprise Architectures",
    "professor_type": "PhD Professor in Enterprise Architecture",
    "doc_type": "slides",
    "folder_path": "C:\\Academic_Courses\\Enterprise Architecture",
    "target": {
      "database_id": "3e8b63e859c881c199e6e795ddf4c976",
      "course_name": "Enterprise Architectures",
      "database_title": "Notes"
    }
  }
}
```

- `subject`: Academic course name.
- `professor_type`: Pedagogical persona prompt calibrating Gemini's depth and technical rigor.
- `doc_type`: `slides` (multimodal vision + speaker notes) or `paper_or_book` (analytical text parsing).
- `folder_path`: Absolute local filesystem path containing documents.
- `target.database_id`: Target Notion database ID where lecture notes will be created.

---

## 🚀 Execution Modes: Web Cockpit vs CLI

### Option A: Web Cockpit (Recommended)
Provides full visual observability and selective batch control:

- **Windows**: Double-click [`Avvia_PHD_Prof.bat`](file:///Avvia_PHD_Prof.bat) (or run via PowerShell: `wscript Avvia_PHD_Prof.vbs`).
- **macOS**: Double-click [`Avvia_PHD_Prof.command`](file:///Avvia_PHD_Prof.command) in Finder.
- **Linux**: Execute from terminal:
  ```bash
  ./Avvia_PHD_Prof.sh
  ```
- **Universal CLI Invocation**:
  ```bash
  python pdf_to_notion.py --mode web
  # Optional arguments:
  # --domain phdprof.test (customizes local domain name, default: phdprof.test)
  # --ssl / --no-ssl      (enables/disables HTTPS; auto-enabled when certs/ exists)
  # --port 443            (customizes port, default: 443 for HTTPS, 80 for HTTP)
  # --no-browser          (prevents opening browser automatically)
  ```

---

### Option B: Interactive Terminal CLI
Suited for headless servers, SSH connections, or terminal purists:

```bash
# Default English interactive CLI
python pdf_to_notion.py --mode cli

# Optional Italian localized interactive CLI
python pdf_to_notion.py --mode cli --lang IT
```

---

## 🏗️ Technical Architecture & Verification Test Suite

PHD Prof is strictly architected under the **Hexagonal Pattern (Ports & Adapters)** in `src/`, ensuring core business logic is completely isolated from HTTP frameworks, third-party SDKs, and local storage mechanisms:

```
[ Inbound Adapters ]
  ├── Web Cockpit (FastAPI + SSE Streamer)
  └── Terminal CLI (I18n Console)
          │
          ▼
    [ Ports ]
          │
          ▼
[ Core Use Cases & Domain ]
  ├── ProcessDocumentUseCase
  └── Domain Models (CourseProfile, SyncEntry, Document)
          │
          ▼
    [ Ports ]
          │
          ▼
[ Outbound Adapters ]
  ├── GeminiLlmAdapter (LLM Inference + Backoff)
  ├── GeminiFileReader (Multimodal PDF & PPTX COM Bridge)
  ├── TextPdfReader (Local PyMuPDF + MarkItDown)
  ├── NotionApiAdapter (REST Client + Block Builder)
  └── JsonStateRepository (Cryptographic SHA-256 State Engine)
```

### Running the Offline Test Suite
The codebase includes comprehensive unit tests with full offline mocks covering all adapters, ports, and use cases:

```bash
python -m pytest
```
*All 84/84 unit tests execute in under 3 seconds with zero external network dependencies.*

---

## 🛠️ Troubleshooting & Diagnostic Guide

### 1. `Error on <file>: 404 Client Error: Not found for url: https://api.notion.com/v1/pages`
- **Root Cause**: Notion REST API responds with `404 Not Found` (rather than `403 Forbidden`) whenever:
  1. The Notion integration has **not been invited/connected** to the specific Course Page or target Database.
  2. The `database_id` configured in your course profile is still set to the template placeholder (`your_notion_notes_database_id_here`), mistakenly uses the View ID (the string after `?v=`) instead of the Database ID (the string before `?v=`), or points to a regular Page instead of a Database.
- **Resolution**:
  1. In Notion, navigate to your Course Page or open the "Notes" database directly.
  2. Click the three dots icon (**`...`**) in the top right corner $\rightarrow$ **Connections** (or **Connect to**) $\rightarrow$ select your integration (`PHD Prof`).
  3. Verify in the Web Cockpit (or in `course_profiles.json`) that `database_id` is the real 32-character hexadecimal database UUID (the string before `?v=`), and not a View ID or plain Page ID.

### 2. `400 Client Error: validation_error` on Notion API
- **Root Cause**: The target Notion database is missing a Title property, or an invalid property schema was provided.
- **Resolution**:
  - Open your Notion database in the browser and ensure it contains a Title column (default is `Name` or `Title`). PHD Prof automatically queries the database schema and maps to whichever column has `type: "title"`.

### 3. Daily LLM Quota Exhausted / RPD Cap Reached (`429 RESOURCE_EXHAUSTED`)
- **Diagnostic Log**: Emitted in telemetry as `Daily LLM quota exhausted` (or `Quota giornaliera LLM esaurita`).
- **Root Cause**: Google Gemini API Free Tier enforces a daily request cap (typically 15–20 RPD on Flash models).
- **Resolution**:
  - The Web Cockpit topbar displays your live remaining RPD. PHD Prof halts the queue cleanly without burning tokens or creating duplicate records. Quota counters automatically reset every 24 hours (tracked via `gemini_usage.json`). You can link a billing card in Google AI Studio for pay-as-you-go high throughput.

### 4. Empty Document Extraction / Zero Content (`ValueError: Empty document content`)
- **Diagnostic Log**: Emitted when extracting zero selectable characters (`ValueError: Il contenuto estratto dal documento è vuoto`).
- **Root Cause**:
  1. *Scanned Image PDFs in `PAPER_OR_BOOK` mode*: The file consists of bitmap image scans without an embedded digital text layer. Local extractors (`PyMuPDF` / `MarkItDown`) detect zero selectable characters.
  2. *Cloud-Only Placeholder Files (OneDrive / iCloud / Google Drive "Files On-Demand")*: The operating system has not downloaded the physical file content to local storage, presenting a 0-byte stub to Python.
- **Resolution**:
  - *For Scanned PDFs*: In your course profile settings, switch `doc_type` to **`slides`**. Slides mode uploads the PDF directly to Google Gemini's multimodal vision API, executing neural visual OCR over mathematical formulas, handwritten margins, and rasterized figures.
  - *For Cloud Files*: Right-click the folder in Windows Explorer or macOS Finder and select **"Always keep on this device"** (or trigger a full local download) before running synchronization.

### 5. `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`
- **Root Cause**: The PDF or PPTX document is currently opened in an external desktop application (e.g. Microsoft PowerPoint, Adobe Acrobat, Foxit PDF Reader) with an exclusive file lock on Windows.
- **Resolution**: Close the file in your viewer or presentation editor before launching batch processing.

### 6. Local Domain & Trusted HTTPS Setup (`https://phdprof.test`)
- **Local Domain & Root SSL Setup**: To navigate directly to `https://phdprof.test` without security warnings or port numbers, double-click `Configura_Dominio_Locale.bat` (Windows) or execute `sudo ./scripts/setup_local_domain.sh` (macOS/Linux). This script performs two actions in one step:
  1. Maps `127.0.0.1 phdprof.test` into your local `hosts` file and flushes DNS cache.
  2. Generates local SSL certificates (if absent) and installs the Root CA into the Windows Trusted Root Certificate Store, enabling green-padlock HTTPS in all browsers.
- **Port Conflict Handling**: PHD Prof binds by default to standard HTTPS port `443` (or `80` if HTTPS is disabled). If port 443 is occupied by another local service, the server automatically falls back to port `8443` (or `8000` for HTTP). You can also specify an explicit port:
  ```bash
  python pdf_to_notion.py --mode web --port 8443
  ```

### 7. Headless PPTX Vector Conversion Fallback (`[PPTX to PDF Warning] COM conversion failed`)
- **Diagnostic Log**: Emitted in telemetry as `[PPTX to PDF Warning] Conversione COM fallita`.
- **Root Cause**: Dual-payload slide extraction (converting slides to high-resolution vector PDF to preserve diagrams for Gemini Vision) relies on Microsoft PowerPoint COM automation on Windows (`win32com`). This interface is unavailable on macOS, Linux, or Windows machines lacking desktop PowerPoint.
- **Behavior & Resolution**: PHD Prof automatically and gracefully falls back to extracting slide titles, body bullet points, and speaker notes via `python-pptx` / `MarkItDown`. While textual synthesis remains exhaustive, vision models will not inspect graphical layouts. To ensure full multimodal diagram fidelity on macOS or Linux, export your presentation to vector PDF directly from Keynote or PowerPoint before dropping it into the monitored course directory.

### 8. Windows PowerShell `PSSecurityException` (`Activate.ps1 cannot be loaded`)
- **Root Cause**: Default Windows security policies restrict running PowerShell scripts within the user scope.
- **Resolution**: Open PowerShell and configure execution policy for the current user:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### 9. Launcher Privileges on macOS / Linux (`Permission denied` on `.command` or `.sh`)
- **Root Cause**: Cloning or extracting archives on Unix-like platforms can strip execution bits from shell scripts.
- **Resolution**: Mark the launchers executable from Terminal:
  ```bash
  chmod +x Avvia_PHD_Prof.command Avvia_PHD_Prof.sh
  ```

### 10. Integration Not Listed in Notion Menu ("Connect to" Empty)
- **Root Cause**: When the internal integration token was generated at [notion.so/profile/integrations](https://www.notion.so/profile/integrations), it was associated with Workspace A (e.g., Personal), while the academic database is located in Workspace B (e.g., University / Organization account).
- **Resolution**: Check the **Associated workspace** dropdown in Notion Integrations. Internal integrations cannot traverse workspace boundaries; recreate the integration within the target workspace hosting your course hub.

---

**Author:** Francesco Colombini  
[GitHub Profile](https://github.com/FRA-0023) · [LinkedIn](https://www.linkedin.com/in/francescocolombini/)
