# LyricLabel

LyricLabel is a Python command-line tool for fetching and embedding song metadata (such as artist, album, title, and genre) into MP3 files using Last.fm API. This tool is designed to help users easily manage and update metadata for their music collection.

---

## Features

- **Fetch Song Metadata**: Fetch artist, album, genre, and year information using song title and artist from the Last.fm API.
- **Embed Metadata**: Edit and embed the fetched metadata directly into MP3 files.
- **Parallel Processing**: Uses `aiohttp` and `asyncio` to fetch metadata for multiple files concurrently.
- **Regex Filename Parser**: Robustly parses `Artist - Title` and `TrackNo - Title` filename patterns.
- **Quiet Mode**: Run in quiet mode to suppress non-essential output with `--quiet`.
- **Dry Run Mode**: Preview what metadata *would* be written to ID3 tags without modifying any files with `--dry-run`.
- **Structured Logging**: All output goes through a rotating file logger (`logs/lyriclabel.log`) for audit trails on bulk runs.
- **Process Directories**: Supports processing all MP3 files in a specified directory and its subdirectories.
- **Error Handling**: Handles various errors, including missing metadata and network issues.

---

## Requirements

- Python 3.10+
- Dependencies are declared in `pyproject.toml` and managed via [uv](https://github.com/astral-sh/uv) or pip.

---

## Setup

### 1. Clone & create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

Using **uv** (recommended):

```bash
pip install uv
uv pip install -e .
```

Or plain pip:

```bash
pip install -e .
```

### 3. API Key

Create a `.env` file in the project root (do **not** commit this file):

```env
LASTFM_API_KEY=your_api_key_here
```

---

## Usage

### Process a single MP3 file

```bash
python main.py path/to/song.mp3
```

### Process all MP3 files in a directory (recursive, concurrent)

```bash
python main.py path/to/music/folder
```

### Quiet mode (auto-selects first result, suppresses prompts)

```bash
python main.py path/to/song.mp3 --quiet
```

### Dry-run mode (log intended changes without writing to files)

```bash
python main.py path/to/song.mp3 --dry-run
```

Combine flags as needed:

```bash
python main.py path/to/folder --quiet --dry-run
```

---

## Project Structure

```
LyricLabel/
├── main.py                     # Entry point; argument parsing, async orchestration
├── pyproject.toml              # Project metadata and dependencies (replaces requirements.txt)
├── .env                        # (user-created, not committed) stores LASTFM_API_KEY
├── logs/
│   └── lyriclabel.log          # Rotating audit log (auto-created at runtime)
└── lyriclabel/
    ├── __init__.py
    ├── logger.py               # Centralised RotatingFileHandler + console logger
    ├── meta_fetcher.py         # Async Last.fm API integration (aiohttp)
    ├── meta_edit.py            # Mutagen-based ID3 tag writer (supports dry-run)
    └── utils/
        ├── __init__.py         # Shared utility helpers (e.g., file validation)
        └── parser.py           # Regex filename parser (Artist - Title, TrackNo - Title)
```

---

## How It Works

1. **Input**: The user passes a file path or directory to `main.py`, optionally with `--quiet` and/or `--dry-run`.
2. **Filename Parsing** (`lyriclabel/utils/parser.py`): Derives artist + title from the filename using regex, handling both `Artist - Title.mp3` and `01 - Title.mp3` formats.
3. **Async API Lookup** (`lyriclabel/meta_fetcher.py`): Uses `aiohttp` to query Last.fm concurrently across multiple files.
4. **Tag Writing** (`lyriclabel/meta_edit.py`): Embeds Artist, Title, Album, Genre, and Year into the MP3's ID3 tags. Skips file writes in dry-run mode.
5. **Logging** (`lyriclabel/logger.py`): All output is routed through a `RotatingFileHandler` (debug+) and a console handler (info+).

---

## Error Handling

- **No Matching Tracks**: Appended to the error list and logged at the end of a run.
- **Network / API Errors**: Caught per-file so a single failure does not abort the whole batch.
- **Invalid MP3 Files**: Detected by Mutagen and logged as errors.

---

## Contributing

Fork the repository, make changes, and open a pull request. Contributions and suggestions are welcome!

---

## Troubleshooting

- **API Key Error**: Ensure `LASTFM_API_KEY` is set in the `.env` file.
- **Missing Modules**: Run `pip install -e .` from the project root.
- **Python version**: Python 3.10 or later is required (uses `X | Y` union type hints).

---

## Notes

- **Security**: Always keep your API key private. Never commit it to a public repository.
- **Performance**: Files in a directory are processed concurrently — large collections benefit significantly from async I/O.

