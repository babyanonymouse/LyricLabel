# Usage Guide

This guide covers installation, command patterns, and practical runbooks for operating LyricLabel.

## Installation

## Prerequisites

- Python `>= 3.10`
- Last.fm API key

## Recommended setup (uv)

```bash
uv venv
source .venv/bin/activate
uv sync
```

Install with dev tools:

```bash
uv sync --dev
```

## Alternate setup (pip)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## API key setup

Create `.env` in repo root:

```env
LASTFM_API_KEY=your_lastfm_api_key
```

## Command Entry Points

Installed script (preferred):

```bash
lyriclabel <path>
```

Module execution:

```bash
python -m lyriclabel.main <path>
```

Top-level wrapper:

```bash
python main.py <path>
```

## Core Commands

## Single file

```bash
lyriclabel "/music/Artist - Song.mp3"
```

## Recursive directory

```bash
lyriclabel "/music/library"
```

## Dry-run safety pass

```bash
lyriclabel "/music/library" --dry-run
```

## Quiet batch mode

```bash
lyriclabel "/music/library" --quiet
```

## Concurrency tuning

```bash
lyriclabel "/music/library" --concurrency 3
```

## Custom log path

```bash
lyriclabel "/music/library" --log-file /tmp/lyriclabel.log
```

## Runbook: Safe Bulk Update

1. Validate key and environment.
2. Run dry-run against target directory.
3. Inspect planned deltas in JSON log.
4. Run write mode without `--dry-run`.
5. Review summary counters.

Example:

```bash
lyriclabel /music/library --dry-run --quiet --log-file /tmp/lyriclabel-preflight.log
lyriclabel /music/library --quiet --log-file /tmp/lyriclabel-apply.log
```

## Interpreting Results

End-of-run summary fields (JSON log):

- `updated`: files written in normal mode
- `would_have_updated`: files with deltas in dry-run mode
- `no_changes`: already aligned metadata
- `metadata_unavailable`: fetch failed or no matches
- `write_failed`: mutagen write failure
- `errors`: count of captured processing errors

## JSON Log Inspection

Display all dry-run planned changes:

```bash
jq 'select(.dry_run == true and .planned_changes != null) | {file: .file_path, changes: .planned_changes}' /tmp/lyriclabel-preflight.log
```

Show run summary:

```bash
jq 'select(.message == "run summary")' /tmp/lyriclabel-preflight.log
```

## Interactive Selection Behavior

When processing a single file in non-quiet mode, LyricLabel may prompt for search result selection.

- `--quiet` disables interactive prompting and auto-selects first result.
- Directory runs are non-interactive.

## Troubleshooting

## Missing API key

Symptoms:

- Metadata unavailable for all files.

Fix:

- Set `LASTFM_API_KEY` in `.env`.

## Rate limiting or server errors

Symptoms:

- Warnings for `429` or `5xx` responses.

Fix:

- Reduce `--concurrency`.
- Re-run; retries are automatic with backoff.

## Invalid MP3 headers

Symptoms:

- Write failures with invalid MP3 header errors.

Fix:

- Validate source files are real MP3s before processing.

## Invalid concurrency value

Symptoms:

- Immediate process failure with exit code `2`.

Fix:

- Use `--concurrency` value of `1` or higher.

