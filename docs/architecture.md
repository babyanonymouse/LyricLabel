# LyricLabel Architecture

This document describes how LyricLabel is structured, how data flows through the system, and where to extend functionality safely.

## System Overview

LyricLabel is a CLI-first pipeline for enriching MP3 ID3 metadata using Last.fm.

High-level flow:

1. Parse CLI arguments and configure logging.
2. Resolve input path (single file or recursive directory scan).
3. Build a shared async HTTP session.
4. For each MP3, parse filename into search terms.
5. Search Last.fm and fetch track details.
6. Offload ID3 write to a worker thread.
7. Emit structured logs and a run summary.

Core modules:

- [lyriclabel/main.py](lyriclabel/main.py): orchestration, async fan-out, result accounting.
- [lyriclabel/meta_fetcher.py](lyriclabel/meta_fetcher.py): Last.fm API access, retry/backoff, metadata extraction.
- [lyriclabel/meta_edit.py](lyriclabel/meta_edit.py): ID3 diffing and writes with dry-run support.
- [lyriclabel/parser.py](lyriclabel/parser.py): filename parsing heuristics for search quality.
- [lyriclabel/logging_config.py](lyriclabel/logging_config.py): console + JSON file logging.
- [main.py](main.py): thin executable entrypoint.

## Execution Model

### Concurrency

- Directory processing uses asyncio with bounded parallelism via `asyncio.Semaphore`.
- `--concurrency` controls max in-flight file tasks. Default is `5`.
- Each file task performs network I/O asynchronously.

### Blocking Operations

- Mutagen writes are blocking and run in a worker thread using `asyncio.to_thread`.
- This keeps the event loop responsive during multi-file runs.

### Session Lifecycle

- A single `aiohttp.ClientSession` is created per run and shared by all file tasks.
- This improves connection reuse and avoids per-file session overhead.

## Data Flow

### 1) Input Discovery

`run_async` in [lyriclabel/main.py](lyriclabel/main.py) determines mode:

- Directory path: recursive `.mp3` discovery.
- File path: single file processing.
- Other: fail with exit code `2`.

### 2) Filename Parsing

`parse_filename` in [lyriclabel/parser.py](lyriclabel/parser.py) returns `ParsedFilename` with:

- `title` for display/write context.
- `search_title` normalized for Last.fm query.
- Optional `artist` when split detected.
- Optional `track_no` when filename starts with track index.

Supported patterns include:

- `Artist - Title.mp3`
- `01 - Title.mp3`
- fallback unstructured filenames.

### 3) Metadata Fetch

`fetch_metadata_from_lastfm_async` in [lyriclabel/meta_fetcher.py](lyriclabel/meta_fetcher.py):

- Validates `LASTFM_API_KEY` is present.
- Performs `track.search`.
- Optionally prompts for selection in non-quiet single-file mode.
- Fetches detail via `track.getInfo`.
- Normalizes output fields: artist, album, track, genre, year.

### 4) Metadata Diff + Write

`edit_metadata` in [lyriclabel/meta_edit.py](lyriclabel/meta_edit.py):

- Reads current ID3 tags.
- Computes field-level delta (`planned_changes`).
- Writes only if differences exist and dry-run is disabled.
- Dry-run logs per-field old/new values without saving.

ID3 frames currently managed:

- `TIT2` (Title)
- `TPE1` (Artist)
- `TALB` (Album)
- `TCON` (Genre)
- `TDRC` (Year)

## Logging and Observability

Configured by [lyriclabel/logging_config.py](lyriclabel/logging_config.py):

- Console logs: human-readable, `INFO` (or `WARNING` in quiet mode).
- File logs: JSON lines, `DEBUG` by default, rotating files.
- Default path on Linux: `~/.local/state/lyriclabel/logs/lyriclabel.log`.

Important emitted events:

- Startup metadata (`dry_run`, `log_path`).
- Per-file processing and warnings.
- Retry/backoff events for API pressure or server faults.
- End-of-run summary counters.

## Error Handling Strategy

Failure model is per-file isolation:

- API failure for one file does not abort the batch.
- Write failure increments `write_failed` and continues.
- Unexpected async task exception is logged and counted.

Retry behavior in [_request_json](lyriclabel/meta_fetcher.py):

- `429` responses: honors `Retry-After` when present.
- `5xx` responses: exponential backoff + jitter.
- network/timeout/json shape errors: bounded retries.

## Exit Codes and Outcomes

Observed exit behavior:

- `0`: completed run (even if some files failed internally).
- `2`: invalid input path or invalid concurrency argument.

Per-file outcomes tracked in `ProcessOutcome.status`:

- `updated`
- `skipped_dry_run`
- `no_changes`
- `metadata_unavailable`
- `write_failed`

## Current Design Notes

- A full config loader exists in [lyriclabel/config.py](lyriclabel/config.py), but the current runtime entry path in [lyriclabel/main.py](lyriclabel/main.py) does not consume it yet.
- The primary runtime source of API key is environment (`LASTFM_API_KEY`), loaded via `python-dotenv`.

## Extension Points

Recommended low-risk extension seams:

- Add providers: abstract fetcher interface and implement additional metadata backends.
- Add tags: extend target/existing tag maps in [lyriclabel/meta_edit.py](lyriclabel/meta_edit.py).
- Add output sinks: append metrics exporter or structured event hooks in logging layer.
- Add path filtering: augment discovery logic in [lyriclabel/main.py](lyriclabel/main.py).

## Sequence Diagram (Text)

1. User invokes CLI.
2. Main configures logging.
3. Main creates shared HTTP session.
4. For each file task:
	- parse filename
	- search Last.fm
	- fetch track info
	- call metadata editor on worker thread
	- emit status
5. Main aggregates statuses and logs summary.

