#!/usr/bin/env bash
set -euo pipefail
: "${UVICORN_WORKERS:=2}"
: "${UVICORN_PORT:=8000}"
# Bind all + headers detrás de Nginx Proxy Manager
exec uvicorn app.main:app \
  --host 0.0.0.0 --port "${UVICORN_PORT}" \
  --workers "${UVICORN_WORKERS}" --proxy-headers --forwarded-allow-ips="*"
