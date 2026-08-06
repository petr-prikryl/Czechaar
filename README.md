# Czecharr

Czecharr is a self-hosted, read-only Radarr and Sonarr companion for finding movie and episode files that do not contain Czech audio.

The application synchronizes Radarr and Sonarr metadata, maps remote library paths to paths visible inside the Czecharr container, analyzes audio streams with `ffprobe`, caches scan results and presents missing Czech audio in a responsive web interface.

## Current Status

This repository is being implemented in staged production checkpoints. The current foundation includes:

- FastAPI backend skeleton with versioned health and readiness endpoints.
- SQLAlchemy and Alembic baseline.
- React, TypeScript and Vite frontend shell.
- Czech and English localization foundation.
- Root developer commands for install, lint, type checking, tests and builds.

## Security Model

Czecharr intentionally does not implement user authentication. Deploy it only behind a trusted reverse proxy, VPN, firewall or IP allowlist. API keys are treated as sensitive configuration and must not be logged, committed or exposed to browsers after saving.

The `/config` directory stores persistent state, including the SQLite database. Protect it with appropriate filesystem permissions and include it in backups.

## Development

```sh
make install
make backend-dev
make frontend-dev
```

Backend API defaults to `http://localhost:8080/api/v1`. The Vite development server proxies API calls during frontend development.

## License

Czecharr is released under the MIT License.
