#!/usr/bin/env bash
# ==============================================================================
# Avvia_PHD_Prof.sh
# Entry point standard shell POSIX per ambienti Unix / macOS / Linux.
# Deferisce l'esecuzione ad Avvia_PHD_Prof.command preservando argomenti ed env.
# ==============================================================================
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

exec "$SCRIPT_DIR/Avvia_PHD_Prof.command" "$@"
