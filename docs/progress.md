# Czecharr Progress Checklist

## Stage 0: Repository Inspection and Plan

- [x] Confirmed workspace repository state.
- [x] Configured required `origin` remote.
- [x] Fetched remote state.
- [x] Selected `main` because the remote has no existing default branch.
- [x] Added implementation plan.
- [x] Added progress checklist.

## Stage 1: Project Foundation

- [x] Backend skeleton
- [x] Frontend skeleton
- [x] SQLite configuration and SQLAlchemy base
- [x] Alembic setup
- [x] Health and readiness endpoints
- [x] Frontend shell and localization foundation
- [x] Test, lint and formatting infrastructure
- [x] Docker development setup
- [x] Initial documentation

## Stage 2: Integrations

- [ ] Integration model
- [ ] Radarr API client
- [ ] Sonarr API client
- [ ] Connection test endpoints
- [ ] Secret-safe settings API
- [ ] Settings UI
- [ ] Mocked tests

## Stage 3: Library Synchronization

- [ ] Radarr synchronization
- [ ] Sonarr synchronization
- [ ] Multi-episode file links
- [ ] Stale records
- [ ] Pagination and filters
- [ ] Synchronization history
- [ ] Tests

## Stage 4: Path Safety and ffprobe

- [ ] Path mappings
- [ ] Allowed media roots
- [ ] ffprobe subprocess runner
- [ ] Audio stream parser
- [ ] Czech-audio detection
- [ ] Analyzer versioning
- [ ] Tests

## Stage 5: Scan Engine

- [ ] Persistent scan runs
- [ ] Bounded concurrency
- [ ] Progress and history
- [ ] Cancellation
- [ ] Cache and fingerprinting
- [ ] Restart recovery
- [ ] Scheduled scans
- [ ] Tests

## Stage 6: Main Web Interface

- [ ] Dashboard
- [ ] Missing Czech Audio page
- [ ] Movies page and details
- [ ] Series page and season expansion
- [ ] Scan history page
- [ ] Ignored items
- [ ] CSV export
- [ ] Responsive layout
- [ ] Frontend tests

## Stage 7: Production Docker Deployment

- [ ] Multi-stage Dockerfile
- [ ] Runtime ffmpeg/ffprobe
- [ ] Startup migrations
- [ ] Non-root runtime
- [ ] Docker Compose files
- [ ] Healthcheck
- [ ] Reverse-proxy examples

## Stage 8: Final Hardening

- [ ] Security review
- [ ] API-key redaction review
- [ ] Path traversal review
- [ ] Subprocess safety review
- [ ] Demo mode
- [ ] Version metadata
- [ ] Complete documentation
- [ ] Full checks
- [ ] Docker image build
- [ ] Final push verification
