"""ID3 tag writer for MP3 files.

Supports a *dry-run* mode in which the tags that **would** be written are
logged but no file is modified.
"""

import mutagen.mp3
from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1
from mutagen.mp3 import MP3

from lyriclabel.logger import get_logger

logger = get_logger(__name__)


def edit_metadata(filepath: str, metadata: dict, dry_run: bool = False) -> None:
    """Write *metadata* into the ID3 tags of the MP3 at *filepath*.

    Parameters
    ----------
    filepath:
        Absolute or relative path to the target MP3 file.
    metadata:
        Dict with keys ``"track"``, ``"artist"``, ``"album"``, ``"genre"``,
        and ``"year"``.
    dry_run:
        When ``True`` the intended tag changes are logged but the file is
        **not** modified.
    """
    if dry_run:
        logger.info(
            "[DRY RUN] Would write to '%s': title=%r, artist=%r, album=%r, "
            "genre=%r, year=%r",
            filepath,
            metadata.get("track"),
            metadata.get("artist"),
            metadata.get("album"),
            metadata.get("genre"),
            metadata.get("year"),
        )
        return

    try:
        audio = MP3(filepath, ID3=ID3)

        audio["TIT2"] = TIT2(encoding=3, text=metadata["track"])
        audio["TPE1"] = TPE1(encoding=3, text=metadata["artist"])
        audio["TALB"] = TALB(encoding=3, text=metadata["album"])

        if "genre" in metadata:
            audio["TCON"] = TCON(encoding=3, text=metadata["genre"])

        if "year" in metadata:
            audio["TDRC"] = TDRC(encoding=3, text=metadata["year"])

        audio.save()

    except mutagen.mp3.HeaderNotFoundError:
        logger.error("Invalid MP3 file: %s", filepath)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error updating metadata for '%s': %s", filepath, exc)

