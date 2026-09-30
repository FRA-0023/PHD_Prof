#!/usr/bin/env bash
# ==============================================================================
# Avvia_PHD_Prof.command
# Launcher one-click per macOS (Finder) e Linux.
#
# Comportamento equivalente ad Avvia_PHD_Prof.vbs su Windows:
# 1. Risolve la directory del progetto.
# 2. Individua l'interprete Python 3 (venv locale, Homebrew Apple Silicon/Intel, PATH).
# 3. Avvia il server FastAPI in background disaccoppiato dal terminale.
# 4. Apre il browser predefinito a http://127.0.0.1:8000.
# 5. Chiude automaticamente la finestra di Terminal.app creata da Finder.
# 6. Alla chiusura del browser, il watchdog interno termina il processo Python.
# ==============================================================================

# Risoluzione canonica della directory dello script (gestisce symlink e spazi)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Risoluzione dinamica interprete Python 3
PYTHON_BIN=""
if [ -x "$SCRIPT_DIR/.venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python3"
elif [ -x "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
elif [ -x "/usr/local/bin/python3" ]; then
    PYTHON_BIN="/usr/local/bin/python3"
elif [ -x "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" ]; then
    PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
elif [ -x "/usr/bin/python3" ]; then
    PYTHON_BIN="/usr/bin/python3"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "=========================================================="
    echo "  [ERRORE] Python 3 non e' stato trovato su questo sistema."
    echo "  Installa Python da https://www.python.org/downloads/"
    echo "  oppure tramite Homebrew: brew install python"
    echo "=========================================================="
    read -n 1 -s -r -p "Premi un tasto per chiudere..."
    echo ""
    exit 1
fi

# Copia automatica .env.example se .env non esiste
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
fi

# Avvio del server in background disaccoppiato dal terminale
# Il log viene indirizzato su phd_prof.log (ignorato da .gitignore)
nohup "$PYTHON_BIN" pdf_to_notion.py --mode web > "$SCRIPT_DIR/phd_prof.log" 2>&1 &

# Su macOS, chiusura silenziosa della finestra di Terminal aperta da Finder
if [ "$(uname)" = "Darwin" ]; then
    osascript -e '
    tell application "Terminal"
        repeat with w in (every window)
            if name of w contains "Avvia_PHD_Prof" then
                close w saving no
            end if
        end repeat
        if (count of windows) is 0 then
            quit
        end if
    end tell
    ' >/dev/null 2>&1 &
fi

exit 0
