"""Content ingestion — ADR 0014, CONTENT_INGESTION.md §§ 2-8.

Standard library only (layout rule 1 permits `pathlib` here; reading audio
bytes is `MediaProbe`'s job, never this module's). No other module guesses a
`ContentKind` — this is the one place that does.
"""

from __future__ import annotations

import logging
import re
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from aqeno.domain.content import (
    Chapter,
    ContentId,
    ContentItem,
    ContentKind,
    Fingerprint,
    LocalFileSource,
    MemberFile,
)
from aqeno.ports.clock import Clock
from aqeno.ports.media_probe import MediaProbe, ProbedFile
from aqeno.ports.persistence import Library

logger = logging.getLogger(__name__)

RECOGNIZED_EXTENSIONS = frozenset(
    {".mp3", ".flac", ".ogg", ".opus", ".m4a", ".m4b", ".wav", ".aac", ".wma"}
)

_AUDIOBOOK_KEYWORDS = ("hörbuch", "audiobook", "lesung", "spoken word")
_DRAMA_KEYWORDS = ("hörspiel", "audio drama", "radio play", "radio drama")

# CONTENT_INGESTION.md § 5: "a fixed constant in code, not a setting". Not
# exhaustive — it exists to catch the ordinary case, not every genre tag ever
# written; rule 8's ambiguity default is what protects the rest.
MUSIC_GENRES = frozenset(
    {
        "pop",
        "rock",
        "electronic",
        "dance",
        "house",
        "techno",
        "hip hop",
        "hip-hop",
        "rap",
        "jazz",
        "classical",
        "metal",
        "folk",
        "country",
        "r&b",
        "soul",
        "blues",
        "indie",
        "alternative",
        "reggae",
        "punk",
        "funk",
    }
)

_MUSIC_ALBUM_MIN_CHAPTERS = 5
_MUSIC_ALBUM_MEAN_MAX = timedelta(minutes=8)
_MUSIC_TRACK_MAX_DURATION = timedelta(minutes=10)

_ARTWORK_STEMS = ("cover", "folder", "front")
_ARTWORK_EXTS = (".jpg", ".jpeg", ".png", ".webp")
_ARTWORK_MIME_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

_DIGIT_RUN = re.compile(r"(\d+)")
_CUE_TITLE_RE = re.compile(r'TITLE\s+"(.*)"', re.IGNORECASE)
_CUE_INDEX01_RE = re.compile(r"INDEX\s+01\s+(\d+):(\d+):(\d+)", re.IGNORECASE)


def natural_sort_key(name: str) -> list[tuple[int, object]]:
    """Digit runs compared numerically, so `Kapitel 2` precedes `Kapitel 10`
    (CONTENT_INGESTION.md § 6 rule 5). Never a byte sort (ADR 0005)."""
    return [
        (1, int(part)) if part.isdigit() else (0, part.casefold())
        for part in _DIGIT_RUN.split(name)
        if part != ""
    ]


# ---------------------------------------------------------------------------
# § 2-3: discovery and grouping into work candidates
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkCandidate:
    """One directory (or one root-level file) that becomes at most one work."""

    directory: Path
    files: tuple[Path, ...]
    is_root_singleton: bool
    """True for a file lying directly in a library root: its own single-chapter
    work, sharing `directory` with unrelated siblings, so sidecar files
    (aqeno.toml, cue, playlist, cover art) in that directory do not apply to it
    (CONTENT_INGESTION.md § 3)."""


def discover_work_candidates(
    roots: Sequence[Path], *, follow_symlinks: bool
) -> list[WorkCandidate]:
    candidates: list[WorkCandidate] = []
    for root in roots:
        if not root.is_dir():
            logger.warning("library root missing or unreadable, skipping: %s", root)
            continue
        visited: set[Path] = set()
        _walk(root, root, follow_symlinks=follow_symlinks, visited=visited, candidates=candidates)
    return candidates


def _walk(
    root: Path,
    directory: Path,
    *,
    follow_symlinks: bool,
    visited: set[Path],
    candidates: list[WorkCandidate],
) -> None:
    try:
        real = directory.resolve()
    except OSError:
        return
    if real in visited:
        return
    visited.add(real)

    try:
        entries = sorted(directory.iterdir())
    except OSError as exc:
        logger.warning("cannot read directory %s: %s", directory, exc)
        return

    audio_files: list[Path] = []
    subdirs: list[Path] = []
    for entry in entries:
        if entry.name.startswith("."):
            continue
        try:
            is_symlink = entry.is_symlink()
            if is_symlink and not follow_symlinks:
                continue
            is_dir = entry.is_dir()
        except OSError:
            continue
        if is_dir:
            subdirs.append(entry)
        elif entry.suffix.lower() in RECOGNIZED_EXTENSIONS:
            audio_files.append(entry)

    if audio_files:
        if directory == root:
            for file in audio_files:
                candidates.append(
                    WorkCandidate(directory=root, files=(file,), is_root_singleton=True)
                )
        else:
            candidates.append(
                WorkCandidate(
                    directory=directory, files=tuple(audio_files), is_root_singleton=False
                )
            )

    for sub in subdirs:
        _walk(root, sub, follow_symlinks=follow_symlinks, visited=visited, candidates=candidates)


