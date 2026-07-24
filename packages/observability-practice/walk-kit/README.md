# Walk-Before-Run Kit — a focused rendering of the practice

A nine-page, self-contained rendering of the observability practice for a team's
**first process**. It is assembled at build time from the source docs in
`../observability-bok/` — edit the source, then regenerate.

## What it contains

- **Front door** — `front-door.md` (the only page authored here)
- **Run kit** — IN-24 (First-Process Run Plan), IN-19 (Discovery Dialogue), IN-04 / IN-05 /
  IN-06 (the capture templates), and the ledger-writer worked example
- **Frame** — the methodology and how-to-walk-a-question

The knowledge areas and the other instruments are deliberately left out: the kit is the
first walk, not the whole reference.

## Build notes

- **Assembled, not edited here.** Every page except the front door is copied from the
  source docs at build time — edit the source, then regenerate.
- **Outside links neutralized.** `neutralize.py` strips every link that points outside the
  nine pages down to plain text, so nothing dead-ends; a line at the foot of the front door
  notes the full body of knowledge is available separately.
- **Dated at render.** The front door carries a `[RENDER DATE]` marker; the build fills it
  with the build date. The kit is a dated snapshot, not the living source.
- **Page text is only ever rewritten in Python, in UTF-8.** `build-kit.sh` copies and builds;
  it never edits page characters. The pages are full of em dashes and arrows, and keeping the
  shell out of the text means no shell's default codepage can mangle them.

## Regenerate

    ./build-kit.sh [SOURCE_DIR] [OUTPUT_DIR]

Requires `mkdocs` and `mkdocs-material`. Defaults: `SOURCE_DIR=../observability-bok`,
`OUTPUT_DIR=./build`. The built site lands in `OUTPUT_DIR/site/` — open `index.html` or
serve the directory.

## Files

| File | What it is |
|---|---|
| `front-door.md` | The authored front door (becomes the kit's home page) |
| `kit-mkdocs.yml` | The focused nav and theme |
| `neutralize.py` | Strips outside-kit links to plain text, and fills the render date |
| `build-kit.sh` | Assembles the nine pages, neutralizes, and builds |
