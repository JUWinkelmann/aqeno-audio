# Raspberry Pi service and local discovery

> **Reference-platform deployment.** This is the reproducible Pi-4 service bootstrap, not an image
> builder or partitioner. ADR 0020/0021/0022 and `docs/architecture/APPLIANCE_ARCHITECTURE.md` remain
> canonical for storage, installation and local administration.

The reference deployment runs AQENO as the unprivileged `aqeno` user from a versioned release below
`/opt/aqeno/releases`, with `/opt/aqeno/current` selecting the active release. Persistent writes go
to the validated `/aqeno-data` mount. Platform bootstrap configuration under `/etc/aqeno` is
reconstructable and contains no AQENO user state.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now avahi-daemon aqeno.service aqeno-web.socket
```

For the reproducible reference path, install the repository and its virtual environment at
`/opt/aqeno`, then run `sudo deploy/install-reference-service.sh`. It creates only the dedicated
user/directories and installs/enables the supplied units; it deliberately does not download code,
rewrite the OS image or start AQENO before configuration has been reviewed. Use
`sudo deploy/aqeno-diagnostics.sh` for service, discovery, journal and listener status.
The supported base must already provide systemd (including `systemd-socket-proxyd`),
`avahi-daemon`, Python and the documented audio/display stack; Node/npm is additionally required
only while this development installer builds the Admin artifact. Missing prerequisites fail before
the release is activated.

RH1 platform setup verifies the Pi 4B, enables I2C, disables onboard audio and applies
`dtoverlay=hifiberry-dac` through an idempotent managed `config.txt` block. The original boot config
is retained once as `.pre-aqeno`; a conflicting HiFiBerry overlay stops installation for inspection.
AQENO selects `plughw:CARD=sndrpihifiberry,DEV=0` by card ID, not numeric order. A reboot is required
after first overlay installation; `deploy/aqeno-diagnostics.sh` reports the actual ALSA cards.

The installer also performs a locked `npm ci`, checks/tests the Admin client and produces the static
`admin/build/`. FastAPI serves that build at `/`; Node and Vite are build-time tools only and are not
started by systemd. If the build is absent, API/playback still start and the missing Web surface is
an explicit deployment defect rather than a playback dependency.

The reference environment selects Qt `eglfs` and hides the pointer. The service starts from
`multi-user.target`, so no desktop, taskbar or window manager is part of the appliance path.
The separate boot-presentation installer remains fail-closed until a canonical AQENO SVG logo and
the real RH1 DSI/display-power path are present; ordinary development never installs Plymouth.

The centrally configured hostname is `AQENO_HOSTNAME` in `/etc/aqeno/platform.env`; its RH1 default
is `aqeno`. The AQENO process listens only on `127.0.0.1:8766`. `aqeno-web.socket` exposes port 80 through
systemd's small socket proxy, so static Admin and `/api/v1` remain same-origin at
`http://aqeno.local`. Avahi publishes `_http._tcp` and `_aqeno-admin._tcp`; its hostname-conflict
handling avoids pretending that two default-named devices can both own `aqeno.local`. Direct IP on
port 80 is diagnostic fallback. Discovery grants no authority: password/session authentication and
physical first ownership remain mandatory.

RH1 deliberately uses HTTP on the trusted local network. A self-signed certificate is not installed
because a browser warning is not acceptable product UX. HTTP cannot protect credentials from a
hostile LAN observer; passkeys, Secure cookies and remote administration therefore remain outside
this boundary until AQENO has a warning-free trusted-certificate design. The reference AQENO units
expose TCP 80 and mDNS UDP 5353 only; SSH and any broader host firewall policy belong to platform
provisioning, not the AQENO API process.

The service writes only below `/aqeno-data` and does not run as root. Playback starts before optional
network readiness; neither Avahi nor the HTTP socket adds `network-online.target` ordering.

For iteration, copy `deploy/rh1.env.example` to ignored `deploy/rh1.local` and use `make pi-dev`,
`pi-status`, `pi-logs`, `pi-health` and periodic `pi-deploy`. The unprivileged deploy user can invoke
only the fixed `aqeno-devctl` operation set. Uploads stage below `/var/tmp/aqeno-upload`; neither the
fast nor release path can name, synchronize or remove `/aqeno-data`.
