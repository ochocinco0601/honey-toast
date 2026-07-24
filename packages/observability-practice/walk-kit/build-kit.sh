#!/usr/bin/env bash
# Regenerate the Walk-Before-Run Kit from the source docs in ../observability-bok/.
# Every page except the front door is copied from the source docs at build time.
# Usage: ./build-kit.sh [SOURCE_DIR] [OUTPUT_DIR]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:-$HERE/../observability-bok}"
OUT="${2:-$HERE/build}"

ROOT_PAGES=(the-methodology how-to-walk-a-question)
INSTR_PAGES=(in-24-first-process-run-plan in-19-discovery-dialogue-protocol \
  in-04-service-profile-template in-05-signal-definition-template \
  in-06-stakeholder-expectation-template worked-example-ledger-writer)

rm -rf "$OUT"
mkdir -p "$OUT/docs/instruments"
for p in "${ROOT_PAGES[@]}";  do cp "$SRC/$p.md"             "$OUT/docs/"; done
for p in "${INSTR_PAGES[@]}"; do cp "$SRC/instruments/$p.md" "$OUT/docs/instruments/"; done

# Authored front door -> the kit home page
cp "$HERE/front-door.md" "$OUT/docs/README.md"
# Strip every link pointing outside the nine pages, and fill the render date.
# All page-text rewriting happens in neutralize.py, in UTF-8; this script only moves files.
python "$HERE/neutralize.py" "$OUT/docs"
# Build
cp "$HERE/kit-mkdocs.yml" "$OUT/mkdocs.yml"
python -m mkdocs build -f "$OUT/mkdocs.yml" -d "$OUT/site"

echo "Built the Walk-Before-Run Kit to: $OUT/site"
