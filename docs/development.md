# Development Guide

This guide is for maintainers and contributors working on LyricLabel internals.

## Local Environment

Recommended setup:

```bash
uv venv
source .venv/bin/activate
uv sync --dev
```

Run CLI locally:

```bash
uv run lyriclabel <path>
```

## Quality Gates

Lint:

```bash
uv run ruff check .
```

Type check:

```bash
uv run mypy .
```

Both should pass before commit.

## Repository Layout

- [lyriclabel/main.py](lyriclabel/main.py): async orchestration and summary reporting.
- [lyriclabel/meta_fetcher.py](lyriclabel/meta_fetcher.py): Last.fm transport and extraction logic.
- [lyriclabel/meta_edit.py](lyriclabel/meta_edit.py): ID3 read/diff/write operations.
- [lyriclabel/parser.py](lyriclabel/parser.py): filename normalization and parse heuristics.
- [lyriclabel/logging_config.py](lyriclabel/logging_config.py): structured logging setup.
- [main.py](main.py): executable wrapper.

## Coding Practices

## Async boundaries

- Keep network I/O async.
- Keep mutagen writes off event loop (`asyncio.to_thread`).
- Avoid creating one HTTP session per file.

## Error handling

- Preserve per-file isolation in batch mode.
- Convert external failures into actionable log events.
- Avoid hard-failing the full run for a single bad file.

## Logging

- Include structured fields via `extra={...}`.
- Prefer stable key names for machine parsing.
- Emit one clear run summary at end.

## Type safety

- Annotate public/internal function signatures.
- Keep return contracts explicit for status-based workflows.

## Contributor Runbook

1. Create branch from current working branch.
2. Implement smallest coherent change.
3. Validate with ruff + mypy.
4. Run targeted dry-run over test files.
5. Commit with task-linked message.

Suggested validation command:

```bash
uv run lyriclabel test --dry-run --quiet --log-file /tmp/lyriclabel-dev-check.log
```

## Safe Change Areas

## Parser heuristics

Where: [lyriclabel/parser.py](lyriclabel/parser.py)

- Add normalization rules carefully.
- Keep backward compatibility with common patterns.

## Metadata fields

Where: [lyriclabel/meta_edit.py](lyriclabel/meta_edit.py)

- Add new ID3 frames behind explicit delta checks.
- Keep dry-run payloads aligned with write behavior.

## Retry/backoff policy

Where: [lyriclabel/meta_fetcher.py](lyriclabel/meta_fetcher.py)

- Tune defaults conservatively.
- Preserve `Retry-After` handling and jitter.

## Known Gaps and Next Improvements

- Wire [lyriclabel/config.py](lyriclabel/config.py) into runtime startup.
- Add unit tests for parser edge cases.
- Add integration tests with Last.fm response fixtures.
- Add explicit API for provider abstraction (future multi-source metadata).

## Release Checklist

1. Confirm lint/type checks pass.
2. Run dry-run on representative sample directory.
3. Run one non-dry run on disposable test files.
4. Verify JSON summary counters and error budget.
5. Update docs if behavior changed.

