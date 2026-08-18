"""Deterministic local-index smoke benchmark for the 10k-library contract."""

from __future__ import annotations

import argparse
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from aqeno.adapters.persistence import open_library
from aqeno.application.management import ProfileContentManagement
from aqeno.domain.access import Audience, AudienceMode
from aqeno.domain.content import ContentId, ContentItem, ContentKind, LocalFileSource
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.persistence import ContentQuery


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10_000)
    parser.add_argument("--max-query-ms", type=float, default=250.0)
    parser.add_argument("--max-bulk-ms", type=float, default=500.0)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="aqeno-library-benchmark-") as temporary:
        library = open_library(Path(temporary))
        started = time.perf_counter()
        content_ids: list[ContentId] = []
        for index in range(args.count):
            title = f"Work {index:05d}"
            content_id = ContentId()
            content_ids.append(content_id)
            library.save_content(
                ContentItem(
                    id=content_id,
                    title=title,
                    kind=ContentKind.AUDIOBOOK,
                    sources=(LocalFileSource(Path(f"/mnt/library/{title}.mp3")),),
                )
            )
        ingest_seconds = time.perf_counter() - started
        for name in ("anna", "paul", "jens", "guest"):
            library.save_profile(_profile(name))
        started = time.perf_counter()
        ProfileContentManagement(library).set_audience(
            tuple(content_ids[:1000]),
            Audience(AudienceMode.SELECTED_PROFILES, ("anna", "paul")),
        )
        bulk_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        result = library.query_content(
            ContentQuery(limit=50, search="Work 099", profile_name="anna")
        )
        query_ms = (time.perf_counter() - started) * 1000
        library.close()
    print(
        f"items={args.count} ingest_seconds={ingest_seconds:.3f} "
        f"bulk_ms={bulk_ms:.3f} query_ms={query_ms:.3f} matches={result.total}"
    )
    if result.total == 0 or query_ms > args.max_query_ms or bulk_ms > args.max_bulk_ms:
        return 1
    return 0


def _profile(name: str) -> Profile:
    return Profile(
        name=name,
        level=ExperienceLevel.STANDARD,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=60),
            night_timeout=timedelta(seconds=15),
            allows_dim=True,
            dim_hold=timedelta(seconds=10),
            interactive_brightness=70,
            dim_brightness=15,
            ambient_brightness=20,
            night_brightness=5,
            led_brightness=15,
        ),
        volume=VolumeLimits(maximum=80, night_maximum=40, headphone_maximum=60),
    )


if __name__ == "__main__":
    raise SystemExit(main())
