"""Write one map from the reading units' folders of a split run, with every call between units matched on both sides.

Usage: python merge.py <register folder>            writes the map
       python merge.py --check <register folder>    says whether the map on disk is the merge of the units now
       python merge.py --reread-check <unit>/<row_id> [--transcripts DIR] <register folder>
                                                    says whether that call's re-read is done (exit 0) or not (exit 1)

Files read and written are those of split-run-formats.md.

What it writes. The register's root `subjects.csv` and `participation.csv`, `merge/unmatched-calls.csv` and
`merge/summary.json`. Nothing else at the root. Same folders and `merge/ids.csv` in, same files out, byte for byte;
run it again at any time.

Flow after flow. At a flow's finish (go.py, when the next flow starts) `merge/ids.csv` records the merge's own
resolution of every row it gives, whole (`write_record`; refused unless the root on disk is the merge's output). A later
merge writes every row the record covers exactly as recorded, with the root corrections recorded to it applied, and
resolves afresh only the rows it does not cover: a later flow's operation never re-points an earlier call, nor makes
it unmatched, and a finished call is never listed unmatched again. New ids are numbered from one above the highest
in `ids.csv` and the lead's rows: inputs only, never the merge's own output, so `--check` can pass in a later flow.
A finished row changes only by a correction recorded in `corrections-applied.csv`; the merge records its own (id
`merge-<n>`, unit blank), once, when it writes, and `--check` fails while one is not yet recorded and writes nothing:
- a unit row corrected (go.py --apply-correction) gives its output row afresh, each changed cell recorded; a unit row
  removed so withdraws its output row by a recorded removal. A finished call is matched again only when its
  correction changed `protocol`, `operation`, `to_unit`, `to_part` or `via`; a correction to any other cell is
  carried onto the recorded row, so a later flow's operation never makes it unmatched;
- a consumer relationship whose operation row is corrected or removed is withdrawn by a recorded removal;
- a service an earlier flow left out and minted as out of scope, now read (a unit with a folder): each recorded call
  to the minted element is resolved afresh against the unit, its changed cells recorded (source `merge: <service>
  read in flow <id>`), a call that does not match listed unmatched; and the minted element withdrawn by a recorded
  removal, so the service is drawn once;
- a consumer relationship is one row per (consumer, broker, topic): when a later flow's participation adds a step to
  the consumer part, its `step_hint` grows by a recorded correction.
A recorded row no longer given stays in `ids.csv` at the next finish as a tombstone (`removed` `yes` when its removal
is recorded): its id still counts for numbering and the row is never minted again. An element's record is its own
row's only (the same row_id): a local id a later reader gives to a new row is a new element, numbered above every
recorded id; a unit row whose own record is a tombstone fails `--check`. A correction re-matches a finished call once:
the record row lists the corrections already in it (`consumed`). `--check` also fails on a `subject_id` used twice.

The lead's own rows. The root tables as they stand before the first merge are the lead's rows (the case, persons, any
flow-level row that belongs to no unit). The first merge copies them, unchanged, to `merge/lead-rows/`; every later merge
reads the lead's rows from there and never from the root, which from then on holds only merge output. A row the lead
adds or changes after the first merge goes into `merge/lead-rows/`; one written into the root by hand is overwritten by
the next merge, and `--check` fails on it until then. Lead rows keep their ids. In them a cell `subject_id`, `from_id`,
`to_id` or `part_of` written `<unit>/<unit-local id>` is replaced by that part's map id.

Numbering. Elements of the units come after the lead's elements, in units.csv order and then file order, numbered from
one above the highest `S<n>` among the lead's rows; then one element per distinct `external:<name>` the calls name, in
name order (a minted element: level `external dependency`, purpose `proposed:`, the first citing call as source,
and `part_kind` from how its calls reach it: `message broker` when a call names it as `via` or publishes to it,
`database` for a `db` call, `cache` for a `cache` call, else `third-party API`, an outside service measured from the
calling side; a kind recorded blank by an earlier merge is given, as a correction the merge makes).
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
- Out of scope: the scopes so far are every flow's go in `scope.json` (written by go.py, read with go.load_all). A
  unit units.csv lists that has no folder, and whose deployable no go so far took in (`services_in`), is out of
  scope: it is not missing, and nothing of it is merged. A unit with a folder is always merged, whatever the go
  worked now took in. A call whose `to_unit` names an out-of-scope unit, or names no unit but a service some go so
  far left out (`services_out`; case ignored), is never unmatched. It goes to `merge/out-of-scope-calls.csv` (the
  same columns) and is drawn to one element per such service, minted after the `external:` ones: band application,
  level `external dependency`, `part_kind` `API service`, purpose `out of scope: ...`. With no scope.json, nothing is out of scope; with no go
  recording the services it took in, no listed unit is.

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
unit folder is in units.csv. An unmatched call does not fail it: re-reading the call is a step of its own, after the
merge.

The re-read of an unmatched call. Each call a merge of the unit folders now leaves unmatched is owed a re-read on both
sides by an agent (the unit reader's definition, "Re-reading an unmatched call"), and is resolved in one of two ways:
- corrected: the re-read corrects the calling unit's calls.csv row, or adds the operation to the called unit's
  operations.csv, so the merge now matches it and it is no longer listed; or
- disputed: the called unit serves nothing that matches, and the re-read says so by putting `disputed: ` before the
  call's `operation`. That label counts only when the replay of the calling unit's calls.csv from Claude Code's
  transcripts (provenance.py; found as reading_check.py finds them, or --transcripts) shows it put in place, the
  cell on disk exactly, by a session that:
  - is a `bfo-unit-reader` subagent (its meta file says so) and ran no shell;
  - opened with Read every line the call's `source` cites, at that path in the workspace (found as reading_check.py
    --unit finds it), and, when `to_unit` is a unit, code under that unit's paths in the workspace;
  - changed this one call row of calls.csv and no other;
  - wrote nothing but the calling unit's calls.csv and, at most, the called unit's operations.csv.
  A tool call whose result is an error is not counted. The unit's first reader wrote its other tables too, so its
  session is never taken for the re-read; a label written by hand, even after a re-read that wrote the row some other
  way, or beside a re-read that labelled another row, resolves nothing; and a call citing no line cannot be disputed.
  One call per re-read session. A label already in the latest finished flow's judged snapshot counts: that flow's
  re-read was checked when it finished.
- A call whose called side is not a unit (`to_unit` names no unit in units.csv, or the call names neither `to_unit`
  nor `to_part`) is resolved only by correcting it: a real unit, `to_part`, or `external:<name>`. A call with no
  `to_unit` (an http call matched against every unit, or a message no unit consumes) may be disputed after a re-read
  of its calling side alone, and is said apart as disputed on the calling side only.
`rereads()` lists every unmatched call with whether it is resolved and, if not, why; run_status.py's split checks hold
the run NOT DONE on each one not resolved. `--reread-check` is that check for one call, the check a job step `reread`
of item `call:<unit>/<row_id>` runs (split-run-formats.md): a call the merge now matches passes.
"""
import csv
import io
import json
import pathlib
import re
import shutil
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import go  # noqa: E402
import provenance  # noqa: E402  (who wrote each unit table, from the transcripts)
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
# The kind (method/part-kinds.csv) a part the merge mints is given, since no reader reads it: an outside dependency
# by how its calls reach it (named as a broker, or by the call's protocol), a service left out at the go as a service.
# An outside service reached by http or rpc is drawn and measured from the calling side, the third-party API's set.
OUTSIDE_KINDS = (("via", "message broker"), ("message", "message broker"), ("db", "database"), ("cache", "cache"))
OUTSIDE_SERVICE_KIND = "third-party API"
LEFT_OUT_KIND = "API service"
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


