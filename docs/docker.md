# Docker Deployment

Czecharr is packaged as one production container that serves the FastAPI backend and the built React frontend on port `8080`.

## Runtime State

Persistent state lives in `/config`. Back up this directory before upgrades because it contains the SQLite database.

Example mounts:

```yaml
volumes:
  - ./config:/config
  - /mnt/media/movies:/movies:ro
  - /mnt/media/tv:/tv:ro
```

Media mounts should be read-only. Czecharr only needs to read files for `ffprobe`.

## Build

```sh
docker build -t czecharr:local .
```

The image installs `ffmpeg`, which provides `ffprobe`, and runs as a non-root `czecharr` user.

Common environment overrides:

```text
CZECHARR_FFPROBE_PATH=ffprobe
CZECHARR_FFPROBE_TIMEOUT=60
CZECHARR_SCAN_CONCURRENCY=2
CZECHARR_STALE_RETENTION_DAYS=30
CZECHARR_SCHEDULED_SCAN_ENABLED=false
CZECHARR_SCHEDULED_SCAN_INTERVAL_MINUTES=1440
```

Optional build metadata:

```sh
docker build \
  --build-arg CZECHARR_GIT_COMMIT="$(git rev-parse --short HEAD)" \
  --build-arg CZECHARR_BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -t czecharr:local .
```

## Compose

```sh
docker compose up --build -d
```

The default Compose file exposes Czecharr at `http://localhost:8787`.

## Startup

The container runs `scripts/start.sh`. Startup reports the current Alembic migration state, applies migrations, then launches one Uvicorn process. A single process avoids duplicate in-process schedulers and scan engines.

## Healthcheck

Docker and Compose use:

```text
GET /api/v1/health
```

Readiness is available at:

```text
GET /api/v1/ready
```
