# Use Observations

**Status:** Open log — the project's primary source of product evidence
**Established:** 2026-08-18 by ADR 0015 § 9

The reference prototype is a learning instrument. What is observed here **may overturn existing
product assumptions**, including those in `PRODUCT_FOUNDATION.md`, in the accepted ADRs and in
`COMPETITIVE_REVIEW.md`. That is the point of it: until now every product assumption in this project
is reasoning, not evidence.

## How to use this file

One entry per observation, newest first. Record what happened, not what it means — an interpretation
belongs in a separate line so it can be wrong without corrupting the observation.

```markdown
### YYYY-MM-DD — short description

**Situation:** what was happening, who was using it, what state the device was in.
**Observed:** what actually happened. No interpretation.
**Reading:** what this might mean. Explicitly a guess.
**Affects:** which document or assumption this touches, if any.
```

An observation that contradicts a document is not a defect in the observation. Note it, and change the
document only when the pattern repeats or the case is unambiguous.

## Questions worth answering through use

Not a checklist to work through — a list of things worth noticing when they happen.

**Interaction paths**
- Which paths are actually used, and which are ignored?
- Is NFC understood without explanation?
- Are Next and Previous understood, and do they mean what the content kind assumes?
- How often is play/pause actually needed?
- How is volume operated — encoder, or something else?
- Which buttons are pressed intuitively, and which are never touched?

**Display**
- Is the display used for browsing, or only for confirmation?
- How do large covers work for recognition by a child who cannot read?
- Is browsing pleasant, or a chore?
- Does the display distract during listening?
- When *should* it disappear — is the configured timeout right?
- Which functions genuinely benefit from it?

**Everyday behaviour**
- Do the LEDs or the display disturb anything, particularly at bedtime?
- Does boot behaviour feel appropriate, or is waiting noticeable?
- Does anything reveal that a computer is involved?
- What is never used at all?
- What unexpected problems appear?
- Which wishes only emerge during use?

## Observations

*None yet — the device has no interface as of 2026-08-18. The first entry belongs here on the first
day a person other than the maintainer operates it.*