def outside_kind(reached):
    """The kind of an outside dependency the calls name, from how they reach it (`reached`: each citing call's protocol,
    or `via` when it names the part as a message call's broker); "" when no call names it any more."""
    if not reached:
        return ""
    return next((kind for how, kind in OUTSIDE_KINDS if how in reached), OUTSIDE_SERVICE_KIND)


def scopes(reg):
    """(services some go so far took in, lower case, or None when no go records them; {service lower case: as the go
    named it} for every service some go so far left out). Every flow's go is in scope.json (go.load_all). A service
    surveyed after every go, which none named in or out, is taken in (code got for an external dependency, go.got_after)."""
    got = go.load_all(reg)
    ins = None
    if any("services_in" in s for s in got):
        ins = {n.strip().lower() for s in got for n in s.get("services_in") or [] if n.strip()}
        ins |= go.got_after(got, go.surveyed_services(reg))
    outs = {n.strip().lower(): n.strip() for s in got for n in s.get("services_out") or [] if n.strip()}
    return ins, outs


def out_of_scope_units(reg):
    """{unit: its service}: each unit units.csv lists that has no folder and whose deployable no go so far took in.
    It owes nothing: it is not missing from the merge, its rows are not judged, and a call to it is out of scope. A
    unit with a folder is always merged. With no go recording the services it took in, none is out of scope."""
    reg = pathlib.Path(reg)
    ins, outs = scopes(reg)
    if ins is None:
        return {}
    out = {}
    for r in tables.table(reg / layout.UNITS_CSV)[1]:
        u = (r.get("unit") or "").strip()
        dep = (r.get("deployable") or "").strip() or u
        if u and u != "flow" and not layout.unit_dir(reg, u).is_dir() and dep.lower() not in ins:
            out[u] = outs.get(dep.lower(), dep)
    return out


