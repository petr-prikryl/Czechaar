#!/usr/bin/env sh
set -eu

APP_USER="${CZECHARR_RUN_USER:-czecharr}"
APP_GROUP="${CZECHARR_RUN_GROUP:-czecharr}"
CONFIG_DIR="${CZECHARR_CONFIG_DIR:-/config}"

if [ "$(id -u)" = "0" ]; then
  mkdir -p "${CONFIG_DIR}"
  if ! chown -R "${APP_USER}:${APP_GROUP}" "${CONFIG_DIR}"; then
    echo "Czecharr startup: could not change ownership of ${CONFIG_DIR}; checking runtime writability" >&2
  fi
  if ! gosu "${APP_USER}:${APP_GROUP}" test -w "${CONFIG_DIR}"; then
    echo "Czecharr startup: config directory ${CONFIG_DIR} is not writable by ${APP_USER}" >&2
    exit 1
  fi
  exec gosu "${APP_USER}:${APP_GROUP}" "$0" "$@"
fi

if [ ! -d "${CONFIG_DIR}" ]; then
  echo "Czecharr startup: config directory ${CONFIG_DIR} does not exist" >&2
  exit 1
fi

if [ ! -w "${CONFIG_DIR}" ]; then
  echo "Czecharr startup: config directory ${CONFIG_DIR} is not writable by $(id -un)" >&2
  exit 1
fi

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
