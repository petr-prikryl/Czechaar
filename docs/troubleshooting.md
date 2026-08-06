# Troubleshooting

## The UI Loads But Tables Are Empty

Create at least one Radarr or Sonarr integration, run a library synchronization, configure path mappings and allowed media roots, then start a scan.

## Connection Test Fails

Check the base URL, API key, TLS setting and network routing from the Czecharr container. API keys are sent through `X-Api-Key`; do not add them to URLs.

## Paths Cannot Be Mapped

Use Settings -> Path mappings to test a sample path returned by Radarr or Sonarr. Ensure the remote prefix matches a complete path prefix and the local prefix points to a mounted path inside the Czecharr container.

## Path Outside Allowed Roots

Add the local media root in Settings. Czecharr will not run `ffprobe` outside explicitly configured roots.

## ffprobe Not Available

The Docker image includes `ffmpeg`, which provides `ffprobe`. For local development, install ffmpeg and set `CZECHARR_FFPROBE_PATH` if the executable is not on `PATH`.

## Database Issues

The SQLite database is stored under `/config`. Back up `/config` before upgrades. If startup migrations fail, inspect container logs and do not delete the database unless you have a verified backup.

`sqlite3.OperationalError: unable to open database file` means `/config` is missing or not writable inside the container. With the standard image, keep the default container user so the entrypoint can prepare the bind mount before dropping privileges. If you override `user:` in Compose, create the host directory and set permissions for that user before starting Czecharr.

## Reverse Proxy Access

Czecharr has no built-in authentication. If it is reachable outside your trusted network, put it behind reverse-proxy authentication, VPN, firewall rules or an IP allowlist.
