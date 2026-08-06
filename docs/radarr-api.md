# Radarr API

Czecharr uses Radarr API v3 in read-only mode.

## Configuration

Each Radarr integration stores:

- Display name
- Enabled state
- Base URL
- API key or API-key environment variable name
- Timeout
- TLS verification flag
- Optional path mappings

The API key is sent in the `X-Api-Key` header. It is never added to query strings.

## Read Operations

The client reads movies from `/api/v3/movie` and system status from `/api/v3/system/status` for connection tests.

Movie synchronization stores Radarr movie IDs, movie-file IDs, title metadata, monitored state, file presence, source paths, relative paths, quality, quality profile, file size, status and poster metadata where available.

## Forbidden Operations

Czecharr does not rename, delete, search, monitor or otherwise mutate Radarr records. The integration client only exposes safe read methods.

## Connection Test

The connection test validates URL reachability, authentication, and basic system information. Error responses are structured and redacted so API keys and credential-bearing URLs are not exposed.
