# Sonarr API

Czecharr uses Sonarr API v3 in read-only mode.

## Configuration

Each Sonarr integration stores:

- Display name
- Enabled state
- Base URL
- Optional Web URL for browser links when it differs from the API URL
- API key or API-key environment variable name
- Timeout
- TLS verification flag
- Optional path mappings

The API key is sent in the `X-Api-Key` header. It is never added to query strings.

`Base URL` is the endpoint used by the backend API client. `Web URL` is only returned to the frontend for "Open in Sonarr" links. This supports deployments where Czecharr reaches Sonarr through an internal or API-only reverse proxy while users open Sonarr through a different public hostname.

## Read Operations

The client reads series from `/api/v3/series`, episodes from `/api/v3/episode`, episode files from `/api/v3/episodefile`, and system status from `/api/v3/system/status`.

Synchronization stores series titles, episode titles, Sonarr series web paths when the API provides a title slug, season and episode numbers, absolute episode numbers when available, monitored state, file presence, air dates, source paths, relative paths, quality, file size and poster metadata.

Sonarr multi-episode files are represented through `media_item_file_links`, so one episode file may be linked to more than one episode item.

## Forbidden Operations

Czecharr does not rename, delete, search, monitor or otherwise mutate Sonarr records. The integration client only exposes safe read methods.

## Connection Test

The connection test validates reachability, authentication and basic system information. Errors are redacted before they are returned to the browser.
