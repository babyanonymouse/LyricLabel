# Configuration Guide

This document defines all runtime configuration surfaces for LyricLabel and their current status.

## Configuration Surfaces

LyricLabel currently supports configuration from:

1. CLI flags
2. Environment variables (`.env` supported)

There is also a TOML config implementation in [lyriclabel/config.py](lyriclabel/config.py), but it is not yet wired into the active CLI runtime in [lyriclabel/main.py](lyriclabel/main.py).

## Required Environment

### `LASTFM_API_KEY`

Purpose:

- Authenticates requests to Last.fm APIs (`track.search`, `track.getInfo`).

Behavior:

- If missing, metadata fetch fails gracefully and files are reported as unavailable.

Set via `.env` in repository root:

```env
LASTFM_API_KEY=your_lastfm_api_key
```

`python-dotenv` loads this value automatically in [lyriclabel/meta_fetcher.py](lyriclabel/meta_fetcher.py).

## CLI Flags

Defined in [lyriclabel/main.py](lyriclabel/main.py):

### Positional

- `path`: MP3 file path or directory path.

### Optional

- `--quiet`
	- Suppresses non-essential console output.
	- Console level becomes `WARNING`.

- `--concurrency <int>`
	- Maximum in-flight file tasks.
	- Must be `>= 1`; otherwise process exits with code `2`.
	- Default: `5`.

- `--log-file <path>`
	- Overrides default JSON log file location.
	- Parent directories are created automatically.

- `--dry-run`
	- Computes and logs planned metadata changes.
	- Does not write to files.

## Logging Configuration

Logging behavior is centralized in [lyriclabel/logging_config.py](lyriclabel/logging_config.py).

### Defaults

- Namespace: `lyriclabel`
- File format: JSON lines
- Rotation: 5 MB, 5 backups
- File level: `DEBUG`

### Default path (Linux)

- `~/.local/state/lyriclabel/logs/lyriclabel.log`
- If `XDG_STATE_HOME` is set: `$XDG_STATE_HOME/lyriclabel/logs/lyriclabel.log`

### Console format

- Human-readable timestamp + level + logger + message.

## Network and Retry Configuration (Code Constants)

In [lyriclabel/meta_fetcher.py](lyriclabel/meta_fetcher.py):

- `DEFAULT_TIMEOUT_SECONDS = 20`
- `DEFAULT_MAX_RETRIES = 4`
- `DEFAULT_USER_AGENT = "LyricLabel/0.1 (+https://codex.atlassian.net)"`

These are currently code-level defaults, not exposed as CLI/config options.

## Future TOML Configuration (Implemented, Not Active)

The parser in [lyriclabel/config.py](lyriclabel/config.py) supports:

- `lastfm_api_key`
- `quiet`
- `concurrency`
- `dry_run`
- `log_file`
- `album_art`
- `max_artwork_bytes`

Path resolution implemented:

- Linux: `~/.config/lyriclabel/config.toml` or `$XDG_CONFIG_HOME/lyriclabel/config.toml`
- Windows: `%APPDATA%/lyriclabel/config.toml` fallback supported

Security behavior implemented:

- On POSIX systems, world/group-readable config permissions are flagged and tightened to `600` where possible.

Note:

- Because this loader is not currently called from active runtime, these settings do not yet affect execution.

## Configuration Precedence (Current Reality)

Active precedence today:

1. CLI flags (for supported options)
2. Environment variables for provider credentials (`LASTFM_API_KEY`)
3. Built-in code defaults

## Operational Recommendations

- Keep `LASTFM_API_KEY` in `.env`, never in source control.
- Use `--dry-run` before large directory updates.
- Reduce `--concurrency` if API rate limiting increases.
- Route logs to a dedicated file path in CI to preserve artifacts.

