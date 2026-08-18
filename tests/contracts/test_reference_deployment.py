from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).parents[2]


def test_systemd_unit_is_unprivileged_hardened_and_restartable() -> None:
    unit = (ROOT / "deploy/systemd/aqeno.service").read_text()
    assert "User=aqeno" in unit
    assert "NoNewPrivileges=true" in unit
    assert "ProtectSystem=strict" in unit
    assert "Restart=on-failure" in unit
    assert "--management-host 127.0.0.1" in unit
    assert "RequiresMountsFor=/aqeno-data" in unit
    assert "network-online.target" not in unit
    assert "ReadWritePaths=/aqeno-data" in unit
    assert "/opt/aqeno/current/venv/bin/python" in unit


def test_avahi_publishes_only_the_existing_http_management_service() -> None:
    service = (ROOT / "deploy/avahi/aqeno.service").read_text()
    ElementTree.fromstring(service)
    assert "<type>_http._tcp</type>" in service
    assert "<port>80</port>" in service
    assert "_aqeno-admin._tcp" in service
    assert "api=v1" in service


def test_reference_hostname_is_central_platform_configuration() -> None:
    platform = (ROOT / "deploy/aqeno-platform.env.example").read_text()
    installer = (ROOT / "deploy/install-reference-service.sh").read_text()
    assert "AQENO_HOSTNAME=aqeno" in platform
    assert 'source "${platform_config}"' in installer
    assert 'hostnamectl set-hostname "${AQENO_HOSTNAME}"' in installer


def test_public_http_socket_proxies_to_loopback_api_without_network_online() -> None:
    socket = (ROOT / "deploy/systemd/aqeno-web.socket").read_text()
    proxy = (ROOT / "deploy/systemd/aqeno-web.service").read_text()
    assert "ListenStream=80" in socket
    assert "127.0.0.1:8766" in proxy
    assert "systemd-socket-proxyd" in proxy
    assert "User=aqeno" in proxy
    assert "network-online.target" not in socket + proxy


def test_reference_environment_is_kiosk_oriented() -> None:
    environment = (ROOT / "deploy/aqeno.env.example").read_text()
    assert "QT_QPA_PLATFORM=eglfs" in environment
    assert "QT_QPA_EGLFS_HIDECURSOR=1" in environment
    assert "AQENO_ADMIN_DIR=/opt/aqeno/current/admin" in environment


def test_installer_refuses_an_ambiguous_install_location() -> None:
    installer = (ROOT / "deploy/install-reference-service.sh").read_text()
    assert "install_root=/opt/aqeno" in installer
    assert "EUID" in installer
    assert "systemctl enable avahi-daemon.service aqeno.service aqeno-web.socket" in installer
    assert "mountpoint -q" in installer
    assert "validate_data_volume(root)" in installer
    assert "create_data_layout(root)" in installer
    assert "systemd-socket-proxyd is required" in installer
    assert "avahi-daemon is required" in installer
    assert "releases/${release_id}" in installer
    assert 'admin/build/." "${staging_root}/admin/' in installer
    assert "rm -rf" not in installer
