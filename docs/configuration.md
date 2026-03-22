# Configuration

LyricLabel resolves settings from four sources in strict priority order.

---

## Configuration Precedence

| Priority | Source              | Example                                  |
|----------|---------------------|------------------------------------------|
| 1 (highest) | CLI Flags        | `--dry-run`, `--concurrency 10`          |
| 2        | Environment Variables | `LYRICLABEL_DRY_RUN=true`             |
| 3        | `config.toml`       | `dry_run = true`                         |
| 4 (lowest)  | Built-in Defaults | `concurrency=5`, `quiet=false`, etc.     |

A value set at a higher priority always wins.
If none of the sources provide a value, the default is used.

---

## Config File Location

### Linux / macOS (XDG-compliant)

LyricLabel follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html).

| Condition                    | Resolved path                                      |
|------------------------------|----------------------------------------------------|
| `XDG_CONFIG_HOME` is set     | `$XDG_CONFIG_HOME/lyriclabel/config.toml`          |
| `XDG_CONFIG_HOME` is not set | `~/.config/lyriclabel/config.toml`                 |

### Windows

| Condition             | Resolved path                                              |
|-----------------------|------------------------------------------------------------|
| `APPDATA` is set      | `%APPDATA%\lyriclabel\config.toml`                         |
| `APPDATA` is not set  | `~/AppData/Roaming/lyriclabel/config.toml`                 |

### Override at runtime

Pass `--config <path>` to use any file, bypassing the default location:

```bash
lyriclabel /music --config ~/my-lyriclabel.toml
```

---

## Security: File Permissions (Linux)

On Linux/macOS, the config file may contain your Last.fm API key.
LyricLabel checks file permissions on startup:

- If the file is readable by group or other (mode `> 600`), it logs a warning.
- It **automatically attempts** to tighten permissions to `0600` (owner read/write only).
- If `chmod` fails (e.g. due to filesystem restrictions), a warning is emitted and the run continues.

Set correct permissions manually if needed:

```bash
chmod 600 ~/.config/lyriclabel/config.toml
```

---

## Environment Variables

| Variable                | Type    | Default | Description                                         |
|-------------------------|---------|---------|-----------------------------------------------------|
| `LASTFM_API_KEY`        | string  | —       | **Required.** Your Last.fm API key.                 |
| `LYRICLABEL_QUIET`      | boolean | `false` | Suppress INFO-level console output.                 |
| `LYRICLABEL_DRY_RUN`    | boolean | `false` | Preview changes without writing to files.           |
| `LYRICLABEL_CONCURRENCY`| integer | `5`     | Maximum number of files processed concurrently.     |
| `LYRICLABEL_LOG_FILE`   | string  | —       | Override the rotating log file path.                |
| `XDG_CONFIG_HOME`       | string  | —       | Override the XDG config base directory. [?]         |
| `XDG_STATE_HOME`        | string  | —       | Override the XDG state base directory for logs. [?] |

Boolean environment variables accept: `1/0`, `true/false`, `yes/no`, `on/off` (case-insensitive).
Any other value raises a `ValueError` at startup.

> **Note on `LASTFM_API_KEY`**: This variable is also loaded from a `.env`
> file in the current working directory via `python-dotenv`.
> The `.env` file is processed at startup before environment variables
> are read, so shell exports override `.env` values.

---

## `config.toml` Reference

Settings can live at the root of the file or inside a `[lyriclabel]` table.
If a `[lyriclabel]` table is present, it takes precedence over root-level keys.

Unknown keys are ignored with a warning logged at startup.

### Sample `config.toml`

```toml
[lyriclabel]
# Required: your Last.fm API key.
# Alternatively, set the LASTFM_API_KEY environment variable.
lastfm_api_key = "your_api_key_here"

# Suppress INFO-level console output. Warnings and errors still appear.
quiet = false

# Maximum concurrent Last.fm API requests. Lower this on slow networks
# or if you encounter frequent 429 (rate limit) responses.
concurrency = 5

# Preview mode: compute and log planned changes, but do NOT write any
# ID3 tags to disk. Useful for auditing a music library before committing.
dry_run = false

# Optional: override the rotating log file path.
# Defaults to ~/.local/state/lyriclabel/logs/lyriclabel.log
# log_file = "/var/log/lyriclabel/lyriclabel.log"
```

### Supported keys

| Key              | Type    | Default | Description                                      |
|------------------|---------|---------|--------------------------------------------------|
| `lastfm_api_key` | string  | —       | Last.fm API key (non-empty string required).     |
| `quiet`          | boolean | `false` | Suppress INFO console messages.                  |
| `concurrency`    | integer | `5`     | Semaphore width; must be ≥ 1.                    |
| `dry_run`        | boolean | `false` | Skip disk writes; log planned changes only.      |
| `log_file`       | string  | —       | Absolute or `~`-expanded path for the log file. |
