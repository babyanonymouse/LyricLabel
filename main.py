import argparse
import os
from lyriclabel.meta_fetcher import fetch_metadata_from_lastfm
from lyriclabel.meta_edit import edit_metadata


def is_valid_audio_file(filepath):
    """Check if the given path is a valid audio file."""
    if not os.path.isfile(filepath):  # Check if file exists
        print(f"Error: File '{filepath}' not found.")
        return False

    if not filepath.lower().endswith((".mp3", ".flac", ".wav")):  # Check format
        print(
            f"Error: Unsupported file format for '{filepath}'. Supported formats: MP3, FLAC, WAV."
        )
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="LyricLabel: Fetch and edit song metadata."
    )
    parser.add_argument("filepath", help="Path to the song file or folder")
    args = parser.parse_args()

    # Convert relative path to absolute path
    absolute_path = os.path.abspath(args.filepath)
    print(f"Processing file: {absolute_path}")

    # Extract title from the filename (we don't need the full path, just the filename)
    filename = os.path.basename(absolute_path)
    title = filename.replace(".mp3", "").strip()

    # Fetch metadata for the song using only the title
    metadata = fetch_metadata_from_lastfm(title)

    if metadata:
        # Embed metadata into the song file
        edit_metadata(absolute_path, metadata)
        print("Metadata successfully added to the song file.")
    else:
        print("Metadata could not be fetched.")


if __name__ == "__main__":
    main()
