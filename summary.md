# LyricLabel — App Summary

## Overview

**LyricLabel** is a Python command-line tool that automatically fetches and embeds song metadata (artist, album, title, genre, and year) into MP3 files using the [Last.fm API](https://www.last.fm/api). It is designed to help users keep their music library well-organised without manually looking up and entering track information.

---

## Core Features

| Feature | Description |
|---|---|
| Metadata Fetching | Retrieves artist, album, genre, and year data from the Last.fm API based on the song's filename. |
| Metadata Embedding | Writes the fetched data directly into the MP3 file's ID3 tags using the Mutagen library. |
| Single-File Processing | Accepts a path to one MP3 file and processes it immediately. |
| Directory Processing | Recursively walks a directory and processes every `.mp3` file found. |
| Quiet Mode | Suppresses non-essential console output with the `--quiet` flag. |
| Error Reporting | Collects and displays all errors (e.g., missing metadata, network failures) at the end of a run. |

---

## Technology Stack

- **Language**: Python 3.x
- **HTTP Requests**: [`requests`](https://pypi.org/project/requests/) — communicates with the Last.fm REST API.
- **MP3 Tag Editing**: [`mutagen`](https://pypi.org/project/mutagen/) — reads and writes ID3 tags in MP3 files.
- **Environment Variables**: [`python-dotenv`](https://pypi.org/project/python-dotenv/) — loads the Last.fm API key from a `.env` file so secrets are never hard-coded.

---

## Project Structure

```
LyricLabel/
├── main.py                  # Entry point; argument parsing and file/directory orchestration
├── requirements.txt         # Pinned Python dependencies
├── .env                     # (user-created, not committed) stores LASTFM_API_KEY
└── lyriclabel/
    ├── __init__.py
    ├── meta_fetcher.py      # Last.fm API integration; fetches track and album metadata
    ├── meta_edit.py         # Mutagen-based ID3 tag writer
    └── utils.py             # Shared utility helpers (e.g., file validation)
```

---

## How It Works

1. **Input**: The user passes a file path or directory path to `main.py`, optionally with `--quiet`.
2. **Title Extraction**: The script derives the song title from the filename (strips the `.mp3` extension).
3. **API Lookup** (`meta_fetcher.py`):
   - `fetch_metadata_from_lastfm` searches Last.fm for the track.
   - `fetch_detailed_metadata` retrieves additional information such as genre, year, and album art.
4. **Tag Writing** (`meta_edit.py`):
   - `edit_metadata` embeds Artist, Title, Album, Genre, and Year into the MP3's ID3 tags.
5. **Error Collection**: Any failures are accumulated and printed together after all files have been processed.

---

## Usage

```bash
# Process a single MP3 file
python main.py path/to/song.mp3

# Process all MP3 files in a directory (recursive)
python main.py path/to/music/folder

# Suppress non-essential output
python main.py path/to/song.mp3 --quiet
```

---

## Setup

1. Clone the repository and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root with your Last.fm API key:
   ```env
   LASTFM_API_KEY=your_api_key_here
   ```
3. Run the tool as shown in the **Usage** section above.

---

## Security Notes

- The Last.fm API key is loaded from a `.env` file and never hard-coded in source files.
- The `.env` file should be added to `.gitignore` to prevent accidental exposure in version control.