# ---------------------------------------------------------------------------
# § 4: identity resolution
# ---------------------------------------------------------------------------


def resolve_identity(fingerprints: Sequence[Fingerprint], library: Library) -> ContentId:
    """A fresh `ContentId` unless matches concentrate in one known work at more
    than half of its stored member files (CONTENT_INGESTION.md § 4)."""
    matches: dict[ContentId, int] = {}
    for fingerprint in fingerprints:
        found = library.find_by_fingerprint(fingerprint)
        if found is not None:
            matches[found] = matches.get(found, 0) + 1

    if len(matches) != 1:
        return ContentId()

    ((content_id, matched_count),) = matches.items()
    total = len(library.get_member_files(content_id))
    if total > 0 and matched_count * 2 > total:
        return content_id
    return ContentId()


# ---------------------------------------------------------------------------
# § 6: chapters
# ---------------------------------------------------------------------------


def _track_number_order(files: Sequence[Path], probes: dict[Path, ProbedFile]) -> list[Path] | None:
    numbers = [probes[f].track_number for f in files]
    if any(n is None for n in numbers) or len(set(numbers)) != len(numbers):
        return None
    return sorted(files, key=lambda f: probes[f].track_number)  # type: ignore[arg-type,return-value]


def _playlist_order(directory: Path, files: Sequence[Path]) -> list[Path] | None:
    file_set = set(files)
    for pattern in ("*.m3u", "*.m3u8", "*.M3U", "*.M3U8"):
        for playlist in sorted(directory.glob(pattern)):
            try:
                lines = playlist.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            ordered: list[Path] = []
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                candidate = (directory / stripped).resolve()
                if candidate in {f.resolve() for f in files}:
                    matching = next((f for f in files if f.resolve() == candidate), None)
                    if matching is not None:
                        ordered.append(matching)
            if ordered and set(ordered) == file_set:
                return ordered
    return None


def _cue_chapters(
    directory: Path, only_file: Path, duration: timedelta | None
) -> list[Chapter] | None:
    """External `.cue` file for a single-file work (CONTENT_INGESTION.md § 6
    rule 2). A CUE referencing a different file, or one that fails to parse, is
    ignored — falling through to the next chapter source is always safe."""
    for cue_path in sorted(directory.glob("*.cue")) + sorted(directory.glob("*.CUE")):
        try:
            text = cue_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        entries: list[tuple[str | None, timedelta]] = []
        pending_title: str | None = None
        for line in text.splitlines():
            title_match = _CUE_TITLE_RE.search(line)
            if title_match:
                pending_title = title_match.group(1)
                continue
            index_match = _CUE_INDEX01_RE.search(line)
            if index_match:
                minutes, seconds, frames = (int(g) for g in index_match.groups())
                start = timedelta(
                    minutes=minutes, seconds=seconds, milliseconds=frames * 1000 // 75
                )
                entries.append((pending_title, start))
                pending_title = None
        if not entries:
            continue
        chapters: list[Chapter] = []
        for i, (title, start) in enumerate(entries):
            end = entries[i + 1][1] if i + 1 < len(entries) else duration
            chap_duration = (end - start) if end is not None else None
            chapters.append(Chapter(index=i, title=title, start=start, duration=chap_duration))
        return chapters
    return None


def build_chapters(
    directory: Path, files: Sequence[Path], probes: dict[Path, ProbedFile]
) -> tuple[Chapter, ...]:
    """CONTENT_INGESTION.md § 6. `files` holds only files that probed with a
    usable duration — an excluded file never reaches here."""
    if len(files) == 1:
        only = files[0]
        probed = probes[only]
        if probed.chapters:
            return tuple(
                Chapter(index=i, title=c.title, start=c.start, duration=c.duration)
                for i, c in enumerate(probed.chapters)
            )
        cue = _cue_chapters(directory, only, probed.duration)
        if cue is not None:
            return tuple(cue)
        return (Chapter(index=0, title=probed.title, start=timedelta(0), duration=probed.duration),)

    order = (
        _playlist_order(directory, files)
        or _track_number_order(files, probes)
        or sorted(files, key=lambda f: natural_sort_key(f.name))
    )

    chapters: list[Chapter] = []
    cursor = timedelta(0)
    for i, path in enumerate(order):
        probed = probes[path]
        duration = probed.duration
        if duration is None:  # pragma: no cover — excluded upstream, defensive only
            continue
        chapters.append(
            Chapter(
                index=i,
                title=probed.title or path.stem,
                start=cursor,
                duration=duration,
                source=LocalFileSource(path=path),
            )
        )
        cursor += duration
    return tuple(chapters)


