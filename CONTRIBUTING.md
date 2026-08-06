# Contributing to Czecharr

## Development

1. Install Python 3.12, Node.js 20 or newer, Docker, ffmpeg and ffprobe.
2. Run `make install`.
3. Start the backend with `make backend-dev`.
4. Start the frontend with `make frontend-dev`.

## Quality Gates

Before opening a change, run:

```sh
make format
make lint
make typecheck
make test
make build
```

Never commit `.env`, local database files, media files, API keys or generated runtime data from `/config`.
