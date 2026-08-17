"""Ports — Protocol definitions for everything outside the domain.

Standard library only. Adapters implement these; the application depends only on
them. See `docs/implementation/PLATFORM_CONTRACTS.md`.
"""

from aqeno.ports.audio import (
    AudioCapabilities,
    AudioEngine,
    AudioFailure,
    FailureClass,
    FailureCode,
    TransportState,
    classify,
)
from aqeno.ports.clock import Clock

__all__ = [
    "AudioCapabilities",
    "AudioEngine",
    "AudioFailure",
    "Clock",
    "FailureClass",
    "FailureCode",
    "TransportState",
    "classify",
]
