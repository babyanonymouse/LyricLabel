# LyricLabel

LyricLabel is a Python command-line tool for fetching and embedding song metadata (such as artist, album, title, and genre) into MP3 files using Last.fm API. This tool is designed to help users easily manage and update metadata for their music collection.

---

## Features

- **Fetch Song Metadata**: Fetch artist, album, genre, and year information using song title and artist from the Last.fm API.
- **Embed Metadata**: Edit and embed the fetched metadata directly into MP3 files.
- **Supports Quiet Mode**: Run the program in quiet mode to suppress non-essential output.
- **Process Directories**: Supports processing all MP3 files in a specified directory and its subdirectories.
- **Error Handling**: Handles various errors, including missing metadata and network issues.

---

## Requirements

To use LyricLabel, you will need:

- Python 3.10+
- `aiohttp` (for async metadata fetching from Last.fm)
- `mutagen` (for editing MP3 metadata)
- `python-dotenv` (for securely storing your API keys)

Create and activate a virtual environment with uv:

- Linux/macOS:

```bash
uv venv
source .venv/bin/activate
```

- Windows:

```bash
uv venv
.venv\Scripts\activate
```

Install dependencies with uv:

```bash
uv sync
```

Install with development tools (ruff and mypy):

```bash
uv sync --dev
```

If uv is not available, install it first:

```bash
pip install uv
```

Legacy venv flow (without uv):

- Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

- Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Then install the dependencies using pip

```bash
pip install -e .
```

---

## Setup

### 1. API Key

Before running the program, you need to set up a **Last.fm API Key**.

- Create a `.env` file in the root of the project (do **not** commit this file to your version control).
- Add your Last.fm API Key in the `.env` file as follows:

```env
LASTFM_API_KEY=your_api_key_here
```

### 2. Install Dependencies

Run the following command to install the required Python libraries:

```bash
uv sync
```

---

## Usage

You can run the program in the following ways:

### Installed CLI Command (Recommended)

After installation, use the global script entrypoint:

```bash
lyriclabel <path_to_file_or_directory>
```

Quiet mode:

```bash
lyriclabel <path_to_file_or_directory> --quiet
```

Tune concurrency (default is 5):

```bash
lyriclabel <path_to_file_or_directory> --concurrency 5
```

Dry-run preview (no file writes):

```bash
lyriclabel <path_to_file_or_directory> --dry-run
```

Override log file location:

```bash
lyriclabel <path_to_file_or_directory> --log-file /tmp/lyriclabel.log
```

### Process a Single File

To process a single MP3 file and embed metadata:

```bash
python -m lyriclabel.main <path_to_file>
```

### Process All MP3 Files in a Directory

To process all MP3 files in a directory:

```bash
python -m lyriclabel.main <path_to_directory>
```

### Quiet Mode

If you want to suppress non-essential output (e.g., prompts or debug information), you can enable **quiet mode** by adding the `--quiet` flag:

```bash
python -m lyriclabel.main <path_to_file_or_directory> --quiet
```

### Dev Quality Commands

Run lint checks:

```bash
uv run ruff check .
```

Run type checks:

```bash
uv run mypy .
```

### Logging

- Console logs are human-readable.
- File logs are JSON lines for easy post-run analysis (`jq`, grep, etc.).
- Quiet mode lowers console noise to warnings/errors only, while file logs remain verbose.
- Default log file location follows XDG state conventions on Linux:
	- `~/.local/state/lyriclabel/logs/lyriclabel.log`
- Dry runs emit `[DRY RUN]` per-field delta messages (old -> new) and include structured fields like `dry_run` and `planned_changes` in JSON logs.
- End-of-run summary includes `would_have_updated` for dry-run auditing.

Example pre-flight report with jq:

```bash
jq 'select(.dry_run == true and .planned_changes != null) | {file: .file_path, planned_changes: .planned_changes}' ~/.local/state/lyriclabel/logs/lyriclabel.log
```

---

## How It Works

### `lyriclabel/main.py`

- The main script where all file processing begins.
- It accepts either a file path or a directory path as input.
- If it's a directory, the script will recursively walk through the folder and process all `.mp3` files.

### `meta_fetcher.py`

- This file contains functions for interacting with the **Last.fm API** to fetch song metadata.
- `fetch_metadata_from_lastfm_async`: Retrieves metadata based on the song title and artist.
- `fetch_detailed_metadata_async`: Fetches detailed metadata such as genre, year, and album information.
- **Important**: The Last.fm API key is stored in an environment variable for security.
- Uses one shared `aiohttp` session per run, with retries and 429-aware backoff.

### `meta_edit.py`

- This file handles the actual editing of the MP3 metadata using **Mutagen**.
- The `edit_metadata` function embeds the fetched metadata into the MP3 file's ID3 tags (Artist, Title, Album, Genre, Year).

### `utils.py`

- Contains utility functions like checking if a file is valid.

---

## Error Handling

- **No Matching Tracks**: If no tracks are found based on the song title, the user is informed, and they can decide to continue or cancel.
- **Detailed Info Fetch Error**: If detailed metadata cannot be fetched, the filename is displayed in the error message, allowing the user to know which file failed.
- **Network or API Errors**: In case of network errors or API issues, an appropriate message is displayed, and the program continues processing other files.

---

## Contributing

If you want to contribute to the project, feel free to fork the repository, make changes, and submit a pull request. Contributions and suggestions are welcome!

---

## Troubleshooting

- **API Key Error**: Ensure that you have set the `LASTFM_API_KEY` in the `.env` file.
- **Missing Modules**: Make sure dependencies are installed with `uv sync` (or `pip install -e .`).
- **VS Code Interpreter**: On Ubuntu and other Linux systems, point VS Code to `.venv/bin/python` created by `uv venv` for correct IntelliSense and imports.

---

## Notes

- **Security**: Always keep your API key private. Never commit it to a public repository.
- **Performance**: If processing a large number of files, it may take some time depending on the number of API requests.
- **Concurrency**: Lower `--concurrency` if you hit API rate limits or run on a constrained network.
- **Logs**: Inspect JSON logs to audit retries, rate limits, and per-file failures.

---
