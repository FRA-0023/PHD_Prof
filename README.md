# 📄 PHD Prof: Antifragile Document ETL Pipeline for Notion

[![Language](https://img.shields.io/badge/Language-Python%203.10+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-Google%20Gemini%20API-4285F4?logo=google)](https://ai.google.dev/)
[![Destination](https://img.shields.io/badge/Destination-Notion%20API-000000?logo=notion)](https://www.notion.so/)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal%20Ports%20%26%20Adapters-green)](#)
[![Reliability](https://img.shields.io/badge/Reliability-Crash--Only%20ETL-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Transform 100+ fragmented slides into rigorous, publication-grade Notion study chapters in under 30 seconds.** Zero manual note-taking, zero duplicate pages, and zero wasted LLM tokens via cryptographic SHA-256 state tracking.

---

## 📌 Table of Contents

1. [Core Value Proposition: Tangible Benefits & ROI](#-core-value-proposition-tangible-benefits--roi)
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

## 🎯 Core Value Proposition: Tangible Benefits & ROI

Graduate students, doctoral researchers, and technical professionals face a severe cognitive bottleneck: **800 to 1,500 slides per course each semester**, presented as fragmented bullet points, truncated formulas, and disconnected architectural diagrams.

```
Traditional Manual Study (4–6 Hours / Lecture)
[ Raw Slides ] ──► [ Manual Reading ] ──► [ Screenshotting Diagrams ] ──► [ Retyping LaTeX Proofs ] ──► [ Partial Notes ]
                                                                                                            ▲
                                                                                       (High cognitive fatigue, lost speaker notes)

PHD Prof Industrial Pipeline (30 Seconds / Lecture)
[ Raw Slides / Decks ] ──► [ 1-Click Cockpit Batch ] ──► [ Publication-Grade Notion Chapter with 300 DPI Figures & LaTeX ]
```

### The Cost of Conventional Study Methods
- **The 4-to-6 Hour Manual Slog**: Transcribing an 80-slide deck into structured notes, cropping diagrams, formatting LaTeX proofs, and deciphering oral commentary consumes **4 to 6 hours per lecture**. Over an entire curriculum, this burns **80+ hours on clerical busywork** instead of deep conceptual mastery.
- **The Hidden Loss of Speaker Commentary**: Up to 60% of critical insights in presentations reside in the professor's spoken delivery (recorded in PPTX speaker notes and footers). Manual summaries and generic PDF extractors almost always discard this commentary.
- **The Naive AI Trap**: Copy-pasting slide text into ChatGPT or Claude yields shallow, generic summaries that lose all spatial diagrams, corrupt complex mathematical notation, truncate arbitrarily on token limits, and re-burn paid tokens every time a prompt is re-run.

---

### Key Advantages & Measurable ROI

| Benefit Pillar | Quantitative Impact | How PHD Prof Delivers It |
| :--- | :--- | :--- |
| **⚡ 10x Time Recovery** | **4–6 hours $\rightarrow$ 30 seconds** per lecture | Drop `.pdf` or `.pptx` decks into your course folder, click *"Sync Selected"*, and let the autonomous engine construct the full chapter. |
| **🧠 Zero Information Loss** | **100% preservation** of oral & visual context | **Dual-Payload Architecture**: Combines vector slide rendering with headless extraction of speaker notes and footers, cross-correlating spoken context with visual models. |
| **📐 Publication-Grade Synthesis** | **Textbook-level** rigor directly in Notion | Synthesizes comprehensive chapters with native LaTeX formulas (`$formula$` and `$$...$$`), syntax-highlighted code blocks, structured mental models, and PhD-level exam preparation questions. |
| **🖼️ High-DPI Visual Delivery** | **300 DPI vector figures** hosted on CDN | Detects diagram bounding boxes via Gemini Vision, crops them at 300 DPI with PyMuPDF, and hosts them on Cloudflare R2, bypassing Notion's 2 MB upload ceiling. |
| **🔒 Cryptographic Idempotency** | **Exact 0 tokens** burned on re-runs | Computes content SHA-256 hashes prior to any API dispatch. Re-scanning a library takes **0 ms and 0 tokens**. Network failures recover cleanly with zero duplicate pages. |
| **💰 Free-Tier Infrastructure** | **\$0.00 operational cost** | Operates comfortably within Google Gemini's generous free tier and Cloudflare R2's free tier with **zero outbound egress fees**. |

---

### Comparative Advantage Matrix

| Evaluation Dimension | Manual Note-Taking | Generic AI Web Chat (ChatGPT / Claude) | PHD Prof Industrial ETL |
| :--- | :--- | :--- | :--- |
| **Processing Speed** | 4 – 6 hours per deck | 15 – 30 minutes of manual copy-paste | **~30 seconds fully automated** |
| **Diagram Extraction** | Manual screenshotting & cropping | Lost (text-only OCR) | **Automated 300 DPI crop + CDN embedding** |
| **Speaker Notes & Footers** | Frequently overlooked | Discarded | **Dual-Payload simultaneous extraction** |
| **Mathematical Proofs** | Manual LaTeX transcription | Prone to syntax breakage | **Native Notion Math Blocks (`$` / `$$`)** |
| **Deduplication & State** | High human error | Resubmitting burns fresh tokens | **Cryptographic SHA-256 state ledger** |
| **Crash Recovery** | Manual rework required | Partial / lost responses | **Crash-only atomic rollback (zero orphans)** |
| **Long-Term Scalability** | Declines with course load | Cluttered chat histories | **Organized relational Notion database** |

---

## 🖥️ The Web Cockpit (Industrial Local Dashboard)

PHD Prof features a zero-build, local-first single-page cockpit accessible by default on standard HTTP port `80` at `http://127.0.0.1` (with automatic port conflict fallback to `8000`). Once configured via our 1-click local domain script, it automatically upgrades to zero-warning trusted HTTPS on port `443` at `https://phdprof.test` (see [Local Domain Setup](docs/LOCAL_DOMAIN_SETUP.md)). Built according to the *Operate* visitor mode and WCAG 2.2 AA accessibility standards:

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
- **Dark / Light Mode Toggle**: Seamlessly switch between dark and light themes via the topbar button (Sun/Moon icon) or keyboard shortcut (`Alt + T`). User preference is persisted in `localStorage` with native fallback to OS `prefers-color-scheme`. Both modes maintain rigorous WCAG 2.2 AA contrast compliance, with a high-contrast industrial dark terminal deck preserved for live telemetry streaming.
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

# Cloudflare R2 Image Storage (Optional: enables visual diagram extraction)
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY=<your-access-key>
R2_SECRET_KEY=<your-secret-key>
R2_BUCKET_NAME=phd-prof-assets
R2_PUBLIC_DOMAIN=https://pub-xxxxxx.r2.dev

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
| `R2_ENDPOINT_URL` | No | Cloudflare R2 global endpoint (do NOT use `.eu.` jurisdictional endpoints) | *None* |
| `R2_ACCESS_KEY` | No | R2 API Token Access Key | *None* |
| `R2_SECRET_KEY` | No | R2 API Token Secret Key | *None* |
| `R2_BUCKET_NAME` | No | Name of the R2 bucket where images are stored | *None* |
| `R2_PUBLIC_DOMAIN` | No | R2 Public URL (e.g. `https://pub-xxxx.r2.dev`) | *None* |
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
| [`Launch_PHD_Prof.bat`](file:///Launch_PHD_Prof.bat) | Windows shortcut launcher triggering the hidden VBS process. | **Yes** |
| [`Launch_PHD_Prof.vbs`](file:///Launch_PHD_Prof.vbs) | Windowless Windows launcher (`WindowStyle = 0`) launching FastAPI and opening default browser without CMD popups. | **Yes** |
| [`Launch_PHD_Prof.command`](file:///Launch_PHD_Prof.command) | One-click double-clickable launcher for macOS Finder with environment autodetection. | **Yes** |
| [`Launch_PHD_Prof.sh`](file:///Launch_PHD_Prof.sh) | POSIX-compliant shell entrypoint for Linux and Unix workstations. | **Yes** |
| [`Configure_Local_Domain.bat`](file:///Configure_Local_Domain.bat) | One-click elevated script configuring local domain `phdprof.test`, trusted Root CA, and port 443 HTTPS. | **Yes** |
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

- **Windows**: Double-click [`Launch_PHD_Prof.bat`](file:///Launch_PHD_Prof.bat) (or run via PowerShell: `wscript Launch_PHD_Prof.vbs`).
- **macOS**: Double-click [`Launch_PHD_Prof.command`](file:///Launch_PHD_Prof.command) in Finder.
- **Linux**: Execute from terminal:
  ```bash
  ./Launch_PHD_Prof.sh
  ```
- **Universal CLI Invocation**:
  ```bash
  # Standard launch on http://127.0.0.1 (Port 80, fallback 8000)
  python pdf_to_notion.py --mode web

  # Optional arguments:
  # --port 80             (customizes port, default: 80 for HTTP, 443 for HTTPS)
  # --ssl / --no-ssl      (forces HTTPS on/off; auto-detected when certs/ exists)
  # --domain phdprof.test (customizes local domain name)
  # --no-browser          (prevents opening browser automatically)
  ```

- **Output Mode Selector**: In the toolbar above the document queue, use the compact segmented control (`Entrambi` / `Note` / `Grafo`):
  - `Entrambi` (default): Complete analytical chapter + visual Mermaid architecture map & examination drills.
  - `Note`: Only the deep textbook synthesis (excluding graphs and study drills).
  - `Grafo`: Only the conceptual architecture diagram, flowchart, active recall drills, and model boundary conditions.
- **On-Demand Graph Append (`+ Grafo`)**: For documents already synchronized (`SYNCED`), a dedicated `+ Grafo` action button in the document table extracts or generates the Mermaid conceptual architecture and appends it directly to the existing Notion page without re-running the entire text synthesis.

---

### Option B: Interactive Terminal CLI
Suited for headless servers, SSH connections, or terminal purists:

```bash
# Default English interactive CLI
python pdf_to_notion.py --mode cli

# Optional Italian localized interactive CLI
python pdf_to_notion.py --mode cli --lang IT

# Direct generation mode override
python pdf_to_notion.py --mode cli --generation-mode both        # Notes + Graphs (default)
python pdf_to_notion.py --mode cli --generation-mode notes_only   # Notes only
python pdf_to_notion.py --mode cli --generation-mode graphs_only  # Conceptual maps only
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
*All 99/99 unit tests execute in under 3 seconds with zero external network dependencies.*

---

## 📚 Documentation & Reference Hub

To maintain maximum signal and focus in this primary manual, detailed diagnostic procedures, advanced host networking, and optional infrastructure setups are organized into dedicated reference guides:

| Document | Focus & Coverage |
| :--- | :--- |
| **[`Troubleshooting & Diagnostic Guide`](docs/TROUBLESHOOTING.md)** | Full breakdown of Notion API 404/400 errors, cross-workspace token mismatches, Gemini RPD rate limiting, scanned PDF handling, Windows file locks (`WinError 32`), and script permissions. |
| **[`Local Domain & Trusted HTTPS Setup`](docs/LOCAL_DOMAIN_SETUP.md)** | Step-by-step setup for `https://phdprof.test`, 1-click local Root CA generation, Windows/macOS/Linux trust store installation, and DNS TTL cache invalidation. |
| **[`Cloudflare R2 & Image Storage Architecture`](docs/CLOUD_STORAGE.md)** | Architecture for high-DPI diagram extraction (Gemini Vision + PyMuPDF), S3/R2 bucket configuration, deterministic SHA-256 deduplication, and the prune utility. |

---

**Author:** Francesco Colombini  
[GitHub Profile](https://github.com/FRA-0023) · [LinkedIn](https://www.linkedin.com/in/francescocolombini/)
