# Docker Deployment

Czecharr is packaged as one production container that serves the FastAPI backend and the built React frontend on port `8080`.

## Runtime State

Persistent state lives in `/config`. Back up this directory before upgrades because it contains the SQLite database. The container entrypoint prepares this directory when it starts and then runs the application as the non-root `czecharr` user.

Example mounts:

```yaml
volumes:
  - ./config:/config
  - /mnt/media/movies:/movies:ro
  - /mnt/media/tv:/tv:ro
```

Media mounts should be read-only. Czecharr only needs to read files for `ffprobe`.

If you override the container user, create the host config directory yourself and make it writable by that user before startup. Otherwise Alembic cannot open `/config/czecharr.db` during migrations.

## Build

```sh
docker build -t czecharr:local .
```

The image installs `ffmpeg`, which provides `ffprobe`. Startup begins with a small root entrypoint so bind-mounted `/config` directories can be prepared, then migrations and the web server run as the non-root `czecharr` user.

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
docker login git.prikryl.cc
docker compose pull
docker compose up -d
```

The default Compose file exposes Czecharr at `http://localhost:8787`.

Minimal deployment service:

```yaml
services:
  czecharr:
    image: git.prikryl.cc/petrprikryl/czecharr:latest
    container_name: czecharr
    environment:
      TZ: Europe/Prague
      CZECHARR_CONFIG_DIR: /config
      CZECHARR_DATABASE_URL: sqlite:////config/czecharr.db
    volumes:
      - ./config:/config
      - /mnt/media/movies:/movies:ro
      - /mnt/media/tv:/tv:ro
    ports:
      - "8787:8080"
    restart: unless-stopped
```

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
