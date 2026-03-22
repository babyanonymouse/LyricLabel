from dataclasses import dataclass
from typing import Literal

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC
import mutagen.mp3

from lyriclabel.logging_config import get_logger


logger = get_logger("editor")


@dataclass(frozen=True)
class MetadataWriteResult:
    status: Literal["updated", "skipped_dry_run", "no_changes", "failed"]
    planned_changes: dict[str, dict[str, str | None]]
    message: str | None = None


def _normalize_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized if normalized else None


def _display_value(value: str | None) -> str:
    return value if value is not None else "<empty>"


def _first_text_value(frame: object) -> str | None:
    text = getattr(frame, "text", None)
    if isinstance(text, list) and text:
        return _normalize_value(str(text[0]))
    if isinstance(text, str):
        return _normalize_value(text)
    return None


def _extract_existing_tags(audio: MP3) -> dict[str, str | None]:
    return {
        "Title": _first_text_value(audio.get("TIT2")),
        "Artist": _first_text_value(audio.get("TPE1")),
        "Album": _first_text_value(audio.get("TALB")),
        "Genre": _first_text_value(audio.get("TCON")),
        "Year": _first_text_value(audio.get("TDRC")),
    }


def _target_tags(metadata: dict[str, str]) -> dict[str, str | None]:
    return {
        "Title": _normalize_value(metadata.get("track")),
        "Artist": _normalize_value(metadata.get("artist")),
        "Album": _normalize_value(metadata.get("album")),
        "Genre": _normalize_value(metadata.get("genre")),
        "Year": _normalize_value(metadata.get("year")),
    }


def _planned_changes(
    existing: dict[str, str | None],
    target: dict[str, str | None],
) -> dict[str, dict[str, str | None]]:
    changes: dict[str, dict[str, str | None]] = {}
    for field, new_value in target.items():
        if new_value is None:
            continue
        old_value = existing.get(field)
        if old_value != new_value:
            changes[field] = {"old": old_value, "new": new_value}
    return changes


def _apply_target_tags(audio: MP3, target: dict[str, str | None]) -> None:
    if target.get("Title") is not None:
        audio["TIT2"] = TIT2(encoding=3, text=target["Title"])
    if target.get("Artist") is not None:
        audio["TPE1"] = TPE1(encoding=3, text=target["Artist"])
    if target.get("Album") is not None:
        audio["TALB"] = TALB(encoding=3, text=target["Album"])
    if target.get("Genre") is not None:
        audio["TCON"] = TCON(encoding=3, text=target["Genre"])
    if target.get("Year") is not None:
        audio["TDRC"] = TDRC(encoding=3, text=target["Year"])


def edit_metadata(
    filepath: str,
    metadata: dict[str, str],
    *,
    dry_run: bool = False,
) -> MetadataWriteResult:
    try:
        # Open the MP3 file
        audio = MP3(filepath, ID3=ID3)

        existing_tags = _extract_existing_tags(audio)
        target = _target_tags(metadata)
        planned_changes = _planned_changes(existing_tags, target)

        if not planned_changes:
            logger.info("no metadata changes required", extra={"file_path": filepath})
            return MetadataWriteResult(
                status="no_changes",
                planned_changes={},
                message="No metadata differences detected.",
            )

        # Edit the ID3 tags
        _apply_target_tags(audio, target)

        if dry_run:
            for field, delta in planned_changes.items():
                logger.warning(
                    "[**DRY RUN**] Update '%s': '%s' -> '%s'",
                    field,
                    _display_value(delta["old"]),
                    _display_value(delta["new"]),
                    extra={
                        "file_path": filepath,
                        "dry_run": True,
                        "planned_changes": {field: delta},
                    },
                )
            logger.info(
                "dry-run changes prepared",
                extra={
                    "file_path": filepath,
                    "dry_run": True,
                    "planned_changes": planned_changes,
                },
            )
            return MetadataWriteResult(
                status="skipped_dry_run",
                planned_changes=planned_changes,
                message="Dry run enabled; no changes written.",
            )

        # Save changes
        audio.save()
        logger.info(
            "metadata write complete",
            extra={
                "file_path": filepath,
                "dry_run": False,
                "planned_changes": planned_changes,
            },
        )
        return MetadataWriteResult(
            status="updated",
            planned_changes=planned_changes,
            message="Metadata updated.",
        )

    except mutagen.mp3.HeaderNotFoundError:
        logger.error("invalid mp3 file", extra={"file_path": filepath}, exc_info=True)
        return MetadataWriteResult(
            status="failed",
            planned_changes={},
            message="Invalid MP3 file header.",
        )
    except Exception:
        logger.error(
            "metadata write failed",
            extra={"file_path": filepath},
            exc_info=True,
        )
        return MetadataWriteResult(
            status="failed",
            planned_changes={},
            message="Unhandled metadata write failure.",
        )
