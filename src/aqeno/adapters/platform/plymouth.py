"""RH1 Plymouth-to-Qt handover.

Plymouth remains an operating-system presentation detail.  AQENO calls only a
fixed command after the first Qt frame; no user input reaches a shell.
"""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


class PlymouthHandover:
    def complete(self) -> None:
        try:
            result = subprocess.run(
                ["plymouth", "quit", "--retain-splash"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            logger.exception("Plymouth handover command failed")
            return
        if result.returncode != 0:
            logger.warning("Plymouth handover failed with exit code %s", result.returncode)

    def fail(self) -> None:
        """Do not leave a normal-looking splash running after UI startup failed."""
        self.complete()
