# Czecharr Implementation Plan

## Repository State

- Working directory: `C:\Users\prikryl\Documents\repos\Czecharr`
- Required remote: `https://git.prikryl.cc/petrprikryl/Czecharr.git`
- Remote HEAD: unavailable after fetch, indicating an empty remote repository.
- Default branch selected: `main`

## Product Scope

Czecharr is a self-hosted read-only media-audit application for Radarr and Sonarr libraries. It imports movies, series, episodes, and media files, maps upstream paths into container-visible paths, inspects audio streams with `ffprobe`, caches results, and shows files that do not contain Czech audio.

## Implementation Stages

1. Repository structure, backend/frontend foundations, health checks, localization, test and lint tooling.
2. Radarr/Sonarr integration models, read-only API clients, connection tests, secret-safe settings API and UI.
3. Library synchronization for movies, series, episodes, media files, multi-episode links, stale records, pagination and filters.
4. Path mappings, allowed media roots, ffprobe runner, parser, Czech-audio detection, analyzer versioning and related tests.
5. Persistent scan engine, bounded concurrency, cancellation, cache reuse, restart recovery, scheduled scans and progress reporting.
6. Main responsive web interface, dashboard, missing-audio table, movies, series, scan history, details, ignored items and CSV export.
7. Production Docker image, startup migrations, Compose files, healthcheck and reverse-proxy examples.
8. Final hardening, demo mode, documentation, full checks, Docker build verification and final push.

## Proposed Directory Tree

```text
Czecharr/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── integrations/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── workers/
│   │   └── main.py
│   ├── tests/
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── i18n/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── types/
│   │   └── utils/
│   ├── tests/
│   ├── package.json
│   └── vite.config.ts
├── docs/
├── scripts/
├── config/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.example.yml
├── .dockerignore
├── .editorconfig
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## Design Decisions

- Backend and database support multiple Radarr and Sonarr integrations from the first migration.
- The API never returns stored API keys, only configured-state metadata.
- Library synchronization and ffprobe scanning are separate operations.
- Media paths are only scanned when they originate from synchronized upstream records and resolve inside an explicitly allowed media root.
- Scans run in a single-process home-server model to avoid duplicate schedulers and duplicate ffprobe workers.
- SQLite state lives under `/config`; media mounts are read-only in Docker examples.
- Czech and English localization are treated as first-class frontend data, with Czech as the default language.
