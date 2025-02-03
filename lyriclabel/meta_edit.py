from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC
import mutagen.mp3


def edit_metadata(filepath, metadata):
    try:
        # Open the MP3 file
        audio = MP3(filepath, ID3=ID3)

        # Edit the ID3 tags
        audio["TIT2"] = TIT2(encoding=3, text=metadata["track"])  # Title (Track Name)
        audio["TPE1"] = TPE1(encoding=3, text=metadata["artist"])  # Artist
        audio["TALB"] = TALB(encoding=3, text=metadata["album"])  # Album

        # Add the missing metadata fields
        if "genre" in metadata:
            audio["TCON"] = TCON(encoding=3, text=metadata["genre"])  # Genre

        if "year" in metadata:
            audio["TDRC"] = TDRC(encoding=3, text=metadata["year"])  # Year

        # Save changes
        audio.save()

    except mutagen.mp3.HeaderNotFoundError:
        print(f"Invalid MP3 file: {filepath}")
    except Exception as e:
        print(f"Error updating metadata for '{filepath}': {e}")
