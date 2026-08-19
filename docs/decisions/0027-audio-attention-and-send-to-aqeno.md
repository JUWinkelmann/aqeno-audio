# ADR 0027 — Audio feedback, attention classes and Send to AQENO

**Status:** Accepted
**Date:** 2026-08-19
**Amends:** `PRODUCT_FOUNDATION.md` § 3 (P25), § 15; `FAILURE_STATES.md` § 6;
`CONFIGURATION_DEFAULTS.md` § 6; `docs/product/FUTURE_PRODUCT_CONCEPTS.md` F1
**Relates to:** ADR 0013, ADR 0015, ADR 0023, ADR 0025, ADR 0026

## Context

AQENO already has a display policy and an illumination policy. It has no audio policy — and yet it
has audio rules, scattered as per-feature clauses: `FAILURE_STATES.md` § 6 defines a failure tone,
`CONFIGURATION_DEFAULTS.md` § 6 defines an acknowledgement tone for an unassigned token, and both
independently state that Night silences them. Every future sound would add another such clause and
another `if night` somewhere.

Two of those clauses are also now wrong in a way that matters. `FAILURE_STATES.md` says "under Night
policy, system sounds are suppressed" as a blanket rule. Applied to a timer or an alarm, that
suppression would make the capability useless: a wake-up that stays silent because the room is dark
is not a wake-up. Night has to distinguish *what kind* of sound is asking to be heard.

Separately, `Send to AQENO` has been a recorded future concept (`FUTURE_PRODUCT_CONCEPTS.md` F1)
with real product weight — it is one of ADR 0023's three pillars — but no normative rules about
delivery, retention, deletion or authorisation. Those decisions have now been made, and they belong
somewhere before anything is built against a guess.

Nothing here is implemented by this ADR. AQENO has no audio-feedback code, no message domain and no
cloud transport, and none is created speculatively.

## Decision

### 1. Silence is the default

> **Silence is the default. Sound must earn its presence.**

This is the audio half of the attention principle (P19) and is recorded as `PRODUCT_FOUNDATION.md`
P25. A sound is justified only if it supports eyes-free operation, confirms a relevant action,
signals a relevant event, or needs timely attention. **Input happening is not a reason to make a
sound.**

AQENO therefore emits no tone for a SELECT detent, a VOLUME detent, or a PREVIOUS, NEXT or HOME
press. Mechanical and tactile feedback stays primary (P20); audio is one output of the user
interface beside display and control illumination, not a running commentary on it.

### 2. Four semantic audio classes

Every AQENO-generated sound belongs to exactly one class. The class — never the individual
feature — decides audibility, level and how it behaves against playing media.

| Class | Meaning | Example |
|---|---|---|
| `FEEDBACK` | short optional confirmation of a relevant action | a timer was started |
| `NOTIFICATION` | something is *available*, not urgent | a personal message arrived |
| `ATTENTION` | something needs noticing soon | a timer finished |
| `ALARM` | a deliberately scheduled wake event | the alarm clock |

The existing per-feature rules become instances: the failure tone is `FEEDBACK` (specifically
`ERROR_SOFT`), and the unassigned-token acknowledgement is `FEEDBACK`.

### 3. Night is not a master mute

> **Dark is not mute. Night is not master mute.**

`DARK` describes visible output (ADR 0026 § 9). `NIGHT` is an attention policy. They are different
concepts and neither implies the other: an alarm may sound with the panel completely black, and a
message arriving at 3 a.m. makes no sound at all.

| Class | Normal | Night |
|---|---|---|
| `FEEDBACK` | allowed | **silent** |
| `NOTIFICATION` | allowed | **silent** |
| `ATTENTION` | allowed | allowed, under a night-safe level |
| `ALARM` | allowed | allowed, under the alarm policy |

This policy is decided in **one place**. No feature may carry its own `if night` branch, which is
precisely the shape the existing scattered clauses were growing into. The night-safe `ATTENTION`
level and the alarm policy's concrete values are UX and real-test questions and stay open.

### 4. Volume is not one number

At least three levels are distinguished, conceptually today and structurally when audio feedback is
built:

- **`MEDIA_VOLUME`** — music, audio drama, podcasts, radio. The physical VOLUME control operates
  this and nothing else.
- **`FEEDBACK_LEVEL`** — short AQENO system sounds. Deliberately bounded and restrained. Media at
  100 % must not produce a confirmation tone at 100 %.
- **`ALARM_VOLUME`** — its own level. A story played very quietly at bedtime must not make the
  morning alarm inaudible.

