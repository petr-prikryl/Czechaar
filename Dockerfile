# syntax=docker/dockerfile:1

ARG NODE_VERSION=20
ARG PYTHON_VERSION=3.12

FROM node:${NODE_VERSION}-bookworm-slim AS frontend-build
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:${PYTHON_VERSION}-slim AS backend-build
WORKDIR /src
COPY backend ./backend
RUN python -m pip install --upgrade pip \
    && python -m pip wheel --wheel-dir /wheels ./backend

FROM python:${PYTHON_VERSION}-slim AS runtime

ARG CZECHARR_GIT_COMMIT=unknown
ARG CZECHARR_BUILD_DATE=unknown

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CZECHARR_CONFIG_DIR=/config \
    CZECHARR_DATABASE_URL=sqlite:////config/czecharr.db \
    CZECHARR_HOST=0.0.0.0 \
    CZECHARR_PORT=8080 \
    CZECHARR_LOG_LEVEL=INFO \
    CZECHARR_FFPROBE_PATH=ffprobe \
    CZECHARR_FFPROBE_TIMEOUT=60 \
    CZECHARR_SCAN_CONCURRENCY=2 \
    CZECHARR_STALE_RETENTION_DAYS=30 \
    CZECHARR_STATIC_DIR=/app/frontend/dist \
    CZECHARR_GIT_COMMIT=${CZECHARR_GIT_COMMIT} \
    CZECHARR_BUILD_DATE=${CZECHARR_BUILD_DATE}

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system czecharr \
    && useradd --system --gid czecharr --home-dir /config --shell /usr/sbin/nologin czecharr

WORKDIR /app/backend

COPY --from=backend-build /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels

COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY --from=frontend-build /src/frontend/dist /app/frontend/dist
COPY scripts/start.sh /usr/local/bin/czecharr-start

RUN chmod +x /usr/local/bin/czecharr-start \
    && mkdir -p /config \
    && chown -R czecharr:czecharr /app /config

USER czecharr

EXPOSE 8080
VOLUME ["/config"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/api/v1/health || exit 1

ENTRYPOINT ["czecharr-start"]
