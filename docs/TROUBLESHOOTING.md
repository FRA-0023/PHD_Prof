# Troubleshooting & Diagnostic Guide

This guide details common diagnostic errors, root causes, and verified recovery procedures across the entire PHD Prof pipeline (Notion API, Google Gemini, local networking, file ingestion, and platform runtimes).

---

## Table of Contents
1. [Notion API: 404 Client Error (Page / Database Not Found)](#1-notion-api-404-client-error-page--database-not-found)
2. [Notion API: 400 Validation Error (Schema Discrepancies)](#2-notion-api-400-validation-error-schema-discrepancies)
3. [Notion API: Cross-Workspace Integration Mismatch](#3-notion-api-cross-workspace-integration-mismatch)
4. [Google Gemini: Daily Quota Limit (429 RESOURCE_EXHAUSTED)](#4-google-gemini-daily-quota-limit-429-resource_exhausted)
5. [Local Web Networking: Port Binding Conflicts (Port 80 / 443)](#5-local-web-networking-port-binding-conflicts-port-80--443)
6. [Local Domain: DNS Resolution & TTL Cache Stalls (`phdprof.test`)](#6-local-domain-dns-resolution--ttl-cache-stalls-phdproftest)
7. [Document Ingestion: Scanned Image PDFs vs Digital PDFs](#7-document-ingestion-scanned-image-pdfs-vs-digital-pdfs)
8. [Windows: PermissionError [WinError 32] (Locked Files)](#8-windows-permissionerror-winerror-32-locked-files)
9. [PowerShell: PSSecurityException (`Activate.ps1 cannot be loaded`)](#9-powershell-pssecurityexception-activateps1-cannot-be-loaded)
10. [Unix/macOS: Launcher Permission Denied (`chmod +x`)](#10-unixmacos-launcher-permission-denied-chmod-x)
11. [Cross-Platform: Headless PPTX COM Automation Fallback](#11-cross-platform-headless-pptx-com-automation-fallback)

---

## 1. Notion API: 404 Client Error (Page / Database Not Found)

### Symptom
```
[Errore] 404 Client Error: Not found for url: https://api.notion.com/v1/pages
```

### Root Cause
Notion's REST API returns `404 Not Found` (rather than `403 Forbidden`) whenever:
1. The **PHD Prof** internal integration has not been invited or shared to the parent course page or the target database.
2. The `database_id` configured in your course profile is using the View ID (the hexadecimal string after `?v=`) instead of the Database ID (the string before `?v=`).
3. The configured ID points to a regular Page instead of a Notion Database (inline or full-page).

### Resolution
1. In Notion, navigate to your root Academic Hub or Course Page.
2. Click the top-right menu icon (**`...`**) $\rightarrow$ **Connections** (or **Connect to**) $\rightarrow$ select your integration (`PHD Prof`).
3. Ensure child database inheritance: if you share the root page, ensure the integration has access to all nested child databases.
4. Verify the database URL structure:
   ```
   https://www.notion.so/{workspace_name}/{DATABASE_ID}?v={VIEW_ID}
                                          ^^^^^^^^^^^^^
                                    Use ONLY this 32-char hex string
   ```

---

## 2. Notion API: 400 Validation Error (Schema Discrepancies)

### Symptom
```
[Errore] 400 Client Error: validation_error - body failed validation: children should not be empty
```
or
```
[Errore] 400 Client Error: validation_error - title is not a property that exists
```

### Root Cause
1. **Empty Block Children**: Attempting to send a block with `"children": []`. PHD Prof's block builder automatically prunes empty children keys before serialization.
2. **Missing Title Property**: The destination Notion database does not have a Title-type column, or the column name does not match.

### Resolution
- Open the Notion database in your browser. Ensure at least one column has property type **Title** (named `Name`, `Title`, or `Titolo`). PHD Prof dynamically inspects database metadata on startup and maps to whichever column holds the Title type.

---

## 3. Notion API: Cross-Workspace Integration Mismatch

### Symptom
When opening Notion's **"Connect to"** dialog, your integration `PHD Prof` does not appear in the search dropdown.

### Root Cause
Internal integrations in Notion are strictly scoped to a single workspace. If the token was created in *Workspace A* (e.g. personal account), it cannot access databases located in *Workspace B* (e.g. university / institutional account).

### Resolution
1. Navigate to [notion.so/profile/integrations](https://www.notion.so/profile/integrations).
2. Check the **Associated workspace** dropdown.
3. If it belongs to a different workspace, create a new internal integration under the correct university workspace, grant Read/Write/Insert capabilities, and update `NOTION_TOKEN` in your `.env` file.

---

## 4. Google Gemini: Daily Quota Limit (429 RESOURCE_EXHAUSTED)

### Symptom
```
[Gemini] RuntimeError: Quota giornaliera LLM esaurita (limite: 20 chiamate/giorno).
```

### Root Cause
The Google Gemini Free Tier enforces a strict daily quota (typically 15–20 RPD on Flash models).

### Resolution
1. The Web Cockpit topbar displays your live remaining RPD. PHD Prof halts processing fast to avoid token burn or half-written records.
2. The quota counter resets automatically every 24 hours (tracked locally in `gemini_usage.json`).
3. To bypass free tier limits, link a billing payment card in [Google AI Studio](https://aistudio.google.com/) for Pay-As-You-Go pricing.

---

## 5. Local Web Networking: Port Binding Conflicts (Port 80 / 443)

### Symptom
```
[Web] Avviso: porta 80 non accessibile o occupata. Fallback su porta 8000...
```
or
```
PermissionError: [Errno 13] Permission denied (binding to port 80/443)
```

### Root Cause
Standard ports `80` (HTTP) and `443` (HTTPS) may already be bound by:
- Windows World Wide Web Publishing Service (IIS)
- Skype, Apache, Nginx, or Docker Desktop
- Non-root user restrictions on Linux/macOS (ports below 1024 require elevated privileges)

### Resilience & Resolution
PHD Prof features automatic port fallback:
- **Port 80 Busy $\rightarrow$ Falls back to 8000**: Access the dashboard at `http://127.0.0.1:8000`.
- **Port 443 Busy $\rightarrow$ Falls back to 8443**: Access the dashboard at `https://phdprof.test:8443`.
- To specify a custom port explicitly:
  ```bash
  python pdf_to_notion.py --mode web --port 8080
  ```

---

## 6. Local Domain: DNS Resolution & TTL Cache Stalls (`phdprof.test`)

### Symptom
Visiting `http://phdprof.test` or `https://phdprof.test` in the browser returns `DNS_PROBE_FINISHED_NXDOMAIN` or `ERR_NAME_NOT_RESOLVED`.

### Root Cause
1. **First-Time Launch**: New clones default to standard plain HTTP on `http://127.0.0.1:80`. The vanity domain `phdprof.test` requires a one-time host mapping.
2. **DNS TTL Cache**: The operating system or browser cached a negative DNS lookup before the host mapping was written.

### Resolution
1. On Windows, right-click `Configura_Dominio_Locale.bat` and run as Administrator.
2. On macOS/Linux, run:
   ```bash
   sudo ./scripts/setup_local_domain.sh
   ```
3. Flush OS DNS resolver cache:
   - **Windows**: `ipconfig /flushdns`
   - **macOS**: `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`
   - **Linux**: `sudo systemd-resolve --flush-caches`
4. If using Chrome, also visit `chrome://net-internals/#dns` and click **"Clear host cache"**.

---

## 7. Document Ingestion: Scanned Image PDFs vs Digital PDFs

### Symptom
```
ValueError: Il contenuto estratto dal documento è vuoto (0 caratteri).
```

### Root Cause
1. **Scanned Bitmaps in `paper_or_book` Mode**: Local text extractors (`PyMuPDF` / `MarkItDown`) expect a selectable text stream. Bitmapped image scans contain zero digital text characters.
2. **Cloud Files On-Demand**: Files stored on OneDrive, iCloud, or Google Drive that have not been physically downloaded locally present as 0-byte stubs.

### Resolution
- **For Scanned Documents**: In `course_profiles.json` (or via the Cockpit modal), set `doc_type` to **`slides`**. Slides mode uploads the file directly to Gemini's multimodal vision API, performing native neural OCR across handwritten notes and image scans.
- **For Cloud Files**: Right-click the folder in File Explorer / Finder and choose **"Always keep on this device"** before batch synchronization.

---

## 8. Windows: PermissionError [WinError 32] (Locked Files)

### Symptom
```
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process
```

### Root Cause
The target PDF or PPTX is currently open in Microsoft PowerPoint, Adobe Acrobat, Foxit, or another application holding an exclusive Windows file handle.

### Resolution
Close the presentation or PDF reader before starting batch synchronization.

---

## 9. PowerShell: PSSecurityException (`Activate.ps1 cannot be loaded`)

### Symptom
```
File C:\...\venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
```

### Root Cause
Windows defaults to a restrictive PowerShell execution policy (`Restricted`).

### Resolution
Execute in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 10. Unix/macOS: Launcher Permission Denied (`chmod +x`)

### Symptom
```
zsh: permission denied: ./Avvia_PHD_Prof.sh
```

### Root Cause
Git or archive extraction may not preserve POSIX execution bits (`+x`).

### Resolution
```bash
chmod +x Avvia_PHD_Prof.sh Avvia_PHD_Prof.command scripts/setup_local_domain.sh
```

---

## 11. Cross-Platform: Headless PPTX COM Automation Fallback

### Symptom
```
[PPTX to PDF Warning] Conversione COM fallita: No module named 'win32com'
```

### Root Cause
High-fidelity slide-to-vector PDF rendering uses Microsoft PowerPoint COM automation (`win32com`), which only exists on Windows workstations with desktop Office installed.

### Behavior & Resolution
PHD Prof automatically degrades gracefully: it extracts slide titles, bullets, and speaker notes via `python-pptx` and `MarkItDown`. Textual synthesis remains comprehensive. If you require Gemini Vision to inspect graphical slide diagrams on macOS or Linux, export your presentation to vector PDF directly from Keynote or LibreOffice before dropping it into the monitored folder.
