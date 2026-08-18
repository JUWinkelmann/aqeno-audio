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
    assert "AQENO_ALSA_DEVICE=plughw:CARD=sndrpihifiberry,DEV=0" in environment


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


def test_rh1_platform_config_selects_miniamp_without_numeric_alsa_identity() -> None:
    fragment = (ROOT / "deploy/rh1/aqeno-rh1-config.txt").read_text()
    installer = (ROOT / "deploy/install-reference-service.sh").read_text()
    configurator = (ROOT / "deploy/rh1/configure-platform.sh").read_text()
    assert "dtparam=i2c_arm=on" in fragment
    assert "dtparam=audio=off" in fragment
    assert "dtoverlay=hifiberry-dac" in fragment
    assert "disable_splash=1" in fragment
    assert "configure-platform.sh" in installer
    assert "Raspberry Pi 4 Model B" in configurator
    assert "conflicting HiFiBerry overlay" in configurator
    assert "hw:0" not in fragment + installer + configurator


def test_remote_deployment_is_bounded_away_from_aqeno_data() -> None:
    remote = (ROOT / "deploy/rh1/remote.sh").read_text()
    helper = (ROOT / "deploy/rh1/aqeno-devctl").read_text()
    sudoers = (ROOT / "deploy/rh1/aqeno-deploy.sudoers").read_text()
    combined = remote + helper + sudoers
    assert "/aqeno-data" not in combined
    assert "/var/tmp/aqeno-upload" in remote
    assert "/var/tmp/aqeno-upload" in helper
    assert "BatchMode=yes" in remote
    assert "sudo -n /usr/local/libexec/aqeno-devctl" in remote
    assert "/usr/local/libexec/aqeno-devctl" in sudoers
    assert "activate-release" in helper
    assert 'mv -Tf "${install_root}/current.next"' in helper
    assert "rsync -rlt --delete" in helper
    assert "deployment uploads may contain only directories and regular files" in helper
    assert '"${repository_root}[rh1]"' in remote
    assert "--no-index --find-links" in helper
    assert 'runuser -u "${deploy_user}"' in helper
    assert "pip install --no-deps --editable" not in helper


def test_boot_presentation_is_appliance_only_asset_driven_and_has_no_delay() -> None:
    environment = (ROOT / "deploy/aqeno.env.example").read_text()
    installer = (ROOT / "deploy/rh1/install-boot-presentation.sh").read_text()
    theme = (ROOT / "deploy/rh1/plymouth/aqeno.script").read_text()
    reference_installer = (ROOT / "deploy/install-reference-service.sh").read_text()
    assert "# AQENO_BOOT_PRESENTATION=plymouth" in environment
    assert "install-boot-presentation.sh" not in reference_installer
    assert "AQENO_LOGO_SOURCE" in installer
    assert "Refusing to invent or install a placeholder" in installer
    assert "quiet" in installer and "splash" in installer
    assert "vt.global_cursor_default=0" in installer
    assert "plymouth-set-default-theme aqeno" in installer
    assert 'Image("aqeno-logo.png")' in theme
    assert "sleep" not in installer.lower() + theme.lower()
