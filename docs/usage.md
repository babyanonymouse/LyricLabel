# Usage

---

## Installation

```bash
# Install the package and its runtime dependencies
uv sync

# The CLI entry point is then available as:
lyriclabel --help
```

For development tools (ruff, mypy):

```bash
uv sync --dev
```

---

## Positional Argument

```
lyriclabel <path>
```

`<path>` must be either:
- An **MP3 file** — processed as a single file.
- A **directory** — all `.mp3` files found recursively are processed.

---

## CLI Flags

| Flag                        | Type    | Default | Description                                                       |
|-----------------------------|---------|---------|-------------------------------------------------------------------|
| `--dry-run` / `--no-dry-run`| boolean | `false` | Preview metadata changes without writing anything to disk.        |
| `--quiet` / `--no-quiet`    | boolean | `false` | Suppress INFO-level console output; only warnings and errors shown. |
| `--concurrency <N>`         | integer | `5`     | Maximum number of files processed in parallel.                    |
| `--log-file <path>`         | string  | —       | Override the rotating log file path.                              |
| `--config <path>`           | string  | —       | Override the config file path (default: XDG location).            |

All boolean flags support the `--no-<flag>` form to explicitly disable a
setting that may be active via environment variable or `config.toml`.

---

## The Dry-Run Safety Net

`--dry-run` is the recommended first step when tagging an unfamiliar
music library.

**What it does:**
1. Parses each filename and queries Last.fm as normal.
2. Reads existing ID3 tags from the MP3 file.
3. Computes the set of changes that *would* be applied.
4. Logs each field delta (`old → new`) with the `[**DRY RUN**]` prefix.
5. **Does not call `audio.save()`** — the file is never modified.

**End-of-run summary** reports `would_have_updated` instead of `updated`,
so you can see exactly how many files would have changed.

**Auditing planned changes with `jq`:**

```bash
jq 'select(.dry_run == true and .planned_changes != null)
    | {file: .file_path, changes: .planned_changes}' \
  ~/.local/state/lyriclabel/logs/lyriclabel.log
```

This lets you review every planned field change before committing to a
live run.

---

## Examples

### Single-file processing

```bash
# Interactive: prompts you to select from the top-10 Last.fm search results.
lyriclabel "The Beatles - Hey Jude.mp3"
```

Single-file mode enables `interactive_select=True`, so you are prompted
to choose from up to ten search results before the tag write occurs.

### Single-file dry run

```bash
lyriclabel "The Beatles - Hey Jude.mp3" --dry-run
```

No files are modified. All planned changes are logged.

### Recursive directory processing

```bash
# Tag every MP3 found under /music (non-interactive, up to 5 concurrent requests)
lyriclabel /music
```

Directory mode is non-interactive: the top search result is selected
automatically for every file.

### Recursive directory with tuned concurrency

```bash
# Raise concurrency for fast networks / large libraries
lyriclabel /music --concurrency 10

# Lower concurrency to avoid Last.fm 429 rate-limit responses
lyriclabel /music --concurrency 2
```

### Dry run before a live library tag

```bash
# Step 1: audit
lyriclabel /music --dry-run --log-file /tmp/lyriclabel-dryrun.log

# Inspect planned changes
jq 'select(.dry_run == true and .planned_changes != null)' \
  /tmp/lyriclabel-dryrun.log

# Step 2: apply if satisfied
lyriclabel /music
```

### Quiet mode (CI / cron)

```bash
lyriclabel /music --quiet --log-file /var/log/lyriclabel/run.log
```

Console output is reduced to warnings and errors.
File logging remains at DEBUG verbosity regardless of `--quiet`.

### Specify an alternate config file

```bash
lyriclabel /music --config ~/staging-config.toml
```

---

## Exit Codes

| Code | Meaning                                               |
|------|-------------------------------------------------------|
| `0`  | Run completed (errors may still have been collected). |
| `2`  | Configuration error or invalid path supplied.         |

---

## Log File Location (default)

| Platform  | Default path                                              |
|-----------|-----------------------------------------------------------|
| Linux     | `~/.local/state/lyriclabel/logs/lyriclabel.log`           |
| macOS [?] | `~/.local/state/lyriclabel/logs/lyriclabel.log`           |
| Windows [?] | Follows `XDG_STATE_HOME` if set; otherwise home-relative |

Override with `--log-file` or `LYRICLABEL_LOG_FILE`.
