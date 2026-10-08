#!/usr/bin/env bash
# ==============================================================================
# Launch_PHD_Prof.sh
# Standard POSIX shell entrypoint for Unix / macOS / Linux environments.
# Delegates execution to Launch_PHD_Prof.command while preserving arguments and environment.
# ==============================================================================
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

exec "$SCRIPT_DIR/Launch_PHD_Prof.command" "$@"
