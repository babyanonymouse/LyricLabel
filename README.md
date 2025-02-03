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

- Python 3.x
- `requests` (for fetching metadata from Last.fm)
- `mutagen` (for editing MP3 metadata)
- `python-dotenv` (for securely storing your API keys)

Activate virtual .venv:

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
pip install -r requirements.txt
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
pip install python-dotenv requests mutagen
```

---

## Usage

You can run the program in the following ways:

### Process a Single File

To process a single MP3 file and embed metadata:

```bash
python main.py <path_to_file>
```

### Process All MP3 Files in a Directory

To process all MP3 files in a directory:

```bash
python main.py <path_to_directory>
```

### Quiet Mode

If you want to suppress non-essential output (e.g., prompts or debug information), you can enable **quiet mode** by adding the `--quiet` flag:

```bash
python main.py <path_to_file_or_directory> --quiet
```

---

## How It Works

### `main.py`

- The main script where all file processing begins.
- It accepts either a file path or a directory path as input.
- If it's a directory, the script will recursively walk through the folder and process all `.mp3` files.

### `meta_fetcher.py`

- This file contains functions for interacting with the **Last.fm API** to fetch song metadata.
- `fetch_metadata_from_lastfm`: Retrieves metadata based on the song title and artist.
- `fetch_detailed_metadata`: Fetches detailed metadata such as genre, year, and album information.
- **Important**: The Last.fm API key is stored in an environment variable for security.

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
- **Missing Modules**: Make sure to install the required dependencies using `pip install -r requirements.txt`.

---

## Notes

- **Security**: Always keep your API key private. Never commit it to a public repository.
- **Performance**: If processing a large number of files, it may take some time depending on the number of API requests.

---
