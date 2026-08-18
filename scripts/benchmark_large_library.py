"""Deterministic local-index smoke benchmark for the 10k-library contract."""

from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

from aqeno.adapters.persistence import open_library
from aqeno.domain.content import ContentId, ContentItem, ContentKind, LocalFileSource
from aqeno.ports.persistence import ContentQuery


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10_000)
    parser.add_argument("--max-query-ms", type=float, default=250.0)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="aqeno-library-benchmark-") as temporary:
        library = open_library(Path(temporary))
        started = time.perf_counter()
        for index in range(args.count):
            title = f"Work {index:05d}"
            library.save_content(
                ContentItem(
                    id=ContentId(),
                    title=title,
                    kind=ContentKind.AUDIOBOOK,
                    sources=(LocalFileSource(Path(f"/mnt/library/{title}.mp3")),),
                )
            )
        ingest_seconds = time.perf_counter() - started
        started = time.perf_counter()
        result = library.query_content(ContentQuery(limit=50, search="Work 099"))
        query_ms = (time.perf_counter() - started) * 1000
        library.close()
    print(
        f"items={args.count} ingest_seconds={ingest_seconds:.3f} "
        f"query_ms={query_ms:.3f} matches={result.total}"
    )
    if result.total == 0 or query_ms > args.max_query_ms:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
