"""The BFO viewer: one page, opened from disk, showing every register it is given.

Usage: python viewer.py [FOLDER_OR_REGISTER ...] [--portfolio FILE] [--out PAGE]

A folder holding flows.csv is a register; any other folder is scanned one level down for registers. With no folder,
./bfo-work is read if it exists. The page (default <first folder>/viewer.html) has three screens: Portfolio, then an
application's Business flows along the 8 milestones, then a flow's Flow map. Viewing only. The portfolio file (optional,
CSV: application_id,application,division,line_of_business,sub_line,register[,mock]) places applications in the
organisation and lists applications with no run yet; without --portfolio, portfolio.csv in a folder given is read; without it, every register is listed with its levels "not recorded".
"""
import argparse
import csv
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import flow_model as fm  # noqa: E402

VERSION = 5
TEMPLATE = HERE / "viewer.template.html"
PORTFOLIO = "portfolio.csv"  # read from the folders given when --portfolio is not


def find_registers(folders):
    regs = []
    for f in folders:
        f = Path(f)
        if (f / "flows.csv").exists():
            regs.append(f)
        elif f.is_dir():
            regs += sorted(d for d in f.iterdir() if d.is_dir() and (d / "flows.csv").exists())
    seen, out = set(), []
    for r in regs:
        k = r.resolve()
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def read_portfolio(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]


def build(folders, portfolio=None):
    """VIEWER (the page's data) and the problems found, one line each."""
    fm.load_kit()
    problems, by_name = [], {}
    for reg in find_registers(folders):
        try:
            info, p = fm.register(reg)
            problems += p
            if reg.name in by_name:
                problems.append(f"{reg}: not shown: another register named '{reg.name}' was read first")
            else:
                by_name[reg.name] = info
        except Exception as e:  # noqa: BLE001  one bad register never stops the page
            problems.append(f"{reg.name}: not read: {type(e).__name__}: {e}")
    apps, used = [], set()
    for r in (read_portfolio(portfolio) if portfolio else []):
        reg = by_name.get(r.get("register", ""))
        if r.get("register") and not reg:
            problems.append(f"portfolio: {r.get('application')}: register '{r['register']}' not found; listed as not mapped")
        if reg:
            used.add(r["register"])
        apps.append({"id": r.get("application_id", ""), "name": r.get("application") or (reg or {}).get("name", ""),
                     "division": r.get("division", ""), "line": r.get("line_of_business", ""), "sub": r.get("sub_line", ""),
                     "register": r.get("register", "") if reg else "", "mock": r.get("mock", "").lower() in ("yes", "true", "1"),
                     "what": (reg or {}).get("what", ""), "flows": (reg or {}).get("flows", []),
                     "updated": (reg or {}).get("updated", "")})
    for name, reg in by_name.items():
        if name not in used:
            apps.append({"id": "", "name": reg["name"], "division": "", "line": "", "sub": "", "register": name,
                         "mock": False, "what": reg["what"], "flows": reg["flows"], "updated": reg["updated"]})
    return {"version": VERSION, "built": datetime.date.today().isoformat(), "apps": apps}, problems


def page(viewer, sources, cmd):
    disc = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n"
            f"     Source: {'; '.join(sources)}\n"
            "     Builder: the BFO viewer's viewer.py\n"
            f"     Build: {cmd}\n-->\n")
    data = json.dumps(viewer, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DISCOVERY__", disc, 1).replace("__VIEWER__", data, 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("folders", nargs="*")
    ap.add_argument("--portfolio")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    folders = a.folders or (["bfo-work"] if Path("bfo-work").is_dir() else [])
    if not folders:
        ap.error("no folder given and no ./bfo-work here")
    portfolio = a.portfolio or next((str(Path(f) / PORTFOLIO) for f in folders if (Path(f) / PORTFOLIO).is_file()), None)
    viewer, problems = build(folders, portfolio)
    out = Path(a.out) if a.out else Path(folders[0]) / "viewer.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = "python viewer.py " + " ".join(Path(f).as_posix() for f in folders) + \
          (f" --portfolio {Path(portfolio).as_posix()}" if portfolio else "") + f" --out {out.as_posix()}"
    out.write_text(page(viewer, [Path(f).as_posix() for f in folders], cmd), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    n = sum(1 for x in viewer["apps"] for f in x["flows"] if f["flowdraw"])
    print(f"{out.resolve()}  ({len(viewer['apps'])} applications, {n} flows drawn)")
    for p in problems:
        print("  " + p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
