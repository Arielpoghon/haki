#!/usr/bin/env bash
# Haki — one-command demo. Fresh clone -> dashboard running.
# Usage: ./demo.sh            (creates venv if missing, installs deps, tests, serves)
#        ./demo.sh --no-test  (skip the test run, just serve)
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "[haki] creating virtualenv…"
  python3 -m venv .venv
fi

if ! "$PY" -c "import fastapi, yaml, httpx" >/dev/null 2>&1; then
  echo "[haki] installing pinned requirements…"
  "$PY" -m pip install -q -r requirements.txt
fi

if [ "${1:-}" != "--no-test" ]; then
  echo "[haki] running the test suite (the verdict matrix is the spec)…"
  "$PY" -m pytest -q
fi

PORT="${PORT:-8000}"
echo
echo "[haki] ✔ tests green"
echo "[haki] Dashboard : http://127.0.0.1:${PORT}"
echo "[haki] API docs  : http://127.0.0.1:${PORT}/docs"
echo "[haki] Audit view: http://127.0.0.1:${PORT}/audit"
echo
exec "$PY" -m uvicorn api.main:app --port "$PORT"
