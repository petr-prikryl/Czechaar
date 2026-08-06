# Czecharr

Czecharr is a self-hosted, read-only Radarr and Sonarr companion for finding movie and episode files that do not contain Czech audio.

The application synchronizes Radarr and Sonarr metadata, maps remote library paths to paths visible inside the Czecharr container, analyzes audio streams with `ffprobe`, caches scan results and presents missing Czech audio in a responsive web interface.

## Features

- Read-only Radarr API v3 and Sonarr API v3 integrations.
- Multiple integrations with API-key redaction in ordinary responses.
- Ordered path mappings from Radarr/Sonarr paths to container-visible paths.
- Explicit allowed media roots before any `ffprobe` execution.
- Audio-stream inspection with `ffprobe` and Czech-audio detection from stream metadata.
- Persistent scan runs, cancellation, cache reuse and scan history.
- Responsive Czech/English web interface for dashboards, missing audio, movies, series, settings and scan history.
- One production Docker container serving both the frontend and backend on port `8080`.

## Quick Start

```sh
docker compose up --build -d
```

Open `http://localhost:8787`.

The default Compose file mounts:

```yaml
volumes:
  - ./config:/config
  - /mnt/media/movies:/movies:ro
  - /mnt/media/tv:/tv:ro
```

Adjust the media paths for your host before scanning. Media mounts should stay read-only.

## Configuration

Important environment variables:

```text
TZ=Europe/Prague
CZECHARR_CONFIG_DIR=/config
CZECHARR_DATABASE_URL=sqlite:////config/czecharr.db
CZECHARR_HOST=0.0.0.0
CZECHARR_PORT=8080
CZECHARR_LOG_LEVEL=INFO
CZECHARR_FFPROBE_PATH=ffprobe
CZECHARR_FFPROBE_TIMEOUT=60
CZECHARR_SCAN_CONCURRENCY=2
```

Do not place Radarr or Sonarr API keys in Compose files unless the file is protected and never committed. Prefer entering them in the Settings UI or supplying protected environment variables where your deployment platform supports that.

## Deployment Notes

The production container runs `scripts/start.sh`, reports the current Alembic migration state, applies pending migrations and then launches a single Uvicorn process. A single process is intentional for the first release because scans and the scheduler are in-process.

More details:

- [Docker deployment](docs/docker.md)
- [Reverse proxy examples](docs/reverse-proxy.md)
- [Implementation plan](docs/implementation-plan.md)

## Security Model

Czecharr intentionally does not implement user authentication. Deploy it only behind a trusted reverse proxy, VPN, firewall or IP allowlist. API keys are treated as sensitive configuration and must not be logged, committed or exposed to browsers after saving.

The `/config` directory stores persistent state, including the SQLite database. Protect it with appropriate filesystem permissions and include it in backups.

Back up `/config` before major upgrades. Do not expose Czecharr directly to the internet.

## Development

```sh
make install
make backend-dev
make frontend-dev
```

Backend API defaults to `http://localhost:8080/api/v1`. The Vite development server proxies API calls during frontend development.

Common commands:

```sh
make format
make lint
make typecheck
make test
make build
make docker-build
```

## License

Czecharr is released under the MIT License.
