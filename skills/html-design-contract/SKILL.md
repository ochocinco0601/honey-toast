---
name: html-design-contract
description: Build rules for any self-contained HTML page an assistant writes (report, dashboard, brief, one-off tool). Covers page skeleton, theming for light and dark, responsive layout, fonts, charts, accessibility and a pre-delivery checklist. Load with frontend-design whenever an HTML file is produced; use it for page mechanics, and frontend-design for visual direction.
---

# HTML design contract

Page mechanics for a single `.html` file that opens straight from disk or a shared drive. `frontend-design` decides how the page looks; this decides that it works.

Precedence: the user's words, then the project's existing design system (the project's instruction files, a tokens or theme file, existing stylesheets), then this file, then your own taste. If a design system exists, use it and ignore the palette and type advice below.

## 1. Skeleton

- Complete document: `<!doctype html>`, `<html lang="en">`, charset and viewport metas, a `<title>`.
- Title is a short name (two to four words) for this specific page, not a category and not a summary with a colon.
- One file. Inline all CSS and JS. Images as `data:` URIs.
- No external requests: no CDN scripts, no Google Fonts, no remote images. The page must render identically offline and behind a firewall. If a library is truly needed, paste its minified source inline and say so in a comment with name and version.
- Fonts: use a system stack. Pick by role, for example `ui-sans-serif, system-ui, "Segoe UI", sans-serif` for body, `ui-serif, Georgia, serif` where a serif is the deliberate choice, `ui-monospace, Consolas, monospace` for identifiers only.
- Do not use `alert`, `confirm` or `prompt`. Build confirmations into the page.
- Do not rely on `window.print()` or downloads for core function.

## 2. Tokens first

Open `<style>` with a `:root` block holding every colour, font and spacing value as a variable. Then derive everything from it.

- Colour: 4 to 6 named tokens, plus separate status colours (good, warning, critical) that are not the accent.
- Type: a body role, a heading role, and a mono role only if needed. One type scale, kept to.
- Neutrals lean slightly toward the accent hue. Pure mid-grey looks unchosen.
- No component rule uses a literal colour. Components use tokens.

## 3. Light and dark

Define the complete light palette on bare `:root`. Then:

```css
:root { color-scheme: light; --bg:…; --fg:…; --accent:…; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { color-scheme: dark; --bg:…; --fg:…; --accent:…; }
}
:root[data-theme="dark"] { color-scheme: dark; --bg:…; --fg:…; --accent:…; }
body { background: var(--bg); color: var(--fg); }
```

- Every token has its first definition on bare `:root`; the dark blocks only redefine.
- `body` always sets an explicit background from a token.
- Do not simply invert. Re-check contrast and make the accent work on both backgrounds.
- A page may commit to one theme on purpose; then set background and all colours explicitly and say so in a comment.

## 4. Layout

- Reading text: max about 65 characters wide (about 68rem total column for pages with tables or figures).
- Side gutter at least 16px at every width. Body never scrolls sideways.
- Spacing between siblings with flex or grid `gap`, not margins.
- Rows wrap or stack to one column near 400px. Children that hold text, code or tables get `min-width: 0`.
- Tables, code and diagrams may exceed the column, each inside its own `overflow-x: auto` wrapper.
- Smallest text 12px. Digits in columns use `font-variant-numeric: tabular-nums`.
- Repeated items (cards, rows, badges) share edges, padding and baselines. Content sets height.
- Border, fill, radius and shadow mark a separate object. Use them by role, not on every block.
- Numbering, eyebrows and dividers only when they carry true information (a real sequence, a real category).

## 5. Complete at rest

- Everything meant to be read is visible when the page loads. Never leave content at `opacity: 0` waiting for a scroll trigger.
- A tool or dashboard opens with realistic example data, labelled as examples.
- Summary before detail. State shown by form (pill, stripe, chip) as well as by number.
- Anything interactive looks interactive and has a visible keyboard focus state. Respect `prefers-reduced-motion`.
- Wrap `localStorage` reads and writes in try/catch; the page must work without them.

## 6. Charts and diagrams

- One scale places marks, ticks and labels. Every label names a value the chart reaches.
- Chart text takes colour from tokens so it reads in both themes.
- In SVG: leave room in the `viewBox` for outer labels, give every shape an explicit fill, keep labels clear of marks.
- Show a selection by fading the rest, not by recolouring.

## 7. Copy

- Name things as the reader knows them, not how the system is built.
- Active voice. A control says what it does. Errors say what went wrong and how to fix it.
- Real content, never lorem ipsum.

## 8. Before delivering

Open the file in a browser and check, once:

1. Width 1440 and width 400: no sideways scroll, nothing clipped or overlapping.
2. Light and dark (switch the OS setting or set `data-theme`): text readable on both.
3. Tab through controls: focus is visible.
4. Browser console: no errors, no blocked requests.
5. Nothing important is hidden until scroll or hover.

Fix what the check shows in one pass, then deliver.
