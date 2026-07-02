#!/usr/bin/env bash
# Stop the Streamlit app started by start.sh (Linux/WSL). Windows equivalent: stop.ps1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT/streamlit.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "No PID file found - app not running (or not started via start.sh)."
    exit 0
fi

pid="$(cat "$PID_FILE")"
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    # negative PID targets the whole process group (see setsid in start.sh)
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid"
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid"
    fi
    echo "Stopped process $pid (and children)"
else
    echo "Process $pid not found (already stopped)."
fi

rm -f "$PID_FILE"