def build(reg, write=False, out=None):
    """Every output file's text, the summary, and the problems that fail --check. `out`, when given, also gets the
    corrections the merge makes to finished rows (`kit`) and its resolution of every row (`resolution`)."""
    reg = pathlib.Path(reg)
    problems = []
    header, lead_s, lead_p, probs = lead_rows(reg, write)
    problems += probs
    _, unit_rows = tables.table(reg / layout.UNITS_CSV)
    outside = out_of_scope_units(reg)
    units = [u["unit"].strip() for u in unit_rows if u.get("unit", "").strip() and u["unit"].strip() != "flow"
             and u["unit"].strip() not in outside]
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

    # the resolution record of the flows finished so far (merge/ids.csv), and the root corrections to its rows
    record = read_record(reg)
    fixes = go.applied_corrections(reg, "subjects")
    kit, resolution = [], []
    cur = go.load(reg) or {}
    flow_now = go.flow_id_of(reg, cur) or cur.get("flow", "")
    dep_of = {(r.get("unit") or "").strip(): (r.get("deployable") or "").strip() or (r.get("unit") or "").strip()
              for r in unit_rows}
    read_now = {x.lower() for u in units if (folder / u).is_dir() for x in (u, dep_of.get(u, u))}

    def now_of(rec):
        """A recorded row as the map holds it: with every root correction recorded to it applied."""
        return go.corrected("subjects", {c: rec.get(c, "") for c in header}, fixes, rec.get("subject_id", ""))

    def settle(rec, fresh, source):
        """`fresh` in place of the recorded row, each cell it changes recorded as a correction the merge makes."""
        was = now_of(rec)
        for c in header:
            if (was.get(c) or "") != (fresh.get(c) or ""):
                kit.append({"table": "subjects", "row": rec.get("subject_id", ""), "column": c,
                            "before": was.get(c) or "", "after": fresh.get(c) or "", "source": source,
                            "why": "a finished flow's row, changed by what the merge reads now"})
        return fresh

    def withdraw(rec, source):
        if not go.removed(fixes, rec.get("subject_id", "")):
            kit.append({"table": "subjects", "row": rec.get("subject_id", ""), "column": "",
                        "before": json.dumps(now_of(rec), ensure_ascii=False), "after": go.REMOVED, "source": source,
                        "why": "a finished flow's row the merge no longer gives"})

    def unit_fixes(u, table, rid):
        return [f for f in go.applied_corrections(reg, table, u) if f.get("row") == rid and f.get("column")]

    def unit_fixed(u, table, rid, rec=None):
        """The columns of this unit row a recorded correction changed since its record row was written (`consumed`
        holds the corrections already in it): its output is made again from the row as corrected."""
        done = set(((rec or {}).get("consumed") or "").split(";")) - {""}
        return {f.get("column") for f in unit_fixes(u, table, rid) if f.get("correction_id") not in done}

    def keep(kind, row, unit="", local="", row_id="", broker="", topic=""):
        table = {"element": "subjects", "call": "calls"}.get(kind)
        consumed = ";".join(f.get("correction_id", "") for f in unit_fixes(unit, table, row_id or local)) if table else ""
        resolution.append(dict(row, record=kind, unit=unit, local=local, row_id=row_id, broker=broker, topic=topic,
                               consumed=consumed, removed=""))
        return row

    def element_record(u, r):
        """The record of this unit element: only the one written for this very row (its row_id); a local id a later
        reader gives again to a new row is a new element."""
        rec = record["element"].get((u, r.get("subject_id", "").strip()))
        return rec if rec and rec.get("row_id", "") == r.get("row_id", "").strip() else None

    # elements
    ids, band, first_el = {}, {}, {}
    for r in lead_s:
        band[r.get("subject_id", "")] = r.get("band", "")
    n = max(max_id(lead_s, "S"), record_max(record, "S"))
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
            rec = element_record(u, r)
            if rec:
                sid = rec["subject_id"]
            else:
                n += 1
                sid = f"S{n:02d}"
            ids[(u, local)] = sid
            first_el.setdefault(u, sid)
            band[sid] = r.get("band", "")
            unit_elements.append((u, r, sid))

    def resolve(u, local):
        local = (local or "").strip()
        if local.startswith(EXTERNAL):
            return ids.get(("", local))
        return ids.get((u, local))

    externals, reached = {}, {}
    for u in units:
        for c in data[u]["calls"]:
            for col in ("to_part", "via"):
                ref = c.get(col, "").strip()
                if ref.startswith(EXTERNAL):
                    externals.setdefault(ref, c.get("source", ""))
                    reached.setdefault(ref, set()).add("via" if col == "via" else c.get("protocol", "").strip().lower())
    ext_rows = []

    def kinded(rec, kind, source):
        """A recorded minted row as the map holds it, given its kind where it was recorded with none (a merge before
        minted parts had one), as a correction the merge makes."""
        row = now_of(rec)
        if (row.get("part_kind") or "").strip() or not kind:
            return row
        return settle(rec, dict(row, part_kind=kind), source)

    for ref in sorted(set(externals) | set(record["external"])):
        rec = record["external"].get(ref)
        kind = outside_kind(reached.get(ref, ()))
        if rec:
            ids[("", ref)] = sid = rec["subject_id"]
            band[sid] = rec.get("band", "")
            if not go.removed(fixes, sid):
                ext_rows.append(keep("external", kinded(rec, kind, f"merge: {ref} given the kind its calls show"),
                                     local=ref))
            continue
        n += 1
        ids[("", ref)] = sid = f"S{n:02d}"
        band[sid] = "technology"
        ext_rows.append(keep("external", {"subject_id": sid, "kind": "element", "band": "technology",
                                          "level": "external dependency", "part_kind": kind,
                                          "name": ref[len(EXTERNAL):],
                                          "purpose": f"proposed: named by the calls as {ref}; no unit reads it",
                                          "source": externals[ref]}, local=ref))

    left_out = scopes(reg)[1]

    def out_service(t):
        """The service a call's to_unit names when it is out of scope: a listed unit outside every scope so far, or a
        name no unit has that some go so far left out."""
        if t in outside:
            return outside[t]
        return left_out.get(t.lower()) if t and t not in data else None

    out_named = {}
    for u in units:
        for c in data[u]["calls"]:
            t = c.get("to_unit", "").strip()
            if t and out_service(t) and not c.get("to_part", "").strip():
                out_named.setdefault(out_service(t), c.get("source", ""))
    now_read = {}  # the minted element's id of each service an earlier flow left out and this merge reads
    for name in sorted(set(out_named) | set(record["out of scope"])):
        rec = record["out of scope"].get(name)
        if rec and name.lower() in read_now:
            now_read[rec["subject_id"]] = name
            withdraw(rec, f"merge: {name} read in flow {flow_now}")
            continue
        if rec:
            ids[("", OUT_OF_SCOPE + name)] = sid = rec["subject_id"]
            band[sid] = rec.get("band", "")
            if not go.removed(fixes, sid):
                ext_rows.append(keep("out of scope", kinded(rec, LEFT_OUT_KIND, f"merge: {name} given the kind of a "
                                                            "service left out"), local=name))
            continue
        n += 1
        ids[("", OUT_OF_SCOPE + name)] = sid = f"S{n:02d}"
        band[sid] = "application"
        ext_rows.append(keep("out of scope", {"subject_id": sid, "kind": "element", "band": "application",
                                              "level": "external dependency", "part_kind": LEFT_OUT_KIND,
                                              "name": name,
                                              "purpose": "out of scope: left out of this run at the go; not read",
                                              "source": out_named[name]}, local=name))

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
        local, rid = r.get("subject_id", "").strip(), r.get("row_id", "").strip()
        rec = element_record(u, r)
        if rec:
            if go.removed(fixes, sid):
                problems.append(f"units/{u}/subjects.csv {rid}: its row was removed in a finished flow (the map's "
                                f"{sid}, a tombstone in merge/ids.csv), and a row_id is never reused: give a new row "
                                "a new row_id")
                continue
            row = (settle(rec, row, f"merge: units/{u}/subjects {rid} corrected")
                   if unit_fixed(u, "subjects", rid, rec) else now_of(rec))
        els.append(keep("element", row, u, local, rid))

    # relationships
    idx = fact_index(reg)
    rn = max(max_id(lead_s, "R"), record_max(record, "R"))
    rels, unmatched, out_of_scope, seen_consumers = [], [], [], set()
    counts = {"calls": 0, "matched": 0, "unmatched": 0, "out_of_scope": 0, "found_by_reader": 0, "proposed": 0}

    def rel(frm, to, text, src, kinds, disputed, proposed, step_hint="", carries="", within="", sequence="", rid=None):
        nonlocal rn
        proposed = proposed or not found(src, kinds, idx)
        counts["proposed" if proposed else "found_by_reader"] += 1
        if rid is None:
            rn += 1
            rid = f"R{rn:02d}"
        b = "application" if band.get(frm) == "application" and band.get(to) == "application" else "technology"
        name = ("disputed: " if disputed else "") + ("proposed: " if proposed else "") + f"{frm} to {to or '?'}: {text}"
        return {"subject_id": rid, "kind": "relationship", "band": b, "part_kind": "interaction",
                "name": name, "from_id": frm, "to_id": to, "step_hint": step_hint, "operation": within,
                "sequence": sequence, "carries_case_id": carries,
                "source": ("proposed: " if proposed and not src.lower().startswith("proposed") else "") + src}

    def as_recorded(rec):
        """A recorded relationship, as the map holds it, counted as its name says (never by fact-base.json now)."""
        row = now_of(rec)
        counts["proposed" if claim(row.get("name"))[1] else "found_by_reader"] += 1
        return row

    def ops_of(u, protocol):
        return [(r.get("part", "").strip(), r) for r in data.get(u, {}).get("operations", [])
                if r.get("protocol", "").strip().lower() == protocol]

    for u in units:
        for c in data[u]["calls"]:
            counts["calls"] += 1
            ref = f"{u}/{c.get('row_id', '')}"
            crid = c.get("row_id", "").strip()
            rec = record["call"].get((u, crid))
            fixed_cols = unit_fixed(u, "calls", crid, rec) if rec else set()
            again = bool(rec) and (rec.get("to_id") in now_read or bool(fixed_cols & MATCHED_ON))
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
                if out_service(to_unit):
                    to = ids[("", OUT_OF_SCOPE + out_service(to_unit))]
                    counts["out_of_scope"] += 1
                    out_of_scope.append({"call": ref, "from_unit": u, "to_unit": to_unit, "protocol": proto,
                                         "operation": c.get("operation", ""), "source": c.get("source", ""),
                                         "why": f"out of scope: {out_service(to_unit)} was left out at the go"})
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
            if rec and not again:  # a finished flow's call: as recorded, never resolved afresh nor listed unmatched
                counts["recorded"] = counts.get("recorded", 0) + 1
                if go.removed(fixes, rec["subject_id"]):
                    problems.append(f"units/{u}/calls.csv {crid}: its row was removed in a finished flow (the map's "
                                    f"{rec['subject_id']}, a tombstone in merge/ids.csv), and a row_id is never reused: "
                                    "give a new row a new row_id")
                else:
                    row = as_recorded(rec)
                    if fixed_cols:  # a cell not matched on, corrected: carried onto the recorded row, never re-matched
                        src = c.get("source", "")
                        if row.get("source", "").startswith("proposed: ") and not src.lower().startswith("proposed"):
                            src = "proposed: " + src
                        row = settle(rec, dict(row, step_hint=c.get("step_hint", ""), operation=c.get("within", "").strip(),
                                               sequence=c.get("sequence", "").strip(),
                                               carries_case_id=c.get("carries_case_id", ""), source=src),
                                     f"merge: units/{u}/calls {crid} corrected")
                    rels.append(keep("call", row, u, crid))
            else:
                if matched:
                    counts["matched"] += 1
                elif why:
                    counts["unmatched"] += 1
                    unmatched.append({"call": ref, "from_unit": u, "to_unit": to_unit, "protocol": proto,
                                      "operation": c.get("operation", ""), "source": c.get("source", ""), "why": why})
                row = rel(frm, to, op, c.get("source", ""), CALL_KINDS.get(proto, set()), disputed, proposed,
                          c.get("step_hint", ""), c.get("carries_case_id", ""), c.get("within", "").strip(),
                          c.get("sequence", "").strip(), rid=rec["subject_id"] if rec else None)
                if rec:
                    row = settle(rec, row, f"merge: {now_read[rec['to_id']]} read in flow {flow_now}"
                                 if rec.get("to_id") in now_read else f"merge: units/{u}/calls {crid} corrected")
                rels.append(keep("call", row, u, crid))
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
                    crec = record["consumer"].get((cid, broker, op))
                    if crec:  # one row per (consumer, broker, topic): a later flow's step grows its step_hint
                        if go.removed(fixes, crec["subject_id"]):
                            continue
                        row = as_recorded(crec)
                        had = [s.strip() for s in (row.get("step_hint") or "").split(";") if s.strip()]
                        more = [s for s in steps if s not in had]
                        if more:
                            row = settle(crec, dict(row, step_hint="; ".join(had + more)),
                                         f"merge: {cu} takes part in step {', '.join(more)}, of a later flow")
                    else:
                        row = rel(cid, broker, f"{op} consumer", orow.get("source", ""), CONSUMER_KINDS, d2, p2,
                                  "; ".join(steps))
                    rels.append(keep("consumer", row, cu, cid, orow.get("row_id", "").strip(), broker, op))

    # participation
    out_p = []
    for r in lead_p:
        row = dict(r)
        row["subject_id"] = lead_id(row.get("subject_id")) or row.get("subject_id", "")
        out_p.append(row)
    unit_p = 0
    finished = any(record.values())
    part_fixes = go.applied_corrections(reg, "participation")

    def part_out(u, r):
        row = {c: (r.get(c) or "") for c in PART_COLS}
        row["subject_id"] = resolve(u, row["subject_id"]) or row["subject_id"]
        return row

    def part_kit(before, now, source):
        """A finished participation row a unit correction changed (now) or removed (now None), recorded on the root
        row as it was (its key), once."""
        key = go.row_key("participation", before)
        if now is None:
            if not go.removed(part_fixes, key):
                kit.append({"table": "participation", "row": key, "column": "", "after": go.REMOVED,
                            "before": json.dumps(go.corrected("participation", before, part_fixes, key),
                                                 ensure_ascii=False),
                            "source": source, "why": "a finished flow's row the merge no longer gives"})
            return
        was = go.corrected("participation", before, part_fixes, key)
        for c in PART_COLS:
            if (was.get(c) or "") != (now.get(c) or ""):
                kit.append({"table": "participation", "row": key, "column": c, "before": was.get(c) or "",
                            "after": now.get(c) or "", "source": source,
                            "why": "a finished flow's row, changed by a correction to its unit row"})

    for u in units:
        unit_fixes = go.applied_corrections(reg, "participation", u) if finished else []
        for r in data[u]["participation"]:
            row = {c: r.get(c, "") for c in PART_COLS}
            got = resolve(u, row["subject_id"])
            if got:
                row["subject_id"] = got
            else:
                unknown(u, r, "subject_id", row["subject_id"])
            mine = [f for f in unit_fixes if f.get("row") == r.get("row_id", "").strip() and f.get("column")]
            if mine:  # the row as it was before its corrections, undone in reverse
                old = dict(r)
                for f in reversed(mine):
                    if f["column"] in old and old[f["column"]] == f.get("after"):
                        old[f["column"]] = f.get("before", "")
                part_kit(part_out(u, old), row, f"merge: units/{u}/participation {r.get('row_id', '').strip()} "
                                                "corrected")
            out_p.append(row)
            unit_p += 1
        for f in unit_fixes:
            if f.get("after") == go.REMOVED and not (f.get("column") or "").strip():
                try:
                    old = json.loads(f.get("before") or "")
                except ValueError:
                    continue
                part_kit(part_out(u, old), None, f"merge: units/{u}/participation {f.get('row')} removed")

    for (u, rid), in_tables in placed.items():
        if rid and len(in_tables) > 1:
            problems.append(f"units/{u}: row_id {rid} used {len(in_tables)} times ({', '.join(in_tables)})")

    produced = {(r["record"], record_key(r)) for r in resolution}
    for kind, table in (("element", "subjects"), ("call", "calls"), ("consumer", "operations")):
        for key, rec in record[kind].items():  # a finished unit row removed (a consumer's operation also corrected)
            u, rid = rec.get("unit", ""), rec.get("row_id") or rec.get("local", "")
            if (kind, key) in produced:
                continue
            fixed = go.applied_corrections(reg, table, u)
            if go.removed(fixed, rid) or (kind == "consumer" and any(f.get("row") == rid for f in fixed)):
                withdraw(rec, f"merge: units/{u}/{table} {rid} {'corrected' if not go.removed(fixed, rid) else 'removed'}")
    gone = {k["row"] for k in kit if k["after"] == go.REMOVED} | {f.get("row") for f in fixes if go.removed([f], f.get("row"))}
    given = {r.get("subject_id") for r in resolution}
    for rec in record["all"]:  # every recorded row not given now stays in the record: a removal, a tombstone
        if rec.get("subject_id") not in given:
            given.add(rec.get("subject_id"))
            resolution.append(dict(rec, removed="yes" if rec.get("subject_id") in gone else rec.get("removed", "")))

    seen_ids = Counter(r.get("subject_id", "") for r in lead_els + els + ext_rows + lead_rels + rels)
    problems += [f"subjects.csv: subject_id {sid} used twice" for sid, k in seen_ids.items() if sid and k > 1]

    subjects = lead_els + els + ext_rows + lead_rels + rels
    summary = {"units": len(units), "rows": len(unit_elements) + counts["calls"] + unit_p,
               "elements": len(lead_els) + len(els) + len(ext_rows), "relationships": len(lead_rels) + len(rels),
               "calls": counts["calls"], "matched": counts["matched"], "unmatched": counts["unmatched"],
               "out_of_scope": counts["out_of_scope"], "found_by_reader": counts["found_by_reader"], "proposed": counts["proposed"]}
    if any(record.values()):
        summary["recorded"] = counts.get("recorded", 0)
    files = {"subjects.csv": tables.text(header, subjects),
             "participation.csv": tables.text(PART_COLS, out_p),
             layout.UNMATCHED_CSV: tables.text(UNMATCHED_COLS, unmatched),
             layout.OUT_OF_SCOPE_CSV: tables.text(UNMATCHED_COLS, out_of_scope),
             layout.SUMMARY_JSON: json.dumps(summary, indent=1) + "\n"}
    if out is not None:
        out.update(kit=kit, resolution=resolution, header=header)
    return files, summary, problems


