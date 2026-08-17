"""GStreamer audio adapter — ADR 0003.

`gstreamer_engine.py` implements `aqeno.ports.audio.AudioEngine` against
`playbin3`; `errors.py` maps its bus errors onto the port's `FailureCode`.
"""

from aqeno.adapters.audio.errors import SourceKind, map_bus_error
from aqeno.adapters.audio.gstreamer_engine import GStreamerAudioEngine, gain_for_volume

__all__ = ["GStreamerAudioEngine", "SourceKind", "gain_for_volume", "map_bus_error"]
