#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo deploy/rh1/configure-platform.sh" >&2
  exit 1
fi

script_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fragment=${script_root}/aqeno-rh1-config.txt
model_file=/proc/device-tree/model

if [[ ! -r ${model_file} ]] || ! tr -d '\0' <"${model_file}" | grep -q '^Raspberry Pi 4 Model B'; then
  echo "RH1 platform configuration requires a Raspberry Pi 4 Model B." >&2
  exit 2
fi

if [[ -f /boot/firmware/config.txt ]]; then
  boot_config=/boot/firmware/config.txt
elif [[ -f /boot/config.txt ]]; then
  boot_config=/boot/config.txt
else
  echo "Raspberry Pi boot config was not found." >&2
  exit 2
fi

python3 - "${boot_config}" "${fragment}" <<'PY'
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

target = Path(sys.argv[1])
fragment = Path(sys.argv[2]).read_text(encoding="utf-8").strip()
begin = "# BEGIN AQENO RH1 — managed by configure-platform.sh"
end = "# END AQENO RH1"
text = target.read_text(encoding="utf-8")

if text.count(begin) != text.count(end) or text.count(begin) > 1:
    raise SystemExit("AQENO managed boot-config block is incomplete or duplicated; inspect manually")

if begin in text:
    before, remainder = text.split(begin, 1)
    _managed, after = remainder.split(end, 1)
    unmanaged = before + after.lstrip("\n")
else:
    unmanaged = text

# Raspberry Pi OS images commonly enable onboard audio with this exact line.
# RH1 deliberately replaces it with the MiniAmp overlay below. Preserve every
# other unmanaged boot setting and the pre-AQENO backup.
unmanaged = "\n".join(
    line for line in unmanaged.splitlines() if line.strip() != "dtparam=audio=on"
) + ("\n" if unmanaged.endswith("\n") else "")

conflicting = [
    line.strip()
    for line in unmanaged.splitlines()
    if re.match(r"^\s*dtoverlay=hifiberry-", line)
    and line.strip() != "dtoverlay=hifiberry-dac"
]
if conflicting:
    raise SystemExit(
        "conflicting HiFiBerry overlay already configured: " + ", ".join(conflicting)
    )

rendered = unmanaged.rstrip() + f"\n\n{begin}\n{fragment}\n{end}\n"
if rendered == text:
    print(f"RH1 platform configuration already current: {target}")
    raise SystemExit(0)

backup = target.with_name(target.name + ".pre-aqeno")
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
    directory = os.open(target.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
except BaseException:
    try:
        os.unlink(temporary_name)
    except FileNotFoundError:
        pass
    raise

print(f"Installed RH1 I2C/HiFiBerry/firmware-splash configuration in {target}")
print("A reboot is required before a newly enabled MiniAmp appears in ALSA.")
PY
