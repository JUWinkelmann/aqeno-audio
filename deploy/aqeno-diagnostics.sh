#!/usr/bin/env bash
set -euo pipefail

echo "AQENO service"
systemctl --no-pager --full status aqeno.service || true
echo
echo "Avahi discovery"
systemctl --no-pager --full status avahi-daemon.service || true
echo
echo "Recent AQENO log"
journalctl -u aqeno.service --no-pager -n 80
echo
echo "Management listener"
ss -ltnp 'sport = :8766' || true
echo
echo "Friendly HTTP listener"
ss -ltnp 'sport = :80' || true
echo
echo "Local mDNS resolution"
getent hosts "$(hostname).local" || true
