import argparse
from lyriclabel.fetch_metadata import fetch_metadata
from lyriclabel.edit_metadata import edit_metadata


def main():
    parser = argparse.ArgumentParser(
        description="LyricLabel: Fetch and edit song metadata."
    )
    parser.add_argument("filepath", help="Path to the song file or folder")
    args = parser.parse_args()

    # Fetch metadata for the song
    metadata = fetch_metadata(args.filepath)

    if metadata:
        # Embed metadata into the song file
        edit_metadata(args.filepath, metadata)
        print("Metadata successfully added to the song file.")
    else:
        print("Metadata could not be fetched.")


if __name__ == "__main__":
    main()
