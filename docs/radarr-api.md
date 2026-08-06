# Radarr API

Czecharr uses Radarr API v3 in read-only mode.

## Configuration

Each Radarr integration stores:

- Display name
- Enabled state
- Base URL
- Optional Web URL for browser links when it differs from the API URL
- API key or API-key environment variable name
- Timeout
- TLS verification flag
- Optional path mappings

The API key is sent in the `X-Api-Key` header. It is never added to query strings.

`Base URL` is the endpoint used by the backend API client. `Web URL` is only returned to the frontend for "Open in Radarr" links. This supports deployments where Czecharr reaches Radarr through an internal or API-only reverse proxy while users open Radarr through a different public hostname.

## Read Operations

The client reads movies from `/api/v3/movie` and system status from `/api/v3/system/status` for connection tests.

Movie synchronization stores Radarr movie IDs, movie-file IDs, title metadata, a Radarr web path based on `tmdbId` when available, monitored state, file presence, source paths, relative paths, quality, quality profile, file size, status and poster metadata where available.

Radarr browser links are generated as `/movie/<tmdbId>` when the API returns `tmdbId`, matching Radarr deployments that expose movie details such as `/movie/1273002`. If `tmdbId` is unavailable, Czecharr falls back to the Radarr movie ID rather than a title-based slug.

## Forbidden Operations

Czecharr does not rename, delete, search, monitor or otherwise mutate Radarr records. The integration client only exposes safe read methods.

## Connection Test

The connection test validates URL reachability, authentication, and basic system information. Error responses are structured and redacted so API keys and credential-bearing URLs are not exposed.