IDS_CSV = f"{layout.MERGE}/ids.csv"  # the resolution record: every finished flow's merge output, whole rows
RECORD_KEYS = ["record", "unit", "local", "row_id", "broker", "topic", "removed", "consumed"]
RECORD_KINDS = ("element", "external", "out of scope", "call", "consumer")
MATCHED_ON = {"protocol", "operation", "to_unit", "to_part", "via"}  # a correction to these re-matches a finished call


def record_key(r):
    """A record row's key within its kind."""
    kind = r.get("record", "")
    if kind in ("element", "call"):
        return (r.get("unit", ""), r.get("local", ""))
    if kind == "consumer":
        return (r.get("local", ""), r.get("broker", ""), r.get("topic", ""))
    return r.get("local", "")


def read_record(reg):
    """{kind: {key: recorded row}} from merge/ids.csv: elements by (unit, local id), externals by `external:<name>`,
    out-of-scope elements by service, calls by (unit, row_id), consumer relationships by (consumer, broker, topic). Where
    a key holds a tombstone and a live row (a local id given again to a new row), the live row is the key's; every row,
    tombstones included, is under `all`."""
    out = {k: {} for k in RECORD_KINDS}
    out["all"] = []
    for r in tables.dicts(pathlib.Path(reg) / IDS_CSV):
        if r.get("record", "") in RECORD_KINDS:
            out["all"].append(r)
            have = out[r["record"]].get(record_key(r))
            if have is None or (have.get("removed") and not r.get("removed")):
                out[r["record"]][record_key(r)] = r
    return out


