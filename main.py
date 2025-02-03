import argparse
import os
from lyriclabel.meta_fetcher import fetch_metadata_from_lastfm
from lyriclabel.meta_edit import edit_metadata


def process_file(filepath, quiet_mode=False):
    """Process a single file: fetch metadata and update it."""
    if not quiet_mode:
        print(f"Processing file: {filepath}")

    # Extract title from the filename (we don't need the full path, just the filename)
    filename = os.path.basename(filepath)
    title = filename.replace(".mp3", "").strip()

    print(f"Extracted title: {title}")  # Debugging line

    # Fetch metadata for the song using only the title
    metadata = fetch_metadata_from_lastfm(title, quiet_mode, filename)

    if metadata:
        # Embed metadata into the song file
        edit_metadata(filepath, metadata)
        if not quiet_mode:
            print(f"Metadata successfully added to '{filepath}'.")
    else:
        if not quiet_mode:
            print(f"Metadata could not be fetched for '{filepath}'.")


def main():
    parser = argparse.ArgumentParser(
        description="LyricLabel: Fetch and edit song metadata."
    )
    parser.add_argument("path", help="Path to the song file or folder")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run in quiet mode (suppress non-essential output)",
    )
    args = parser.parse_args()

    # Get absolute path
    absolute_path = os.path.abspath(args.path)

    # If it's a directory, process all mp3 files in it
    if os.path.isdir(absolute_path):
        if not args.quiet:
            print(f"Processing all mp3 files in directory: {absolute_path}")
        for root, dirs, files in os.walk(absolute_path):
            for file in files:
                if file.lower().endswith(".mp3"):
                    file_path = os.path.join(root, file)
                    process_file(file_path, quiet_mode=args.quiet)

    # If it's a file, process it directly
    elif os.path.isfile(absolute_path):
        process_file(absolute_path, quiet_mode=args.quiet)

    else:
        print(f"The path '{absolute_path}' is not a valid file or directory.")


if __name__ == "__main__":
    main()
