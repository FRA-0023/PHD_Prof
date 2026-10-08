# Local Domain & Port Architecture Guide (`phdprof.test`)

This guide explains how local domain resolution, port allocations, and SSL/TLS certificates work in PHD Prof. It provides a complete, beginner-friendly walkthrough to take you from a fresh clone on port 80 to a clean, zero-warning `https://phdprof.test` experience on port 443.

---

## 1. Core Concepts: Domains, Ports & TLS Explained

If you have never configured a local domain or web server before, here is the mental model:

### Why `phdprof.test`?
- Standard web browsers access local services via IP addresses like `http://127.0.0.1:8000` or `http://localhost:8000`.
- The Internet Engineering Task Force (IETF RFC 2606 and RFC 6761) permanently reserves four special top-level domains: `.test`, `.example`, `.invalid`, and `.localhost`.
- Because `.test` is globally reserved, it can **never be registered on the public internet**. By mapping `phdprof.test` to your local machine (`127.0.0.1`), you get a clean vanity URL with zero risk of collision with public websites or external DNS hijacking.

### The Anatomy of Ports: Standard vs Custom
- **Standard HTTP (Port 80)**: When you visit `http://example.com`, your browser automatically connects to port 80 behind the scenes and hides the port number.
- **Standard HTTPS (Port 443)**: When you visit `https://example.com`, your browser automatically connects to port 443 behind the scenes and hides the port number.
- **Non-Standard Ports (e.g. 8000, 8443)**: If a server cannot bind to port 80 or 443 (e.g. because another program is using them), you must explicitly type the port in the address bar (e.g. `http://127.0.0.1:8000`).

---

## 2. The Two Operating Modes

PHD Prof is designed with zero-friction progressive enhancement:

```
[ Fresh Clone ]
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Mode 1: Out-of-the-Box Standard HTTP (Port 80)         │
│ • No setup required                                    │
│ • URL: http://127.0.0.1 (or http://localhost)          │
│ • Conflict fallback: http://127.0.0.1:8000             │
└────────────────────────────────────────────────────────┘
      │
      │ (1-Click Run: Configure_Local_Domain.bat)
      ▼
┌────────────────────────────────────────────────────────┐
│ Mode 2: Trusted Green-Lock HTTPS (Port 443)            │
│ • Custom domain: https://phdprof.test                  │
│ • Local Root CA installed in OS trust store            │
│ • Conflict fallback: https://phdprof.test:8443         │
└────────────────────────────────────────────────────────┘
```

