# Local Domain & Trusted HTTPS Setup (`phdprof.test`)

This guide explains local domain resolution, port allocations, and how to upgrade from standard HTTP (port 80) to zero-warning trusted HTTPS (port 443) using `phdprof.test`.

---

## 1. Default First-Time Access (Out of the Box)

When you clone PHD Prof and run it for the first time:
- **Default Port**: Standard HTTP port **80** (accessible at `http://127.0.0.1` or `http://localhost`).
- **Port Conflict Fallback**: If port 80 is occupied (e.g. IIS, Skype, Apache), the server automatically falls back to **port 8000** (`http://127.0.0.1:8000`).
- **Why Port 80?**: On a fresh clone, local TLS certificates have not yet been generated in `certs/`, and the custom domain `phdprof.test` has not been mapped into your operating system's `hosts` file. Attempting to access `https://phdprof.test` out of the box will fail because no DNS record exists and no certificate is installed.

---

## 2. Upgrading to Trusted HTTPS on Port 443 (`phdprof.test`)

To enjoy a clean browser experience with the custom local domain `https://phdprof.test` without security warnings or awkward port numbers:

### Automated 1-Click Setup (Recommended)

#### On Windows:
1. Locate `Configura_Dominio_Locale.bat` in the repository root.
2. Double-click it. It will request Administrator elevation (UAC prompt) and automatically:
   - Generate a custom local Root Certificate Authority (CA) and server TLS certificates in `certs/`.
   - Install the Root CA into the **Windows Trusted Root Certification Authorities** store.
   - Append `127.0.0.1 phdprof.test` to `C:\Windows\System32\drivers\etc\hosts`.
   - Flush the Windows DNS resolver cache (`ipconfig /flushdns`).

#### On macOS / Linux:
1. Open Terminal in the repository root.
2. Run the elevated setup script:
   ```bash
   sudo ./scripts/setup_local_domain.sh
   ```
   - On macOS: Installs the Root CA into the System Keychain (`security add-trusted-cert`).
   - On Linux: Registers the Root CA in `/usr/local/share/ca-certificates/` or `/etc/ca-certificates/trust-source/anchors/` and updates system trust anchors.
   - Appends `127.0.0.1 phdprof.test` to `/etc/hosts`.

---

## 3. How the Local CA & TLS Pipeline Works Under the Hood

The setup scripts invoke `scripts/generate_certificates.py`, which leverages Python's `cryptography` library:

1. **Root CA Generation (`certs/ca.crt` & `certs/ca.key`)**:
   - Generates a 4096-bit RSA private key and self-signed X.509 Root CA certificate valid for 10 years (`CN=PHD Prof Local Root CA`).
   - Sets CA basic constraints: `CA:TRUE`, `keyCertSign`, `cRLSign`.
2. **Server Certificate Generation (`certs/server.crt` & `certs/server.key`)**:
   - Generates a 2048-bit RSA private key for the local server.
   - Signs the certificate with the local Root CA.
   - Injects Subject Alternative Names (SAN):
     - `DNS:phdprof.test`
     - `DNS:localhost`
     - `IP:127.0.0.1`
3. **Security Invariant**:
   - Private keys (`certs/*.key`) and certificates (`certs/*.crt`) are strictly **gitignored** and never committed to version control.

---

## 4. DNS TTL & Cache Invalidation

If your browser shows an error or redirects to search after configuring the domain:
- Operating systems and browsers cache negative DNS lookups (NXDOMAIN) for a duration determined by their internal TTL.
- **Flush Windows DNS**:
  ```cmd
  ipconfig /flushdns
  ```
- **Flush Chrome / Edge Host Cache**:
  Open `chrome://net-internals/#dns` (or `edge://net-internals/#dns`) and click **"Clear host cache"**.

---

## 5. Port Conflict Handling (Port 443 vs 8443)

When HTTPS mode is active:
- PHD Prof attempts to bind to standard HTTPS port **443**.
- If port 443 is already bound by another daemon, the runtime automatically falls back to **port 8443** (`https://phdprof.test:8443`).
- You can override the port at any time via CLI or `.env`:
  ```bash
  python pdf_to_notion.py --mode web --port 8443
  ```
