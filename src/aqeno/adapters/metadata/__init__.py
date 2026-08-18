"""`mutagen`-backed `MediaProbe` — ADR 0014 § 1.

`mutagen_probe.py` is the only module in the codebase that imports `mutagen`.
"""

from aqeno.adapters.metadata.mutagen_probe import MutagenProbe

__all__ = ["MutagenProbe"]
