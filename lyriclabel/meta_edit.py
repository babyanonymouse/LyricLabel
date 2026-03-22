from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC
import mutagen.mp3

from lyriclabel.logging_config import get_logger


logger = get_logger("editor")


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
        logger.info("metadata write complete", extra={"file_path": filepath})

    except mutagen.mp3.HeaderNotFoundError:
        logger.error("invalid mp3 file", extra={"file_path": filepath}, exc_info=True)
    except Exception:
        logger.error(
            "metadata write failed",
            extra={"file_path": filepath},
            exc_info=True,
        )
