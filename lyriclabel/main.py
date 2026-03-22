import asyncio
import argparse
import os

from lyriclabel.meta_edit import edit_metadata
from lyriclabel.meta_fetcher import create_lastfm_session, fetch_metadata_from_lastfm_async
from lyriclabel.parser import parse_filename


def _discover_mp3_files(path: str) -> list[str]:
    file_paths: list[str] = []
    for root, _, files in os.walk(path):
        for filename in files:
            if filename.lower().endswith(".mp3"):
                file_paths.append(os.path.abspath(os.path.join(root, filename)))
    # De-duplicate defensively to avoid double writes in odd directory structures.
    return list(dict.fromkeys(file_paths))


async def process_file(
    filepath: str,
    *,
    quiet_mode: bool = False,
    error_list: list[str] | None = None,
    semaphore: asyncio.Semaphore,
    interactive_select: bool = False,
    session,
) -> list[str]:
    """Process a single file: fetch metadata and update it."""
    async with semaphore:
        if not quiet_mode:
            print(f"Processing file: {filepath}")

        # Extract title from the filename (we only need the basename).
        filename = os.path.basename(filepath)
        parsed = parse_filename(filename)

        if error_list is None:
            error_list = []

        metadata = await fetch_metadata_from_lastfm_async(
            session,
            parsed,
            quiet_mode,
            filename,
            error_list,
            interactive_select=interactive_select,
        )

        if metadata:
            # Keep the display title from the filename while using cleaned search terms.
            metadata["track"] = parsed.title
            # Mutagen writes are blocking; run on a thread to avoid stalling the event loop.
            await asyncio.to_thread(edit_metadata, filepath, metadata)
            if not quiet_mode:
                print(f"Metadata successfully added to '{filepath}'.")
        elif not quiet_mode:
            print(f"Metadata could not be fetched for '{filepath}'.")

        return error_list


async def run_async(
    absolute_path: str,
    *,
    quiet_mode: bool,
    concurrency: int,
) -> tuple[int, list[str]]:
    error_list: list[str] = []
    semaphore = asyncio.Semaphore(concurrency)

    async with create_lastfm_session() as session:
        if os.path.isdir(absolute_path):
            if not quiet_mode:
                print(f"Processing all mp3 files in directory: {absolute_path}")

            file_paths = _discover_mp3_files(absolute_path)
            tasks = [
                process_file(
                    file_path,
                    quiet_mode=quiet_mode,
                    error_list=error_list,
                    semaphore=semaphore,
                    interactive_select=False,
                    session=session,
                )
                for file_path in file_paths
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    error_list.append(
                        f"Unexpected async processing error: {type(result).__name__}: {result}"
                    )
            return 0, error_list

        if os.path.isfile(absolute_path):
            await process_file(
                absolute_path,
                quiet_mode=quiet_mode,
                error_list=error_list,
                semaphore=semaphore,
                interactive_select=not quiet_mode,
                session=session,
            )
            return 0, error_list

    return 2, [f"The path '{absolute_path}' is not a valid file or directory."]


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
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Maximum number of files to process concurrently (default: 5)",
    )
    args = parser.parse_args()

    if args.concurrency < 1:
        print("--concurrency must be at least 1")
        return 2

    absolute_path = os.path.abspath(args.path)

    status_code, error_list = asyncio.run(
        run_async(
            absolute_path,
            quiet_mode=args.quiet,
            concurrency=args.concurrency,
        )
    )

    if status_code == 2:
        print(error_list[0])
        return 2

    if error_list:
        print("\nErrors during processing:")
        for error in error_list:
            print(f"- {error}")

    return 0
