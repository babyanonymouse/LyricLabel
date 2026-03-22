import asyncio
import os
import random
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import aiohttp
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"
DEFAULT_USER_AGENT = "LyricLabel/0.1 (+https://codex.atlassian.net)"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_RETRIES = 4


@asynccontextmanager
async def create_lastfm_session(
    user_agent: str = DEFAULT_USER_AGENT,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> AsyncIterator[aiohttp.ClientSession]:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    headers = {"User-Agent": user_agent}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        yield session


async def _request_json(
    session: aiohttp.ClientSession,
    params: dict[str, str],
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict[str, Any]:
    for attempt in range(max_retries + 1):
        try:
            async with session.get(LASTFM_BASE_URL, params=params) as response:
                if response.status == 429 and attempt < max_retries:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        sleep_seconds = float(retry_after)
                    else:
                        # Exponential backoff with jitter for rate limit bursts.
                        sleep_seconds = (2 ** attempt) + random.uniform(0, 0.25)
                    await asyncio.sleep(sleep_seconds)
                    continue

                if response.status >= 500 and attempt < max_retries:
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 0.25))
                    continue

                response.raise_for_status()
                payload = await response.json(content_type=None)
                if not isinstance(payload, dict):
                    raise ValueError("Unexpected non-dict JSON payload from Last.fm")
                return cast(dict[str, Any], payload)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            if attempt >= max_retries:
                raise
            await asyncio.sleep((2 ** attempt) + random.uniform(0, 0.25))

    raise RuntimeError("Failed to get JSON response from Last.fm")


def _coerce_tracks(search_data: dict) -> list[dict]:
    tracks = search_data.get("results", {}).get("trackmatches", {}).get("track", [])
    if isinstance(tracks, dict):
        return [tracks]
    if isinstance(tracks, list):
        return [track for track in tracks if isinstance(track, dict)]
    return []


def _extract_year(track_details: dict) -> str:
    release_date = str(track_details.get("release_date", "")).strip()
    if len(release_date) >= 4 and release_date[:4].isdigit():
        return release_date[:4]

    published = str(track_details.get("wiki", {}).get("published", "")).strip()
    if len(published) >= 4 and published[:4].isdigit():
        return published[:4]
    return "Unknown"


def _extract_genre(track_details: dict) -> str:
    tags = track_details.get("toptags", {}).get("tag", [])
    if isinstance(tags, dict):
        tags = [tags]
    if not isinstance(tags, list) or not tags:
        return "Unknown"
    first_tag = tags[0]
    if not isinstance(first_tag, dict):
        return "Unknown"
    return str(first_tag.get("name", "Unknown"))


async def fetch_detailed_metadata_async(
    session: aiohttp.ClientSession,
    track: dict,
    filename: str | None = None,
    error_list: list[str] | None = None,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict | None:
    if error_list is None:
        error_list = []

    params = {
        "method": "track.getInfo",
        "artist": str(track.get("artist", "")),
        "track": str(track.get("name", "")),
        "api_key": LASTFM_API_KEY or "",
        "format": "json",
    }

    try:
        track_info_data = await _request_json(session, params, max_retries=max_retries)
    except Exception as exc:
        error_list.append(f"Error fetching detailed info for '{filename}': {exc}")
        return None

    track_details = track_info_data.get("track")
    if not isinstance(track_details, dict):
        error_list.append(f"Detailed info could not be fetched for {filename}")
        return None

    artist_data = track_details.get("artist", {})
    if isinstance(artist_data, dict):
        artist_name = str(artist_data.get("name", "Unknown"))
    else:
        artist_name = str(artist_data or "Unknown")

    album_data = track_details.get("album", {})
    if isinstance(album_data, dict):
        album_title = str(album_data.get("title", "Unknown"))
    else:
        album_title = str(album_data or "Unknown")

    return {
        "artist": artist_name,
        "album": album_title,
        "track": str(track_details.get("name", "Unknown")),
        "genre": _extract_genre(track_details),
        "year": _extract_year(track_details),
    }


async def fetch_metadata_from_lastfm_async(
    session: aiohttp.ClientSession,
    song_name: str,
    quiet_mode: bool = False,
    filename: str | None = None,
    error_list: list[str] | None = None,
    *,
    interactive_select: bool = False,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict | None:
    if error_list is None:
        error_list = []

    if not LASTFM_API_KEY:
        error_list.append("LASTFM_API_KEY is missing. Add it to your .env file.")
        return None

    if not quiet_mode:
        print(f"Searching for song: {song_name}")

    params = {
        "method": "track.search",
        "track": song_name,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    try:
        search_data = await _request_json(session, params, max_retries=max_retries)
    except Exception as exc:
        error_list.append(f"Network error occurred for '{song_name}': {exc}")
        return None

    tracks = _coerce_tracks(search_data)
    if not tracks:
        error_list.append(f"No matching tracks found for '{song_name}'.")
        return None

    if not quiet_mode:
        print(f"Found {len(tracks)} result(s) for '{song_name}':\n")
        for i, track in enumerate(tracks[:10], start=1):
            artist = track.get("artist", "Unknown")
            name = track.get("name", "Unknown")
            print(f"{i}. Artist: {artist}, Track: {name}")

    selected_track = tracks[0]
    if interactive_select and not quiet_mode:
        try:
            choice = int(input("\nPlease select the track number (or 0 to cancel): "))
            if choice == 0:
                error_list.append(f"Search cancelled for '{song_name}'.")
                return None
            if 1 <= choice <= len(tracks):
                selected_track = tracks[choice - 1]
            else:
                error_list.append(f"Invalid choice for '{song_name}'.")
                return None
        except ValueError:
            error_list.append(f"Invalid choice for '{song_name}'.")
            return None

    return await fetch_detailed_metadata_async(
        session,
        selected_track,
        filename,
        error_list,
        max_retries=max_retries,
    )
