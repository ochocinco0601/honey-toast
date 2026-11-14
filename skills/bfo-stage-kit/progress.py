"""Mapping's progress, in plain lines for the person, read from the register as each part of the map is written.

Usage: python progress.py <register folder>    print the lines not yet announced (and record them as announced)

While a flow is mapped (after the go, before its mapping is done), each part of the map the walk writes for the flow
worked now gives one line, once: "Mapping Placing an order, 3 of 7: its stages are written: Pay, Ship and Confirm."
The page's wait (page/page_ask.py watch or poll) prints each as a PROGRESS line, which wakes the session, and the
session sends it to the person as it is; the work page and the home screen show the latest, so the person never waits
through mapping on one line while the map's tables are written one by one. Announced lines are kept in progress.json in the register folder. Python standard library only.
"""
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FILE = "progress.json"


def rows(reg, name):
    p = pathlib.Path(reg) / f"{name}.csv"
    if not p.is_file():
        return []
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, csv.Error, UnicodeDecodeError):  # a table mid-write: read again next time
        return []


def v(r, k):
    return (r.get(k) or "").strip()


def and_list(names):
    names = [n for n in names if n]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1] if names else ""


def mapping_now(reg):
    """(the flow's name, its id in flows.csv or None) while a flow is being mapped, else None."""
    import brief
    import go
    scope = go.load(reg)
    if not scope or not scope.get("flow"):
        return None
    ph = dict(brief.phases(reg))
    if ph.get(brief.CAPABILITY) in ("done", "not picked"):
        return None
    name = scope["flow"]
    fid = next((v(r, "flow_id") for r in rows(reg, "flows") if v(r, "name").lower() == name.strip().lower()), None)
    return name, fid or (scope.get("flow_id") or None)


def parts(reg, fid):
    """[(key, what is written)] for the parts of the map written so far for flow `fid`, in the walk's order."""
    if not fid:
        return []
    flow = next((r for r in rows(reg, "flows") if v(r, "flow_id") == fid), None)
    moves = [r for r in rows(reg, "lifecycle") if v(r, "flow") == fid]
    stages = sorted((r for r in rows(reg, "stages") if v(r, "flow") == fid),
                    key=lambda r: int(v(r, "order")) if v(r, "order").isdigit() else 0)
    st_ids = {v(r, "stage") for r in stages}
    steps = [r for r in rows(reg, "steps") if v(r, "stage") in st_ids]
    step_ids = {v(r, "step") for r in steps}
    carried = [r for r in rows(reg, "participation") if v(r, "step") in step_ids]
    impact = [r for r in rows(reg, "step-impact") if v(r, "step") in step_ids]
    out = []
    if flow and (v(flow, "starts_at") or v(flow, "ends_at")):
        out.append(("start-end", "where it starts and where it ends is written"))
    if moves:
        out.append(("path", f"the path the work takes is written, {len(moves)} moves"))
    if stages:
        out.append(("stages", f"its stages are written: {and_list([v(r, 'name') for r in stages])}"))
    if steps:
        out.append(("steps", f"its steps are written, {len(steps)} of them"))
    if carried:
        out.append(("carried", "the services, stores and people that carry each step are written"))
    if flow and v(flow, "delivers"):
        out.append(("capability", "what the flow does for the business is named"))
    if impact:
        out.append(("at-stake", "what is at stake at each step is written"))
    return out


TOTAL = 7  # the parts `parts` names, in order


def load(reg):
    p = pathlib.Path(reg) / FILE
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def new_lines(reg):
    """The lines for parts written since the last call, each said once, and recorded as said."""
    reg = pathlib.Path(reg)
    try:
        now = mapping_now(reg)
    except Exception:  # noqa: BLE001 - a run record mid-write: look again next time
        return []
    if not now:
        return []
    name, fid = now
    got = load(reg)
    said = set(got.get("announced", {}).get(fid or name, []))
    order = ["start-end", "path", "stages", "steps", "carried", "capability", "at-stake"]
    lines, keys = [], []
    for key, what in parts(reg, fid):
        if key not in said:
            lines.append(f"Mapping {name}, {order.index(key) + 1} of {TOTAL}: {what}.")
            keys.append(key)
    if lines:
        got.setdefault("announced", {}).setdefault(fid or name, []).extend(keys)
        got["latest"] = lines[-1]
        (reg / FILE).write_text(json.dumps(got, ensure_ascii=False) + "\n", encoding="utf-8")
    return lines


def latest(reg):
    """The last progress line said, while its flow is still being mapped; else ""."""
    try:
        return load(reg).get("latest", "") if mapping_now(pathlib.Path(reg)) else ""
    except Exception:  # noqa: BLE001
        return ""


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 1 or not pathlib.Path(argv[0]).is_dir():
        print(__doc__, file=sys.stderr)
        return 2
    import run_lock  # the command writes progress.json in the register; the page's wait calls new_lines in-process
    run_lock.guard(argv[0])
    for line in new_lines(argv[0]):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