# ---------------------------------------------------------------------------
# § 9: the aqeno.toml sidecar
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Sidecar:
    title: str | None = None
    kind: ContentKind | None = None
    language: str | None = None


def _read_sidecar(directory: Path) -> _Sidecar:
    path = directory / "aqeno.toml"
    if not path.is_file():
        return _Sidecar()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        logger.warning("ignoring malformed aqeno.toml in %s: %s", directory, exc)
        return _Sidecar()

    title = raw.get("title")
    title = title if isinstance(title, str) else None
    language = raw.get("language")
    language = language if isinstance(language, str) else None

    kind: ContentKind | None = None
    kind_raw = raw.get("kind")
    if isinstance(kind_raw, str):
        try:
            kind = ContentKind(kind_raw)
        except ValueError:
            logger.warning("aqeno.toml in %s: unknown kind %r, ignored", directory, kind_raw)

    return _Sidecar(title=title, kind=kind, language=language)


# ---------------------------------------------------------------------------
# § 5: kind inference
# ---------------------------------------------------------------------------


def _first_present(values: Sequence[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None


def infer_kind(
    *,
    existing: ContentItem | None,
    sidecar: _Sidecar,
    probes: Sequence[ProbedFile],
    chapters: tuple[Chapter, ...],
) -> tuple[ContentKind, str]:
    """First matching rule wins (CONTENT_INGESTION.md § 5). Returns
    `(kind, rule)` so the caller can store why."""
    if existing is not None and existing.kind_overridden:
        return existing.kind, "1-manager-override"

    if sidecar.kind is not None:
        return sidecar.kind, "2-aqeno-toml"

    if any(p.path.suffix.lower() == ".m4b" for p in probes):
        return ContentKind.AUDIOBOOK, "3-m4b-extension"

    genre = _first_present([p.genre for p in probes])
    album = _first_present([p.album for p in probes])
    tag_text = " ".join(v for v in (genre, album) if v).casefold()

    if any(keyword in tag_text for keyword in _AUDIOBOOK_KEYWORDS):
        return ContentKind.AUDIOBOOK, "4-audiobook-keyword"
    if any(keyword in tag_text for keyword in _DRAMA_KEYWORDS):
        return ContentKind.AUDIO_DRAMA, "5-drama-keyword"

    genre_cf = (genre or "").casefold()
    if any(g in genre_cf for g in MUSIC_GENRES) and len(chapters) >= _MUSIC_ALBUM_MIN_CHAPTERS:
        durations = [c.duration for c in chapters if c.duration is not None]
        if len(durations) == len(chapters):
            mean = sum(durations, timedelta()) / len(durations)
            if mean < _MUSIC_ALBUM_MEAN_MAX:
                return ContentKind.MUSIC_ALBUM, "6-music-genre-and-shape"

    if (
        len(chapters) == 1
        and chapters[0].duration is not None
        and chapters[0].duration < _MUSIC_TRACK_MAX_DURATION
    ):
        return ContentKind.MUSIC_TRACK, "7-short-single-file"

    return ContentKind.AUDIO_DRAMA, "8-ambiguity-default"


# ---------------------------------------------------------------------------
# § 7: artwork extraction
# ---------------------------------------------------------------------------


def _resolve_artwork(
    *,
    content_id: ContentId,
    directory: Path | None,
    first_probe: ProbedFile,
    artwork_dir: Path,
) -> Path | None:
    if first_probe.artwork is not None:
        ext = _ARTWORK_MIME_EXT.get(first_probe.artwork_mime or "", ".jpg")
        target = artwork_dir / f"{content_id.value}{ext}"
        if not target.exists():
            try:
                artwork_dir.mkdir(parents=True, exist_ok=True)
                target.write_bytes(first_probe.artwork)
            except OSError as exc:
                logger.warning("could not extract artwork for %s: %s", content_id.value, exc)
                return None
        return target

    if directory is not None:
        for stem in _ARTWORK_STEMS:
            for ext in _ARTWORK_EXTS:
                for candidate_name in (f"{stem}{ext}", f"{stem}{ext.upper()}"):
                    candidate = directory / candidate_name
                    if candidate.is_file():
                        return candidate
    return None


# ---------------------------------------------------------------------------
# § 2, 7, 8: putting one work candidate together
# ---------------------------------------------------------------------------


def _ingest_candidate(
    candidate: WorkCandidate,
    *,
    library: Library,
    probe: MediaProbe,
    clock: Clock,
    artwork_dir: Path,
) -> ContentId | None:
    unchanged_ids: set[ContentId] = set()
    unchanged = True
    for path in candidate.files:
        known = library.find_member_by_path(str(path))
        try:
            stat = path.stat()
        except OSError:
            unchanged = False
            break
        if known is None or known[1].size_bytes != stat.st_size or known[1].mtime != stat.st_mtime:
            unchanged = False
            break
        unchanged_ids.add(known[0])
    if unchanged and len(unchanged_ids) == 1:
        content_id = next(iter(unchanged_ids))
        library.mark_available((content_id,), last_seen=clock.now())
        return content_id

    probes: dict[Path, ProbedFile] = {}
    for path in candidate.files:
        try:
            probed = probe.probe(path)
        except OSError as exc:
            logger.warning("source unreadable, excluded from its work: %s (%s)", path, exc)
            continue
        if probed is None or probed.duration is None:
            logger.warning("no usable duration, excluded from its work: %s", path)
            continue
        probes[path] = probed

    if not probes:
        return None  # CONTENT_INGESTION.md § 10: no work created.

    usable_files = [f for f in candidate.files if f in probes]
    fingerprints = [probes[f].fingerprint for f in usable_files]
    content_id = resolve_identity(fingerprints, library)
    existing = library.get_content(content_id)

    chapters = build_chapters(candidate.directory, usable_files, probes)
    ordered_paths = [c.source.path if c.source is not None else usable_files[0] for c in chapters]

    sidecar = _Sidecar() if candidate.is_root_singleton else _read_sidecar(candidate.directory)
    kind, rule = infer_kind(
        existing=existing, sidecar=sidecar, probes=list(probes.values()), chapters=chapters
    )

    if len(usable_files) == 1:
        duration = probes[usable_files[0]].duration
    else:
        duration = chapters[-1].start + chapters[-1].duration if chapters[-1].duration else None

    title = (
        sidecar.title
        or _first_present([probes[f].album for f in usable_files])
        or (candidate.directory.name if not candidate.is_root_singleton else None)
        or usable_files[0].stem
    )
    language = sidecar.language or _first_present([probes[f].language for f in usable_files])
    artwork = _resolve_artwork(
        content_id=content_id,
        directory=None if candidate.is_root_singleton else candidate.directory,
        first_probe=probes[ordered_paths[0]],
        artwork_dir=artwork_dir,
    )

    item = ContentItem(
        id=content_id,
        title=title,
        kind=kind,
        sources=tuple(LocalFileSource(path=p) for p in ordered_paths),
        chapters=chapters,
        duration=duration,
        artwork=artwork,
        language=language,
        kind_overridden=existing.kind_overridden if existing is not None else False,
        available=True,
        last_seen=clock.now(),
        kind_inference_rule=rule,
    )

    member_files = tuple(
        MemberFile(
            path=path,
            ordinal=i,
            size_bytes=probes[path].size_bytes,
            mtime=probes[path].mtime,
            fingerprint=probes[path].fingerprint,
            replaygain=probes[path].replaygain,
        )
        for i, path in enumerate(ordered_paths)
    )

    library.save_content(item, member_files=member_files)
    return content_id


# ---------------------------------------------------------------------------
# § 2: the whole scan pass
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScanSummary:
    candidates_seen: int
    works_touched: int
    works_marked_unavailable: int


def run_scan(
    *,
    library: Library,
    probe: MediaProbe,
    clock: Clock,
    roots: Sequence[Path],
    follow_symlinks: bool,
    artwork_dir: Path,
) -> ScanSummary:
    """Runs off the playback thread; commits per work, never holds a
    transaction across a probe (CONTENT_INGESTION.md § 2)."""
    usable_roots = tuple(root.resolve() for root in roots if root.is_dir())
    previously_known: set[ContentId] = set()
    for item in library.list_content():
        members = library.get_member_files(item.id)
        if any(_under_root(member.path, root) for member in members for root in usable_roots):
            previously_known.add(item.id)
    touched: set[ContentId] = set()

    candidates = discover_work_candidates(roots, follow_symlinks=follow_symlinks)
    for candidate in candidates:
        content_id = _ingest_candidate(
            candidate, library=library, probe=probe, clock=clock, artwork_dir=artwork_dir
        )
        if content_id is not None:
            touched.add(content_id)

    stale = tuple(previously_known - touched)
    if stale:
        library.mark_unavailable(stale)

    return ScanSummary(
        candidates_seen=len(candidates),
        works_touched=len(touched),
        works_marked_unavailable=len(stale),
    )


def _under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except (OSError, ValueError):
        return False
    return True
