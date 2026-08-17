"""SQLite-backed `Library` — ADR 0007 § "Domain data".

WAL mode, `synchronous=NORMAL`, `foreign_keys=ON`. See ADR 0007 § 2 for why
`NORMAL` and not `FULL`: it cannot corrupt the file, and the few seconds of
resume precision it might cost on power loss is exactly the trade-off
`CONFIGURATION_DEFAULTS.md` § 4 already accepted (resume error after power loss
<= 12 s) in exchange for not fsyncing an SD card 8,600 times a day.

`open_library()` is the only place that opens a connection, runs migrations and
classifies the database's health. Everything else is on `SqliteLibrary`.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from aqeno.adapters.persistence.migrations import apply_migrations
from aqeno.domain.content import (
    Chapter,
    ContentId,
    ContentItem,
    ContentKind,
    HttpSource,
    LocalFileSource,
    Source,
)
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.persistence import (
    DatabaseCorruptError,
    DatabaseHealth,
    TagMapping,
    UnknownContentError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StoredTagMapping:
    uid: str
    content_id: ContentId


def _content_row_to_item(conn: sqlite3.Connection, row: sqlite3.Row) -> ContentItem:
    content_id = ContentId(uuid.UUID(row["id"]))

    source_rows = conn.execute(
        "SELECT * FROM content_source WHERE content_id = ? ORDER BY ordinal", (row["id"],)
    ).fetchall()
    sources: list[Source] = []
    for source_row in source_rows:
        if source_row["source_type"] == "local_file":
            sources.append(LocalFileSource(path=Path(source_row["path"])))
        else:
            sources.append(HttpSource(url=source_row["url"], seekable=bool(source_row["seekable"])))

    chapter_rows = conn.execute(
        "SELECT * FROM chapter WHERE content_id = ? ORDER BY idx", (row["id"],)
    ).fetchall()
    chapters = tuple(
        Chapter(
            index=chapter_row["idx"],
            title=chapter_row["title"],
            start=timedelta(seconds=chapter_row["start_seconds"]),
            duration=(
                timedelta(seconds=chapter_row["duration_seconds"])
                if chapter_row["duration_seconds"] is not None
                else None
            ),
            source=(
                LocalFileSource(path=Path(chapter_row["source_path"]))
                if chapter_row["source_path"] is not None
                else None
            ),
        )
        for chapter_row in chapter_rows
    )

    return ContentItem(
        id=content_id,
        title=row["title"],
        kind=ContentKind(row["kind"]),
        sources=tuple(sources),
        chapters=chapters,
        duration=(
            timedelta(seconds=row["duration_seconds"])
            if row["duration_seconds"] is not None
            else None
        ),
        artwork=Path(row["artwork"]) if row["artwork"] is not None else None,
        language=row["language"],
        kind_overridden=bool(row["kind_overridden"]),
    )


def _profile_row_to_profile(row: sqlite3.Row) -> Profile:
    return Profile(
        name=row["name"],
        level=ExperienceLevel(row["level"]),
        role=Role(row["role"]),
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=row["inactivity_timeout_seconds"]),
            night_timeout=timedelta(seconds=row["night_timeout_seconds"]),
            allows_dim=bool(row["allows_dim"]),
            dim_hold=(
                timedelta(seconds=row["dim_hold_seconds"])
                if row["dim_hold_seconds"] is not None
                else None
            ),
            interactive_brightness=row["interactive_brightness"],
            dim_brightness=row["dim_brightness"],
            ambient_brightness=row["ambient_brightness"],
            night_brightness=row["night_brightness"],
            led_brightness=row["led_brightness"],
        ),
        volume=VolumeLimits(
            maximum=row["volume_maximum"],
            night_maximum=row["volume_night_maximum"],
            headphone_maximum=row["volume_headphone_maximum"],
        ),
        ambient_enabled=bool(row["ambient_enabled"]),
    )


class SqliteLibrary:
    """Implements `aqeno.ports.persistence.Library` against `aqeno.db`."""

    def __init__(self, conn: sqlite3.Connection, *, health: DatabaseHealth) -> None:
        self._conn = conn
        self._health = health

    # -- lifecycle -----------------------------------------------------------

    def health(self) -> DatabaseHealth:
        return self._health

    def close(self) -> None:
        self._conn.close()

    # -- content -------------------------------------------------------------

    def upsert_content(self, item: ContentItem) -> None:
        content_id_text = str(item.id.value)
        self._write(lambda: self._upsert_content_locked(item, content_id_text))

    def _upsert_content_locked(self, item: ContentItem, content_id_text: str) -> None:
        conn = self._conn
        conn.execute(
            """
            INSERT INTO content (id, title, kind, duration_seconds, artwork, language,
                                  kind_overridden, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                kind = excluded.kind,
                duration_seconds = excluded.duration_seconds,
                artwork = excluded.artwork,
                language = excluded.language,
                kind_overridden = excluded.kind_overridden
            """,
            (
                content_id_text,
                item.title,
                item.kind.value,
                item.duration.total_seconds() if item.duration is not None else None,
                str(item.artwork) if item.artwork is not None else None,
                item.language,
                int(item.kind_overridden),
            ),
        )
        conn.execute("DELETE FROM content_source WHERE content_id = ?", (content_id_text,))
        for ordinal, source in enumerate(item.sources):
            if isinstance(source, LocalFileSource):
                conn.execute(
                    "INSERT INTO content_source (content_id, ordinal, source_type, path) "
                    "VALUES (?, ?, 'local_file', ?)",
                    (content_id_text, ordinal, str(source.path)),
                )
            else:
                conn.execute(
                    "INSERT INTO content_source "
                    "(content_id, ordinal, source_type, url, seekable) "
                    "VALUES (?, ?, 'http', ?, ?)",
                    (content_id_text, ordinal, source.url, int(source.seekable)),
                )
        conn.execute("DELETE FROM chapter WHERE content_id = ?", (content_id_text,))
        for chapter in item.chapters:
            conn.execute(
                "INSERT INTO chapter "
                "(content_id, idx, title, start_seconds, duration_seconds, source_path) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    content_id_text,
                    chapter.index,
                    chapter.title,
                    chapter.start.total_seconds(),
                    chapter.duration.total_seconds() if chapter.duration is not None else None,
                    str(chapter.source.path) if chapter.source is not None else None,
                ),
            )

    def get_content(self, content_id: ContentId) -> ContentItem | None:
        row = self._conn.execute(
            "SELECT * FROM content WHERE id = ?", (str(content_id.value),)
        ).fetchone()
        return _content_row_to_item(self._conn, row) if row is not None else None

    def list_content(self) -> tuple[ContentItem, ...]:
        rows = self._conn.execute("SELECT * FROM content ORDER BY title").fetchall()
        return tuple(_content_row_to_item(self._conn, row) for row in rows)

    def remove_content(self, content_id: ContentId) -> None:
        self._write(
            lambda: self._conn.execute("DELETE FROM content WHERE id = ?", (str(content_id.value),))
        )

    # -- tag mappings ----------------------------------------------------------

    def map_tag(self, uid: str, content_id: ContentId) -> None:
        def do() -> None:
            try:
                self._conn.execute(
                    "INSERT INTO tag_mapping (uid, content_id) VALUES (?, ?) "
                    "ON CONFLICT(uid) DO UPDATE SET content_id = excluded.content_id",
                    (uid, str(content_id.value)),
                )
            except sqlite3.IntegrityError as exc:
                raise UnknownContentError(f"no such content: {content_id.value}") from exc

        self._write(do)

    def resolve_tag(self, uid: str) -> ContentId | None:
        row = self._conn.execute(
            "SELECT content_id FROM tag_mapping WHERE uid = ?", (uid,)
        ).fetchone()
        return ContentId(uuid.UUID(row["content_id"])) if row is not None else None

    def unmap_tag(self, uid: str) -> None:
        self._write(lambda: self._conn.execute("DELETE FROM tag_mapping WHERE uid = ?", (uid,)))

    def list_tags(self) -> tuple[TagMapping, ...]:
        rows = self._conn.execute("SELECT uid, content_id FROM tag_mapping ORDER BY uid").fetchall()
        return tuple(
            StoredTagMapping(uid=row["uid"], content_id=ContentId(uuid.UUID(row["content_id"])))
            for row in rows
        )

    # -- profiles ------------------------------------------------------------

    def save_profile(self, profile: Profile) -> None:
        def do() -> None:
            self._conn.execute(
                """
                INSERT INTO profile (
                    name, level, role, ambient_enabled,
                    inactivity_timeout_seconds, night_timeout_seconds, allows_dim,
                    dim_hold_seconds, interactive_brightness, dim_brightness,
                    ambient_brightness, night_brightness, led_brightness,
                    volume_maximum, volume_night_maximum, volume_headphone_maximum
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    level = excluded.level,
                    role = excluded.role,
                    ambient_enabled = excluded.ambient_enabled,
                    inactivity_timeout_seconds = excluded.inactivity_timeout_seconds,
                    night_timeout_seconds = excluded.night_timeout_seconds,
                    allows_dim = excluded.allows_dim,
                    dim_hold_seconds = excluded.dim_hold_seconds,
                    interactive_brightness = excluded.interactive_brightness,
                    dim_brightness = excluded.dim_brightness,
                    ambient_brightness = excluded.ambient_brightness,
                    night_brightness = excluded.night_brightness,
                    led_brightness = excluded.led_brightness,
                    volume_maximum = excluded.volume_maximum,
                    volume_night_maximum = excluded.volume_night_maximum,
                    volume_headphone_maximum = excluded.volume_headphone_maximum
                """,
                (
                    profile.name,
                    profile.level.value,
                    profile.role.value,
                    int(profile.ambient_enabled),
                    profile.display.inactivity_timeout.total_seconds(),
                    profile.display.night_timeout.total_seconds(),
                    int(profile.display.allows_dim),
                    (
                        profile.display.dim_hold.total_seconds()
                        if profile.display.dim_hold is not None
                        else None
                    ),
                    profile.display.interactive_brightness,
                    profile.display.dim_brightness,
                    profile.display.ambient_brightness,
                    profile.display.night_brightness,
                    profile.display.led_brightness,
                    profile.volume.maximum,
                    profile.volume.night_maximum,
                    profile.volume.headphone_maximum,
                ),
            )

        self._write(do)

    def get_profile(self, name: str) -> Profile | None:
        row = self._conn.execute("SELECT * FROM profile WHERE name = ?", (name,)).fetchone()
        return _profile_row_to_profile(row) if row is not None else None

    def list_profiles(self) -> tuple[Profile, ...]:
        rows = self._conn.execute("SELECT * FROM profile ORDER BY name").fetchall()
        return tuple(_profile_row_to_profile(row) for row in rows)

    # -- resume ----------------------------------------------------------------

    def get_resume(self, content_id: ContentId, profile_name: str) -> timedelta | None:
        row = self._conn.execute(
            "SELECT position_seconds FROM resume_position "
            "WHERE content_id = ? AND profile_name = ?",
            (str(content_id.value), profile_name),
        ).fetchone()
        return timedelta(seconds=row["position_seconds"]) if row is not None else None

    def set_resume(self, content_id: ContentId, profile_name: str, position: timedelta) -> None:
        def do() -> None:
            content_id_text = str(content_id.value)
            existing = self._conn.execute(
                "SELECT position_seconds FROM resume_position "
                "WHERE content_id = ? AND profile_name = ?",
                (content_id_text, profile_name),
            ).fetchone()
            # CONFIGURATION_DEFAULTS.md § 4: skip the write when the position has
            # not advanced — paused playback writes nothing, and it also bounds
            # SD-card wear from the 10-second persistence interval.
            if existing is not None and existing["position_seconds"] >= position.total_seconds():
                return
            self._conn.execute(
                """
                INSERT INTO resume_position (content_id, profile_name, position_seconds, updated_at)
                VALUES (?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                ON CONFLICT(content_id, profile_name) DO UPDATE SET
                    position_seconds = excluded.position_seconds,
                    updated_at = excluded.updated_at
                """,
                (content_id_text, profile_name, position.total_seconds()),
            )

        self._write(do)

    # -- internals -------------------------------------------------------------

    def _write(self, fn: Callable[[], None]) -> None:
        """Runs `fn` in its own transaction.

        In `DEGRADED_READ_ONLY` health the write is skipped and logged rather
        than raised: local playback must keep working even though nothing
        persists (ADR 0007 § "Degraded operation").
        """
        if self._health is DatabaseHealth.DEGRADED_READ_ONLY:
            logger.warning("persistence is degraded (read-only filesystem); write discarded")
            return
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            fn()
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        else:
            self._conn.execute("COMMIT")


def open_library(data_dir: Path | None = None) -> SqliteLibrary:
    """Open (creating if needed) `aqeno.db` under `data_dir`.

    Raises `DatabaseCorruptError` if the file exists but is not a valid SQLite
    database, and `SchemaTooNewError` if its schema is newer than this build
    understands. Neither error deletes or touches the file — recovery from
    either is an explicit action taken elsewhere, never automatic (ADR 0007).
    """
    from aqeno.config.paths import data_dir as default_data_dir

    directory = data_dir if data_dir is not None else default_data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    db_path = directory / "aqeno.db"

    conn = sqlite3.connect(db_path, timeout=5, isolation_level=None)
    conn.row_factory = sqlite3.Row

    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.DatabaseError as exc:
        conn.close()
        raise DatabaseCorruptError(f"{db_path} failed integrity check: {exc}") from exc
    if integrity != "ok":
        conn.close()
        raise DatabaseCorruptError(f"{db_path} failed integrity check: {integrity}")

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    apply_migrations(conn, db_path=db_path)

    health = DatabaseHealth.OK
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("ROLLBACK")
    except sqlite3.OperationalError:
        health = DatabaseHealth.DEGRADED_READ_ONLY
        logger.warning("%s is not writable; persistence entering degraded mode", db_path)

    return SqliteLibrary(conn, health=health)