def record_max(record, letter):
    """The highest id of `letter` the record holds, tombstones included."""
    return max([int(m.group(1)) for r in record["all"]
                for m in [re.fullmatch(letter + r"(\d+)", r.get("subject_id", ""))] if m], default=0)


def record_problems(reg):
    """Why the merge's resolution cannot be kept at a flow's finish: the root tables on disk are not what a merge
    gives now, or the merge makes corrections not yet recorded. [] when it can."""
    reg = pathlib.Path(reg)
    if not (reg / layout.UNITS_CSV).is_file():
        return []
    got = {}
    files, _, problems = build(reg, out=got)
    for name in ("subjects.csv", "participation.csv"):
        p = reg / name
        if not p.is_file() or p.read_bytes().decode("utf-8", errors="replace") != files[name]:
            problems.append(f"{name} is not what a merge of the unit folders gives now: run merge.py")
    if got["kit"]:
        problems.append(f"{len(got['kit'])} correction(s) the merge makes are not recorded yet: run merge.py")
    return problems


def write_record(reg):
    """At a flow's finish (go.py keeps the finished flow): merge/ids.csv, the merge's own resolution of every row it
    gives, whole, so that later merges write each as recorded. Refused (ValueError) unless the root on disk is what
    the merge gives now, since the merge drops row_id and the record cannot be rebuilt from the root."""
    reg = pathlib.Path(reg)
    wrong = record_problems(reg)
    if wrong:
        raise ValueError("; ".join(wrong))
    got = {}
    build(reg, out=got)
    (reg / layout.MERGE).mkdir(exist_ok=True)
    tables.write(reg / IDS_CSV, RECORD_KEYS + list(got["header"]), got["resolution"])


