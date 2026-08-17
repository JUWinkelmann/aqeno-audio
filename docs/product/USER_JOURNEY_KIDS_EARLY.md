# User Journey — Kids Early

## Persona
A roughly three-year-old child who cannot be expected to read. A Manager performs initial setup.

## Journey

### 1. Unboxing and setup — REMOTE / TOUCH
Manager powers AQENO, joins Wi-Fi if desired, creates a Kids Early profile and adds initial content. The child does not participate in technical setup.

### 2. First encounter — TOUCH / PHYSICAL
AQENO presents a calm screen with a very small number of large image tiles. No reading is required. The rotary control changes volume; press toggles play/pause.

### 3. Independent playback — TOUCH
Child taps an image. Audio starts immediately. No confirmation dialog.

### 4. Screen disappears — AUTOMATIC
After a short period without visual interaction, the display turns fully off while audio continues. Routine playback events never wake it.

### 5. Eyes-free control — PHYSICAL
With the screen off, volume, play/pause and next/previous remain available and predictable.

### 6. Physical object — NFC
An approved tag/object starts its assigned content or Action immediately. A failed/unassigned tag does not expose technical errors.

### 7. Bedtime — AUTOMATIC / PHYSICAL
Night policy forces all visual output off. Audio continues. Physical controls remain usable without causing display wake or bright LEDs.

### 8. Help needed
If content cannot play, AQENO uses a calm, recoverable state. It does not expose URLs, HTTP codes, Linux errors or configuration UI to the child.

## UX constraints
- no reading requirement;
- no modal dead ends;
- no ads, notifications, streaks or infinite feeds;
- no settings entry through accidental child interaction;
- screen is not required for routine listening;
- visual feedback from button LEDs follows profile/display policy and can reach true off.
