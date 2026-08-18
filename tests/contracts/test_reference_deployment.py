from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_systemd_unit_is_unprivileged_hardened_and_restartable() -> None:
    unit = (ROOT / "deploy/systemd/aqeno.service").read_text()
    assert "User=aqeno" in unit
    assert "NoNewPrivileges=true" in unit
    assert "ProtectSystem=strict" in unit
    assert "Restart=on-failure" in unit
    assert "--management-host 0.0.0.0" in unit


def test_avahi_publishes_only_the_existing_http_management_service() -> None:
    service = (ROOT / "deploy/avahi/aqeno.service").read_text()
    assert "<type>_http._tcp</type>" in service
    assert "<port>8766</port>" in service
    assert "api=v1" in service
