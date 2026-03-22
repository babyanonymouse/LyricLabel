# Architecture

LyricLabel is structured as a three-stage async pipeline:
**Parse → Fetch → Write**.
Each stage is cleanly separated: the parser never touches the network,
the fetcher never touches the disk, and the writer runs on a thread pool
to avoid blocking the event loop.

---

## Module Map

```
lyriclabel/
├── main.py           # CLI entry point, async orchestrator
├── meta_fetcher.py   # Last.fm API client (aiohttp)
├── meta_edit.py      # ID3 tag writer (mutagen)
├── parser.py         # Filename → ParsedFilename heuristics
├── config.py         # XDG-aware configuration loader
└── logging_config.py # Dual-sink (console + rotating JSON file) logging
```

---

## Async Orchestration

### Entry point: `asyncio.run` → `run_async`

`main()` calls `asyncio.run(run_async(...))` once.
All async work lives inside that single event loop.

### Shared session

```python
async with create_lastfm_session() as session:
    ...
```

One `aiohttp.ClientSession` is created for the entire run and shared
across all file-processing coroutines.
This reuses the underlying TCP connection pool and avoids the
per-request overhead of opening new connections.

### Semaphore-bounded concurrency

```python
semaphore = asyncio.Semaphore(concurrency)  # default: 5

async def process_file(..., semaphore: asyncio.Semaphore, ...) -> ProcessOutcome:
    async with semaphore:
        ...
```

The semaphore is the only gate that controls how many files are being
actively fetched at once.
When `concurrency=5`, at most five `track.search` → `track.getInfo`
round-trips are in flight simultaneously, which keeps LyricLabel within
Last.fm's informal rate limits without requiring a server-side quota.

### Directory fan-out: `asyncio.gather`

```python
tasks = [process_file(fp, ...) for fp in file_paths]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

All tasks are submitted together; the semaphore ensures that no more
than `concurrency` of them are actively running at any moment.
`return_exceptions=True` prevents a single failing file from
short-circuiting the rest of the batch — errors are collected and
reported after all files are processed.

### Retry and back-off

`_request_json` in `meta_fetcher.py` retries up to `DEFAULT_MAX_RETRIES`
(4) times with exponential back-off and jitter:

```python
sleep_seconds = (2 ** attempt) + random.uniform(0, 0.25)
```

HTTP 429 responses respect the `Retry-After` header when present.
HTTP 5xx responses use the same back-off formula.

---

## I/O Separation: `asyncio.to_thread` for Disk Writes

`mutagen` performs synchronous, blocking filesystem operations
(read headers, validate, rewrite ID3 frames).
Calling blocking code directly in a coroutine stalls the entire event
loop for the duration of the disk write.

LyricLabel isolates this by offloading `edit_metadata` to a worker
thread from the default `ThreadPoolExecutor`:

```python
write_result = await asyncio.to_thread(
    edit_metadata,
    filepath,
    metadata,
    dry_run=dry_run,
)
```

This means:
- The `aiohttp` network loop keeps running for other files while the
  disk write is in progress.
- Thread-safety is maintained because each call operates on a distinct
  filepath with no shared mutable state.
- Dry-run mode short-circuits before `audio.save()`, so no thread
  contention occurs at all.

---

## Parser: `lyriclabel/parser.py`

### Goal

Convert a raw MP3 filename into a `ParsedFilename` that carries two
distinct titles:

| Field          | Purpose                                                       |
|----------------|---------------------------------------------------------------|
| `title`        | Display name written into the ID3 `TIT2` tag.                |
| `search_title` | Cleaned string sent to the Last.fm API search endpoint.       |
| `artist`       | Extracted artist for the Last.fm `artist` parameter (or `None`). |

Keeping these separate means the ID3 tag faithfully reflects the
original filename (e.g. `"Song feat. Artist"`), while the API query
uses a simplified string that yields better search relevance.

### Three-level ranked heuristics

The parser tries three patterns in priority order:

#### 1. Structured `Artist - Title` split (highest priority)

```python
DELIMITER_PATTERN = re.compile(r"\s*[-_~|]\s*")
```

All delimiter positions in the stem are found.
Each split is scored by how balanced the two halves are:

```python
key=lambda item: (abs(len(item[1][0]) - len(item[1][1])), item[0])
```

The split with the smallest length difference wins.
Ties are broken by position (earlier split wins).

This correctly handles filenames like:
- `"The Beatles - Hey Jude.mp3"` → artist=`"The Beatles"`, title=`"Hey Jude"`
- `"artist~title~extra.mp3"` → picks the most balanced delimiter pair

#### 2. Track-number prefix (fallback)

```python
TRACK_NUMBER_PATTERN = re.compile(r"^\s*(\d{1,3})(?:[.\-_\s]+)(.+)$")
```

Matches `"01. Song Name"`, `"3-Track Title"`, etc.
Extracts `track_no` and sets `artist=None`.

#### 3. Unstructured fallback

The entire stem is used as the title with no artist extraction.

### Search normalisation

Both `artist` and `search_title` are passed through
`_normalize_for_search`, which:

1. Strips featuring clauses: `[feat. X]`, `(ft. X)` (case-insensitive).
2. Collapses extra whitespace.
3. Normalises `&` and `and` to `"and"` for consistent API matching.

The display `title` skips this normalisation, so the ID3 tag retains
the original artist-credited form of the track name.

---

## Data Flow Diagram

```
filename.mp3
     │
     ▼
parse_filename()         parser.py
     │
     │  ParsedFilename
     │  ├── title          (display, written to ID3)
     │  ├── search_title   (cleaned, sent to Last.fm)
     │  └── artist         (or None)
     │
     ▼
fetch_metadata_from_lastfm_async()   meta_fetcher.py
     │  track.search → track.getInfo (via aiohttp, semaphore-gated)
     │
     │  metadata dict
     │  {artist, album, track, genre, year}
     │
     ▼
asyncio.to_thread(edit_metadata)     meta_edit.py  (thread pool)
     │  mutagen reads existing ID3 tags
     │  computes planned_changes diff
     │  if not dry_run: audio.save()
     │
     ▼
ProcessOutcome {status, file_path}   main.py
     │
     ▼
Counter summary + error report
```