def _record_kit(reg, kit):
    """The corrections the merge makes, appended to corrections-applied.csv: a finished row re-pointed, withdrawn or
    grown, each recorded so the freeze accepts it."""
    import datetime
    if not kit:
        return
    have = len([r for r in go.table_rows(reg, "corrections-applied")[1]
                 if (r.get("correction_id") or "").startswith("merge-")])
    now = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    go.record_applied(reg, [dict(k, correction_id=f"merge-{have + i}", applied_at=now, unit="")
                            for i, k in enumerate(kit, 1)])


def merge(reg):
    reg = pathlib.Path(reg)
    got = {}
    files, summary, problems = build(reg, write=True, out=got)
    (reg / layout.MERGE).mkdir(exist_ok=True)
    for name, text in files.items():
        with open(reg / name, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    _record_kit(reg, got["kit"])
    return summary, problems


def check(reg):
    reg = pathlib.Path(reg)
    got = {}
    files, summary, problems = build(reg, write=False, out=got)
    if got["kit"]:
        problems.append(f"{len(got['kit'])} correction(s) the merge makes to finished rows are not recorded yet: run "
                        "merge.py")
    if (reg / layout.LEAD_ROWS).is_dir():
        for name, text in files.items():
            p = reg / name
            if not p.is_file() or p.read_bytes().decode("utf-8", errors="replace") != text:
                hint = " (rows the lead adds after the first merge go in merge/lead-rows/)" if "/" not in name else ""
                problems.append(f"{name}: not what a merge of the unit folders gives now; run merge.py{hint}")
    return summary, problems


def _call_row(reg, unit, rid):
    return next((r for r in tables.table(reg / layout.UNITS / unit / "calls.csv")[1]
                 if r.get("row_id", "").strip() == rid), None)


def _is_re_read(s, prov, reg, ws, unit, row, to_unit, units):
    """Session s is the re-read of the call `row` of `unit`, as the module's docstring says: the replay of the calling
    unit's calls.csv (`prov`, provenance.py) shows it changing this one call row and nothing else there."""
    root = reg.resolve()
    own = paths.norm(layout.unit_dir(root, unit) / "calls.csv")
    allowed = {own} | ({paths.norm(layout.unit_dir(root, to_unit) / "operations.csv")} if to_unit in units else set())
    written = {p for _, p in s.writes}
    cited = rc.cited_in(row.get("source", ""))
    touched = prov.tables["calls"].changed.get(s, {}) if "calls" in prov.tables else {}
    rows = set().union(*touched.values()) if touched else set()
    if provenance.agent_type(s.path, provenance.READER_TYPE)[1] or s.shell or not written <= allowed or not cited \
            or rows != {row.get("row_id", "").strip()}:
        return False
    reads = s.ok_reads()
    for path, a, b in cited:  # the cited lines themselves, in the workspace
        if not paths.covered(a, b, reads.get(paths.norm(ws / path), [])):
            return False
    if to_unit in units:  # under the called unit's paths in the workspace
        under = [paths.norm(ws / p) + "/" for p in rc.unit_paths(reg, to_unit)]
        return any(q.startswith(u) for q in reads for u in under)
    return True


def _corrected_only(to_unit, why, units):
    """The called side was never read (to_unit names no unit, or the call names neither to_unit nor to_part): only a
    correction of the row resolves it."""
    return bool(to_unit and to_unit not in units) or why.startswith("names neither")


def rereads(reg, transcripts=None):
    """[{call, to_unit, why, resolved, calling_side_only, problem}], one per call a merge of the unit folders now
    leaves unmatched (the module's docstring says when one is resolved). `calling_side_only`: the call names no unit
    (`to_unit` blank), so its re-read could open only the calling side. The transcripts are read only when a call is
    labelled disputed."""
    reg = pathlib.Path(reg)
    files, _, _ = build(reg)
    left = list(csv.DictReader(io.StringIO(files[layout.UNMATCHED_CSV])))
    if not left:
        return []
    units = {u["unit"].strip() for u in tables.table(reg / layout.UNITS_CSV)[1] if u.get("unit", "").strip()}
    ws = rc.workspace(reg.resolve(), [p for u in sorted(units) for p in rc.unit_paths(reg, u)])
    provs, out = {}, []
    for u in left:
        call, to_unit, why = u["call"], u.get("to_unit", "").strip(), u.get("why", "")
        unit, rid = call.split("/", 1)
        row = _call_row(reg, unit, rid) or {}
        if _corrected_only(to_unit, why, units):
            problem = (f"{call} unmatched ({why}): the called side is not a unit, so only a correction resolves it: "
                       "correct the row (to_unit a unit in units.csv, to_part, or external:<name>)")
        elif not claim(row.get("operation"))[0]:
            problem = (f"{call} unmatched ({why}): not re-read; re-read it on both sides and correct the row, or label "
                       "its operation `disputed: ` when the called unit serves nothing that matches")
        else:
            if unit not in provs:
                provs[unit] = provenance.unit(reg, unit, transcripts)
            prov = provs[unit]
            rid, who = row.get("row_id", "").strip(), None
            if prov.cell("calls", rid, "operation") == row.get("operation"):
                who = prov.setter("calls", rid, "operation")
            ok = who == provenance.SNAPSHOT or (who is not None and _is_re_read(who, prov, reg, ws, unit, row,
                                                                                to_unit, units))
            problem = None if ok else (
                f"{call} labelled disputed with no re-read behind it in the transcripts: a session that ran no shell, "
                f"opened {row.get('source', '') or 'the lines the call cites (it cites none, so it cannot be disputed)'}"
                + (f", opened {to_unit}'s code" if to_unit in units else "")
                + f" and wrote the label into units/{unit}/calls.csv, and nothing else"
                + (f" but units/{to_unit}/operations.csv" if to_unit in units else ""))
        out.append({"call": call, "to_unit": to_unit, "why": why, "resolved": problem is None,
                    "calling_side_only": not to_unit and not _corrected_only(to_unit, why, units), "problem": problem})
    return out


def reread_check(reg, call, transcripts=None):
    """(passed, line) for one call's re-read: passes when the merge now matches it, or it is resolved as disputed."""
    reg = pathlib.Path(reg)
    call = call[len("call:"):] if call.startswith("call:") else call  # the job item's name, as jobs.py fills {item}
    unit, _, rid = call.partition("/")
    if not rid or _call_row(reg, unit, rid) is None:
        return False, f"{call}: no such call in units/{unit}/calls.csv"
    got = next((r for r in rereads(reg, transcripts) if r["call"] == call), None)
    if got is None:
        return True, f"{call}: matched by the merge"
    return got["resolved"], f"{call}: " + ("re-read and labelled disputed" if got["resolved"] else got["problem"])


def _take(argv, flag):
    if flag not in argv:
        return None
    i = argv.index(flag)
    value = argv[i + 1] if i + 1 < len(argv) else None
    del argv[i:i + 2]
    return value


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    argv = list(argv)
    call, transcripts = _take(argv, "--reread-check"), _take(argv, "--transcripts")
    if call is not None:
        if len(argv) != 1:
            print(__doc__)
            return 2
        ok, line = reread_check(argv[0], call, transcripts)
        print(line)
        return 0 if ok else 1
    is_check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if len(args) != 1:
        print(__doc__)
        return 2
    if not is_check:
        import run_lock  # the register is written by one run at a time
        run_lock.guard(args[0])
    summary, problems = (check if is_check else merge)(args[0])
    print(json.dumps(summary))
    for p in problems:
        print("PROBLEM: " + p)
    if is_check:
        print("merge check: " + ("ok" if not problems else f"FAILED, {len(problems)} problem(s)"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
