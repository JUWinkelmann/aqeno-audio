# Organising media for AQENO

Copy your audio onto AQENO with an ordinary file manager. **You do not have to reorganise your
collection first** — a messy library still plays. The conventions below simply let AQENO present it
well without you editing a single MP3.

AQENO's rule for itself is: *accept messy, infer obvious, never guess.* Where it cannot tell, it
shows something plain and honest rather than something confident and wrong. You can always correct
it, and your correction is permanent.

## What AQENO understands

**A folder is one item.** All audio files in one folder are a single thing to play — one title, one
cover, one place you left off. A twenty-file audiobook is one audiobook, not twenty tracks.

```
Benjamin Blümchen/
    Folge 12/
        01.mp3
        02.mp3
        03.mp3
        cover.jpg
```

`Folge 12` is one item with three parts and one cover. `Benjamin Blümchen` holds only folders, so it
is a shelf and not an item itself.

**Numbered parts play in order.** `01`, `02`, `10` play in that order — never `1, 10, 2`. Track
numbers in the file's tags are used first if they are there.

**A single loose file is its own item.** `Gute-Nacht-Geschichte.mp3` becomes *Gute-Nacht-Geschichte*.
No tags needed.

**Tags are used when they are useful.** A real album and title from the file's tags win over the
folder name. But a tag that only says `Audio CD`, `Unknown Artist` or `Track 01` is treated as if it
were empty — the folder name is better information, so AQENO uses that instead.

**Covers**, in this order:

1. artwork embedded in the audio file;
2. an image named like the audio file — `Folge 12.mp3` and `Folge 12.jpg`;
3. `cover.jpg` or `folder.jpg` in the folder;
4. if the folder holds exactly one image, that one;
5. otherwise AQENO's own cover. `.jpg`, `.jpeg`, `.png` and `.webp` all work.

If a folder holds several images and none is named `cover.jpg`, AQENO uses its own rather than
guessing between them.

**Playlists.** An `.m3u` or `.m3u8` file in the folder sets the play order, and that beats filenames.

**A note beside the media.** For anything AQENO gets wrong, put an `aqeno.toml` in the folder:

```toml
title = "Der Puppenmacher"
kind = "audio_drama"
language = "de"
```

This always wins over anything AQENO works out for itself.

## Not required

- Correct or complete ID3 tags.
- A cover for every item.
- A particular folder structure, naming scheme or depth.
- Renaming anything, or tidying up first.

## What AQENO will not try to work out

It reads only what is unmistakable, so it will not surprise you later:

- It does not decide that a folder name is a **series**. `Import/` is not a series, and AQENO cannot
  tell that from `Benjamin Blümchen/` — so it claims neither.
- It does not read episode numbers out of filenames.
- It does not join `CD1/` and `CD2/` into one item. Two folders are two items.
- It does not look anything up on the internet.
- It never changes your files: no retagging, no renaming, no moving, no rewriting playlists.

## When AQENO cannot tell

```
Import/
    audio1.mp3
    audio2.mp3
    holiday.jpg
    scan.jpg
```

This plays. It gets a plain title, AQENO's own cover — not `holiday.jpg` — and appears in Admin as
*may need your attention*. Nothing is claimed about it, and nothing stops you using it.

Admin reports this the useful way round: *"200 items found, 196 ready, 4 may need your attention."*
Imperfect presentation never blocks an import.

## Correcting something

In Admin you can set the title, the kind, the language and the cover. From then on that value is
yours: later imports leave it alone, and so does repairing the underlying tags. If you want AQENO to
work it out again, clear the correction.

Corrections survive everything else too — adding media, renaming the folder, moving it to another
disk, retagging the files. Where you left off in a story, and any NFC tag you assigned to it, survive
the same way.