`ATTENTION` may initially be derived from these by the central policy rather than exposing a fourth
user-visible setting. Concrete values are a real-test question.

Today's `VolumeLimits` (maximum, night maximum, headphone maximum) remains the media ceiling and is
unchanged. The child ceiling stays a hearing-protection limit on media, and no system sound may be
used to exceed it.

### 5. Audio focus, in one small policy

Not a framework. One policy with four rules:

- `FEEDBACK` — does not interrupt playing media.
- `NOTIFICATION` — does not pause media. Whether brief ducking helps is a sound and real-test
  question, deliberately unanswered.
- `ATTENTION` — may temporarily lower media.
- `ALARM` — takes over audio under the alarm policy.
- **Message playback is content, not a notification.** Playing a personal message pauses media and
  resumes it afterwards, subject to the existing playback contracts (ADR 0009's resume behaviour
  applies unchanged).

### 6. Send to AQENO is personal connection, not messaging

An authorised person records a short voice message for an AQENO. Parent to child, grandparent to
grandchild, family to an older or assisted relative.

It is explicitly **not** a messenger, chat, social feature, public channel or notification platform.

**The message is not recorded on the device.** AQENO needs no microphone for this. Recording happens
in an authorised client: choose recipient → record → stop → optionally listen → send. No editor, no
filters, no messenger complexity.

### 7. The cloud is the courier, not the archive

> **The cloud is the courier, not the archive.**

Normative delivery sequence:

```text
sender records → client uploads → cloud holds an encrypted transport payload
  → target AQENO downloads it completely → integrity verified
  → payload committed atomically to local persistent storage
  → AQENO acknowledges successful local persistence
  → cloud transport payload deleted immediately
```

**Deletion is gated on the acknowledgement, never on the download.** "Download started" and
"transfer completed" are both insufficient. A network drop, a partial download, an integrity
failure, a local write error, a restart mid-delivery or a missing acknowledgement must never cause
the cloud copy to be discarded as delivered. The eventual transport must therefore be designed
retry-safe and idempotent.

If the device is offline the message waits in transport storage and is not lost; the sender may
later see a delivery status. That waiting must not quietly become a permanent cloud mailbox.

**Payload and metadata are different things.** The immediate-deletion rule is absolute for the
personal audio payload. Minimal service metadata — delivery status, technical operation, security
and abuse prevention, and billing if an optional service ever exists — follows data minimisation
(`AGENTS.md` § Security and privacy). No hidden durable cloud message history is created.

**No unsolicited messages.** Only senders the device owner or an administrator has authorised may
send, and an AQENO is never a publicly discoverable address. The concrete identity and pairing
mechanism is open.

Transport encryption, access control, sender authorisation, recipient binding, temporary storage,
immediate payload deletion, local retention and local deletion are all required of any
implementation. **End-to-end encryption is not claimed** and must not be, until it is actually
designed and implemented.

### 8. Delivered means local, and local means playable again

Once delivered, a message is ordinary local AQENO content and plays offline. Cloud deletion must
never mean the message can only be heard once.

Messages are **not** deleted automatically after first playback. A child should be able to hear a
grandparent's voice again. AQENO therefore needs a small local message collection — which must not
become a smartphone inbox.

Local retention must be able to express `DELETE_AFTER_PLAYBACK`, `KEEP_7_DAYS`, `KEEP_30_DAYS` and
`KEEP_UNTIL_DELETED`. `KEEP_30_DAYS` is the current hypothesis for a default and is **not** a
product invariant; real use decides it. Retention configuration belongs to the administration
client, not to a device setting. Messages must be deletable; the physical device interaction for
deletion is deliberately not invented here, and must not land on a long press, swipe, double press
or chord (ADR 0024 § A2).

### 9. Arrival never interrupts

> **New does not mean urgent. Available does not mean interrupt.**

A newly arrived message is **never** played automatically, for privacy, sleep, an ongoing
listen, an unsuitable moment and simple user control.

- **Normal state:** one very restrained `NOTIFICATION` sound and a brief, calm visual presence — a
  heart and who it is from. Then it simply remains available. No badge, no red counter, no repeated
  tone, no blinking, no banner, no prompt to listen now.
- **Night:** completely silent. No sound, no display wake, no control illumination, no automatic
  playback. Download, verification, local persistence, acknowledgement and cloud deletion happen in
  the background; the message becomes visible at the next suitable active moment.

This is the concrete form of C7 in `INTERACTION_MATRIX.md`, which stays recorded there.

### 10. Sound roles are stable; sound assets are replaceable

