"""Start a new register: copy register-template/ into a new, empty register folder, and never over earlier work.

Usage: python start_register.py <register folder>

Copies every CSV file in register-template/, and RUN.md unless the folder already has one. REGISTER.md is not
copied. If the folder already holds any CSV file, it is a register from an earlier run: nothing is copied, and the
script exits non-zero with a message saying so."""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "register-template"


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0])
    held = sorted(p.name for p in reg.glob("*.csv")) if reg.is_dir() else []
    if held:
        print(f"refused: {reg} already holds a register ({', '.join(held)}). Nothing was copied, so the earlier "
              "work is untouched. Start the new register in a new, empty folder.", file=sys.stderr)
        return 2
    reg.mkdir(parents=True, exist_ok=True)
    for f in sorted(TEMPLATE.glob("*.csv")):
        shutil.copy2(f, reg / f.name)
    if not (reg / "RUN.md").exists():
        shutil.copy2(TEMPLATE / "RUN.md", reg / "RUN.md")
    print(f"register started: {reg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
