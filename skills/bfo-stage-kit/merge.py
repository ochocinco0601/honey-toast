"""Write one map from the reading units' folders of a split run, with every call between units matched on both sides.

Usage: python merge.py <register folder>            writes the map
       python merge.py --check <register folder>    says whether the map on disk is the merge of the units now

Files read and written are those of split-run-formats.md.

What it writes. The register's root `subjects.csv` and `participation.csv`, `merge/unmatched-calls.csv` and
`merge/summary.json`. Nothing else at the root. Same folders in, same files out, byte for byte; run it again at any time.

The lead's own rows. The root tables as they stand before the first merge are the lead's rows (the case, persons, any
flow-level row that belongs to no unit). The first merge copies them, unchanged, to `merge/lead-rows/`; every later merge
reads the lead's rows from there and never from the root, which from then on holds only merge output. A row the lead
adds or changes after the first merge goes into `merge/lead-rows/`; one written into the root by hand is overwritten by
the next merge, and `--check` fails on it until then. Lead rows keep their ids. In them a cell `subject_id`, `from_id`,
`to_id` or `part_of` written `<unit>/<unit-local id>` is replaced by that part's map id.

Numbering. Elements of the units come after the lead's elements, in units.csv order and then file order, numbered from
one above the highest `S<n>` among the lead's rows; then one element per distinct `external:<name>` the calls name, in
name order (a minted element: level `external dependency`, purpose `proposed:`, the first citing call as source).
Relationships are numbered from one above the highest lead `R<n>`, one per row of each unit's `calls.csv` in units.csv
order and file order, each followed by the consumer relationships it first gives rise to. Every unit-local id is
replaced; `row_id` is dropped. The unit `flow` is the lead's and is not read from units/.

A relationship row. `from_id`, `to_id`; `band` application when both ends are application elements, else technology;
`part_kind` interaction; `step_hint` and `carries_case_id` from the call; `name` `<from> to <to>: <the call as the
caller wrote it>`; `operation` from the call's `within` (the calling part's own operation the call is made within) and
`sequence` from its `sequence`, each as the reader wrote it, so a call serving several steps keeps its `; `-joined
list. A unit folder whose calls.csv predates those two columns merges with them blank (blank `operation` means the
pages join the call to its step). A consumer relationship has no call row and leaves both blank.

Matching a call (the unit's `calls.csv` row).
- `to_part` set (a store, a broker, `external:<name>`): matched to that part; never listed unmatched. A unit-local id
  the unit's subjects.csv does not have fails `--check`.
- http with `to_unit`: matched to an http operation of that unit. Both sides are normalised: method upper case; scheme,
  host and port dropped; query and fragment dropped; trailing slash dropped; every path parameter (`{x}`, `:x`, `<x>`,
  `${x}`, `%s`, a segment with a quote or `+`, digits, a 24-hex or 36-character id) made one placeholder. An exact
  match wins; else the caller's path may end with the callee's, or the callee's with the caller's, whole segments only
  (so a base prefix on either side is allowed and `/customerorders` never matches `/orders`); the longest overlap wins.
  Two different operations equally good: ambiguous, listed unmatched, never guessed. An unmatched call is drawn to the
  named unit's first element.
- http with neither `to_unit` nor `to_part`: exact match only, against every unit.
- rpc with `to_unit`: the operation as served, compared after trimming, case ignored.
- message (a publish): matched to every `message` operation of the same queue or topic name in any unit (its
  consumers). Drawn as publisher -> broker (`via`, or `to_part` when `via` is blank), and once per consumer and broker,
  consumer -> broker with name `... : <queue> consumer`, its step_hint the steps the consumer's participation rows give
  that part. No consumer: listed unmatched; the publisher -> broker relationship is still drawn.
- Unmatched calls go to `merge/unmatched-calls.csv` with `why`, and are still in the map once.
- Out of scope: a call whose `to_unit` is no unit but a service the person left out at the go (`services_out` in
  `scope.json`, written by go.py; case ignored) is never unmatched. It goes to `merge/out-of-scope-calls.csv` (the
  same columns) and is drawn to one element per such service, minted after the `external:` ones: band application,
  level `external dependency`, purpose `out of scope: ...`. With no scope.json, nothing is out of scope.

Found by the reader. A relationship is fact only when a code-reader fact in `<reg>/fact-base.json` (not `in_test`) sits
at a citation in its call's `source` cell: same file (the fact's path equal to the cited path or ending with
`/` + it), its line inside the cited line or range (a citation with no line never counts), and of a kind that is a
call of that protocol: http `outbound_http`, `client_binding`; rpc those and `grpc_method`; message
`message_publisher`; db and cache `durable_read`, `durable_write`; a consumer relationship (from the consumer's
operation row's source) `message_consumer`, `message_subscription`, `event_binding`. One such citation is enough.
Otherwise, or when the reader wrote `proposed:`, `name` starts `proposed: ` and so does `source` (the kit's pages draw
a call whose source starts `proposed` as proposed). A `disputed:` claim stays: `disputed: proposed: ...`.

--check exits 0 only when: the lead's snapshot exists; the root tables, unmatched-calls.csv and summary.json on disk
are exactly what a merge of the unit folders gives now (so every unit row is in the map, once, and every call is
matched or listed unmatched); every unit row has a row_id unique in its unit; every unit-local id resolves; and every
unit folder is in units.csv.
"""
import json
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import go  # noqa: E402
import reading_check as rc  # noqa: E402
import paths  # noqa: E402
import tables  # noqa: E402
import register_layout as layout  # noqa: E402

