# Development

---

## Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) — fast Python package and project manager

Install `uv` if not present:

```bash
pip install uv
# or via the official installer (recommended):
curl -Ls https://astral.sh/uv/install.sh | sh
```

---

## `uv` Workflow

### 1. Create and activate a virtual environment

```bash
# Linux / macOS
uv venv
source .venv/bin/activate

# Windows
uv venv
.venv\Scripts\activate
```

### 2. Install runtime dependencies

```bash
uv sync
```

This reads `pyproject.toml` and `uv.lock`, installs the exact pinned
versions, and installs `lyriclabel` itself in editable mode.

### 3. Install development tools

```bash
uv sync --dev
```

Adds `ruff` (linter/formatter) and `mypy` (type checker) to the
environment without polluting the runtime dependency set.

### 4. Add a new runtime dependency

```bash
uv add <package>
```

`uv` updates `pyproject.toml` and re-locks `uv.lock` atomically.
Commit both files together.

### 5. Add a development-only dependency

```bash
uv add --dev <package>
```

### 6. Update a pinned dependency

```bash
uv lock --upgrade-package <package>
uv sync
```

---

## Running the Tool Locally

```bash
# Via the installed entry point
lyriclabel <path>

# Or explicitly via the module
python -m lyriclabel.main <path>
```

---

## Code Quality

### Lint

```bash
uv run ruff check .
```

`ruff` is configured in `pyproject.toml`:
- Line length: 88
- Target: Python 3.11
- Active rule sets: `E` (pycodestyle errors), `F` (Pyflakes), `UP` (pyupgrade)
- `E501` (line-too-long) is ignored in favour of readable docstrings.

Auto-fix safe issues:

```bash
uv run ruff check . --fix
```

### Type checking

```bash
uv run mypy .
```

`mypy` is configured in `pyproject.toml` with:
- `warn_return_any = true`
- `warn_unused_configs = true`
- `check_untyped_defs = true`
- `ignore_missing_imports = true`

---

## Logging Architecture: `lyriclabel/logging_config.py`

LyricLabel uses a two-sink logging setup configured once at startup by
`configure_logging()`.
Both sinks attach to the `lyriclabel` namespace logger so that all
child loggers (`lyriclabel.main`, `lyriclabel.fetcher`, etc.) inherit
the same handlers automatically.

### Sink 1 — RotatingFileHandler (engineering audit trail)

```
File:        ~/.local/state/lyriclabel/logs/lyriclabel.log  (default)
Format:      JSON Lines (one JSON object per log record)
Level:       DEBUG (always verbose, regardless of --quiet)
Max size:    5 MB per file
Backups:     5 rotated files kept (lyriclabel.log.1 … lyriclabel.log.5)
Encoding:    UTF-8
Open mode:   Lazy (file is not created until the first log record)
```

Because the file handler runs at DEBUG and uses JSON Lines, every
internal event — retry attempts, semaphore acquisitions, planned field
deltas, dry-run previews — is recorded with full structured context.
This makes post-run analysis with `jq` or `grep` straightforward.

**Why `RotatingFileHandler` instead of `TimedRotatingFileHandler`?**
Size-based rotation bounds disk usage predictably regardless of how
often the tool is run.
5 MB × 6 files = 30 MB maximum — a safe ceiling for a developer machine.

### Sink 2 — StreamHandler (console)

```
Target:  stderr (default StreamHandler)
Format:  "YYYY-MM-DD HH:MM:SS | LEVEL    | logger | message"
Level:   INFO  (normal mode)
         WARNING  (when --quiet is active)
```

Quiet mode does not silence the file handler.
Operators running LyricLabel in a cron job or CI pipeline can set
`--quiet` to keep the terminal clean while retaining full DEBUG logs in
the file for later inspection.

### JsonFormatter

`JsonFormatter` extends `logging.Formatter` and emits one JSON object
per record.
Standard `LogRecord` attributes (`name`, `lineno`, etc.) are included
by default.
Any keyword arguments passed via `extra={...}` are merged into the top-
level JSON object, enabling structured queries like:

```bash
# Find every file that would have been updated in a dry run
jq 'select(.dry_run == true and .planned_changes != null)
    | {file: .file_path, changes: .planned_changes}' \
  ~/.local/state/lyriclabel/logs/lyriclabel.log

# Show all retry events
jq 'select(.message == "lastfm rate limited, backing off")
    | {attempt: .attempt, sleep: .sleep_seconds}' \
  ~/.local/state/lyriclabel/logs/lyriclabel.log

# End-of-run summary for the last run
jq 'select(.message == "run summary")' \
  ~/.local/state/lyriclabel/logs/lyriclabel.log | tail -1
```

### Startup and shutdown

`configure_logging` is idempotent: it removes and closes any previously
registered handlers before attaching new ones.
This prevents handler duplication in test suites that call the function
multiple times.

`atexit.register(logging.shutdown)` ensures all buffered log records are
flushed and file handles are closed cleanly even if the process exits
abnormally.

---

## Project Structure

```
LyricLabel/
├── pyproject.toml           # Project metadata, dependencies, tool config
├── uv.lock                  # Exact pinned dependency versions (commit this)
├── README.md                # Quick-start overview
├── docs/                    # Extended documentation (this directory)
│   ├── architecture.md
│   ├── configuration.md
│   ├── development.md
│   └── usage.md
└── lyriclabel/
    ├── __init__.py
    ├── main.py              # CLI entry point and async orchestrator
    ├── meta_fetcher.py      # Last.fm aiohttp client
    ├── meta_edit.py         # mutagen ID3 writer
    ├── parser.py            # Filename heuristics
    ├── config.py            # XDG-aware TOML config loader
    ├── logging_config.py    # Dual-sink logging setup
    └── utils.py             # Shared file utilities
```
