"""Power loss must not corrupt the library — ADR 0007 § "Open verification".

This is the single test that most directly protects the product requirement in
`PLATFORM_CONTRACTS.md` § "Persistence contract": *unexpected power loss must
not corrupt the library*. A three-year-old switches the device off by pulling
the plug, and the library has to survive that.

Approach: a child process opens the SQLite library and writes resume
checkpoints in a tight loop, exactly as real playback would every
`CONFIGURATION_DEFAULTS.md` § 4 resume interval (10 s) — except compressed to a
counter instead of wall-clock seconds, since nothing here may call
`time.sleep()`. The parent spin-polls (no sleep) until the child has made some
progress, then sends `SIGKILL` with no warning — no graceful shutdown, no
chance to flush anything the OS had not already committed. Only *after* the
child is confirmed dead does the parent read the child's last-written
"true position" marker: reading it before the kill would be racing an
extremely fast loop and would not reflect what actually happened at the
moment of death. The parent then reopens the library in-process and checks
it.

What this proves: a process torn down mid-write (mid-transaction or between
transactions) leaves `aqeno.db` in a state that (a) still opens without
`DatabaseCorruptError`, and (b) reports a resume position within the
`CONFIGURATION_DEFAULTS.md` § 4 tolerance (<= 12 s behind the true position) of
where the child actually was.

What this does NOT prove: `PRAGMA synchronous=NORMAL` (ADR 0007 § 2) means a
commit can be acknowledged before it is durably on disk, so a real *power*
loss — the disk itself losing power, not just the process being killed — can
lose slightly more than a killed process does, since the OS page cache
generally survives a process kill but not a power cut. That gap is inherent to
the `NORMAL` trade-off the ADR makes deliberately and is not something an
in-process or subprocess-kill test can exercise without pulling real power to
real storage; it is out of reach here and stays an open verification item on
Reference hardware, as ADR 0007 itself says.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from aqeno.adapters.persistence import open_library
from aqeno.domain.content import ContentId, ContentItem, ContentKind, LocalFileSource

_CHECKPOINT_INTERVAL = 10
"""Mirrors CONFIGURATION_DEFAULTS.md § 4: resume persists every 10 simulated seconds."""

_ACCEPTABLE_RESUME_ERROR = 12
"""CONFIGURATION_DEFAULTS.md § 4: acceptable resume error after power loss."""

_MAX_SIMULATED_SECONDS = 100_000
"""Safety bound so the child cannot spin forever if synchronisation ever misses."""

_CHILD_SCRIPT = f"""
import os
import sys
sys.path.insert(0, {str(Path(__file__).resolve().parents[2] / "src")!r})

from datetime import timedelta
from pathlib import Path

from aqeno.adapters.persistence import open_library
from aqeno.domain.content import ContentId
import uuid

data_dir = Path(sys.argv[1])
progress_path = Path(sys.argv[2])
content_id = ContentId(uuid.UUID(sys.argv[3]))
profile_name = sys.argv[4]

library = open_library(data_dir)
tmp_path = progress_path.with_suffix(".tmp")
for elapsed in range({_MAX_SIMULATED_SECONDS}):
    if elapsed % {_CHECKPOINT_INTERVAL} == 0:
        library.set_resume(content_id, profile_name, timedelta(seconds=elapsed))
    # Atomic: the parent must never observe a torn/partial write after the kill.
    tmp_path.write_text(str(elapsed))
    os.replace(tmp_path, progress_path)
