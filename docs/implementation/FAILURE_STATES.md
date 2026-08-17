# Failure States

**Date:** 2026-08-17
**Closes:** gap G08

`USER_JOURNEY_KIDS_EARLY.md` § 8 requires "a calm, recoverable state" with no URLs, HTTP codes,
Linux errors or configuration UI shown to a child. That sentence is not implementable, so this
document enumerates what can actually go wrong and what each case does.

## The constraint that shapes everything

`PlaybackError` is a **Group D event** in `DISPLAY_STATE_MACHINE.md`: it produces no display
transition in any state. So when the screen is off and something fails, **the screen stays off**.

This is not an oversight to work around. It means failure feedback is audible or absent, never
visual-by-waking. And under Night policy, system sounds are suppressed — so a failure at 3 a.m.
produces *nothing* except a log entry.

That is the correct behaviour. A child who is asleep or falling asleep is not helped by a beep, and
`PRODUCT_FOUNDATION.md` § 6 makes darkness a core requirement rather than a preference. Silence is
the calm state.

## Severity classes

| Class | Meaning | Response shape |
|---|---|---|
| `TRANSIENT` | Expected to resolve itself | Retry silently. Not a failure until retries are exhausted. |
| `CONTENT` | This item cannot play now; everything else still works | Stop this item calmly. Library stays usable. |
| `DEVICE` | AQENO itself is impaired | Degrade, keep whatever still works, tell a Manager. |

## The table

| # | Failure | Class | Audio | Display | Child experiences | Manager sees | Recovery |
|---:|---|---|---|---|---|---|---|
| 1 | Source file missing or moved | `CONTENT` | stops | **no wake** | nothing happens; tile marked unavailable when screen is on | path, last-seen date | item plays again if the file returns |
| 2 | File unreadable or corrupt | `CONTENT` | stops | no wake | as above | container/codec detail | none automatic |
| 3 | Codec unsupported | `CONTENT` | stops | no wake | as above | codec name, how to convert | none automatic |
| 4 | Stream unreachable | `CONTENT` | stops | no wake | as above | URL, reachability | retry on next launch |
| 5 | Stream interrupted mid-playback | `TRANSIENT` → `CONTENT` | continues, then stops | no wake | brief silence, then nothing | attempt count | automatic, then manual |
| 6 | Buffering | `TRANSIENT` | pauses briefly | **no wake** | a short gap | nothing | automatic |
| 7 | Decoder failure mid-item | `CONTENT` | stops | no wake | nothing happens | element and position | none automatic |
| 8 | Unassigned NFC tag | `CONTENT` | unaffected | **no wake** | nothing happens | UID, offered for assignment | Manager assigns it |
| 9 | No audio device | `DEVICE` | impossible | no wake | nothing plays | device state | reconnect |
| 10 | Audio device removed while playing | `DEVICE` | stops | no wake | silence | device state | resumes on reconnect |
| 11 | Library empty | `CONTENT` | n/a | n/a | calm empty screen, no error | setup guidance | Manager adds content |
| 12 | Storage full or read-only | `DEVICE` | **continues** | no wake | unchanged | degraded-mode banner | free space |
| 13 | Database corrupt | `DEVICE` | unavailable | no wake | calm empty screen | explicit repair action | **Manager decides. Never automatic.** |
| 14 | Settings file malformed | `DEVICE` | continues on defaults | no wake | unchanged | which keys were rejected | fix the file |

## Rules

1. **No modal dialogs, anywhere in a child-facing surface.** No dead ends (`AGENTS.md`).
2. **Nothing is ever deleted in response to a failure.** A missing file does not remove the item; a
   corrupt database is not wiped to make startup succeed. Losing a child's library to fix an error
   message is not a recovery strategy (ADR 0007 § 6).
3. **Resume positions survive every failure.** If the source returns, playback continues where it
   stopped.
4. **Retry is bounded and silent.** Streams: 3 attempts with 1 s, 3 s and 9 s backoff, then stop as
   `CONTENT`. No retry indicator on a child surface.
5. **Technical detail exists, but only for a Manager**, and only in the Manager surface. Never in the
   Kids UI, never spoken, never on a tile.
6. **A failure sound, where enabled, is one short quiet tone** — never repeated, never alarming, and
   **never while Night policy is active** (`CONFIGURATION_DEFAULTS.md` § 6). Default off.
7. **Unavailable is a state, not an error.** Items that cannot play are shown dimmed and are still
   selectable — a child pressing them gets silence, not a message. This keeps the library stable
   rather than making tiles vanish and reappear.
8. **`DEVICE` failures never take audio down with them if audio still works.** Case 12 is the test of
   this: a full disk stops persistence, not playback.

## What is logged

Every case above is logged with its class, a stable failure code, and the technical detail. Nothing
is logged that identifies listening behaviour beyond what is needed to diagnose the failure —
`AGENTS.md` forbids collecting data merely because it is available, and `P08 Care, not surveillance`
applies to logs too. Retention follows gap G10 when that is closed.

## Failure codes

Stable identifiers, so the UI and logs never depend on a message string:

`source_missing` · `source_unreadable` · `codec_unsupported` · `stream_unreachable` ·
`stream_interrupted` · `decode_failed` · `tag_unassigned` · `audio_device_missing` ·
`audio_device_lost` · `library_empty` · `storage_unwritable` · `database_corrupt` ·
`settings_invalid`

The audio adapter maps every GStreamer bus error onto one of these. **No GStreamer message text
crosses the port boundary** — that is the boundary at which technical language would otherwise leak
towards the UI.

## Deliberately not covered

Pairing and recovery failures during on-device `SETUP` are Manager-facing flows with their own
affordances. Network configuration in a future Management UI is likewise outside this playback
failure contract (ADR 0012). Nothing in this document depends on either surface.