> **Semantic sound roles are stable. Concrete sound assets are replaceable.**

Domain and application code reference semantic roles — `MESSAGE_ARRIVED`, `ACTION_CONFIRMED`,
`TIMER_FINISHED`, `ERROR_SOFT` — never a file name. The mapping from role to asset lives in
replaceable presentation configuration, so a sound can be exchanged without a domain change, a new
event type or a migration.

A missing final asset therefore **never blocks** the message domain, the attention policy, the
Device UI, the night policy or audio focus. A clearly marked development placeholder is acceptable
during development, provided its provenance is clean for that use, and must never be mislabelled as
a production asset.

### 11. Sound identity, sources and provenance

The intended character is warm, soft, calm, friendly, high-quality, unobtrusive and timeless — not
smartphone, PC, video game, toy, hospital device, microwave, alarm system or smart-home gadget.

**AQENO does not imitate another product's sound identity.** References are described by properties
— warm, short, soft, restrained, calm, organic, non-urgent — never by naming another product to
sound like.

Three source categories are permitted, and no rule prefers one: existing assets whose rights clearly
allow the actual product use; sounds generated with generative audio tools; and own edits of
material whose rights permit it. What decides is quality, suitability, rights, provenance and
replaceability.

Before any asset ships, verify commercial use, embedding in commercial software or hardware,
redistribution as part of the product, modification if needed, attribution, other conditions, and
traceable origin. **"Free" does not mean commercially usable.** NC-licensed assets are excluded.
CC0-like releases are practically attractive but are not exempt from checking; CC BY is not excluded
where the conditions can be met deliberately. For generated assets, the generating service's terms
**at generation time** must be checked — output rights, product integration, redistribution, plan
dependencies, attribution — and never assumed from general knowledge.

For each shipped sound, provenance is documented: asset id, semantic role, source type, source or
tool, creator, reference, acquisition or generation date, original licence reference, original file,
modifications, final file and approval version; for generated assets additionally the prompt, tool
and selected variant. Originals are kept, not only the final export. **Where this record lives is a
later implementation decision** — a machine-readable registry may be justified once assets exist;
none is built now.

Final approval requires listening on the real AQENO audio path — Pi → MiniAmp → RH1 speakers, later
in a real enclosure — at very low and normal levels, in a quiet room and a dark bedroom, against
speech and against music, repeatedly. Pleasant over headphones is not approval.

## Alternatives considered

**Keep per-feature sound rules.** Rejected: it is what produced a blanket "Night suppresses system
sounds" that would silence an alarm, and every new sound would add another branch.

**Treat Night as a master mute.** Rejected in § 3: it makes timers and alarms useless and confuses a
visual rule with an attention rule.

**One volume number.** Rejected in § 4: a quiet bedtime story would leave the morning alarm
inaudible, and a confirmation tone would inherit media loudness.

**Delete the cloud payload when the download completes.** Rejected in § 7: a completed transfer is
not a verified, persisted, acknowledged delivery, and the failure mode is a lost personal message.

**Delete messages after first playback.** Rejected in § 8: hearing a familiar voice again is the
point of the feature. It remains available as a retention *option*.

**Announce arrival like a notification.** Rejected in § 9 and by P19. Available is not urgent.

**Require AI-generated sounds, or forbid them.** Both rejected in § 11: the source is not the
criterion; rights, quality and provenance are.

**Claim end-to-end encryption now.** Rejected in § 7: an unimplemented security claim is worse than
none.

## Consequences

- The audio policy is a single decision point, so the scattered clauses in `FAILURE_STATES.md` § 6
  and `CONFIGURATION_DEFAULTS.md` § 6 become instances of `FEEDBACK` rather than independent rules.
  Their present behaviour is unchanged; only their authority moves.
- `FAILURE_STATES.md`'s blanket "system sounds are suppressed under Night" is corrected: it is true
  of `FEEDBACK` and `NOTIFICATION`, and would have been a defect once a timer existed.
- The Device UI can present messages when a message domain exists, and nothing about cloud
  transport, upload status, servers or licences ever appears on the device.
- No code changes. AQENO has no audio-feedback implementation, no message domain and no transport,
  and this ADR creates none. `VolumeLimits`, `PlaybackSession` and the display machine are untouched.
- Timer and alarm work inherits § 2 and § 3 before either is built, and the open items C1 (snooze on
  the VOLUME press) and C2 (cancelling a running timer blind) stay open in `INTERACTION_MATRIX.md`.
- Sound assets cannot block development, and cannot ship without a provenance record.