"""


def _spin_wait_for_progress(progress_path: Path, *, at_least: int, timeout_seconds: float) -> int:
    """Busy-poll (no `time.sleep()`) until the child reports progress, or give up.

    Synchronises on the child's own progress counter rather than on wall-clock
    time — the safety timeout below only guards against the child never
    starting at all, it is not the synchronisation mechanism. Used only to
    confirm the child is alive and writing; the *value* read here is not used
    as ground truth, because it necessarily precedes the kill and an
    extremely fast loop can move far beyond it before the signal lands.
    """
    deadline = time.monotonic() + timeout_seconds
    last = -1
    while time.monotonic() < deadline:
        try:
            text = progress_path.read_text()
            last = int(text) if text else -1
        except (FileNotFoundError, ValueError):
            last = -1
        if last >= at_least:
            return last
    raise TimeoutError(f"child never reached progress {at_least}; last seen {last}")


def _read_progress(progress_path: Path) -> int:
    """Reads the child's last-written "true position" marker.

    Only safe to call after the child is confirmed dead: the write is atomic
    (temp file + `os.replace`), so this always sees a complete value.
    """
    return int(progress_path.read_text())


def test_process_killed_mid_write_leaves_the_library_openable_and_resume_close(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    progress_path = tmp_path / "progress.txt"
    content_id = ContentId()
    profile_name = "kids-early"

    setup_library = open_library(data_dir)
    setup_library.save_content(
        ContentItem(
            id=content_id,
            title="Power Loss Fixture",
            kind=ContentKind.AUDIOBOOK,
            sources=(LocalFileSource(path=Path("/media/fixture.mp3")),),
        )
    )
    setup_library.close()

    script_path = tmp_path / "_write_resume_until_killed.py"
    script_path.write_text(_CHILD_SCRIPT)

    child = subprocess.Popen(
        [
            sys.executable,
            str(script_path),
            str(data_dir),
            str(progress_path),
            str(content_id.value),
            profile_name,
        ],
        env=os.environ.copy(),
    )
    try:
        # Confirm the child is alive and has started writing, then kill it with
        # no warning. The exact progress value observed here is not used as
        # ground truth — see `_read_progress`.
        _spin_wait_for_progress(progress_path, at_least=1, timeout_seconds=30.0)
        os.kill(child.pid, signal.SIGKILL)
    finally:
        child.wait(timeout=10)

    assert child.returncode != 0, "the child must have been killed, not exited on its own"

    true_elapsed_at_kill = _read_progress(progress_path)

    # The library must open without raising DatabaseCorruptError or SchemaTooNewError.
    library = open_library(data_dir)
    try:
        resume = library.get_resume(content_id, profile_name)

        assert resume is not None, "a checkpoint at t=0 was written before the kill"

        last_checkpoint = (true_elapsed_at_kill // _CHECKPOINT_INTERVAL) * _CHECKPOINT_INTERVAL
        lag = true_elapsed_at_kill - resume.total_seconds()

        assert 0 <= lag <= _ACCEPTABLE_RESUME_ERROR, (
            f"resume lagged the true position by {lag}s, "
            f"outside the {_ACCEPTABLE_RESUME_ERROR}s tolerance "
            f"(true={true_elapsed_at_kill}, resume={resume.total_seconds()}, "
            f"expected checkpoint>={last_checkpoint})"
        )
    finally:
        library.close()


def test_repeated_kills_never_corrupt_the_library(tmp_path: Path) -> None:
    """ADR 0007's own verification note: pull power "repeatedly" and confirm the
    library still opens. Three short rounds stand in for "repeatedly" here."""
    data_dir = tmp_path / "data"
    content_id = ContentId()
    profile_name = "kids-early"

    setup_library = open_library(data_dir)
    setup_library.save_content(
        ContentItem(
            id=content_id,
            title="Repeated Kill Fixture",
            kind=ContentKind.AUDIOBOOK,
            sources=(LocalFileSource(path=Path("/media/fixture.mp3")),),
        )
    )
    setup_library.close()

    for round_number in range(3):
        progress_path = tmp_path / f"progress-{round_number}.txt"
        script_path = tmp_path / f"_write_resume_until_killed_{round_number}.py"
        script_path.write_text(_CHILD_SCRIPT)

        child = subprocess.Popen(
            [
                sys.executable,
                str(script_path),
                str(data_dir),
                str(progress_path),
                str(content_id.value),
                profile_name,
            ],
            env=os.environ.copy(),
        )
        try:
            _spin_wait_for_progress(progress_path, at_least=15, timeout_seconds=30.0)
            os.kill(child.pid, signal.SIGKILL)
        finally:
            child.wait(timeout=10)

        library = open_library(data_dir)  # must not raise
        library.close()