### Mode 1: Out-of-the-Box HTTP (First Run)
- When you clone the repository and run `python pdf_to_notion.py --mode web` (or double-click [`Launch_PHD_Prof.bat`](file:///Launch_PHD_Prof.bat)), PHD Prof starts in **Mode 1**.
- It listens on standard HTTP port **80** at `http://127.0.0.1`.
- If port 80 is occupied by another service (e.g. Windows IIS, Skype, Apache), it automatically falls back to **port 8000** (`http://127.0.0.1:8000`).
- You do **not** need to touch any system files to use Mode 1.

### Mode 2: Trusted HTTPS on `phdprof.test` (Upgraded State)
- Running the 1-click configuration script upgrades your system to **Mode 2**.
- PHD Prof binds to standard HTTPS port **443** using custom TLS certificates signed by a local Root Certificate Authority.
- You navigate to `https://phdprof.test` with a green padlock, no security warnings, and no port numbers.

---

## 3. Why Local HTTPS Requires a Private Root CA

Understanding why we use a private Root CA prevents common security misconceptions:

1. **Why Not Let's Encrypt?**  
   Public Certificate Authorities (like Let's Encrypt) require validating domain ownership via public DNS records or internet HTTP challenges. Since `phdprof.test` is a reserved private domain that only exists on your computer, public CAs cannot issue certificates for it.

2. **Why Not a Simple Self-Signed Certificate?**  
   When a web server presents a plain self-signed certificate, modern browsers (Chrome, Edge, Firefox, Safari) show an aggressive full-page warning: *"Your connection is not private"* (`NET::ERR_CERT_AUTHORITY_INVALID`). You would have to click past this warning every time.

3. **The Industrial Solution: Private Root CA**  
   PHD Prof generates its own Root Certificate Authority (`PHD Prof Local Root CA`) and imports it into your operating system's **Trusted Root Certification Authorities** store.
   - Once your OS trusts the Root CA, any server certificate issued by it for `phdprof.test` is **automatically trusted 100%** by all browsers without warnings.
   - Private keys (`certs/*.key`) are strictly generated on your machine and excluded from version control (`.gitignore`).

---

## 4. 1-Click Automated Setup Walkthrough

### On Windows (Recommended)

1. Open File Explorer and navigate to the project directory: `c:\Documenti\Bots\PHD_Prof`.
2. Locate the file: **[`Configure_Local_Domain.bat`](file:///Configure_Local_Domain.bat)**.
3. Double-click it.
4. **User Account Control (UAC) Prompt**: Windows will display a popup: *"Do you want to allow this app to make changes to your device?"*  
   Click **Yes** (administrator rights are required to edit the system `hosts` file and install the Root CA).
5. The script runs automatically in an elevated console window:
   - **Step 4.1**: Checks `C:\Windows\System32\drivers\etc\hosts`. If missing, appends `127.0.0.1 phdprof.test`.
   - **Step 4.2**: Runs `scripts/generate_certificates.py` to create `ca.crt`, `ca.key`, `server.crt`, and `server.key` in `certs/`.
   - **Step 4.3**: Uses Windows `certutil` to import `certs/ca.crt` into the Local Machine Trusted Root store.
   - **Step 4.4**: Refreshes Windows DNS cache (`ipconfig /flushdns`).
6. Press any key to close the window when prompted: `Setup completed successfully!`.
7. **Important**: Completely restart your browser (close all browser windows and reopen) so the browser reloads the updated operating system certificate store.
8. Start the web cockpit via [`Launch_PHD_Prof.bat`](file:///Launch_PHD_Prof.bat) and visit:  
   **`https://phdprof.test/`**

---

### On macOS

1. Open **Terminal** and navigate to the project root:
   ```bash
   cd /path/to/PHD_Prof
   ```
2. Run the setup script with administrative privileges:
   ```bash
   sudo ./scripts/setup_local_domain.sh
   ```
3. Enter your macOS account password when prompted.
4. The script automatically:
   - Appends `127.0.0.1 phdprof.test` to `/etc/hosts`.
   - Generates local TLS certificates in `certs/`.
   - Installs and trusts `certs/ca.crt` in the **macOS System Keychain** (`/Library/Keychains/System.keychain`).
   - Flushes macOS mDNSResponder and directory service cache (`dscacheutil -flushcache`).
5. Restart Safari, Chrome, or your default browser.
6. Launch via [`Launch_PHD_Prof.command`](file:///Launch_PHD_Prof.command) or `./Launch_PHD_Prof.sh`.

---

### On Linux (Ubuntu / Debian / Arch / Fedora)

1. Open your terminal and run:
   ```bash
   sudo ./scripts/setup_local_domain.sh
   ```
2. The script:
   - Appends `127.0.0.1 phdprof.test` to `/etc/hosts`.
   - Generates certificates in `certs/`.
   - Copies `ca.crt` to `/usr/local/share/ca-certificates/phdprof_ca.crt` (or `/etc/ca-certificates/trust-source/anchors/`) and executes `update-ca-certificates`.
   - Flushes `systemd-resolved` cache (`resolvectl flush-caches`).
3. Restart your browser.
4. Launch via `./Launch_PHD_Prof.sh`.

---

## 5. Manual Verification (Under the Hood)

If you want to manually verify each component, here is how to inspect your system:

### 1. Verify `hosts` File Mapping
- **Windows**: Open PowerShell and run:
  ```powershell
  Get-Content C:\Windows\System32\drivers\etc\hosts | Select-String "phdprof.test"
  ```
  Expected output:
  ```
  127.0.0.1       phdprof.test
  ```
- **Test Connectivity**: Run `ping phdprof.test`. It should reply immediately from `127.0.0.1`.

### 2. Verify Windows Certificate Store
1. Press `Win + R`, type `certlm.msc` (Certificates - Local Computer), and press Enter.
2. In the left panel, expand: **Trusted Root Certification Authorities** $\rightarrow$ **Certificates**.
3. In the list, look for: **`PHD Prof Local Root CA`**.
4. Double-click it. Windows should show: *"This certificate is OK."*

### 3. Verify Certificate Files on Disk
Inspect the `certs/` folder in the project root:
- `certs/ca.crt`: Public Root CA certificate.
- `certs/ca.key`: Private key of the Root CA (restricted, gitignored).
- `certs/server.crt`: Server certificate chain (Server Cert + Root CA).
- `certs/server.key`: Private key of the web server (gitignored).

---

## 6. DNS TTL & Negative Cache Invalidation

A common source of confusion for first-time users is **Negative DNS Caching**:

### Why Did My Browser Open a Google Search or Say "Site Not Reachable"?
If you typed `phdprof.test` into your browser's address bar *before* running the domain setup script:
1. Your browser asked Windows DNS: *"Where is phdprof.test?"*
2. Windows answered: *"This domain does not exist (NXDOMAIN)"*.
3. Modern operating systems and browsers cache this negative response for a **Time-To-Live (TTL)** period of 5 to 15 minutes.
4. Even after you add the domain to `hosts`, the browser may keep showing the cached failure until the cache expires or is flushed.

### How to Flush the Cache Instantly

#### Step 1: Flush Operating System DNS Cache
- **Windows**:
  ```cmd
  ipconfig /flushdns
  ```
- **macOS**:
  ```bash
  sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
  ```
- **Linux**:
  ```bash
  sudo resolvectl flush-caches
  ```

#### Step 2: Flush Browser Internal Host Cache
Chromium-based browsers (Google Chrome, Microsoft Edge, Brave, Opera) maintain their own internal DNS socket cache independent of Windows:
1. Open a new tab in **Google Chrome** or **Brave**:
   - Navigate to: `chrome://net-internals/#dns`
   - Click the button: **"Clear host cache"**.
   - Navigate to: `chrome://net-internals/#sockets`
   - Click the button: **"Flush socket pools"**.
2. Open a new tab in **Microsoft Edge**:
   - Navigate to: `edge://net-internals/#dns`
   - Click: **"Clear host cache"**.

#### Step 3: Use Full URL in Address Bar
When entering the address for the first time, always type the explicit protocol prefix:  
Type **`https://phdprof.test/`** (not just `phdprof.test`), so the browser knows it is a web URL rather than a search engine query.

---

## 7. Port Binding & Conflict Resolution Matrix

PHD Prof includes active socket detection (`_check_port()`) before starting the web server. It tests if the chosen port is open and automatically chooses a conflict fallback:

| Ingestion Mode | Default Port | Conflict Fallback Port | Trigger Condition |
| :--- | :--- | :--- | :--- |
| **HTTP (Mode 1)** | `80` | `8000` | Fresh clone, no certificates, or explicit `--no-ssl` |
| **HTTPS (Mode 2)** | `443` | `8443` | Certificates exist in `certs/` |

### Common Programs That Occupy Port 80
- **Windows IIS (World Wide Web Publishing Service)**: Often running in the background on Windows Pro/Enterprise.
- **Skype / WebRTC clients**: Historically bind to port 80/443.
- **Apache / XAMPP / WampServer**: Local PHP development environments.
- **Docker Desktop**: If containers map `-p 80:80`.

**How PHD Prof Reacts**:
If port 80 is occupied, you will see this notification in the console:
```
[Web] Notice: Port 80 unavailable or in use. Falling back to port 8000...
[Web] Cockpit started at http://127.0.0.1:8000 (listening on 127.0.0.1:8000, SSL=False)
```
The browser tab opens automatically at `http://127.0.0.1:8000` without throwing any crash or socket error.

### Common Programs That Occupy Port 443
- **VMware Workstation Host Agent (`vmware-hostd.exe`)**: Frequently reserves port 443 on Windows developer machines.
- **Local reverse proxies / Traefik / Nginx**.

**How PHD Prof Reacts**:
If port 443 is occupied, PHD Prof falls back to port **8443**:
```
[Web] Notice: Port 443 unavailable or in use. Falling back to port 8443...
[Web] Cockpit started at https://phdprof.test:8443 (listening on 127.0.0.1:8443, SSL=True)
```

---

## 8. Custom Port & Host Overrides

You can override default networking parameters at any time:

### Via Command-Line Interface (CLI)
```bash
# Force custom port (e.g. 5000)
python pdf_to_notion.py --mode web --port 5000

# Force standard HTTP even if certificates exist
python pdf_to_notion.py --mode web --no-ssl --port 8080

# Listen on all network interfaces (LAN access)
python pdf_to_notion.py --mode web --host 0.0.0.0
```

### Via `.env` Configuration
Add the following optional variables to your root `.env`:
```env
# Custom listening port
WEB_PORT=8443

# Custom host interface
WEB_HOST=127.0.0.1

# Custom domain mapping
WEB_DOMAIN=phdprof.test
```

---

## 9. Diagnostic Matrix & Troubleshooting

| Symptom | Probable Cause | Verified Resolution |
| :--- | :--- | :--- |
| `ERR_NAME_NOT_RESOLVED` or browser opens Google search | `phdprof.test` is not yet in the `hosts` file, or browser cached a negative DNS lookup. | 1. Double-click [`Configure_Local_Domain.bat`](file:///Configure_Local_Domain.bat).<br>2. Run `ipconfig /flushdns`.<br>3. In Chrome, go to `chrome://net-internals/#dns` and clear host cache.<br>4. Type `https://` before `phdprof.test`. |
| `NET::ERR_CERT_AUTHORITY_INVALID` | Certificates were generated, but the Root CA was not installed into the OS trust store. | Run [`Configure_Local_Domain.bat`](file:///Configure_Local_Domain.bat) as Administrator so `certutil` registers `ca.crt` in the Root store. Restart all browser windows. |
| Browser shows URL with `:8000` or `:8443` | Standard ports 80 or 443 were busy, so the runtime activated automatic fallback. | This is completely normal behavior. If you want standard ports, identify the occupying program (e.g. `netstat -ano \| findstr :80`) and stop it. |
| `PermissionError: [Errno 13] Permission denied` | Binding to ports below 1024 on macOS/Linux requires superuser privileges. | On Linux/macOS, run `sudo python3 pdf_to_notion.py --mode web`, or use an unprivileged port like `--port 8000`. On Windows, standard user accounts can bind to 80/443 without issues. |
| Antivirus warns about modifying `hosts` | Security software (e.g. Windows Defender, Kaspersky) blocks automated writes to `hosts`. | Temporarily allow the action in your antivirus, or open Notepad as Administrator, open `C:\Windows\System32\drivers\etc\hosts`, and add `127.0.0.1 phdprof.test` manually. |
