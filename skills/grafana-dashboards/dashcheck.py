"""Check a Grafana dashboard change. Standard library only. Reads classic JSON and the v2 schema.

  python dashcheck.py check BEFORE.json AFTER.json --allow-file allow.txt   every change declared, every declared change made
  python dashcheck.py check AFTER.json                                      a new dashboard: structural checks only
  python dashcheck.py held CHANGES_DIR LIVE.json                            do all earlier changes still hold?
  python dashcheck.py values BEFORE_V.json AFTER_V.json --changed KEY ...   panel numbers: only expected panels may move
  python dashcheck.py paths FILE.json [TEXT]                                 list paths (containing TEXT) to write the declaration

Paths are the ones `check` prints. In allow.txt, one path per line, * matches anything, # starts a comment.
A path prefixed with ? may stay unchanged; any other declared path that did not change is a failure.
Values files: {"range": {"from": "<absolute>", "to": "<absolute>"},
               "panels": {"<panel key>": {"title": ..., "series": n, "points": n, "last": x, ... , "error": null}}}
Exit 0 = PASS, 1 = FAIL.
"""
import argparse
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

VAR_RE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)|\[\[([A-Za-z_][A-Za-z0-9_]*)")
BUILTIN_VARS = {"interval", "interval_ms", "timeFilter", "timeFilterRange", "range", "range_s", "range_ms"}
QUERY_PATH_RE = re.compile(r"targets|queries|query|expr|datasource|templating|variables")
ORDERED_RE = re.compile(r"(templating\.list|variables|rows|tabs|queries|targets)$")
ITEM_RE = re.compile(r"^(.*\[[A-Za-z]+=[^\]]*\])")
LABEL_PATH_RE = re.compile(r"(alias|legendFormat|displayName)$")
SPECIAL_DS = {"-- Mixed --", "-- Dashboard --", "-- Grafana --", "grafana", "dashboard", "mixed"}


# ---------- loading ----------

def load(path):
    """Return (dashboard body, format, meta). format is 'v1' or 'v2'."""
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    meta = {}
    if isinstance(data.get("dashboard"), dict):
        meta = data.get("meta") or {}
        data = data["dashboard"]
    if isinstance(data.get("spec"), dict) and "apiVersion" in data:
        meta = {"name": (data.get("metadata") or {}).get("name"), **((data.get("metadata") or {}).get("annotations") or {})}
        data = data["spec"]
    fmt = "v2" if ("elements" in data or "layout" in data) else "v1"
    return data, fmt, meta


# ---------- normalising: give list items stable names so reordering is not a change ----------

def ident(x):
    if not isinstance(x, dict):
        return None
    for k in ("id", "name", "refId"):
        if isinstance(x.get(k), (str, int)) and not isinstance(x.get(k), bool):
            return f"{k}={x[k]}"
    s = x.get("spec")
    if isinstance(s, dict):
        el = s.get("element")
        if isinstance(el, dict) and el.get("name"):
            return f"el={el['name']}"
        for k in ("name", "refId", "title"):
            if isinstance(s.get(k), (str, int)):
                return f"{k}={s[k]}"
    return None


def v1_panels(dash):
    for p in dash.get("panels") or []:
        yield p, None
        for child in p.get("panels") or []:
            yield child, p.get("id")


def normalize(dash, fmt):
    if fmt == "v1":
        out = {k: v for k, v in dash.items() if k not in ("id", "version", "iteration", "panels")}
        panels = []
        for p, row in v1_panels(dash):
            q = {k: v for k, v in p.items() if k != "panels"}
            if row is not None:
                q["_inRow"] = row
            panels.append(q)
        out["panels"] = panels
        return out
    out = json.loads(json.dumps(dash))
    for _, v in walk(out.get("layout") or {}):
        if isinstance(v, dict) and v.get("kind") == "AutoGridLayout":
            for i, it in enumerate((v.get("spec") or {}).get("items") or []):
                if isinstance(it.get("spec"), dict):
                    it["spec"]["(position)"] = i
    return out


def flatten(obj, prefix="", out=None):
    out = {} if out is None else out
    if isinstance(obj, dict) and obj:
        for k, v in obj.items():
            flatten(v, f"{prefix}.{k}" if prefix else str(k), out)
    elif isinstance(obj, list) and obj:
        keys = [ident(v) for v in obj]
        keyed = all(keys) and len(set(keys)) == len(keys)
        if keyed and ORDERED_RE.search(prefix):
            out[f"{prefix}.(order)"] = ", ".join(keys)
        for i, v in enumerate(obj):
            flatten(v, f"{prefix}[{keys[i] if keyed else i}]", out)
    elif not isinstance(obj, (dict, list)):
        out[prefix] = obj
    return out


def walk(obj, prefix=""):
    """Yield (path, value) for every node."""
    yield prefix, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{prefix}[{i}]")


# ---------- structural problems ----------

def panel_items(dash, fmt):
    """Yield (key, title, body) per panel. key is the v1 id or the v2 element name."""
    if fmt == "v1":
        for p, _ in v1_panels(dash):
            if p.get("type") != "row":
                yield str(p.get("id")), p.get("title", ""), p
    else:
        for name, el in (dash.get("elements") or {}).items():
            yield name, ((el or {}).get("spec") or {}).get("title", ""), el


def variables(dash, fmt):
    """Return {name: (is_datasource_variable, body)}."""
    out = {}
    if fmt == "v1":
        for v in (dash.get("templating") or {}).get("list") or []:
            out[v.get("name")] = (v.get("type") == "datasource", v)
    else:
        lists = [dash.get("variables") or []]
        lists += [v["variables"] for _, v in walk(dash.get("layout") or {})
                  if isinstance(v, dict) and isinstance(v.get("variables"), list)]
        for lst in lists:
            for v in lst:
                spec = v.get("spec") or {}
                out[spec.get("name")] = (v.get("kind") == "DatasourceVariable", v)
    return out


def problems(dash, fmt, meta):
    found = set()
    if meta.get("provisioned") or meta.get("grafana.app/managedBy"):
        found.add(("warn", "dashboard is provisioned or managed from another source: an API save can be overwritten"))

    if fmt == "v1":
        seen = {}
        for p, _ in v1_panels(dash):
            if "id" in p:
                seen[p["id"]] = seen.get(p["id"], 0) + 1
        for pid, n in seen.items():
            if n > 1:
                found.add(("error", f"panel id {pid} is used {n} times"))
    else:
        refs = {v.get("name") for _, v in walk(dash.get("layout") or {}) if isinstance(v, dict) and v.get("kind") == "ElementReference"}
        elements = set((dash.get("elements") or {}).keys())
        for missing in sorted(refs - elements):
            found.add(("error", f"layout places '{missing}' but no element of that name exists"))
        for unplaced in sorted(elements - refs):
            found.add(("error", f"element '{unplaced}' is not placed in the layout, so it does not show"))

    vars_ = variables(dash, fmt)
    has_ds_var = any(is_ds for is_ds, _ in vars_.values())
    scan = list(panel_items(dash, fmt))
    for key, title, body in scan + [(f"variable {n}", n, b) for n, (_, b) in vars_.items()]:
        for path, s in walk(body):
            if not isinstance(s, str):
                continue
            for m in VAR_RE.finditer(s):
                name = m.group(1) or m.group(2)
                if name.startswith("__") or name in BUILTIN_VARS or name in vars_:
                    continue
                level = "error" if QUERY_PATH_RE.search(path) and not LABEL_PATH_RE.search(path) else "warn"
                found.add((level, f"{key}: ${name} is used but no dashboard variable defines it"))

    for key, title, body in scan:
        if (fmt == "v1" and "libraryPanel" in body) or (fmt == "v2" and body.get("kind") == "LibraryPanel"):
            found.add(("warn", f"panel {key} is a library panel: the dashboard holds only a reference; its definition is shared by every dashboard that uses it"))
        if not has_ds_var:
            continue
        for path, v in walk(body):
            if path.endswith("datasource") and isinstance(v, dict):
                ref = v.get("uid") or v.get("name")
                if isinstance(ref, str) and ref and not ref.startswith("$") and ref not in SPECIAL_DS:
                    found.add(("warn", f"panel {key} names datasource '{ref}' directly although the dashboard has a datasource variable"))

    boxes_sets = []
    if fmt == "v1":
        boxes_sets.append([(p.get("id"), p["gridPos"]) for p in dash.get("panels") or [] if isinstance(p.get("gridPos"), dict)])
    else:
        for _, v in walk(dash.get("layout") or {}):
            if isinstance(v, dict) and v.get("kind") == "GridLayout":
                items = []
                for it in (v.get("spec") or {}).get("items") or []:
                    s = it.get("spec") or {}
                    items.append(((s.get("element") or {}).get("name"), {"x": s.get("x"), "y": s.get("y"), "w": s.get("width"), "h": s.get("height")}))
                boxes_sets.append(items)
    for boxes in boxes_sets:
        for i, (a_id, a) in enumerate(boxes):
            for b_id, b in boxes[i + 1:]:
                try:
                    if a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]:
                        found.add(("warn", f"panels {a_id} and {b_id} overlap on the grid"))
                except (KeyError, TypeError):
                    pass
    return found


def users_of_variables(dash, fmt, names):
    users = {}
    for key, title, body in panel_items(dash, fmt):
        for _, s in walk(body):
            if isinstance(s, str):
                for m in VAR_RE.finditer(s):
                    if (m.group(1) or m.group(2)) in names:
                        users[key] = title
    return users


# ---------- modes ----------

def read_allow(args):
    patterns = list(args.allow or [])
    if args.allow_file:
        with open(args.allow_file, encoding="utf-8-sig") as f:
            patterns += [ln.split("#", 1)[0].strip() for ln in f]
    return [p for p in patterns if p]


def compile_pattern(p):
    return re.compile(re.escape(p.lstrip("?")).replace(r"\*", ".*"))


def show(v):
    return json.dumps(v, ensure_ascii=False)[:200]


def order_unchanged(path, old, new):
    """An added or removed item is not a reorder: compare the order of the items present in both."""
    if not path.endswith(".(order)") or path not in old or path not in new:
        return False
    a, b = old[path].split(", "), new[path].split(", ")
    common = set(a) & set(b)
    return [x for x in a if x in common] == [x for x in b if x in common]


def paths_mode(argv):
    ap = argparse.ArgumentParser(prog="dashcheck.py paths")
    ap.add_argument("file")
    ap.add_argument("contains", nargs="?", default="", help="show only paths containing this text")
    args = ap.parse_args(argv)
    dash, fmt, _ = load(args.file)
    for k, v in flatten(normalize(dash, fmt)).items():
        if args.contains in k:
            print(f"{k} = {show(v)}")
    return 0


def check_mode(argv):
    ap = argparse.ArgumentParser(prog="dashcheck.py check")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--allow", action="append")
    ap.add_argument("--allow-file")
    args = ap.parse_args(argv)
    if len(args.files) > 2:
        ap.error("give AFTER, or BEFORE and AFTER")

    after, fmt_a, meta_a = load(args.files[-1])
    after_problems = problems(after, fmt_a, meta_a)
    before_problems, unexpected, not_made = set(), [], []

    if len(args.files) == 2:
        before, fmt_b, meta_b = load(args.files[0])
        if fmt_b != fmt_a:
            print(f"BEFORE is {fmt_b} and AFTER is {fmt_a}: the format changed, so a path-by-path comparison is meaningless.")
            print("Save the format migration as its own change first, then make this change against the migrated version.\n\nRESULT: FAIL")
            return 1
        before_problems = problems(before, fmt_b, meta_b)
        patterns = read_allow(args)
        compiled = [(p, compile_pattern(p)) for p in patterns]
        old, new = flatten(normalize(before, fmt_b)), flatten(normalize(after, fmt_a))
        changes = [(k, old.get(k, "<absent>"), new.get(k, "<absent>")) for k in sorted(set(old) | set(new))
                   if old.get(k, "<absent>") != new.get(k, "<absent>") and not order_unchanged(k, old, new)]
        hit, shown = set(), set()
        print(f"FORMAT {fmt_a}   CHANGES ({len(changes)})")
        for path, o, n in changes:
            matched = [p for p, rx in compiled if rx.fullmatch(path)]
            hit.update(matched)
            if not matched:
                unexpected.append(path)
            mark = "ok" if matched else "!!"
            item = ITEM_RE.match(path)
            whole = None
            if item and (o == "<absent>" or n == "<absent>"):
                side = old if o == "<absent>" else new
                if not any(k.startswith(item.group(1)) for k in side):
                    whole = ("added" if o == "<absent>" else "removed", item.group(1))
            if whole:
                if (mark, whole) not in shown:
                    shown.add((mark, whole))
                    print(f"  {mark} {whole[0]}: {whole[1]}")
                continue
            print(f"  {mark} {path}\n       before: {show(o)}\n       after:  {show(n)}")
        not_made = [p for p in patterns if p not in hit and not p.startswith("?")]
        for p in not_made:
            print(f"  !! declared but did not change: {p}")

        changed_vars = set()
        for path, _, _ in changes:
            m = re.match(r"(?:templating\.list|variables)\[name=([^\]]+)\]", path)
            if m:
                changed_vars.add(m.group(1))
        if changed_vars:
            users = users_of_variables(after, fmt_a, changed_vars)
            if users:
                print(f"\nPANELS USING THE CHANGED VARIABLES ({', '.join(sorted(changed_vars))}): include them in the numbers check")
                for key, title in sorted(users.items()):
                    print(f"  {key} '{title}'")

    introduced = sorted(after_problems - before_problems)
    existing = sorted(after_problems & before_problems)
    if introduced:
        print("\nPROBLEMS THIS CHANGE INTRODUCES" if len(args.files) == 2 else "\nPROBLEMS")
        for level, msg in introduced:
            print(f"  {level}: {msg}")
    if existing:
        print("\nALREADY PRESENT BEFORE THE CHANGE (report, do not fix now)")
        for level, msg in existing:
            print(f"  {level}: {msg}")

    failed = unexpected or not_made or any(level == "error" for level, _ in introduced)
    print(f"\nRESULT: {'FAIL' if failed else 'PASS'}")
    if unexpected:
        print(f"  {len(unexpected)} change(s) not declared (marked !!)")
    if not_made:
        print(f"  {len(not_made)} declared change(s) not made")
    return 1 if failed else 0


def held_mode(argv):
    ap = argparse.ArgumentParser(prog="dashcheck.py held")
    ap.add_argument("changes_dir", help="folder of earlier changes; a pass counts once it was saved (has live.json)")
    ap.add_argument("live")
    args = ap.parse_args(argv)

    def order(name):
        m = re.match(r"(\d+)", name)
        return (int(m.group(1)) if m else 10**9, name)

    def patterns(path):
        if not os.path.isfile(path):
            return []
        with open(path, encoding="utf-8-sig") as f:
            return [compile_pattern(ln.split("#", 1)[0].strip()) for ln in f if ln.split("#", 1)[0].strip()]

    pins = {}
    for name in sorted(os.listdir(args.changes_dir), key=order):
        d = os.path.join(args.changes_dir, name)
        files = {f: os.path.join(d, f) for f in ("before.json", "after.json", "live.json", "allow.txt", "released.txt")}
        if not all(os.path.isfile(files[f]) for f in ("after.json", "live.json", "allow.txt")):
            continue
        pats = patterns(files["allow.txt"])
        for k in [k for k in pins if any(rx.fullmatch(k) for rx in pats)]:
            del pins[k]
        dash, fmt, _ = load(files["after.json"])
        after_flat = flatten(normalize(dash, fmt))
        for k, v in after_flat.items():
            if any(rx.fullmatch(k) for rx in pats):
                pins[k] = (v, name)
        if os.path.isfile(files["before.json"]):
            bdash, bfmt, _ = load(files["before.json"])
            for k in flatten(normalize(bdash, bfmt)):
                if k not in after_flat and any(rx.fullmatch(k) for rx in pats):
                    pins[k] = ("<absent>", name)
        for rx in patterns(files["released.txt"]):
            for k in [k for k in pins if rx.fullmatch(k)]:
                del pins[k]
    live, fmt, _ = load(args.live)
    now = flatten(normalize(live, fmt))
    undone = []
    for k, (v, src) in sorted(pins.items()):
        cur = now.get(k, "<absent>")
        if cur == v:
            continue
        if k.endswith(".(order)") and "<absent>" not in (cur, v) and order_unchanged(k, {k: v}, {k: cur}):
            continue
        undone.append((k, v, src, cur))
    for k, v, src, cur in undone:
        print(f"  !! {k}  (set by {src})\n       set to: {show(v)}\n       now:    {show(cur)}")
    print(f"\nRESULT: {'FAIL - an earlier change no longer holds' if undone else 'PASS - all earlier changes still hold'} ({len(pins)} paths checked)")
    if undone:
        print("  If the user says the later state is intended, list these paths in released.txt in that change's folder.")
    return 1 if undone else 0


def values_mode(argv):
    ap = argparse.ArgumentParser(prog="dashcheck.py values")
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--changed", action="extend", nargs="+", default=[], help="keys of panels expected to change")
    ap.add_argument("--tolerance", type=float, default=1e-6, help="relative difference treated as equal")
    args = ap.parse_args(argv)
    docs = []
    for p in (args.before, args.after):
        with open(p, encoding="utf-8-sig") as f:
            d = json.load(f)
        if not isinstance(d.get("range"), dict) or not d["range"].get("from") or not isinstance(d.get("panels"), dict):
            print(f"{p}: needs a 'range' with absolute 'from'/'to' and 'panels' as an object keyed by panel\n\nRESULT: FAIL")
            return 1
        docs.append(d)
    before, after = docs
    if before["range"] != after["range"]:
        print(f"time ranges differ: {before['range']} vs {after['range']}; not comparable\n\nRESULT: FAIL")
        return 1

    def same(a, b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(a - b) <= 1e-12 + args.tolerance * max(abs(a), abs(b))
        return a == b

    def bad(v):
        return v.get("error") or not v.get("series") or not v.get("points")

    failed, changed = False, set(args.changed)
    bp, apn = before["panels"], after["panels"]
    for key in sorted(set(bp) | set(apn), key=lambda s: (len(s), s)):
        b, a = bp.get(key), apn.get(key)
        title = (a or b or {}).get("title", "")
        if b is None or a is None:
            if key in changed and a is not None:
                if bad(a):
                    print(f"  !! panel {key} '{title}': new, but empty or failing: {a.get('error') or 'no data'}")
                    failed = True
                else:
                    print(f"  ?? panel {key} '{title}': new; show these numbers to the user: {show(a)}")
            elif key in changed:
                print(f"  ok panel {key} '{title}': removed as declared")
            else:
                print(f"  !! panel {key} '{title}': present only {'after' if b is None else 'before'} the change")
                failed = failed or key not in changed
            continue
        diffs = [k for k in sorted(set(a) | set(b)) if k != "title" and not same(a.get(k), b.get(k))]
        if key in changed:
            if bad(a) and not bad(b):
                print(f"  !! panel {key} '{title}': returned data before, now empty or failing: {a.get('error') or 'no data'}")
                failed = True
            elif bad(a):
                print(f"  !! panel {key} '{title}': still empty or failing after the change: {a.get('error') or 'no data'}")
                failed = True
            else:
                print(f"  ?? panel {key} '{title}': show the user these numbers and ask whether they are right")
                if not diffs:
                    print("       numbers unchanged: this change does not show in numbers; give the user the panel link to look at")
                for k in diffs:
                    print(f"       {k}: {b.get(k)} -> {a.get(k)}")
        elif diffs:
            print(f"  !! panel {key} '{title}': not expected to change, but its numbers did")
            for k in diffs:
                print(f"       {k}: {b.get(k)} -> {a.get(k)}")
            failed = True
        elif bad(b):
            print(f"  .. panel {key} '{title}': empty or failing before the change too")
    print(f"\nRESULT: {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


def main():
    modes = {"check": check_mode, "held": held_mode, "values": values_mode, "paths": paths_mode}
    if len(sys.argv) < 2 or sys.argv[1] not in modes:
        print(__doc__)
        return 2
    return modes[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
