# Path Mapping

Radarr and Sonarr often return paths from their own containers. Czecharr must map those paths to locations visible inside the Czecharr container before `ffprobe` can inspect a file.

Example:

```text
Remote path: /data/movies/Avatar (2009)/Avatar.mkv
Local path:  /movies/Avatar (2009)/Avatar.mkv
```

## Rules

- Mappings can be global or scoped to one integration.
- Mappings can apply to Radarr, Sonarr or both.
- Prefixes are normalized for separators.
- Prefix matching uses complete path prefixes, not arbitrary substrings.
- The longest matching remote prefix wins.
- Priority is used as a deterministic tie-breaker.
- Only the matched prefix is replaced.
- The resulting local path must be inside an enabled allowed media root.

## Allowed Media Roots

Allowed media roots explicitly define what Czecharr may read. Examples:

```text
/movies
/tv
/media
```

If a mapped file is outside every enabled root, the scan state becomes `path_outside_allowed_roots`.
If no mapping matches but the original Radarr/Sonarr path is already inside an enabled root,
Czecharr uses that original path directly. This supports deployments where Radarr, Sonarr and
Czecharr mount media at the same container paths. If no mapping matches and the original path is
not inside an enabled root, the scan state becomes `path_not_mapped`.

## Docker

Prefer matching paths across Radarr, Sonarr and Czecharr when possible. If paths differ, mount media read-only in Czecharr:

```yaml
volumes:
  - /mnt/media/movies:/movies:ro
  - /mnt/media/tv:/tv:ro
```
