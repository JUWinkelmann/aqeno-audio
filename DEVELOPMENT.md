# Development

**Closes:** gap G03. Toolchain, repository layout, and how to run and test AQENO.

Technology decisions live in `docs/decisions/`. This document describes only how to work with them.

## Toolchain

| Tool | Version | Source |
|---|---|---|
| Python | ≥ 3.11, developed on 3.13 | system (ADR 0001) |
| PySide6 / Qt 6 | 6.x | **system packages** — see below |
| GStreamer + PyGObject | 1.x | **system packages** — see below |
| pytest, ruff, mypy | current | virtual environment |

**PySide6 and PyGObject must come from system packages, not pip.** PyGObject binds to the system
GStreamer and GObject introspection data, and installing it through pip on Debian or Raspberry Pi OS
reliably produces a broken build. The virtual environment is therefore created with
`--system-site-packages` so it can see them, while pytest, ruff and mypy are installed into it.

> **Verify before relying on it:** whether Raspberry Pi OS Trixie packages PySide6 at a usable
> version. This is a P2 feasibility item. On Fedora (the development machine) `python3-pyside6` and
> `python3-gobject` are available.

### Setup

```bash
# Fedora (development machine)
sudo dnf install python3-pyside6 python3-gobject \
     gstreamer1 gstreamer1-plugins-base gstreamer1-plugins-good

# Debian / Raspberry Pi OS
sudo apt install python3-pyside6 python3-gi python3-gi-cairo \
     gir1.2-gstreamer-1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On RH1, install the optional I2C control stack as well:

```bash
pip install -e ".[dev,rh1]"
```

The `rh1` packages (`adafruit-blinka`, `adafruit-circuitpython-seesaw` and
`adafruit-circuitpython-neokey`) are MIT-licensed and are used only by the concrete controls
adapter. They are not imported by the headless Core.

## Repository layout

Directories mirror the layers in `ARCHITECTURE.md`. The nesting is the architecture, not filing.

```
src/aqeno/
  domain/          # entities, value objects, state machines. Standard library only.
  application/     # use cases, services, policies. Standard library only.
  ports/           # Protocol definitions. Standard library only.
  adapters/
    audio/         # GStreamer          (ADR 0003)
    display/       # panel power, brightness
    led/           # user-facing LEDs
    input/         # I2C encoder, NeoKey, keyboard simulator
    nfc/           # simulated first, PN532 later
    persistence/   # SQLite + TOML      (ADR 0007)
    network/
    fakes/         # used by tests and by the desktop run target
  ui/
    qml/           # appliance views: presentation and user intentions only
    models/        # concrete Python/QML boundary; calls application use cases
    i18n/          # .ts sources, compiled .qm  (ADR 0005)
  management/      # local FastAPI/OpenAPI presentation adapter (ADR 0018)
  config/          # defaults, validation against CONFIGURATION_DEFAULTS.md
  __main__.py      # composition root: the only place adapters are chosen
tests/
  unit/  contracts/  scenarios/  hardware/  conftest.py
tools/             # import-boundary check, i18n extraction, calibration helper
docs/
```

### Rules the layout enforces

1. **`domain/`, `application/`, `ports/` and `config/` import only the standard library** and each
   other. No Qt, no GStreamer, no `gi`, no `board`/`busio`, no `RPi.*`.
2. **Only `adapters/` may reach the network.** Nothing else may import `socket`, `http`, `urllib` or
   any client library. The Core stays fully functional with no network at all (ADR 0010 § 1). A port
   may *describe* network state — describing it needs no socket.
3. **`__main__.py` is the only module that selects adapters.** Everything else receives its
   dependencies. This is what makes the fake-backed desktop run target possible without a flag
   scattered through the code.
4. **Dependencies point inward.** `adapters/` may import `ports/` and `domain/`, never `ui/`.
   `ui/` talks to `application/`, never to `adapters/` — that rule is what keeps a future service
   layer possible without building one today.
5. **No module reads the wall clock.** The `Clock` port is injected (ADR 0008 § 4).
6. **No hardcoded timeout, brightness or volume value.** Everything comes from `config/`, which is
   validated against `CONFIGURATION_DEFAULTS.md`.
7. **Hardware adapters are named for the technology they speak, not the board they were first
   tested on** — `adapters/input/i2c_seesaw.py`, not `adapters/input/pi.py`. The Raspberry Pi
   configuration is AQENO Reference Hardware 1, the first implementation of these ports and
   explicitly not the only possible one (ADR 0010 § 2).

Rules 1, 2 and 4 are enforced by `tests/unit/test_import_boundaries.py`, not by discipline
(ADR 0008 § 6). Each was verified to actually fail on a real violation — a boundary test that cannot
fail is worse than none.

## Running

```bash
# Desktop, all hardware faked — the normal development loop
python -m aqeno --profile kids-early --fake-hardware

# Open the local core, verify persistence and adapter construction, then exit
python -m aqeno --profile kids-early --fake-hardware --check

# Desktop, real audio, faked controls and display power
python -m aqeno --profile kids-early --fake-hardware=input,display,nfc

