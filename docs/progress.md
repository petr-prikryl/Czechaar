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

- [x] Integration model
- [x] Radarr API client
- [x] Sonarr API client
- [x] Connection test endpoints
- [x] Secret-safe settings API
- [x] Settings UI
- [x] Mocked tests

## Stage 3: Library Synchronization

- [x] Radarr synchronization
- [x] Sonarr synchronization
- [x] Multi-episode file links
- [x] Stale records
- [x] Pagination and filters
- [x] Synchronization history
- [x] Tests

## Stage 4: Path Safety and ffprobe

- [x] Path mappings
- [x] Allowed media roots
- [x] ffprobe subprocess runner
- [x] Audio stream parser
- [x] Czech-audio detection
- [x] Analyzer versioning
- [x] Tests

## Stage 5: Scan Engine

- [x] Persistent scan runs
- [x] Bounded concurrency
- [x] Progress and history
- [x] Cancellation
- [x] Cache and fingerprinting
- [x] Restart recovery
- [x] Scheduled scans
- [x] Tests

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
