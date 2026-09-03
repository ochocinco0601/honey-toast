# Exemplar — Pitstop arc42 documentation

Filled-in arc42 chapters covering one system end to end, used by Phase 1 to calibrate output
structure and detail level. Read 2-3 chapters plus `arc42/arc42.md` (the index).

## Source and licence

Copied from the Pitstop garage-management sample application:
https://github.com/EdwinVW/pitstop — `docs/arc42/` and `docs/ADRs/`. Apache License 2.0,
copyright Edwin van Wijk. Unmodified. The full licence text is in `LICENSE` beside this file,
as section 4 of that licence requires of anyone redistributing the work.

Pitstop is a public sample application for a fictitious garage. It is a demonstration system,
not a production one.

## What is here and what is not

| Included | Omitted |
|---|---|
| `arc42/` — 13 chapter files | `img/` — rendered PNG diagrams |
| `ADRs/` — the 10 decision records the chapters cite | `diagrams/` — PlantUML sources |

Chapters 3, 5, 6, 7 and 10 link out to rendered diagrams (`img/*.png`) and their PlantUML sources
(`diagrams/*.puml`). Neither directory was copied, so those links do not resolve here — the
surrounding prose and tables carry the calibration signal, and the pictures are at the upstream
repository if they are wanted.
ADR cross-links (`../ADRs/...`) resolve within this directory.
