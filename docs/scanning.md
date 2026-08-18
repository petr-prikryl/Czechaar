# Scanning

Czecharr separates library synchronization from media scanning.

## Synchronization

Synchronization reads current Radarr and Sonarr metadata and updates local media records. Missing upstream records are marked stale instead of being deleted immediately.

## ffprobe

Scans run `ffprobe` without a shell. The media path is passed as one subprocess argument.

```text
ffprobe -v error -select_streams a -show_entries stream=index,codec_name,codec_long_name,channels,channel_layout,sample_rate,bit_rate:stream_tags=language,title -of json MEDIA_PATH
```

Captured output is bounded, timeouts terminate the process, and failures are stored as explicit scan states instead of being treated as missing Czech audio.

## Metadata Repair

When a stream is clearly Czech but lacks usable stream metadata, the Missing Czech Audio diagnostics can generate an `ffmpeg` repair plan for that specific audio stream. That repair plan is not executed automatically and does not edit files in the media mounts. The generated command remuxes a copy under `/config/repair` with `-c copy` and metadata such as `language=cze` and `title=Čeština`.

Verify the generated copy manually before replacing any original file, then rescan the item in Radarr/Sonarr and Czecharr.

If `CZECHARR_METADATA_EDIT_ENABLED=true` is set and the mapped media file is under an allowed media
root and writable, diagnostics also show a direct metadata action for MKV files. That action runs
`mkvpropedit` without a shell and updates the selected audio track in place with `language=ces` and
`name=Čeština`. Leave this disabled and keep media mounts read-only unless in-place edits are
intended.

## Czech Audio Detection

Detection uses audio-stream metadata only. It checks normalized language tags and stream titles. File names, directory names, Radarr titles, Sonarr titles and subtitles are not definitive proof.

Default Czech language codes are:

```text
cs
cz
ces
cze
```

Default title indicators include `czech`, `cestina`, `cesky`, `cesky dabing`, `cz dabing` and `czech dubbing`, with boundary-aware matching for short indicators.

The Settings UI can add or remove recognized language codes and title indicators. Czecharr stores those settings in the database and includes a hash of them in the analyzer version, so successful cached scans are invalidated when detection behavior changes.

## Cache

Successful scan results are reused only when the mapped local path, file size, modification timestamp and analyzer version match. Force-rescan bypasses the cache.

## Scan Engine

The scan engine persists scan runs and scan-run items, uses bounded concurrency, supports cancellation and marks interrupted runs during startup recovery. Scheduled scans are disabled by default and are run through the same scan history path.

Runtime scanning settings such as `CZECHARR_FFPROBE_PATH`, `CZECHARR_FFPROBE_TIMEOUT`, `CZECHARR_MKVPROPEDIT_PATH`, `CZECHARR_METADATA_EDIT_ENABLED`, `CZECHARR_SCAN_CONCURRENCY`, scheduler interval, stale-record retention and timezone are environment-controlled and visible in Settings.
