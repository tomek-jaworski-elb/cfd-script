#!/usr/bin/env bash
# Start the Streamlit app in the background (Linux/WSL). Windows equivalent: start.ps1
set -euo pipefail

PORT="${1:-8501}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT/streamlit.pid"
LOG_FILE="$ROOT/streamlit.log"
ERR_FILE="$ROOT/streamlit.err.log"
STREAMLIT_BIN="$ROOT/venv_wsl_test/bin/streamlit"

if [ -f "$PID_FILE" ]; then
    existing_pid="$(cat "$PID_FILE")"
    if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
        echo "Already running (PID $existing_pid) at http://localhost:$PORT"
        exit 0
    fi
fi

if [ ! -x "$STREAMLIT_BIN" ]; then
    echo "venv not found at $STREAMLIT_BIN - run: python3 -m venv venv_wsl_test && venv_wsl_test/bin/pip install -r requirements.txt"
    exit 1
fi

cd "$ROOT"
# setsid makes the streamlit process its own session/group leader (pgid == pid),
# so stop.sh can kill the whole tree with `kill -- -PID`.
# fileWatcherType none: the repo lives on a Windows drive mounted into WSL
# (DrvFs/9p) - Streamlit's default watcher takes ~50s to initialize there,
# stalling the very first page load.
setsid "$STREAMLIT_BIN" run app.py --server.headless true --server.port "$PORT" \
    --server.fileWatcherType none \
    >"$LOG_FILE" 2>"$ERR_FILE" </dev/null &
proc_pid=$!
echo "$proc_pid" >"$PID_FILE"

deadline=$((SECONDS + 120))
while [ "$SECONDS" -lt "$deadline" ]; do
    if curl -s -o /dev/null "http://localhost:$PORT"; then
        echo "App running at http://localhost:$PORT (PID $proc_pid)"
        exit 0
    fi
    sleep 1
done

echo "Timed out waiting for app to respond. Check $LOG_FILE / $ERR_FILE"
exit 1
