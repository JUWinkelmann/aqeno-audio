"""Prefer the fast-deployed source tree in the dedicated RH1 developer venv."""

from __future__ import annotations

import sys

SOURCE = "/opt/aqeno/dev/source/src"
if SOURCE not in sys.path:
    sys.path.insert(0, SOURCE)
