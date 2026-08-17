"""Shared test fixtures.

Two rules from ADR 0008 that are easy to break and hard to notice:
  - no `time.sleep()` anywhere in tests; advance `FakeClock` instead;
  - no audio files in the repository; fixtures are generated at test time.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from aqeno.adapters.fakes import FakeClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def aqeno_state_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point every AQENO location at a temporary directory (ADR 0007 § 4).

    Tests must never touch real device state.
    """
    for variable in ("AQENO_CONFIG_DIR", "AQENO_DATA_DIR", "AQENO_STATE_DIR"):
        monkeypatch.setenv(variable, str(tmp_path / variable.lower()))
    yield tmp_path
