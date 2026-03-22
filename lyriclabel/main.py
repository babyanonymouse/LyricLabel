import argparse
import os

from lyriclabel.meta_edit import edit_metadata
from lyriclabel.meta_fetcher import fetch_metadata_from_lastfm


def process_file(filepath: str, quiet_mode: bool = False, error_list: list[str] | None = None) -> list[str]:
    """Process a single file: fetch metadata and update it."""
    if not quiet_mode:
        print(f"Processing file: {filepath}")

    # Extract title from the filename (we only need the basename).
    filename = os.path.basename(filepath)
    title = filename.replace(".mp3", "").strip()

    if error_list is None:
        error_list = []

    metadata = fetch_metadata_from_lastfm(title, quiet_mode, filename, error_list)

    if metadata:
        edit_metadata(filepath, metadata)
        if not quiet_mode:
            print(f"Metadata successfully added to '{filepath}'.")
    elif not quiet_mode:
        print(f"Metadata could not be fetched for '{filepath}'.")

    return error_list


def main() -> int:
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

    absolute_path = os.path.abspath(args.path)
    error_list: list[str] = []

    if os.path.isdir(absolute_path):
        if not args.quiet:
            print(f"Processing all mp3 files in directory: {absolute_path}")
        for root, _, files in os.walk(absolute_path):
            for file in files:
                if file.lower().endswith(".mp3"):
                    file_path = os.path.join(root, file)
                    error_list = process_file(
                        file_path, quiet_mode=args.quiet, error_list=error_list
                    )
    elif os.path.isfile(absolute_path):
        error_list = process_file(
            absolute_path, quiet_mode=args.quiet, error_list=error_list
        )
    else:
        print(f"The path '{absolute_path}' is not a valid file or directory.")
        return 2

    if error_list:
        print("\nErrors during processing:")
        for error in error_list:
            print(f"- {error}")

    return 0
