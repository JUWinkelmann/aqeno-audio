#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo deploy/rh1/install-boot-presentation.sh" >&2
  exit 1
fi

script_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repository_root=$(cd "${script_root}/../.." && pwd)
logo_source=${AQENO_LOGO_SOURCE:-${repository_root}/branding/aqeno-logo.svg}
theme_source=${script_root}/plymouth
theme_target=/usr/share/plymouth/themes/aqeno

for command in plymouth-set-default-theme rsvg-convert update-initramfs; do
  command -v "${command}" >/dev/null || {
    echo "Required boot-presentation command is missing: ${command}" >&2
    exit 2
  }
done
if [[ ! -f ${logo_source} ]]; then
  echo "Canonical AQENO SVG logo is missing: ${logo_source}" >&2
  echo "Refusing to invent or install a placeholder boot identity." >&2
  exit 2
fi

"${script_root}/configure-platform.sh"

if [[ -f /boot/firmware/cmdline.txt ]]; then
  cmdline=/boot/firmware/cmdline.txt
elif [[ -f /boot/cmdline.txt ]]; then
  cmdline=/boot/cmdline.txt
else
  echo "Raspberry Pi kernel command line was not found." >&2
  exit 2
fi

python3 - "${cmdline}" <<'PY'
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

target = Path(sys.argv[1])
lines = target.read_text(encoding="utf-8").splitlines()
if len(lines) != 1:
    raise SystemExit("Raspberry Pi cmdline.txt must contain exactly one line")
arguments = lines[0].split()
required = (
    "quiet",
    "splash",
    "loglevel=3",
    "systemd.show_status=auto",
    "rd.udev.log_level=3",
    "vt.global_cursor_default=0",
    "plymouth.ignore-serial-consoles",
)
for argument in required:
    if argument not in arguments:
        arguments.append(argument)
rendered = " ".join(arguments) + "\n"
if rendered == lines[0] + "\n":
    raise SystemExit(0)

backup = target.with_name(target.name + ".pre-aqeno-plymouth")
if not backup.exists():
    shutil.copy2(target, backup)
descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary_name, target.stat().st_mode)
    os.replace(temporary_name, target)
except BaseException:
    try:
        os.unlink(temporary_name)
    except FileNotFoundError:
        pass
    raise
PY

install -d -o root -g root -m 0755 "${theme_target}"
install -o root -g root -m 0644 "${theme_source}/aqeno.plymouth" "${theme_target}/aqeno.plymouth"
install -o root -g root -m 0644 "${theme_source}/aqeno.script" "${theme_target}/aqeno.script"
rsvg-convert --keep-aspect-ratio --width 280 --height 160 \
  --output "${theme_target}/aqeno-logo.png.partial" "${logo_source}"
chmod 0644 "${theme_target}/aqeno-logo.png.partial"
mv -Tf "${theme_target}/aqeno-logo.png.partial" "${theme_target}/aqeno-logo.png"
plymouth-set-default-theme aqeno
update-initramfs -u

echo "Installed AQENO Plymouth theme from ${logo_source}."
echo "Enable AQENO_BOOT_PRESENTATION=plymouth only with a validated RH1 Device UI/display adapter."
