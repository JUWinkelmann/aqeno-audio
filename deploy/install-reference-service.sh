#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo deploy/install-reference-service.sh" >&2
  exit 1
fi

source_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "${source_root}"
install_root=/opt/aqeno
data_root=/aqeno-data
platform_config=/etc/aqeno/platform.env

if ! mountpoint -q "${data_root}"; then
  echo "AQENO-DATA is not mounted at ${data_root}; refusing to install." >&2
  exit 1
fi
if [[ ! -f "${data_root}/volume.json" ]]; then
  echo "AQENO-DATA marker is missing; provision and validate Data first." >&2
  exit 1
fi
for required_command in npm python3 hostnamectl systemctl mountpoint; do
  if ! command -v "${required_command}" >/dev/null; then
    echo "Required command is missing: ${required_command}" >&2
    exit 1
  fi
done
if [[ ! -x /lib/systemd/systemd-socket-proxyd ]]; then
  echo "systemd-socket-proxyd is required for the friendly port-80 entry." >&2
  exit 1
fi
if ! systemctl cat avahi-daemon.service >/dev/null 2>&1; then
  echo "avahi-daemon is required for aqeno.local discovery." >&2
  exit 1
fi

AQENO_INSTALL_DATA_ROOT="${data_root}" PYTHONPATH="${source_root}/src" python3 -c '
import os
from pathlib import Path
from aqeno.appliance.storage import CapacityLevel, create_data_layout, validate_data_volume
root = Path(os.environ["AQENO_INSTALL_DATA_ROOT"])
existing = [entry for entry in root.iterdir() if entry.name != "volume.json"]
if not existing:
    create_data_layout(root)
_marker, capacity = validate_data_volume(root)
if capacity.level is CapacityLevel.CRITICAL:
    raise SystemExit("AQENO-DATA has insufficient installation reserve")
'

version=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
revision=$(git -C "${source_root}" rev-parse --short=12 HEAD 2>/dev/null || printf source)
release_id="${version}-${revision}"
release_root="${install_root}/releases/${release_id}"
staging_root="${release_root}.staging"

(cd "${source_root}/admin" && npm ci && npm run check && npm test && npm run build)

getent group aqeno >/dev/null || groupadd --system aqeno
id aqeno >/dev/null 2>&1 || useradd --system --gid aqeno --home-dir "${data_root}" aqeno
for group_name in audio video input i2c gpio; do
  if getent group "${group_name}" >/dev/null; then
    usermod -a -G "${group_name}" aqeno
  fi
done

if [[ ! -d "${release_root}" ]]; then
  if [[ -e "${staging_root}" ]]; then
    echo "Incomplete release staging exists: ${staging_root}; inspect it before retrying." >&2
    exit 1
  fi
  install -d -o root -g root -m 0755 "${install_root}/releases" "${staging_root}"
  python3 -m venv --system-site-packages "${staging_root}/venv"
  "${staging_root}/venv/bin/pip" install "${source_root}"
  "${staging_root}/venv/bin/python" -c 'import aqeno'
  install -d -o root -g root -m 0755 "${staging_root}/admin"
  cp -a "${source_root}/admin/build/." "${staging_root}/admin/"
  mv "${staging_root}" "${release_root}"
fi

install -d -o aqeno -g aqeno -m 0750 \
  "${data_root}/state/config" "${data_root}/state/artwork/original" \
  "${data_root}/state/identity" "${data_root}/media" \
  "${data_root}/cache/artwork" "${data_root}/cache/index" \
  "${data_root}/tmp/imports" "${data_root}/tmp/backup" \
  "${data_root}/tmp/restore" "${data_root}/backups"
install -d -o aqeno -g aqeno -m 0700 "${data_root}/state/secrets"
AQENO_APPLIANCE=1 AQENO_DATA_ROOT="${data_root}" PYTHONPATH="${source_root}/src" \
  python3 -c '
from aqeno.appliance.migration import migrate_prototype_data
from aqeno.config.paths import paths
result = migrate_prototype_data(paths())
if result.source_found:
    print(f"Prototype migration: {len(result.copied)} copied, {len(result.already_present)} already present")
'
chown -R aqeno:aqeno \
  "${data_root}/state" "${data_root}/media" "${data_root}/cache" \
  "${data_root}/tmp" "${data_root}/backups"
install -d -o root -g aqeno -m 0750 /etc/aqeno
install -o root -g aqeno -m 0640 "${source_root}/deploy/aqeno.env.example" /etc/aqeno/aqeno.env
if [[ ! -e "${platform_config}" ]]; then
  install -o root -g root -m 0644 "${source_root}/deploy/aqeno-platform.env.example" "${platform_config}"
fi
# shellcheck disable=SC1090
source "${platform_config}"
if [[ ! ${AQENO_HOSTNAME:-} =~ ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$ ]]; then
  echo "Invalid AQENO_HOSTNAME in ${platform_config}." >&2
  exit 1
fi
hostnamectl set-hostname "${AQENO_HOSTNAME}"
ln -sfn "releases/${release_id}" "${install_root}/current.next"
mv -Tf "${install_root}/current.next" "${install_root}/current"
install -o root -g root -m 0644 "${source_root}/deploy/systemd/aqeno.service" /etc/systemd/system/aqeno.service
install -o root -g root -m 0644 "${source_root}/deploy/systemd/aqeno-web.service" /etc/systemd/system/aqeno-web.service
install -o root -g root -m 0644 "${source_root}/deploy/systemd/aqeno-web.socket" /etc/systemd/system/aqeno-web.socket
install -d -o root -g root -m 0755 /etc/avahi/services
install -o root -g root -m 0644 "${source_root}/deploy/avahi/aqeno.service" /etc/avahi/services/aqeno.service

systemctl daemon-reload
systemctl enable avahi-daemon.service aqeno.service aqeno-web.socket
echo "Installed AQENO release ${release_id}. Open http://${AQENO_HOSTNAME}.local after starting AQENO."
