"""Last.fm metadata fetcher — async edition.

Uses ``aiohttp`` for non-blocking HTTP requests so that multiple files can
be processed concurrently.  Pass a shared ``aiohttp.ClientSession`` into
each function to reuse the underlying TCP connection pool.
"""

import asyncio
import os

import aiohttp
from dotenv import load_dotenv

from lyriclabel.logger import get_logger
from lyriclabel.utils.parser import parse_filename

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
_BASE_URL = "http://ws.audioscrobbler.com/2.0/"

logger = get_logger(__name__)


async def fetch_metadata_from_lastfm(
    session: aiohttp.ClientSession,
    song_name: str,
    quiet_mode: bool = False,
    filename: str | None = None,
    error_list: list | None = None,
) -> dict | None:
    """Search Last.fm for *song_name* and return a metadata dict or ``None``.

    In quiet mode the first result is chosen automatically.  In interactive
    mode the user is prompted to select a track.

    Parameters
    ----------
    session:
        A live ``aiohttp.ClientSession`` to reuse for the request.
    song_name:
        The query string sent to the Last.fm track.search endpoint.
    quiet_mode:
        When ``True`` the first search result is chosen without prompting.
    filename:
        Original filename (used in error messages).
    error_list:
        Mutable list that error messages are appended to.
    """
    if error_list is None:
        error_list = []

    logger.info("Searching for song: %s", song_name)

    params = {
        "method": "track.search",
        "track": song_name,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    try:
        async with session.get(_BASE_URL, params=params) as response:
            response.raise_for_status()
            search_data = await response.json(content_type=None)

        if "results" in search_data and "trackmatches" in search_data["results"]:
            tracks = search_data["results"]["trackmatches"]["track"]
            if tracks:
                if not quiet_mode:
                    logger.info(
                        "Found %d result(s) for '%s':", len(tracks), song_name
                    )
                    for i, track in enumerate(tracks):
                        logger.info(
                            "  %d. Artist: %s, Track: %s",
                            i + 1,
                            track["artist"],
                            track["name"],
                        )

                if quiet_mode:
                    return await fetch_detailed_metadata(
                        session, tracks[0], filename, error_list
                    )

                # Interactive selection — run blocking input() off the event loop
                raw = await asyncio.to_thread(
                    input, "\nPlease select the track number (or 0 to cancel): "
                )
                try:
                    choice = int(raw)
                except ValueError:
                    error_list.append(f"Invalid input for '{song_name}'.")
                    return None

                if choice == 0:
                    error_list.append(f"Search cancelled for '{song_name}'.")
                    return None
                elif 1 <= choice <= len(tracks):
                    return await fetch_detailed_metadata(
                        session, tracks[choice - 1], filename, error_list
                    )
                else:
                    error_list.append(f"Invalid choice for '{song_name}'.")
                    return None
            else:
                error_list.append(f"No matching tracks found for '{song_name}'.")
                return None
        else:
            error_list.append(f"No results found for song: '{song_name}'.")
            return None

    except aiohttp.ClientError as exc:
        error_list.append(f"Network error occurred for '{song_name}': {exc}")
        return None
    except ValueError as exc:
        error_list.append(f"Error decoding the response for '{song_name}': {exc}")
        return None
    except Exception as exc:  # noqa: BLE001
        error_list.append(
            f"An unexpected error occurred for '{song_name}': {exc}"
        )
        return None


async def fetch_detailed_metadata(
    session: aiohttp.ClientSession,
    track: dict,
    filename: str | None = None,
    error_list: list | None = None,
) -> dict | None:
    """Fetch detailed track info from Last.fm using ``track.getInfo``.

    Parameters
    ----------
    session:
        A live ``aiohttp.ClientSession`` to reuse for the request.
    track:
        A track dict as returned by the ``track.search`` endpoint.
    filename:
        Original filename (used in error messages).
    error_list:
        Mutable list that error messages are appended to.
    """
    if error_list is None:
        error_list = []

    params = {
        "method": "track.getInfo",
        "artist": track["artist"],
        "track": track["name"],
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    try:
        async with session.get(_BASE_URL, params=params) as response:
            response.raise_for_status()
            track_info_data = await response.json(content_type=None)

        if "track" in track_info_data:
            details = track_info_data["track"]
            metadata = {
                "artist": details.get("artist", {}).get("name", "Unknown"),
                "album": details.get("album", {}).get("title", "Unknown"),
                "track": details.get("name", "Unknown"),
                "genre": (
                    "Unknown"
                    if not details.get("toptags", {}).get("tag")
                    else details["toptags"]["tag"][0].get("name", "Unknown")
                ),
                # release_date may be absent; slice safely
                "year": (details.get("release_date") or "Unknown")[:4],
            }
            return metadata
        else:
            error_list.append(
                f"Detailed info could not be fetched for {filename}"
            )
            return None

    except aiohttp.ClientError as exc:
        error_list.append(
            f"Error fetching detailed info for '{filename}': {exc}"
        )
        return None
    except KeyError as exc:
        error_list.append(
            f"Missing expected metadata field for '{filename}': {exc}"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        error_list.append(
            f"An unexpected error occurred while fetching detailed info for '{filename}': {exc}"
        )
        return None


def extract_artist_and_title(filename: str) -> tuple[str | None, str]:
    """Thin wrapper around :func:`lyriclabel.utils.parser.parse_filename`.

    Kept for backwards compatibility with any external callers.
    """
    return parse_filename(filename)

