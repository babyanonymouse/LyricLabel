# LyricLabel — App Summary

## Overview

**LyricLabel** is a Python command-line tool that automatically fetches and embeds song metadata (artist, album, title, genre, and year) into MP3 files using the [Last.fm API](https://www.last.fm/api). It is designed to help users keep their music library well-organised without manually looking up and entering track information.

---

## Core Features

| Feature | Description |
|---|---|
| Metadata Fetching | Retrieves artist, album, genre, and year data from the Last.fm API based on the song's filename. |
| Metadata Embedding | Writes the fetched data directly into the MP3 file's ID3 tags using the Mutagen library. |
| Async Parallel Processing | Uses `aiohttp` and `asyncio` to fetch metadata for multiple files concurrently, dramatically reducing wall-clock time for large collections. |
| Regex Filename Parser | Robustly derives artist + title from filenames in `Artist - Title.mp3` and `TrackNo - Title.mp3` formats. |
| Single-File Processing | Accepts a path to one MP3 file and processes it immediately. |
| Directory Processing | Recursively walks a directory and processes every `.mp3` file found. |
| Quiet Mode | Suppresses non-essential console output and auto-selects the first search result with the `--quiet` flag. |
| Dry Run Mode | Logs what *would* be written to ID3 tags without modifying any files when `--dry-run` is passed. |
| Structured Logging | All output is routed through a `RotatingFileHandler` writing to `logs/lyriclabel.log` for bulk-run auditing. |
| Error Reporting | Collects and logs all errors (e.g., missing metadata, network failures) at the end of a run. |

---

## Technology Stack

- **Language**: Python 3.10+
- **Async HTTP**: [`aiohttp`](https://pypi.org/project/aiohttp/) — non-blocking requests to the Last.fm REST API.
- **MP3 Tag Editing**: [`mutagen`](https://pypi.org/project/mutagen/) — reads and writes ID3 tags in MP3 files.
- **Environment Variables**: [`python-dotenv`](https://pypi.org/project/python-dotenv/) — loads the Last.fm API key from a `.env` file so secrets are never hard-coded.
- **Dependency Management**: [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — modern Python packaging, compatible with uv and pip.

---

## Project Structure

```
LyricLabel/
├── main.py                     # Entry point; argument parsing, async orchestration
├── pyproject.toml              # Project metadata and dependencies
├── .env                        # (user-created, not committed) stores LASTFM_API_KEY
├── logs/
│   └── lyriclabel.log          # Rotating audit log (auto-created at runtime)
└── lyriclabel/
    ├── __init__.py
    ├── logger.py               # Centralised RotatingFileHandler + console logger
    ├── meta_fetcher.py         # Async Last.fm API integration (aiohttp)
    ├── meta_edit.py            # Mutagen-based ID3 tag writer (supports --dry-run)
    └── utils/
        ├── __init__.py         # Shared utility helpers (e.g., file validation)
        └── parser.py           # Regex filename parser
```

---

## How It Works

1. **Input**: The user passes a file path or directory path to `main.py`, optionally with `--quiet` and/or `--dry-run`.
2. **Filename Parsing** (`lyriclabel/utils/parser.py`): Derives artist + title from the filename using regex — handles `Artist - Title.mp3` and `01 - Title.mp3` formats.
3. **Async API Lookup** (`lyriclabel/meta_fetcher.py`): Uses `aiohttp` within a shared `ClientSession` to query Last.fm concurrently for all files in a directory.
4. **Tag Writing** (`lyriclabel/meta_edit.py`): Embeds Artist, Title, Album, Genre, and Year into the MP3's ID3 tags.  In dry-run mode, the intended changes are logged and no files are modified.
5. **Logging** (`lyriclabel/logger.py`): All output routes through a `RotatingFileHandler` (debug+) and a console handler (info+).

---

## Usage

```bash
# Process a single MP3 file
python main.py path/to/song.mp3

# Process all MP3 files in a directory (recursive, concurrent)
python main.py path/to/music/folder

# Suppress non-essential output
python main.py path/to/song.mp3 --quiet

# Preview what would be written without modifying files
python main.py path/to/song.mp3 --dry-run

# Combine flags
python main.py path/to/folder --quiet --dry-run
```

---

## Setup

1. Clone the repository and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e .
   ```
2. Create a `.env` file in the project root with your Last.fm API key:
   ```env
   LASTFM_API_KEY=your_api_key_here
   ```
3. Run the tool as shown in the **Usage** section above.

---

## Security Notes

- The Last.fm API key is loaded from a `.env` file and never hard-coded in source files.
- The `.env` file is listed in `.gitignore` to prevent accidental exposure.