SUBJECT_COLS = ("subject_id,kind,band,level,part_kind,name,purpose,application_id,repository,owner,owner_as_of,"
                "responder,responder_as_of,from_id,to_id,step_hint,operation,sequence,part_of,map_link,"
                "carries_case_id,source").split(",")
PART_COLS = "subject_id,step,involvement,operation,activity,decision_point,reply_decision_point".split(",")
UNMATCHED_COLS = layout.UNMATCHED_COLS
OUT_OF_SCOPE = "out-of-scope:"
UNIT_TABLES = layout.UNIT_TABLES
ID_CELLS = ("subject_id", "from_id", "to_id", "part_of")
HTTP = {"outbound_http", "client_binding"}
CALL_KINDS = {"http": HTTP, "rpc": HTTP | {"grpc_method"}, "message": {"message_publisher"},
              "db": {"durable_read", "durable_write"}, "cache": {"durable_read", "durable_write"}}
CONSUMER_KINDS = {"message_consumer", "message_subscription", "event_binding"}
PARAM = re.compile(r"\{.*\}|:.+|<.*>|\$\{.*\}|%[a-z]|\d+|[0-9a-fA-F]{24}|[0-9a-fA-F-]{36}")
EXTERNAL = "external:"
UNIT_REF = re.compile(r"([a-z0-9-]+)/(.+)")


def claim(text):
    """(disputed, proposed, the claim without those prefixes)."""
    t, d, p = (text or "").strip(), False, False
    while True:
        low = t.lower()
        if low.startswith("disputed:"):
            d, t = True, t[9:].strip()
        elif low.startswith("proposed:"):
            p, t = True, t[9:].strip()
        else:
            return d, p, t


def is_param(seg):
    return bool(PARAM.fullmatch(seg)) or any(c in seg for c in "\"'+")


def http_key(op):
    """(METHOD, path segments with parameters as '{}'), or None when op is not `METHOD url-or-path`."""
    m = re.match(r"\s*([A-Za-z]+)\s+(\S.*?)\s*$", op or "")
    if not m:
        return None
    target = re.sub(r"^[A-Za-z][A-Za-z0-9+.-]*://[^/]*", "", m.group(2))
    target = re.split(r"[?#]", target)[0]
    return m.group(1).upper(), tuple("{}" if is_param(s) else s for s in target.split("/") if s)


