import argparse
import os
from lyriclabel.meta_fetcher import fetch_metadata_from_lastfm
from lyriclabel.meta_edit import edit_metadata


def process_file(filepath, quiet_mode=False, error_list=None):
    """Process a single file: fetch metadata and update it."""
    if not quiet_mode:
        print(f"Processing file: {filepath}")

    # Extract title from the filename (we don't need the full path, just the filename)
    filename = os.path.basename(filepath)
    title = filename.replace(".mp3", "").strip()

    # Initialize an error list if not passed
    if error_list is None:
        error_list = []

    # Fetch metadata for the song using only the title
    metadata = fetch_metadata_from_lastfm(title, quiet_mode, filename, error_list)

    if metadata:
        # Embed metadata into the song file
        edit_metadata(filepath, metadata)
        if not quiet_mode:
            print(f"Metadata successfully added to '{filepath}'.")
    else:
        if not quiet_mode:
            print(f"Metadata could not be fetched for '{filepath}'.")

    return error_list


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

    # Initialize a list to collect all errors
    error_list = []

    # If it's a directory, process all mp3 files in it
    if os.path.isdir(absolute_path):
        if not args.quiet:
            print(f"Processing all mp3 files in directory: {absolute_path}")
        for root, dirs, files in os.walk(absolute_path):
            for file in files:
                if file.lower().endswith(".mp3"):
                    file_path = os.path.join(root, file)
                    error_list = process_file(
                        file_path, quiet_mode=args.quiet, error_list=error_list
                    )

    # If it's a file, process it directly
    elif os.path.isfile(absolute_path):
        error_list = process_file(
            absolute_path, quiet_mode=args.quiet, error_list=error_list
        )

    else:
        print(f"The path '{absolute_path}' is not a valid file or directory.")

    # At the end of processing, display all collected errors
    if error_list:
        print("\nErrors during processing:")
        for error in error_list:
            print(f"- {error}")


if __name__ == "__main__":
    main()
