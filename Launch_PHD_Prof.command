#!/usr/bin/env bash
# ==============================================================================
# Launch_PHD_Prof.command
# One-click desktop launcher for macOS (Finder) and Linux.
#
# Equivalent behavior to Launch_PHD_Prof.vbs on Windows:
# 1. Resolves canonical project directory.
# 2. Discovers Python 3 interpreter (local venv, Homebrew Apple Silicon/Intel, PATH).
# 3. Launches FastAPI server in background detached from terminal.
# 4. Automatically opens default browser to https://phdprof.test (or http://127.0.0.1).
# 5. Silently closes Terminal.app window spawned by Finder.
# 6. On browser tab close, the internal watchdog shuts down the Python process.
# ==============================================================================

# Canonical script directory resolution (handles symlinks and whitespace)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Dynamic Python 3 interpreter resolution
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
    echo "  [ERROR] Python 3 was not found on this system."
    echo "  Install Python from https://www.python.org/downloads/"
    echo "  or via Homebrew: brew install python"
    echo "=========================================================="
    read -n 1 -s -r -p "Press any key to close..."
    echo ""
    exit 1
fi

# Auto-copy .env.example if .env does not exist
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
fi

# Launch background server detached from terminal
# Output is routed to phd_prof.log (ignored in .gitignore)
nohup "$PYTHON_BIN" pdf_to_notion.py --mode web > "$SCRIPT_DIR/phd_prof.log" 2>&1 &

# On macOS, silently close Terminal window spawned by Finder
if [ "$(uname)" = "Darwin" ]; then
    osascript -e '
    tell application "Terminal"
        repeat with w in (every window)
            if name of w contains "Launch_PHD_Prof" then
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
