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
import threading
import uuid
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

from aqeno.adapters.persistence.migrations import apply_migrations
from aqeno.domain.access import (
    AccessDecision,
    AccessSource,
    Audience,
    AudienceMode,
    Collection,
    CollectionId,
    EffectiveAccess,
)
from aqeno.domain.content import (
    Chapter,
    ContentId,
    ContentItem,
    ContentKind,
    Fingerprint,
    HttpSource,
    LocalFileSource,
    MemberFile,
    ReplayGain,
    Source,
)
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.persistence import (
    ContentPage,
    ContentQuery,
    DatabaseCorruptError,
    DatabaseHealth,
    TagMapping,
    UnknownContentError,
)

logger = logging.getLogger(__name__)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _effective_access_params(profile_name: str) -> tuple[str, str, str, str]:
    return (profile_name, profile_name, profile_name, profile_name)


def _effective_access_sql(content_expression: str) -> str:
    """Set-oriented implementation of domain/access.py's precedence rule."""
    return f"""
    (
      (SELECT decision FROM content_access_override
       WHERE content_id = {content_expression} AND profile_name = ?) = 'allow'
      OR
      (
        (SELECT decision FROM content_access_override
         WHERE content_id = {content_expression} AND profile_name = ?) IS NULL
        AND
        (
          EXISTS (
            SELECT 1 FROM collection_member cm
            JOIN collection_audience ca ON ca.collection_id = cm.collection_id
            LEFT JOIN collection_audience_profile cap
              ON cap.collection_id = ca.collection_id AND cap.profile_name = ?
            WHERE cm.content_id = {content_expression}
              AND (ca.mode = 'shared' OR cap.profile_name IS NOT NULL)
          )
          OR
          (
            NOT EXISTS (
              SELECT 1 FROM collection_member cm
              JOIN collection_audience ca ON ca.collection_id = cm.collection_id
              WHERE cm.content_id = {content_expression}
            )
            AND
            (
              NOT EXISTS (SELECT 1 FROM content_audience
                          WHERE content_id = {content_expression})
              OR EXISTS (SELECT 1 FROM content_audience
                         WHERE content_id = {content_expression} AND mode = 'shared')
              OR EXISTS (SELECT 1 FROM content_audience_profile
                         WHERE content_id = {content_expression} AND profile_name = ?)
            )
          )
        )
      )
    )
    """


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
        available=bool(row["available"]),
        last_seen=row["last_seen"],
        kind_inference_rule=row["kind_inference_rule"],
    )


