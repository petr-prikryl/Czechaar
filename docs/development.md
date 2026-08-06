# Development

## Requirements

- Python 3.12
- Node.js 20 or newer
- npm
- Docker for image validation
- ffmpeg/ffprobe for local media scan testing

## Setup

```sh
make install
```

Run backend and frontend development servers in separate shells:

```sh
make backend-dev
make frontend-dev
```

The backend listens on `http://localhost:8080/api/v1`. The Vite development server proxies API requests.

## Checks

```sh
make format
make lint
make typecheck
make test
make build
make docker-build
```

Backend tests mock Radarr, Sonarr and `ffprobe` behavior. Frontend tests use Vitest and React Testing Library.

## Migrations

Create Alembic migrations under `backend/alembic/versions` and commit them. Runtime startup applies migrations and fails clearly if migration cannot complete.

```sh
make migrate
```

## Demo Mode

Set `CZECHARR_DEMO_MODE=true` to seed deterministic demo data at startup. Demo mode is disabled by default and should not be enabled for normal production use.