# Reference hardware
python -m aqeno --profile kids-early
```

The normal desktop command opens the minimal Kids Early Device UI. It uses the keyboard simulator;
without `--fake-hardware`, the composition root selects the RH1 I2C controls adapter and the
headless Core remains available when no display adapter is present. To run the same Core without
Qt or a display, select only the fake audio and input boundaries:

```bash
python -m aqeno --profile kids-early --fake-hardware=audio,input
```

The `--check` form remains the fast composition and persistence smoke test; it deliberately does not
start Qt. There is no temporary terminal-control UI.

With `--fake-hardware`, semantic input events come from the keyboard simulator:

| Key | Event |
|---|---|
| `↑` / `↓` | `VolumeDelta` ± one encoder step |
| `Space` | `TogglePlayback` |
| `→` / `←` | `Next` / `Previous` |
| `w` | `WakeRequest` |
| `a` / `d` | `FocusPrevious` / `FocusNext` — NAV rotation |
| `s` | `Select` — NAV press, activates the focused tile |
| `b` | `Back` — the contextual back that LEFT will carry, not a control of its own |
| `1`–`9` | `NfcPresented` with a fixed test UID |
| `0` | `NfcRemoved` |
| `n` | toggle `night_active` |

The intended control set is LEFT · NAV · RIGHT · VOL (ADR 0024 § A1). The simulator covers all four:
`←`/`→` are LEFT/RIGHT, `a`/`d`/`s` are the NAV encoder, `↑`/`↓`/`Space` are VOL. `b` is a stand-in
for the contextual back that LEFT will carry once a browsing level exists — it is not a fifth
control, and it is currently the only way to leave Now Playing without touch.

Note what the simulator does *not* cover: it emits semantic events directly and therefore bypasses
`MappedInputBus`, so it exercises the four controls' meanings but never their bindings. Mapping is
covered by `tests/unit/test_control_mapping.py` instead.

Like a waking touch, a navigation key that wakes a dark panel is consumed and selects nothing.
Volume and Play/Pause are deliberately different: they act immediately and never wake, so a first
volume step in a dark room is not spent on lighting the screen.

The simulator is not a debug afterthought — `FIRST_VERTICAL_SLICE.md` requires it, and the dark-room
and display-state scenarios are exercised through it long before the I2C hardware exists.

## Working against the Reference hardware

**Almost all development happens on the desktop.** Copying to the Pi for every change is not the
workflow and would make the loop unusable.

| Runs on the desktop | Needs the Pi |
|---|---|
| Full Kids Early UI in a window | Real panel power `OFF` and backlight control |
| Real audio through GStreamer | I2C rotary encoder and NeoKey |
| Keyboard simulator for all semantic inputs | User-facing LEDs, including true off |
| Library, persistence, resume, migrations | NFC reader, once it exists |
| The whole display **state machine**, as logical state | Boot and wake timing against the targets |
| Every test except `-m hardware` | Volume calibration in dB(A) |

The important asymmetry: on the desktop, `OFF` is a **logical state** that the fake display adapter
records and tests assert. The window does not go dark. Whether the panel truly stops emitting light is
the one product requirement the desktop cannot answer — along with the boot budget. Both are
`-m hardware` territory, and neither should be assumed from a green desktop run.

### Getting code onto the Pi

RH1 is a deployment target; the development checkout remains the source of truth. The reference
installer creates an unprivileged SSH account in the bounded `aqeno-deploy` group and installs one
fixed root helper. Configure the host locally (the file is ignored by Git):

```bash
cp deploy/rh1.env.example deploy/rh1.local
# edit host/user/optional key path; use SSH keys, never a password in this file
```

The fast loop builds the Admin assets, delta-transfers source/build output to a bounded staging path,
activates `/opt/aqeno/dev`, restarts the service and performs the local API health check:

```bash
make pi-dev
make pi-status
make pi-logs          # follow; Ctrl-C stops only the local SSH command
make pi-restart
make pi-health
```

Regularly test the real immutable release shape:

```bash
make pi-deploy
make pi-health
make pi-diagnostics
```

`pi-deploy` builds a wheel plus Admin bundle, installs a new
`/opt/aqeno/releases/<version-build>/`, atomically switches `current`, and returns to the previous
release if its restart/health check fails. Neither path transfers, mirrors or removes `/aqeno-data`.
`rsync --delete` is confined to newly uploaded staging or `/opt/aqeno/dev`; the privileged helper
rejects paths outside `/var/tmp/aqeno-upload`. It exposes only deploy, status, logs, restart, health
and diagnostics — no arbitrary root command. Coding agents may use those Make targets with the same
SSH key and bounded sudo rule; they do not need root SSH or unrestricted sudo.

Typical hardware iteration is: change → local tests → `make pi-dev` → physical test →
`make pi-logs` → correct → `make pi-dev`. The SD card remains in RH1. `localhost` development and
Vite hot reload remain separate and require no Avahi, port 80, sudo or host-name changes.

## Testing

```bash
pytest                      # everything except hardware
pytest tests/unit           # fast loop, milliseconds
pytest -m hardware          # on the Pi only, with hardware attached
ruff check . && ruff format --check .
mypy src/aqeno/domain src/aqeno/application src/aqeno/ports
```

Strategy, layers and the invariant-to-test mapping are in ADR 0008. Two rules worth repeating because
they are easy to break:

- **No `time.sleep()` in tests.** Advance `FakeClock` instead.
- **No audio files in the repository.** Fixtures are generated at test time.

## Before committing

```bash
ruff check . && mypy src/aqeno/domain src/aqeno/application src/aqeno/ports && pytest
```

Then check `AGENTS.md` § Definition of done. Commits stay conceptually narrow so a single
AI-assisted change can be reverted on its own (`MISTAKES.md` M-001), and authorship trailers stay
honest (ADR 0006 § 7).
