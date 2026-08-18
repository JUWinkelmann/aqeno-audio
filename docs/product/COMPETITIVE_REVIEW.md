# Competitive Review

**Status:** Benchmark and productization reference — **not** a scope authority
**Date:** 2026-08-18
**Reclassified:** 2026-08-18 by ADR 0015
**Full report:** https://claude.ai/code/artifact/3ffe71af-1d98-4f43-bdc4-f25431f3a5ba
**Sources:** all web sources retrieved 2026-08-18; the full report carries the citation list.

## What this document is, and is not

This began as an adversarial product review: twelve competing products, 35 usage situations, and a
deliberate attempt to prove that AQENO has no independent product value. The research is accurate and
is kept in full.

**Its role changed on the day it was written.** ADR 0015 establishes that AQENO is built to be
excellent for its actual users, not to justify a business, and that existing products are benchmarks
and teachers rather than judges of what AQENO may contain. This document is therefore read for four
things only:

- what a product solves outstandingly well;
- what works badly in daily use;
- what we would do differently for AQENO;
- which proven solution we should not reinvent.

**It has no authority over scope.** Two sentences in particular are not arguments:

> *"Not a USP"* does not mean *"do not build"*.
>
> *"A competitor already does this"* is not a reason to drop an AQENO capability.

The relevant follow-up question is always: **how would we solve this optimally for AQENO?**

## What each product does outstandingly well

| Product | Does outstandingly well | Fails in daily use | What we take from it |
|---|---|---|---|
| **Toniebox 2** | Zero-step launch: object on box, audio plays. Genuinely nothing to learn. Sleep timer fades light and volume together; sunrise wake instead of an alarm tone. | Own content limited to 90 minutes per creative figure. Progress lives on the figure, so siblings displace each other. Ear controls are imprecise in reviews. No headphone jack in generation 2. Usage data goes to the cloud. | The launch gesture is the benchmark for Kids Early. Fading light *and* volume together is a better sleep timer than either alone. Progress must belong to the listener, not the token — AQENO already does this. |
| **Yoto Player 3** | Proves a display belongs in this category when it stays small and quiet. Card in / card out as start and stop. Excellent bedtime range: night light, ok-to-wake, sleep sounds. | Cards are keys to content on Yoto servers; the club subscription got more expensive and users report expiring credits. Own recordings need account access or file transfer. | Physical insertion as an explicit stop gesture is worth considering. Night-time functions are expected in this category, not extras. |
| **hörbert** | The strongest simplicity in the market: no display, no menus, "once set up nothing can be changed by accident". One product in child, senior, accessible and care variants. Local content, no subscription. | Changing content means physically swapping the memory card — a relative living hours away cannot help. No library, no per-title progress. | Fixed, few, unchangeable controls beat configurable ones for the assisted case. The remote-care gap is real and AQENO's answer to it should be deliberate. |
| **Relish Simple Music Player** | Two large buttons, audio feedback, a volume dial that never reaches zero so the device is never silently "on". Built for dementia, used in care homes. | Only playlist playback; no library, no remote help. | The volume dial that cannot reach zero is a small, excellent idea. Audio feedback as a first-class output, not an afterthought. |
| **enna** | Realises "someone else administers, the user only consumes" for adults, with NFC cards on a dock. Shared family feed. | A tablet with all a tablet's failure modes; video-centric; subscription required for the basic function. | The receiving-side interaction model is the closest existing relative of `Send to AQENO`. Their subscription requirement is the thing to avoid. |
| **tigerbox touch** | Proves a touchscreen is viable in a children's audio device. | Touch is the only path — a broken screen is a dead device. Content behind cards and an annual subscription. | Never let the display become the only way to operate the device. AQENO's failure specification already requires this. |
| **Phoniebox** | Complete content freedom, free, large community, mature RFID handling, MQTT and GPIO. | Version 3's own feature status lists touchscreen/display support, rotary encoder and web-UI configuration as missing, and resume as in progress. Setup requires maker knowledge. | The pieces it lacks are the pieces AQENO cares most about. Its plugin and RPC architecture is worth reading before we invent our own equivalents. |
| **TonUINO** | Very small hardware, voice-guided configuration menu, no screen needed to assign a card. | Folder-based mental model; no library concept. | Spoken confirmation during configuration is a good idea for a device with no keyboard. |
| **Alexa / Echo Show** | Answers anything without navigation. Studied with the German Alzheimer's association with positive results for entertainment and carer relief. | Voice control is unreliable with memory or speech difficulties; poor reach for sensory impairment; a permanently open microphone. | Predictability is a feature. A physical control that always means the same thing is the counter-design, and that is AQENO's position. |
| **Tablet in kiosk mode** | Free, flexible, immediately available. | Maintenance, updates, and leaving the app by accident. | The failure mode to design against — AQENO must never feel like a computer running an app. |
| **DAB radio / CD player** | Unbeatably simple for one job. | One job only. | A single dedicated control for a single frequent action beats any menu. |

## Where AQENO has a real advantage

Kept from the original analysis, because knowing where we are genuinely ahead is useful — not because
AQENO needs the advantage to be justified.

1. **An existing collection becomes an operable library.** Forty MP3s of a CD rip become one work with
   chapters, artwork and exact progress, startable by a child who cannot read, with no account and no
   cloud. Nobody joins both halves: Phoniebox has the content freedom but not the interface, hörbert
   has the interface but no library, Yoto needs an account and manual playlist work. This is also the
   most economically concrete difference — 80 audio dramas as figures cost roughly €1360.

