"""Regex-based filename parser for MP3 files.

Supports two common naming patterns:
- ``Artist - Title.mp3``  →  artist="Artist", title="Title"
- ``TrackNo - Title.mp3`` →  artist=None,     title="Title"
  (where TrackNo is a purely numeric prefix, e.g. ``01``)
"""

import re


def parse_filename(filename: str) -> tuple[str | None, str]:
    """Parse an MP3 filename into ``(artist, title)``.

    Parameters
    ----------
    filename:
        Bare filename **including** the ``.mp3`` extension.

    Returns
    -------
    tuple[str | None, str]
        ``(artist, title)`` where *artist* is ``None`` when only a track
        number (or no delimiter) is present.
    """
    # Strip the .mp3 extension (case-insensitive)
    name = re.sub(r"\.mp3$", "", filename, flags=re.IGNORECASE).strip()

    # Match "Left - Right" where the delimiter is a hyphen or en-dash
    match = re.match(r"^(.+?)\s*[-\u2013]\s*(.+)$", name)
    if match:
        left = match.group(1).strip()
        right = match.group(2).strip()

        # If the left side is purely numeric it is a track number, not an artist
        if re.match(r"^\d+$", left):
            return None, _clean_title(right)

        return left, _clean_title(right)

    # Fallback: no delimiter found — treat the whole name as the title
    return None, _clean_title(name)


def _clean_title(title: str) -> str:
    """Strip common noise patterns from a song title."""
    # Remove "(feat. …)" / "(ft. …)" annotations
    title = re.sub(r"\(feat[^)]*\)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\(ft\.[^)]*\)", "", title, flags=re.IGNORECASE)
    # Collapse internal whitespace
    title = re.sub(r"\s+", " ", title)
    return title.strip()
