"""LyricLabel entry point.

Orchestrates file/directory processing using async I/O for parallel
Last.fm API requests.  Supports ``--quiet`` and ``--dry-run`` flags.
"""

import argparse
import asyncio
import os

import aiohttp

from lyriclabel.logger import get_logger
from lyriclabel.meta_edit import edit_metadata
from lyriclabel.meta_fetcher import fetch_metadata_from_lastfm
from lyriclabel.utils.parser import parse_filename

logger = get_logger("lyriclabel")


async def process_file(
    session: aiohttp.ClientSession,
    filepath: str,
    quiet_mode: bool = False,
    dry_run: bool = False,
    error_list: list | None = None,
) -> list:
    """Fetch metadata for *filepath* and write ID3 tags (unless dry-run).

    Parameters
    ----------
    session:
        Shared ``aiohttp.ClientSession`` for HTTP requests.
    filepath:
        Absolute path to the MP3 file.
    quiet_mode:
        When ``True`` suppresses informational output and auto-selects the
        first search result.
    dry_run:
        When ``True`` logs intended tag changes without modifying any file.
    error_list:
        Mutable list that error messages are appended to.
    """
    if error_list is None:
        error_list = []

    logger.debug("Processing file: %s", filepath)

    filename = os.path.basename(filepath)
    artist, title = parse_filename(filename)

    # Build a richer query when the artist is known
    query = f"{title} {artist}" if artist else title

    metadata = await fetch_metadata_from_lastfm(
        session, query, quiet_mode, filename, error_list
    )

    if metadata:
        edit_metadata(filepath, metadata, dry_run=dry_run)
        if not dry_run:
            logger.info("Metadata successfully added to '%s'.", filepath)
    else:
        logger.warning("Metadata could not be fetched for '%s'.", filepath)

    return error_list


async def _run(args: argparse.Namespace) -> None:
    """Async entry point that processes one file or an entire directory."""
    absolute_path = os.path.abspath(args.path)
    error_list: list[str] = []

    async with aiohttp.ClientSession() as session:
        if os.path.isdir(absolute_path):
            logger.info(
                "Processing all MP3 files in directory: %s", absolute_path
            )
            tasks = []
            for root, _dirs, files in os.walk(absolute_path):
                for filename in files:
                    if filename.lower().endswith(".mp3"):
                        fp = os.path.join(root, filename)
                        tasks.append(
                            process_file(
                                session,
                                fp,
                                quiet_mode=args.quiet,
                                dry_run=args.dry_run,
                                error_list=error_list,
                            )
                        )
            # Process all files concurrently
            await asyncio.gather(*tasks)

        elif os.path.isfile(absolute_path):
            await process_file(
                session,
                absolute_path,
                quiet_mode=args.quiet,
                dry_run=args.dry_run,
                error_list=error_list,
            )

        else:
            logger.error(
                "The path '%s' is not a valid file or directory.", absolute_path
            )

    if error_list:
        logger.warning("Errors during processing:")
        for error in error_list:
            logger.warning("  - %s", error)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LyricLabel: Fetch and edit song metadata."
    )
    parser.add_argument("path", help="Path to the song file or folder")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run in quiet mode (suppress non-essential output)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Log what WOULD be written to ID3 tags without modifying any files"
        ),
    )
    args = parser.parse_args()

    asyncio.run(_run(args))


if __name__ == "__main__":
    main()

