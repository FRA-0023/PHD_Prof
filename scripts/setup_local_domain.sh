#!/usr/bin/env bash
# ==============================================================================
# setup_local_domain.sh
# Configures local domain 'phdprof.test' pointing to 127.0.0.1 in /etc/hosts (macOS / Linux).
# ==============================================================================

set -e

HOSTS_FILE="/etc/hosts"
DOMAIN="phdprof.test"
IP="127.0.0.1"

if grep -qE "^[[:space:]]*${IP}[[:space:]]+${DOMAIN}" "$HOSTS_FILE" 2>/dev/null; then
    echo "[OK] ${DOMAIN} is already present in ${HOSTS_FILE}."
else
    echo "[*] Adding ${DOMAIN} to ${HOSTS_FILE} (requires sudo)..."
    echo -e "\n${IP}\t${DOMAIN}" | sudo tee -a "$HOSTS_FILE" > /dev/null
    echo "[OK] Successfully added ${DOMAIN} to ${HOSTS_FILE}."
fi

# Generate certificates if missing
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ ! -f "$PROJECT_ROOT/certs/server.crt" ]; then
    echo "[*] Generating local SSL certificates..."
    python3 "$SCRIPT_DIR/generate_certificates.py" || python "$SCRIPT_DIR/generate_certificates.py"
fi

if [ -f "$PROJECT_ROOT/certs/ca.crt" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "[*] Adding Root CA to macOS System Keychain..."
        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$PROJECT_ROOT/certs/ca.crt" 2>/dev/null || true
        echo "[OK] Root CA added to macOS Keychain."
    elif [ -d "/usr/local/share/ca-certificates" ]; then
        echo "[*] Adding Root CA to Linux system trust store (Debian/Ubuntu)..."
        sudo cp "$PROJECT_ROOT/certs/ca.crt" /usr/local/share/ca-certificates/phdprof_ca.crt
        sudo update-ca-certificates >/dev/null 2>&1 || true
        echo "[OK] Root CA added to Linux certificates."
    fi
fi

# Flush DNS cache depending on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder 2>/dev/null || true
    echo "[OK] macOS DNS cache flushed."
elif command -v resolvectl >/dev/null 2>&1; then
    sudo resolvectl flush-caches || true
    echo "[OK] Linux DNS cache flushed."
fi

echo "Done! You can now access https://${DOMAIN}/"
