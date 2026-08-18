from __future__ import annotations

from subprocess import CompletedProcess

from aqeno.adapters.platform.plymouth import PlymouthHandover


def test_plymouth_handover_uses_one_fixed_bounded_command(monkeypatch) -> None:
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("aqeno.adapters.platform.plymouth.subprocess.run", run)

    PlymouthHandover().complete()

    assert calls == [
        (
            ["plymouth", "quit", "--retain-splash"],
            {"check": False, "capture_output": True, "text": True, "timeout": 5},
        )
    ]
