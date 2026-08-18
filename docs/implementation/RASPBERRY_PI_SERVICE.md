# Raspberry Pi service and local discovery

The reference deployment runs AQENO as the unprivileged `aqeno` user. Install the repository at
`/opt/aqeno`, copy `deploy/systemd/aqeno.service` to `/etc/systemd/system/`, and copy
`deploy/avahi/aqeno.service` to `/etc/avahi/services/`. Create the directories named in
`deploy/aqeno.env.example`, owned by `aqeno`, then copy that file to `/etc/aqeno/aqeno.env`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now avahi-daemon aqeno.service
```

Avahi publishes the existing HTTP service as `_http._tcp`; clients can use
`http://aqeno.local:8766`. Direct IP access remains available. Discovery grants no authority: every
management operation still requires the management key, except the one-time pairing exchange.

The unit restarts failures, writes only below `/var/lib/aqeno` and `/var/cache/aqeno`, and does not
run as root. Playback starts in the AQENO process before optional network readiness is required.