2. **A device the user never administers, maintained remotely by a relative.** hörbert requires a
   physical card swap; enna solves it as a tablet with a mandatory subscription. Audio-first remote
   curation with no subscription for the basic function is unoccupied.

3. **The device outlives its manufacturer.** Toniebox needs its cloud, Yoto cards are keys to servers,
   tigerbox lives on a subscription, enna *is* the service. AQENO has nothing that can be switched
   off. This does not carry a purchase decision on its own, but it is the one place where AQENO is
   structurally rather than gradually different.

## Commodity, and legitimately ours anyway

The original review carried a "kill list" of capabilities that do not differentiate AQENO. That list
is accurate and is kept **with its meaning corrected**: these are things AQENO should not *market* as
innovations. Whether to build them is decided by ADR 0015 § 1 and the decision order in `AGENTS.md`.

NFC and open tokens · touchscreen · having a display · local file playback · internet radio ·
podcasts · reliable resume · physical controls · offline operation · true display-off · sleep timer
and night mode · adaptive experience levels · the User/Manager/Owner role model · personal audio
messages · "content, not files" · token-to-action and scenes · hardware abstraction and the
Reference/Compatible/Community levels · Raspberry Pi, Python, Qt, QML.

Several of these are load-bearing for the primary design case and will be built. Their presence on
this list means only that they will not be presented as differentiation.

## Weaknesses worth acting on

These are the findings that survive the reframing intact, because they are about AQENO's own quality
rather than about competitive position.

| # | Finding | Why it still matters |
|---|---|---|
| 1 | **No update or recovery path exists.** It is the only row of the failure comparison with no answer. | A failed update is the most realistic way a self-built device dies. Applies regardless of market. |
| 2 | **Setup requires maker knowledge and there is no interface yet.** hörbert reaches audio in two steps; AQENO currently cannot. | The primary design case is daily use by a child. Until switching on produces sound, the case is untested. |
| 3 | **Cherry MX switches contradict the accessibility promise.** Small, light keyboard switches are the opposite of "large and forgiving controls". | Fine for the primary design case, wrong for the design horizon. Restate the promise or change the switches — later, from experience. |
| 4 | **The project carries product-company scope at one person's capacity.** Compatibility programme, OEM language, service tiers, licensing strategy. | ADR 0015 § 6 defers all of it to a productisation phase. The documents should not read as if it were current work. |
| 5 | **No user evidence exists.** 850 tests, zero observed uses. | ADR 0015 § 9 answers this: the reference prototype is a learning instrument and `USE_OBSERVATIONS.md` is where its evidence goes. |
| 6 | **Personal audio messages for children are solved better elsewhere today.** Creative Tonie records remotely, with household invitations for grandparents. | Not a reason to drop `Send to AQENO` (ADR 0015 § 6). It is a reason to know the benchmark: whatever we build should be at least as easy for the sender. |

## Conflicts found with the current documentation

Recorded per ADR 0015. Nothing here is a scheduled change; items marked **act** are worth resolving
when the surrounding work happens.

| # | Conflict | Status |
|---|---|---|
| C1 | `PRODUCT_FOUNDATION.md` § 1 opened by defining AQENO against the Toniebox, and § 13 was titled "Capabilities beyond a Toniebox" with the claim that AQENO "differentiates through architecture". | **Resolved 2026-08-18** — both reframed; § 0 now carries the motivation. |
| C2 | This review's original recommendation was to narrow AQENO to its two differentiating advantages and to defer the Device UI, on the grounds that a 7-inch display is not justified by comparison. | **Superseded** by ADR 0015 § 4. Display, encoder, keys and NFC are evaluated by real use, not by comparison. |
| C3 | `ROADMAP.md` P1 gates the MVP freeze on prototype testing with "representative users", and P3 says "freeze only after P1/P2 evidence". | **Act.** Under ADR 0015 the current evidence source is real use of the reference prototype by its actual user. Broader user testing belongs to the design horizon and to productisation. |
| C4 | `PRODUCT_FOUNDATION.md` § 12 defines Reference / Compatible / Community hardware levels, implying a support programme. | **Act, low priority.** Mark as design horizon rather than current commitment; it is productisation work (ADR 0015 § 6). |
| C5 | `P15 Show capability, never absence` made the only monetisable service undiscoverable — nobody could learn that `Send to AQENO` exists. | **Dissolved** by ADR 0015 § 6: the feature is no longer defined by monetisation, so there is no paid tier to hide. P15 stands unchanged. |
| C6 | `docs/DOCUMENTATION_GAPS.md` G19 asks to consolidate Ambient/photo-frame because it is "over-documented relative to its scope". | **Keep as is.** Consolidation for readability remains fine; deletion for lack of differentiation does not (ADR 0015 § 2). |
| C7 | ADR 0004 keeps a proprietary-commercial path open at a stated product cost, and ADR 0012 excludes Qt Virtual Keyboard partly on licensing grounds. | **Watch.** Both are currently on hold or independently justified, so nothing degrades today. If a licence constraint ever costs the reference device quality, ADR 0015 § 6 decides against the constraint. |
| C8 | `AGENTS.md` § "Productive work only" was the only guard against scope growth, and it argued from milestones rather than value. | **Resolved 2026-08-18** — § "Deciding what to build" adds the value test and the decision order. |