def match_http(call_op, ops, named):
    """(part, None) for the one best operation in ops [(part, operation)], else (None, why)."""
    key = http_key(call_op)
    if not key:
        return None, f"the call {call_op!r} is not METHOD and path"
    method, cs = key
    hits = []
    for part, op in ops:
        k = http_key(op)
        if not k or k[0] != method:
            continue
        os_ = k[1]
        if os_ == cs:
            score = (2, len(os_))
        elif named and cs and os_ and (cs[-len(os_):] == os_ or os_[-len(cs):] == cs):
            score = (1, min(len(cs), len(os_)))
        else:
            continue
        hits.append((score, part, op))
    if not hits:
        return None, f"serves no {method} operation matching /{'/'.join(cs)}"
    top = max(h[0] for h in hits)
    tops = [h for h in hits if h[0] == top]
    if len({(h[1], h[2]) for h in tops}) > 1:
        return None, "ambiguous: " + "; ".join(f"{h[1]} {h[2]}" for h in tops)
    return tops[0][1], None


def fact_index(reg):
    idx = {}
    for f in rc.fact_base(reg) or []:
        if f.get("in_test"):
            continue
        idx.setdefault(paths.norm(f.get("file", "")), []).append((int(f.get("line") or 0), f.get("kind")))
    return idx


def found(source, kinds, idx):
    for path, a, b in rc.cited_in(source or ""):
        if a is None:
            continue
        p = paths.norm(path)
        for fp, ents in idx.items():
            if (fp == p or fp.endswith("/" + p)) and any(a <= n <= b and k in kinds for n, k in ents):
                return True
    return False


def max_id(rows, letter):
    nums = [int(m.group(1)) for r in rows for m in [re.fullmatch(letter + r"(\d+)", r.get("subject_id", ""))] if m]
    return max(nums, default=0)


def lead_rows(reg, write):
    """(subjects header, subject rows, participation rows, problems) of the lead, snapshotting them on first merge."""
    snap = reg / layout.LEAD_ROWS
    if not snap.is_dir():
        if not write:
            return SUBJECT_COLS, [], [], ["merge/lead-rows/ is missing: the register has not been merged yet"]
        snap.mkdir(parents=True)
        for name, cols in (("subjects.csv", SUBJECT_COLS), ("participation.csv", PART_COLS)):
            src = reg / name
            if src.is_file():
                shutil.copyfile(src, snap / name)
            else:
                tables.write(snap / name, cols, [])
    sh, srows = tables.table(snap / "subjects.csv")
    _, prows = tables.table(snap / "participation.csv")
    return sh or SUBJECT_COLS, srows, prows, []


