import asyncio
import argparse
import os
from collections import Counter
from dataclasses import dataclass

from dotenv import load_dotenv

from lyriclabel.config import AppConfig, load_config, parse_env_bool
from lyriclabel.logging_config import configure_logging, get_logger
from lyriclabel.meta_edit import edit_metadata
from lyriclabel.meta_fetcher import create_lastfm_session, fetch_metadata_from_lastfm_async
from lyriclabel.parser import parse_filename


logger = get_logger("main")


@dataclass(frozen=True)
class ProcessOutcome:
    status: str
    file_path: str


@dataclass(frozen=True)
class RuntimeSettings:
    api_key: str | None
    quiet: bool
    concurrency: int
    dry_run: bool
    log_file: str | None


def _resolve_settings(args: argparse.Namespace, file_config: AppConfig) -> RuntimeSettings:
    env_api_key = os.getenv("LASTFM_API_KEY")
    env_log_file = os.getenv("LYRICLABEL_LOG_FILE")

    env_quiet = parse_env_bool(os.getenv("LYRICLABEL_QUIET"), key_name="LYRICLABEL_QUIET")
    env_dry_run = parse_env_bool(
        os.getenv("LYRICLABEL_DRY_RUN"), key_name="LYRICLABEL_DRY_RUN"
    )

    env_concurrency_raw = os.getenv("LYRICLABEL_CONCURRENCY")
    env_concurrency: int | None = None
    if env_concurrency_raw is not None:
        try:
            env_concurrency = int(env_concurrency_raw)
        except ValueError as exc:
            raise ValueError(
                "Invalid LYRICLABEL_CONCURRENCY environment value. Must be an integer >= 1."
            ) from exc

    quiet = (
        args.quiet
        if args.quiet is not None
        else (env_quiet if env_quiet is not None else file_config.quiet)
    )
    dry_run = (
        args.dry_run
        if args.dry_run is not None
        else (env_dry_run if env_dry_run is not None else file_config.dry_run)
    )
    concurrency = (
        args.concurrency
        if args.concurrency is not None
        else (
            env_concurrency if env_concurrency is not None else file_config.concurrency
        )
    )
    log_file = (
        args.log_file
        if args.log_file is not None
        else (env_log_file if env_log_file is not None else file_config.log_file)
    )
    api_key = env_api_key or file_config.lastfm_api_key

    if concurrency < 1:
        raise ValueError("Invalid concurrency value. Must be >= 1.")

    return RuntimeSettings(
        api_key=api_key,
        quiet=quiet,
        concurrency=concurrency,
        dry_run=dry_run,
        log_file=log_file,
    )


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
    api_key: str,
    quiet_mode: bool = False,
    error_list: list[str] | None = None,
    semaphore: asyncio.Semaphore,
    interactive_select: bool = False,
    session,
    dry_run: bool = False,
) -> ProcessOutcome:
    """Process a single file: fetch metadata and update it."""
    async with semaphore:
        if not quiet_mode:
            logger.info("processing file", extra={"file_path": filepath})

        # Extract title from the filename (we only need the basename).
        filename = os.path.basename(filepath)
        parsed = parse_filename(filename)

        if error_list is None:
            error_list = []

        metadata = await fetch_metadata_from_lastfm_async(
            session,
            api_key,
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
            write_result = await asyncio.to_thread(
                edit_metadata,
                filepath,
                metadata,
                dry_run=dry_run,
            )
            if write_result.status == "failed":
                if write_result.message:
                    error_list.append(f"{filepath}: {write_result.message}")
                return ProcessOutcome(status="write_failed", file_path=filepath)
            if write_result.status == "updated" and not quiet_mode:
                logger.info("metadata updated", extra={"file_path": filepath})
            if write_result.status == "skipped_dry_run" and not quiet_mode:
                logger.info("dry-run write skipped", extra={"file_path": filepath})
            return ProcessOutcome(status=write_result.status, file_path=filepath)

        if not quiet_mode:
            logger.warning("metadata unavailable", extra={"file_path": filepath})
        return ProcessOutcome(status="metadata_unavailable", file_path=filepath)



async def run_async(
    absolute_path: str,
    *,
    api_key: str,
    quiet_mode: bool,
    concurrency: int,
    dry_run: bool,
) -> tuple[int, list[str], Counter[str]]:
    error_list: list[str] = []
    semaphore = asyncio.Semaphore(concurrency)
    status_counts: Counter[str] = Counter()

    async with create_lastfm_session() as session:
        if os.path.isdir(absolute_path):
            if not quiet_mode:
                logger.info(
                    "processing directory",
                    extra={
                        "path": absolute_path,
                        "concurrency": concurrency,
                        "dry_run": dry_run,
                    },
                )

            file_paths = _discover_mp3_files(absolute_path)
            tasks = [
                process_file(
                    file_path,
                    api_key=api_key,
                    quiet_mode=quiet_mode,
                    error_list=error_list,
                    semaphore=semaphore,
                    interactive_select=False,
                    session=session,
                    dry_run=dry_run,
                )
                for file_path in file_paths
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, BaseException):
                    error_list.append(
                        f"Unexpected async processing error: {type(result).__name__}: {result}"
                    )
                    logger.error(
                        "unexpected async processing error",
                        exc_info=(type(result), result, result.__traceback__),
                    )
                    continue
                status_counts[result.status] += 1
            return 0, error_list, status_counts

        if os.path.isfile(absolute_path):
            result = await process_file(
                absolute_path,
                api_key=api_key,
                quiet_mode=quiet_mode,
                error_list=error_list,
                semaphore=semaphore,
                interactive_select=not quiet_mode,
                session=session,
                dry_run=dry_run,
            )
            status_counts[result.status] += 1
            return 0, error_list, status_counts

    return 2, [f"The path '{absolute_path}' is not a valid file or directory."], status_counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LyricLabel: Fetch and edit song metadata."
    )
    parser.add_argument("path", help="Path to the song file or folder")
    parser.add_argument(
        "--quiet",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run in quiet mode (overrides env/config)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Maximum number of files to process concurrently (overrides env/config)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Optional path for the rotating log file (overrides env/config)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to config.toml (default: XDG config location)",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Preview metadata changes without writing to files (overrides env/config)",
    )
    args = parser.parse_args()

    load_dotenv()

    try:
        loaded_config = load_config(args.config)
        settings = _resolve_settings(args, loaded_config.config)
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return 2

    log_path = configure_logging(quiet=settings.quiet, log_file=settings.log_file)
    logger.info(
        "lyriclabel start",
        extra={
            "log_path": str(log_path),
            "dry_run": settings.dry_run,
            "config_path": str(loaded_config.path),
            "config_exists": loaded_config.exists,
        },
    )
    logger.debug(
        "config resolved",
        extra={"config_path": str(loaded_config.path), "config_exists": loaded_config.exists},
    )
    for warning in loaded_config.warnings:
        logger.warning(warning)

    if not settings.api_key:
        logger.error(
            "missing LASTFM_API_KEY",
            extra={"config_path": str(loaded_config.path)},
        )
        return 2

    absolute_path = os.path.abspath(args.path)

    status_code, error_list, status_counts = asyncio.run(
        run_async(
            absolute_path,
            api_key=settings.api_key,
            quiet_mode=settings.quiet,
            concurrency=settings.concurrency,
            dry_run=settings.dry_run,
        )
    )

    if status_code == 2:
        logger.error(error_list[0])
        return 2

    if error_list:
        logger.warning("errors encountered during processing")
        for error in error_list:
            logger.error(error)

    logger.info(
        "run summary",
        extra={
            "dry_run": settings.dry_run,
            "updated": status_counts.get("updated", 0),
            "would_have_updated": status_counts.get("skipped_dry_run", 0),
            "no_changes": status_counts.get("no_changes", 0),
            "metadata_unavailable": status_counts.get("metadata_unavailable", 0),
            "write_failed": status_counts.get("write_failed", 0),
            "errors": len(error_list),
        },
    )
    logger.info("lyriclabel complete", extra={"errors": len(error_list)})
    return 0
