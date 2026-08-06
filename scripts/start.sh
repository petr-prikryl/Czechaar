#!/usr/bin/env sh
set -eu

cd /app/backend

echo "Czecharr startup: current database migration state"
python -m alembic current

echo "Czecharr startup: applying database migrations"
python -m alembic upgrade head

echo "Czecharr startup: launching API and web server"
exec python -m uvicorn app.main:app \
  --host "${CZECHARR_HOST:-0.0.0.0}" \
  --port "${CZECHARR_PORT:-8080}" \
  --proxy-headers \
  --forwarded-allow-ips "${CZECHARR_FORWARDED_ALLOW_IPS:-*}"