def build(reg, write=False):
    """Every output file's text, the summary, and the problems that fail --check."""
    reg = pathlib.Path(reg)
    problems = []
    header, lead_s, lead_p, probs = lead_rows(reg, write)
    problems += probs
    _, unit_rows = tables.table(reg / layout.UNITS_CSV)
    units = [u["unit"].strip() for u in unit_rows if u.get("unit", "").strip() and u["unit"].strip() != "flow"]
    folder = reg / layout.UNITS
    if folder.is_dir():
        for d in sorted(p.name for p in folder.iterdir() if p.is_dir()):
            if d not in units:
                problems.append(f"units/{d}/ is not in units.csv: its rows are not in the map")
    data, placed = {}, {}
    for u in units:
        if not (folder / u).is_dir():
            problems.append(f"units/{u}/ is missing")
        data[u] = {t: tables.table(folder / u / f"{t}.csv")[1] for t in UNIT_TABLES}
        for t in UNIT_TABLES:
            for i, r in enumerate(data[u][t], 2):
                rid = r.get("row_id", "").strip()
                if not rid:
                    problems.append(f"units/{u}/{t}.csv line {i}: no row_id")
                placed.setdefault((u, rid), []).append(t)

    # elements
    ids, band, first_el = {}, {}, {}
    for r in lead_s:
        band[r.get("subject_id", "")] = r.get("band", "")
    n = max_id(lead_s, "S")
    unit_elements = []
    for u in units:
        for r in data[u]["subjects"]:
            if r.get("kind", "").strip() == "relationship":
                problems.append(f"units/{u}/subjects.csv {r.get('row_id')}: a relationship row; calls go in calls.csv")
                continue
            local = r.get("subject_id", "").strip()
            if (u, local) in ids:
                problems.append(f"units/{u}/subjects.csv {r.get('row_id')}: subject_id {local} used twice")
                continue
            n += 1
            ids[(u, local)] = sid = f"S{n:02d}"
            first_el.setdefault(u, sid)
            band[sid] = r.get("band", "")
            unit_elements.append((u, r, sid))

    def resolve(u, local):
        local = (local or "").strip()
        if local.startswith(EXTERNAL):
            return ids.get(("", local))
        return ids.get((u, local))

    externals = {}
    for u in units:
        for c in data[u]["calls"]:
            for ref in (c.get("to_part", ""), c.get("via", "")):
                ref = ref.strip()
                if ref.startswith(EXTERNAL):
                    externals.setdefault(ref, c.get("source", ""))
    ext_rows = []
    for ref in sorted(externals):
        n += 1
        ids[("", ref)] = sid = f"S{n:02d}"
        band[sid] = "technology"
        ext_rows.append({"subject_id": sid, "kind": "element", "band": "technology", "level": "external dependency",
                         "name": ref[len(EXTERNAL):],
                         "purpose": f"proposed: named by the calls as {ref}; no unit reads it",
                         "source": externals[ref]})

    scope = go.load(reg) or {}
    left_out = {s.strip().lower(): s.strip() for s in scope.get("services_out") or [] if s.strip()}
    out_named = {}
    for u in units:
        for c in data[u]["calls"]:
            t = c.get("to_unit", "").strip()
            if t and t not in data and t.lower() in left_out and not c.get("to_part", "").strip():
                out_named.setdefault(left_out[t.lower()], c.get("source", ""))
    for name in sorted(out_named):
        n += 1
        ids[("", OUT_OF_SCOPE + name)] = sid = f"S{n:02d}"
        band[sid] = "application"
        ext_rows.append({"subject_id": sid, "kind": "element", "band": "application", "level": "external dependency",
                         "name": name, "purpose": "out of scope: left out of this run at the go; not read",
                         "source": out_named[name]})

    def unknown(u, row, col, local):
        problems.append(f"units/{u} {row.get('row_id')}: {col} {local!r} is not an element of the unit")

    def lead_id(value):
        m = UNIT_REF.fullmatch((value or "").strip())
        return ids.get((m.group(1), m.group(2))) if m else None

    out_s = []
    for r in lead_s:
        row = dict(r)
        for c in ID_CELLS:
            row[c] = lead_id(row.get(c)) or row.get(c, "")
        out_s.append(row)
    lead_els = [r for r in out_s if r.get("kind", "").strip() != "relationship"]
    lead_rels = [r for r in out_s if r.get("kind", "").strip() == "relationship"]
    els = []
    for u, r, sid in unit_elements:
        row = {c: r.get(c, "") for c in header}
        row["subject_id"] = sid
        if row.get("part_of", "").strip():
            got = resolve(u, row["part_of"])
            if got:
                row["part_of"] = got
            else:
                unknown(u, r, "part_of", row["part_of"])
        els.append(row)

    # relationships
    idx = fact_index(reg)
    rn = max_id(lead_s, "R")
    rels, unmatched, out_of_scope, seen_consumers = [], [], [], set()
    counts = {"calls": 0, "matched": 0, "unmatched": 0, "out_of_scope": 0, "found_by_reader": 0, "proposed": 0}

    def rel(frm, to, text, src, kinds, disputed, proposed, step_hint="", carries="", within="", sequence=""):
        nonlocal rn
        proposed = proposed or not found(src, kinds, idx)
        counts["proposed" if proposed else "found_by_reader"] += 1
        rn += 1
        b = "application" if band.get(frm) == "application" and band.get(to) == "application" else "technology"
        name = ("disputed: " if disputed else "") + ("proposed: " if proposed else "") + f"{frm} to {to or '?'}: {text}"
        rels.append({"subject_id": f"R{rn:02d}", "kind": "relationship", "band": b, "part_kind": "interaction",
                     "name": name, "from_id": frm, "to_id": to, "step_hint": step_hint, "operation": within,
                     "sequence": sequence, "carries_case_id": carries,
                     "source": ("proposed: " if proposed and not src.lower().startswith("proposed") else "") + src})

    def ops_of(u, protocol):
        return [(r.get("part", "").strip(), r) for r in data.get(u, {}).get("operations", [])
                if r.get("protocol", "").strip().lower() == protocol]

    for u in units:
        for c in data[u]["calls"]:
            counts["calls"] += 1
            ref = f"{u}/{c.get('row_id', '')}"
            disputed, proposed, op = claim(c.get("operation"))
            proto = c.get("protocol", "").strip().lower()
            to_unit, to_part, via = (c.get(k, "").strip() for k in ("to_unit", "to_part", "via"))
            frm = resolve(u, c.get("from_part"))
            if not frm:
                unknown(u, c, "from_part", c.get("from_part"))
                frm = ""
            to, matched, why, consumers, broker = "", False, "", [], None
            if proto == "message":
                broker_ref = via or to_part
                if broker_ref:
                    broker = resolve(u, broker_ref)
                    if not broker:
                        unknown(u, c, "via", broker_ref)
                for cu in units:
                    for part, orow in ops_of(cu, "message"):
                        if claim(orow.get("operation"))[2] == op:
                            consumers.append((cu, part, orow))
                matched = bool(consumers)
                why = "" if matched else f"no unit consumes {op!r}"
                to = broker or (resolve(consumers[0][0], consumers[0][1]) if consumers else "") or ""
            elif to_part:
                to = resolve(u, to_part) or ""
                if not to:
                    unknown(u, c, "to_part", to_part)
                matched = bool(to)
            elif to_unit:
                if to_unit not in data and to_unit.lower() in left_out:
                    to = ids[("", OUT_OF_SCOPE + left_out[to_unit.lower()])]
                    counts["out_of_scope"] += 1
                    out_of_scope.append({"call": ref, "from_unit": u, "to_unit": to_unit, "protocol": proto,
                                         "operation": c.get("operation", ""), "source": c.get("source", ""),
                                         "why": f"out of scope: {left_out[to_unit.lower()]} was left out at the go"})
                elif to_unit not in data:
                    why = f"{to_unit} is not a unit in units.csv"
                else:
                    ops = ops_of(to_unit, proto)
                    if proto == "http":
                        part, why = match_http(op, [(p, claim(r.get("operation"))[2]) for p, r in ops], named=True)
                        why = why and f"{to_unit} {why}"
                    else:
                        part = next((p for p, r in ops if claim(r.get("operation"))[2].lower() == op.lower()), None)
                        why = None if part else f"{to_unit} serves no {proto} operation {op!r}"
                    if part:
                        to, matched = resolve(to_unit, part) or "", True
                        if not to:
                            unknown(to_unit, {"row_id": "operations"}, "part", part)
                    else:
                        to = first_el.get(to_unit, "")
            elif proto == "http":
                pool = [(f"{cu}\t{p}", claim(r.get("operation"))[2]) for cu in units for p, r in ops_of(cu, "http")]
                part, why = match_http(op, pool, named=False)
                if part:
                    cu, p = part.split("\t", 1)
                    to, matched = resolve(cu, p) or "", True
            else:
                why = "names neither to_unit nor to_part"
            if matched:
                counts["matched"] += 1
            elif why:
                counts["unmatched"] += 1
                unmatched.append({"call": ref, "from_unit": u, "to_unit": to_unit, "protocol": proto,
                                  "operation": c.get("operation", ""), "source": c.get("source", ""), "why": why})
            rel(frm, to, op, c.get("source", ""), CALL_KINDS.get(proto, set()), disputed, proposed,
                c.get("step_hint", ""), c.get("carries_case_id", ""), c.get("within", "").strip(),
                c.get("sequence", "").strip())
            if proto == "message" and broker:
                for cu, part, orow in consumers:
                    cid = resolve(cu, part)
                    if not cid:
                        unknown(cu, orow, "part", part)
                        continue
                    if (cid, broker, op) in seen_consumers:
                        continue
                    seen_consumers.add((cid, broker, op))
                    d2, p2, _ = claim(orow.get("operation"))
                    steps = list(dict.fromkeys(p.get("step", "").strip() for p in data[cu]["participation"]
                                               if p.get("subject_id", "").strip() == part and p.get("step", "").strip()))
                    rel(cid, broker, f"{op} consumer", orow.get("source", ""), CONSUMER_KINDS, d2, p2, "; ".join(steps))

    # participation
    out_p = []
    for r in lead_p:
        row = dict(r)
        row["subject_id"] = lead_id(row.get("subject_id")) or row.get("subject_id", "")
        out_p.append(row)
    unit_p = 0
    for u in units:
        for r in data[u]["participation"]:
            row = {c: r.get(c, "") for c in PART_COLS}
            got = resolve(u, row["subject_id"])
            if got:
                row["subject_id"] = got
            else:
                unknown(u, r, "subject_id", row["subject_id"])
            out_p.append(row)
            unit_p += 1

    for (u, rid), in_tables in placed.items():
        if rid and len(in_tables) > 1:
            problems.append(f"units/{u}: row_id {rid} used {len(in_tables)} times ({', '.join(in_tables)})")

    subjects = lead_els + els + ext_rows + lead_rels + rels
    summary = {"units": len(units), "rows": len(unit_elements) + counts["calls"] + unit_p,
               "elements": len(lead_els) + len(els) + len(ext_rows), "relationships": len(lead_rels) + len(rels),
               "calls": counts["calls"], "matched": counts["matched"], "unmatched": counts["unmatched"],
               "out_of_scope": counts["out_of_scope"], "found_by_reader": counts["found_by_reader"], "proposed": counts["proposed"]}
    files = {"subjects.csv": tables.text(header, subjects),
             "participation.csv": tables.text(PART_COLS, out_p),
             layout.UNMATCHED_CSV: tables.text(UNMATCHED_COLS, unmatched),
             layout.OUT_OF_SCOPE_CSV: tables.text(UNMATCHED_COLS, out_of_scope),
             layout.SUMMARY_JSON: json.dumps(summary, indent=1) + "\n"}
    return files, summary, problems


def merge(reg):
    reg = pathlib.Path(reg)
    files, summary, problems = build(reg, write=True)
    (reg / layout.MERGE).mkdir(exist_ok=True)
    for name, text in files.items():
        with open(reg / name, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return summary, problems


def check(reg):
    reg = pathlib.Path(reg)
    files, summary, problems = build(reg, write=False)
    if (reg / layout.LEAD_ROWS).is_dir():
        for name, text in files.items():
            p = reg / name
            if not p.is_file() or p.read_bytes().decode("utf-8", errors="replace") != text:
                hint = " (rows the lead adds after the first merge go in merge/lead-rows/)" if "/" not in name else ""
                problems.append(f"{name}: not what a merge of the unit folders gives now; run merge.py{hint}")
    return summary, problems


def main(argv):
    is_check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if len(args) != 1:
        print(__doc__)
        return 2
    summary, problems = (check if is_check else merge)(args[0])
    print(json.dumps(summary))
    for p in problems:
        print("PROBLEM: " + p)
    if is_check:
        print("merge check: " + ("ok" if not problems else f"FAILED, {len(problems)} problem(s)"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