def _member_file_row_to_member_file(row: sqlite3.Row) -> MemberFile:
    return MemberFile(
        path=Path(row["path"]),
        ordinal=row["ordinal"],
        size_bytes=row["size_bytes"],
        mtime=row["mtime"],
        fingerprint=Fingerprint(size_bytes=row["size_bytes"], digest=row["fingerprint"]),
        replaygain=ReplayGain(
            track_gain_db=row["track_gain_db"],
            track_peak=row["track_peak"],
            album_gain_db=row["album_gain_db"],
            album_peak=row["album_peak"],
        ),
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
        self._lock = threading.RLock()

    # -- lifecycle -----------------------------------------------------------

    def health(self) -> DatabaseHealth:
        return self._health

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- content -------------------------------------------------------------

    def save_content(
        self, item: ContentItem, *, member_files: tuple[MemberFile, ...] | None = None
    ) -> None:
        content_id_text = str(item.id.value)
        self._write(lambda: self._upsert_content_locked(item, content_id_text, member_files))

    def _upsert_content_locked(
        self,
        item: ContentItem,
        content_id_text: str,
        member_files: tuple[MemberFile, ...] | None,
    ) -> None:
        conn = self._conn
        conn.execute(
            """
            INSERT INTO content (id, title, kind, duration_seconds, artwork, language,
                                  kind_overridden, available, last_seen, kind_inference_rule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                kind = excluded.kind,
                duration_seconds = excluded.duration_seconds,
                artwork = excluded.artwork,
                language = excluded.language,
                kind_overridden = excluded.kind_overridden,
                available = excluded.available,
                last_seen = excluded.last_seen,
                kind_inference_rule = excluded.kind_inference_rule
            """,
            (
                content_id_text,
                item.title,
                item.kind.value,
                item.duration.total_seconds() if item.duration is not None else None,
                str(item.artwork) if item.artwork is not None else None,
                item.language,
                int(item.kind_overridden),
                int(item.available),
                item.last_seen,
                item.kind_inference_rule,
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

        if member_files is not None:
            conn.execute("DELETE FROM member_file WHERE content_id = ?", (content_id_text,))
            for member in member_files:
                conn.execute(
                    """
                    INSERT INTO member_file
                        (content_id, ordinal, path, size_bytes, fingerprint, mtime,
                         track_gain_db, track_peak, album_gain_db, album_peak)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        content_id_text,
                        member.ordinal,
                        str(member.path),
                        member.size_bytes,
                        member.fingerprint.digest,
                        member.mtime,
                        member.replaygain.track_gain_db,
                        member.replaygain.track_peak,
                        member.replaygain.album_gain_db,
                        member.replaygain.album_peak,
                    ),
                )

    def find_by_fingerprint(self, fingerprint: Fingerprint) -> ContentId | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT content_id FROM member_file WHERE size_bytes = ? AND fingerprint = ? "
                "LIMIT 1",
                (fingerprint.size_bytes, fingerprint.digest),
            ).fetchone()
            return ContentId(uuid.UUID(row["content_id"])) if row is not None else None

    def get_member_files(self, content_id: ContentId) -> tuple[MemberFile, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM member_file WHERE content_id = ? ORDER BY ordinal",
                (str(content_id.value),),
            ).fetchall()
            return tuple(_member_file_row_to_member_file(row) for row in rows)

    def find_member_by_path(self, path: str) -> tuple[ContentId, MemberFile] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM member_file WHERE path = ? LIMIT 1", (path,)
            ).fetchone()
            if row is None:
                return None
            return ContentId(uuid.UUID(row["content_id"])), _member_file_row_to_member_file(row)

    def mark_available(self, content_ids: tuple[ContentId, ...], *, last_seen: float) -> None:
        if not content_ids:
            return

        def do() -> None:
            self._conn.executemany(
                "UPDATE content SET available = 1, last_seen = ? WHERE id = ?",
                [(last_seen, str(cid.value)) for cid in content_ids],
            )

        self._write(do)

    def mark_unavailable(self, content_ids: tuple[ContentId, ...]) -> None:
        if not content_ids:
            return

        def do() -> None:
            self._conn.executemany(
                "UPDATE content SET available = 0 WHERE id = ?",
                [(str(cid.value),) for cid in content_ids],
            )

        self._write(do)

    def get_content(self, content_id: ContentId) -> ContentItem | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM content WHERE id = ?", (str(content_id.value),)
            ).fetchone()
            return _content_row_to_item(self._conn, row) if row is not None else None

    def list_content(self) -> tuple[ContentItem, ...]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM content ORDER BY title").fetchall()
            return tuple(_content_row_to_item(self._conn, row) for row in rows)

    def query_content(self, query: ContentQuery) -> ContentPage:
        clauses: list[str] = []
        params: list[object] = []
        if query.search is not None:
            clauses.append("lower(title) LIKE ? ESCAPE '\\'")
            params.append(f"%{_escape_like(query.search.casefold())}%")
        if query.kind is not None:
            clauses.append("kind = ?")
            params.append(query.kind.value)
        if query.available is not None:
            clauses.append("available = ?")
            params.append(int(query.available))
        if query.profile_name is not None:
            clauses.append(_effective_access_sql("content.id"))
            params.extend(_effective_access_params(query.profile_name))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock:
            total = int(
                self._conn.execute(f"SELECT COUNT(*) FROM content{where}", params).fetchone()[0]
            )
            page_clauses = list(clauses)
            page_params = list(params)
            if query.after is not None:
                after_title, after_id = query.after
                page_clauses.append("(lower(title), id) > (?, ?)")
                page_params.extend((after_title, str(after_id.value)))
            page_where = f" WHERE {' AND '.join(page_clauses)}" if page_clauses else ""
            page_params.append(query.limit)
            rows = self._conn.execute(
                f"SELECT * FROM content{page_where} ORDER BY lower(title), id LIMIT ?",
                page_params,
            ).fetchall()
            return ContentPage(
                items=tuple(_content_row_to_item(self._conn, row) for row in rows), total=total
            )

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
        with self._lock:
            row = self._conn.execute(
                "SELECT content_id FROM tag_mapping WHERE uid = ?", (uid,)
            ).fetchone()
            return ContentId(uuid.UUID(row["content_id"])) if row is not None else None

    def unmap_tag(self, uid: str) -> None:
        self._write(lambda: self._conn.execute("DELETE FROM tag_mapping WHERE uid = ?", (uid,)))

    def list_tags(self) -> tuple[TagMapping, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT uid, content_id FROM tag_mapping ORDER BY uid"
            ).fetchall()
            return tuple(
                TagMapping(uid=row["uid"], content_id=ContentId(uuid.UUID(row["content_id"])))
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
        with self._lock:
            row = self._conn.execute("SELECT * FROM profile WHERE name = ?", (name,)).fetchone()
            return _profile_row_to_profile(row) if row is not None else None

    def list_profiles(self) -> tuple[Profile, ...]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM profile ORDER BY name").fetchall()
            return tuple(_profile_row_to_profile(row) for row in rows)

    def remove_profile(self, name: str) -> None:
        self._write(lambda: self._conn.execute("DELETE FROM profile WHERE name = ?", (name,)))

    # -- personal listening state -----------------------------------------

    def set_favorite(self, profile_name: str, content_id: ContentId, favorite: bool) -> None:
        def do() -> None:
            values = (profile_name, str(content_id.value))
            if favorite:
                self._conn.execute(
                    "INSERT OR IGNORE INTO favorite (profile_name, content_id) VALUES (?, ?)",
                    values,
                )
            else:
                self._conn.execute(
                    "DELETE FROM favorite WHERE profile_name = ? AND content_id = ?", values
                )

        self._write(do)

    def is_favorite(self, profile_name: str, content_id: ContentId) -> bool:
        with self._lock:
            return (
                self._conn.execute(
                    "SELECT 1 FROM favorite WHERE profile_name = ? AND content_id = ?",
                    (profile_name, str(content_id.value)),
                ).fetchone()
                is not None
            )

    def list_favorites(self, profile_name: str, query: ContentQuery) -> ContentPage:
        clauses = ["favorite.profile_name = ?", _effective_access_sql("content.id")]
        params: list[object] = [profile_name, *_effective_access_params(profile_name)]
        if query.search is not None:
            clauses.append("lower(content.title) LIKE ? ESCAPE '\\'")
            params.append(f"%{_escape_like(query.search.casefold())}%")
        if query.kind is not None:
            clauses.append("content.kind = ?")
            params.append(query.kind.value)
        if query.available is not None:
            clauses.append("content.available = ?")
            params.append(int(query.available))
        where = " AND ".join(clauses)
        with self._lock:
            total = int(
                self._conn.execute(
                    "SELECT COUNT(*) FROM content "
                    "JOIN favorite ON favorite.content_id = content.id "
                    f"WHERE {where}",
                    params,
                ).fetchone()[0]
            )
            if query.after is not None:
                clauses.append("(lower(content.title), content.id) > (?, ?)")
                params.extend((query.after[0], str(query.after[1].value)))
            params.append(query.limit)
            rows = self._conn.execute(
                "SELECT content.* FROM content JOIN favorite ON favorite.content_id = content.id "
                f"WHERE {' AND '.join(clauses)} ORDER BY lower(content.title), content.id LIMIT ?",
                params,
            ).fetchall()
            return ContentPage(
                items=tuple(_content_row_to_item(self._conn, row) for row in rows), total=total
            )

    # -- access ------------------------------------------------------------

    def set_content_audience(self, content_ids: tuple[ContentId, ...], audience: Audience) -> None:
        def do() -> None:
            for content_id in content_ids:
                cid = str(content_id.value)
                self._conn.execute(
                    "INSERT INTO content_audience (content_id, mode) VALUES (?, ?) "
                    "ON CONFLICT(content_id) DO UPDATE SET mode = excluded.mode",
                    (cid, audience.mode.value),
                )
                self._conn.execute(
                    "DELETE FROM content_audience_profile WHERE content_id = ?", (cid,)
                )
                self._conn.executemany(
                    "INSERT INTO content_audience_profile (content_id, profile_name) VALUES (?, ?)",
                    [(cid, name) for name in audience.profile_names],
                )

        self._write(do)

    def set_content_overrides(
        self,
        content_ids: tuple[ContentId, ...],
        profile_names: tuple[str, ...],
        decision: AccessDecision | None,
    ) -> None:
        def do() -> None:
            values = [
                (str(content_id.value), profile_name)
                for content_id in content_ids
                for profile_name in profile_names
            ]
            if decision is None:
                self._conn.executemany(
                    "DELETE FROM content_access_override WHERE content_id = ? AND profile_name = ?",
                    values,
                )
            else:
                self._conn.executemany(
                    "INSERT INTO content_access_override (content_id, profile_name, decision) "
                    "VALUES (?, ?, ?) ON CONFLICT(content_id, profile_name) DO UPDATE SET "
                    "decision = excluded.decision",
                    [(cid, profile, decision.value) for cid, profile in values],
                )

        self._write(do)

    def get_content_audience(self, content_id: ContentId) -> Audience | None:
        cid = str(content_id.value)
        with self._lock:
            row = self._conn.execute(
                "SELECT mode FROM content_audience WHERE content_id = ?", (cid,)
            ).fetchone()
            if row is None:
                return None
            profiles = self._conn.execute(
                "SELECT profile_name FROM content_audience_profile WHERE content_id = ? "
                "ORDER BY profile_name",
                (cid,),
            ).fetchall()
            return Audience(
                mode=AudienceMode(row["mode"]),
                profile_names=tuple(profile["profile_name"] for profile in profiles),
            )

    def effective_access(self, content_id: ContentId, profile_name: str) -> EffectiveAccess:
        cid = str(content_id.value)
        with self._lock:
            override = self._conn.execute(
                "SELECT decision FROM content_access_override "
                "WHERE content_id = ? AND profile_name = ?",
                (cid, profile_name),
            ).fetchone()
            if override is not None:
                decision = AccessDecision(override["decision"])
                return EffectiveAccess(
                    allowed=decision is AccessDecision.ALLOW,
                    source=AccessSource.MEDIA_OVERRIDE,
                    explicit_decision=decision,
                )
            collections = self._conn.execute(
                "SELECT ca.collection_id, ca.mode, cap.profile_name "
                "FROM collection_member cm JOIN collection_audience ca "
                "ON ca.collection_id = cm.collection_id "
                "LEFT JOIN collection_audience_profile cap "
                "ON cap.collection_id = ca.collection_id AND cap.profile_name = ? "
                "WHERE cm.content_id = ?",
                (profile_name, cid),
            ).fetchall()
            if collections:
                allowed = any(
                    row["mode"] == AudienceMode.SHARED.value or row["profile_name"] is not None
                    for row in collections
                )
                return EffectiveAccess(
                    allowed=allowed,
                    source=AccessSource.COLLECTION,
                    inherited_collection_ids=tuple(
                        CollectionId(uuid.UUID(row["collection_id"])) for row in collections
                    ),
                )
            audience = self.get_content_audience(content_id)
            if audience is not None:
                return EffectiveAccess(
                    allowed=(
                        audience.mode is AudienceMode.SHARED
                        or profile_name in audience.profile_names
                    ),
                    source=AccessSource.MEDIA_AUDIENCE,
                )
            return EffectiveAccess(allowed=True, source=AccessSource.SHARED_DEFAULT)

    def can_profile_access(self, content_id: ContentId, profile_name: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                f"SELECT 1 FROM content WHERE id = ? AND {_effective_access_sql('content.id')}",
                (str(content_id.value), *_effective_access_params(profile_name)),
            ).fetchone()
            return row is not None

    # -- collections -------------------------------------------------------

    def save_collection(self, collection: Collection) -> None:
        def do() -> None:
            cid = str(collection.id.value)
            self._conn.execute(
                "INSERT INTO collection (id, name) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET name = excluded.name",
                (cid, collection.name),
            )
            self._conn.execute("DELETE FROM collection_member WHERE collection_id = ?", (cid,))
            self._conn.executemany(
                "INSERT INTO collection_member (collection_id, content_id) VALUES (?, ?)",
                [(cid, str(content_id.value)) for content_id in collection.content_ids],
            )

        self._write(do)

    def get_collection(self, collection_id: CollectionId) -> Collection | None:
        cid = str(collection_id.value)
        with self._lock:
            row = self._conn.execute("SELECT * FROM collection WHERE id = ?", (cid,)).fetchone()
            if row is None:
                return None
            members = self._conn.execute(
                "SELECT content_id FROM collection_member "
                "WHERE collection_id = ? ORDER BY content_id",
                (cid,),
            ).fetchall()
            return Collection(
                id=collection_id,
                name=row["name"],
                content_ids=tuple(ContentId(uuid.UUID(member["content_id"])) for member in members),
            )

    def list_collections(self) -> tuple[Collection, ...]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id FROM collection ORDER BY lower(name), id"
            ).fetchall()
        return tuple(
            collection
            for row in rows
            if (collection := self.get_collection(CollectionId(uuid.UUID(row["id"])))) is not None
        )

    def remove_collection(self, collection_id: CollectionId) -> None:
        self._write(
            lambda: self._conn.execute(
                "DELETE FROM collection WHERE id = ?", (str(collection_id.value),)
            )
        )

    def set_collection_audience(self, collection_id: CollectionId, audience: Audience) -> None:
        def do() -> None:
            cid = str(collection_id.value)
            self._conn.execute(
                "INSERT INTO collection_audience (collection_id, mode) VALUES (?, ?) "
                "ON CONFLICT(collection_id) DO UPDATE SET mode = excluded.mode",
                (cid, audience.mode.value),
            )
            self._conn.execute(
                "DELETE FROM collection_audience_profile WHERE collection_id = ?", (cid,)
            )
            self._conn.executemany(
                "INSERT INTO collection_audience_profile "
                "(collection_id, profile_name) VALUES (?, ?)",
                [(cid, name) for name in audience.profile_names],
            )

        self._write(do)

    def get_collection_audience(self, collection_id: CollectionId) -> Audience | None:
        cid = str(collection_id.value)
        with self._lock:
            row = self._conn.execute(
                "SELECT mode FROM collection_audience WHERE collection_id = ?", (cid,)
            ).fetchone()
            if row is None:
                return None
            profiles = self._conn.execute(
                "SELECT profile_name FROM collection_audience_profile WHERE collection_id = ? "
                "ORDER BY profile_name",
                (cid,),
            ).fetchall()
            return Audience(
                mode=AudienceMode(row["mode"]),
                profile_names=tuple(profile["profile_name"] for profile in profiles),
            )

    # -- resume ----------------------------------------------------------------

    def get_resume(self, content_id: ContentId, profile_name: str) -> timedelta | None:
        with self._lock:
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

    def _write(self, fn: Callable[[], object]) -> None:
        """Runs `fn` in its own transaction.

        In `DEGRADED_READ_ONLY` health the write is skipped and logged rather
        than raised: local playback must keep working even though nothing
        persists (ADR 0007 § "Degraded operation").
        """
        with self._lock:
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

    conn = sqlite3.connect(db_path, timeout=5, isolation_level=None, check_same_thread=False)
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
