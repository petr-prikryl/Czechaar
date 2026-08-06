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
docker login git.prikryl.cc
docker compose pull
docker compose up -d
```

Open `http://localhost:8787`.

The default Compose file uses the published image and mounts:

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

Adjust the media paths for your host before scanning. Media mounts should stay read-only.

The container prepares the bind-mounted `./config` directory at startup and then drops privileges before running migrations and the web server. If you override the container user in Compose or your platform blocks ownership changes on bind mounts, make sure the host config directory is writable by the runtime user.

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
CZECHARR_STALE_RETENTION_DAYS=30
```

Do not place Radarr or Sonarr API keys in Compose files unless the file is protected and never committed. Prefer entering them in the Settings UI or supplying protected environment variables where your deployment platform supports that.

## Deployment Notes

The production container runs `scripts/start.sh`, reports the current Alembic migration state, applies pending migrations and then launches a single Uvicorn process. A single process is intentional for the first release because scans and the scheduler are in-process.

More details:

- [Architecture](docs/architecture.md)
- [Radarr API](docs/radarr-api.md)
- [Sonarr API](docs/sonarr-api.md)
- [Path mapping](docs/path-mapping.md)
- [Scanning](docs/scanning.md)
- [Docker deployment](docs/docker.md)
- [Reverse proxy examples](docs/reverse-proxy.md)
- [Development](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Implementation plan](docs/implementation-plan.md)

## Security Model

Czecharr intentionally does not implement user authentication. Deploy it only behind a trusted reverse proxy, VPN, firewall or IP allowlist. API keys are treated as sensitive configuration and must not be logged, committed or exposed to browsers after saving.

The `/config` directory stores persistent state, including the SQLite database. Protect it with appropriate filesystem permissions, keep it writable by the Czecharr container and include it in backups.

Back up `/config` before major upgrades. Do not expose Czecharr directly to the internet.

## Backup and Restore

Backups should include the full `/config` directory, especially `czecharr.db`. Stop the container or make an SQLite-safe backup before copying the database.

Restore by stopping Czecharr, replacing `/config` with the backup contents, then starting the container again. Startup migrations will apply any newer schema changes.

## Radarr and Sonarr Setup

Create an API key in each Arr application and enter it in Czecharr Settings. Czecharr uses the `X-Api-Key` header and performs only read operations. Configure path mappings when the paths reported by Radarr/Sonarr differ from the paths mounted into Czecharr.

Use **Base URL** for the API endpoint Czecharr should call. Use **Web URL** when the browser should open a different public Radarr/Sonarr host from the Czecharr UI. For example, the API can use `https://prxrdr.prikryl.cc` while Web URL points to `https://radarr.prikryl.cc`; Sonarr can be configured the same way with its own public host.

## Known Limitations

- No built-in authentication; protect the app externally.
- The first release runs one backend process because the scheduler and scan engine are in-process.
- Demo integrations are disabled and use `.invalid` hostnames; they are for UI development data only.

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
