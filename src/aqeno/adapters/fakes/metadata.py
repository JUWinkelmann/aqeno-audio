"""In-memory `MediaProbe` fake — a dict of path to `ProbedFile`.

Lets the whole ingestion policy be tested without real audio files
(CONTENT_INGESTION.md § 12). Tests that need real container shapes use the
`mutagen`-backed adapter against generated fixtures instead.
"""

from __future__ import annotations

from pathlib import Path

from aqeno.ports.media_probe import ProbedFile


class FakeMediaProbe:
    def __init__(self, files: dict[Path, ProbedFile] | None = None) -> None:
        self._files = dict(files) if files is not None else {}

    def add(self, probed: ProbedFile) -> None:
        self._files[probed.path] = probed

    def probe(self, path: Path) -> ProbedFile | None:
        return self._files.get(path)
