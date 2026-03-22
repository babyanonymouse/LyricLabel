from dataclasses import dataclass
import re


DELIMITER_PATTERN = re.compile(r"\s*[-_~|]\s*")
TRACK_NUMBER_PATTERN = re.compile(r"^\s*(\d{1,3})(?:[.\-_\s]+)(.+)$")
WHITESPACE_PATTERN = re.compile(r"\s+")
FEAT_PATTERN = re.compile(
    r"\s*[\[(]\s*(?:feat|ft)\.?\s+[^\])]+[\])]\s*",
    re.IGNORECASE,
)
DOUBLE_MP3_PATTERN = re.compile(r"(?:\.mp3)+$", re.IGNORECASE)
AND_PATTERN = re.compile(r"\b(and|&)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedFilename:
    raw_filename: str
    title: str
    search_title: str
    artist: str | None = None
    track_no: str | None = None
    is_structured: bool = False


def _normalize_spaces(value: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", value).strip()


def _strip_mp3_extensions(filename: str) -> str:
    stripped = DOUBLE_MP3_PATTERN.sub("", filename)
    return stripped.strip()


def _normalize_for_search(value: str) -> str:
    # Remove featuring segments that often reduce Last.fm search relevance.
    without_feat = FEAT_PATTERN.sub(" ", value)
    without_feat = _normalize_spaces(without_feat)
    return _normalize_spaces(AND_PATTERN.sub("and", without_feat))


def _find_artist_title_split_candidates(stem: str) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for match in DELIMITER_PATTERN.finditer(stem):
        left = _normalize_spaces(stem[: match.start()])
        right = _normalize_spaces(stem[match.end() :])
        if left and right:
            candidates.append((left, right))
    return candidates


def _pick_best_candidate(candidates: list[tuple[str, str]]) -> tuple[str, str] | None:
    if not candidates:
        return None

    # Ranked heuristic: prefer balanced splits; preserve earliest split for ties.
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (abs(len(item[1][0]) - len(item[1][1])), item[0]),
    )
    return ranked[0][1]


def parse_filename(filename: str) -> ParsedFilename:
    raw = filename
    stem = _strip_mp3_extensions(filename)
    stem = _normalize_spaces(stem)

    # First, try the most common structured pattern: Artist - Title.
    candidate = _pick_best_candidate(_find_artist_title_split_candidates(stem))
    if candidate is not None:
        artist, title = candidate
        return ParsedFilename(
            raw_filename=raw,
            title=title,
            search_title=_normalize_for_search(title),
            artist=_normalize_for_search(artist),
            track_no=None,
            is_structured=True,
        )

    # Next, match TrackNo - Title style when no artist split was found.
    track_match = TRACK_NUMBER_PATTERN.match(stem)
    if track_match:
        track_no = track_match.group(1)
        title = _normalize_spaces(track_match.group(2))
        return ParsedFilename(
            raw_filename=raw,
            title=title,
            search_title=_normalize_for_search(title),
            artist=None,
            track_no=track_no,
            is_structured=True,
        )

    # Fallback for unstructured names.
    return ParsedFilename(
        raw_filename=raw,
        title=stem,
        search_title=_normalize_for_search(stem),
        artist=None,
        track_no=None,
        is_structured=False,
    )