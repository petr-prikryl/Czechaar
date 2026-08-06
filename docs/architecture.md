# Architecture

Czecharr is a monorepo with a Python backend and React frontend.

## Backend

The backend uses FastAPI, Pydantic 2, SQLAlchemy 2, Alembic and SQLite. API routes live under `backend/app/api/v1`. Business logic is separated into services for Arr clients, synchronization, path mapping, `ffprobe` inspection, scan execution, scheduling and demo data.

SQLite is the default database and is stored in `/config/czecharr.db` in Docker. Alembic migrations are applied by `scripts/start.sh` before Uvicorn starts.

The initial production image runs one Uvicorn process. This is intentional because the scan runner and scheduler are in-process and should not be duplicated by multiple workers.

## Frontend

The frontend uses React, TypeScript, Vite, Tailwind CSS, TanStack Query and TanStack Table. It is built in a Docker build stage and served by FastAPI from `frontend/dist`.

Visible UI strings are routed through the localization layer in `frontend/src/i18n/messages.ts`. Czech is the default locale; English is available in Settings.

## Data Flow

1. Integrations are configured for Radarr and Sonarr.
2. Library sync retrieves read-only metadata and media file paths.
3. Path mappings translate remote paths to container-visible paths.
4. Allowed media roots validate mapped local paths.
5. The scan engine runs bounded `ffprobe` jobs.
6. Audio stream metadata is normalized and Czech audio is detected.
7. Results are cached using path, size, modification time and analyzer version.
8. The UI queries dashboard, media, scan and settings APIs.

## Security Boundaries

Czecharr has no authentication by design. It must be protected by a reverse proxy, VPN, firewall or IP allowlist. API keys are stored in the SQLite database or referenced through environment variables. Ordinary API responses report only whether an API key is configured.

Media paths are never accepted directly from anonymous API callers for scanning. Scan paths are derived from synchronized media records, mapped through configured prefixes and validated against explicit allowed roots.
