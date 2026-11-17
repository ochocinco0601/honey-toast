"""Record the person's go on the plan as data the run follows: scope.json, and the checks per finding in
run-settings.json.

Usage: python go.py <register folder> --flow "<the flow to start with>" --words "<their go, verbatim>"
                    [--in <service,...> --out <service,...>] [--judges N] [--given "<when>"] [--test]
       python go.py <register folder> --stage-ids <id,...>      once the stages are cut (Phase 2)
       python go.py <register folder> --depth "<id>=measure|alerting|runbooks,..."   how far each stage goes, once
                                                                  cut; a stage not named is mapped only
       python go.py <register folder> --add-flow "<name>" --words "<their words>"   at the offer of the next flow:
                                                                  a flow the first look missed, added to the list
       python go.py <register folder> --mapping-ends <flow id>     the mapping skill run alone, at its map stop: the
                                                                  phases after mapping set not picked, so the flow
                                                                  counts finished and the next flow can be offered
       python go.py <register folder> --measures-reviewed --decision go|changes --words "<their answer, verbatim>"
                    [--given] [--test]                            their review of the proposed measures (phase 4's
                                                                  stop, before any alert): `go` keeps a snapshot of
                                                                  the flow's own rows, and only `go` closes it
       python go.py <register folder> --back-to-measures <correction id,...>   a later step needs a measure: the
                                                                  open corrections it filed to proposing the measures'
                                                                  tables take the run back to phase 4 and the review
                                                                  of the measures, then on to where it was
       python go.py <register folder> --alerts-reviewed --decision go|changes --words "<their answer, verbatim>"
                    [--given] [--test]                            their review of the proposed alerts (phase 5):
                                                                  only `go` closes the review
       python go.py <register folder> --answers <answers file> [--test]   the person's picks from the page, as
                                                                  ask-on-a-page saves them: refused unless their
                                                                  choice_id is the open choice's in depth.json now;
                                                                  recorded as --flow or --depth, words verbatim;
                                                                  its topics (talk:* and talk-words:*) go into
                                                                  RUN.md verbatim, never into the pick, and a post
                                                                  of topics alone records them alone

The go asks only which flow comes first. The services read are the first look's recommendation (orientation.json),
else every surveyed service, and the checks per finding the kit's default of three: shown, never asked. Given, `--in` and
`--out` override the services: every service in survey.csv (kind `service`) is then named once; a name the survey
does not have, a service left unnamed, or one named both ways is refused and nothing is written. `--stages` is
refused: the stages are picked after mapping (`--depth`). `--test` labels a go given by a
test standing in for the person. Every run checks every finding that cites code (judges.py, run_status.py's split
checks), so the go writes `judges` into run-settings.json, keeping its other settings: `--judges` when the person
gives a number, else three. `--stage-ids`
adds the ids of exactly the stages the person named, each a stage in stages.csv. Each call prints the line for
RUN.md's `- **Scope:**`. Exit 0 written, 2 refused. Python standard library only."""
import argparse
import csv
import datetime
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import register_layout as layout  # noqa: E402
import run_lock  # noqa: E402


OTHER_FLOWS = "other_flows"  # every flow started in this register but the one worked now, by its name at the go
IN_UNITS = "mapped_in_units"  # in a flow's record, set by its go: it is read in units and every finding judged; a
# flow an earlier release took the go of has none, and keeps the sample of ten it drew
EARLIER = "earlier-flows"  # earlier-flows/<flow id>/<table>.csv: a finished flow's rows as they were when the next began
KEPT_TABLES = ("flows", "stages", "steps", "subjects", "participation", "lifecycle", "measures", "expectations",
               "failure-modes", "remedies", "step-impact", "case-attributes", "agent-system", "measure-gaps", "alerts")
# not kept: about, sources, how-made, capabilities, product-names and set-aside describe the whole map and grow with it
IDS = (("flows", "flow_id"), ("stages", "stage"), ("steps", "step"), ("subjects", "subject_id"),
       ("lifecycle", "move_id"), ("expectations", "expectation_id"), ("failure-modes", "mode_id"),
       ("remedies", "remedy"), ("measures", "handle"))


# the columns that name one row of a table where its first column does not (a part's work on each step, a flow's
# attributes, a part's gaps, a step's impacts): a sampled or corrected row is named by all of them
ROW_KEYS = {"participation": ("subject_id", "step", "operation"), "case-attributes": ("flow", "attribute"),
            "measure-gaps": ("element", "question"), "step-impact": ("step", "impact_category"),
            "agent-system": ("agent", "id")}
CORRECTIONS, APPLIED = "corrections.csv", "corrections-applied.csv"
APPLIED_COLS = ("correction_id", "table", "row", "column", "before", "after", "why", "source", "applied_at", "unit",
                "words")  # `words`: the person's own words on a row they add (--added), recorded with it
REMOVED = "(row removed)"  # `after` of a recorded removal
# The message each kind of answer answers, as the run keeps it (brief.py writes them when it renders the stop).
SHOWN_FILES = {"flow": "flows-brief.md", "next flow": "next-flow.md", "depth": "depth-pick.md",
               "measures review": "measures-review.md", "alerts review": "alert-review.md"}


def said_back_since(reg, since):
    """The lines of the say-back the person last answered, when that is their latest answer and came after `since`
    (a file's time), else None."""
    import case
    from datetime import datetime
    d = case.decisions(reg)
    if not d or d[-1].get("stop") != "say-back":
        return None
    try:
        at = datetime.fromisoformat(d[-1]["at"]).timestamp()
    except (KeyError, ValueError):
        return None
    return d[-1].get("shown") if at >= since else None


def record_decision(reg, stop, words, source, test=False, shown=None):
    """One answer of the person's, appended to the case's decisions with the text they were answering: the kept
    message of that stop, or, where the run keeps none, a line saying so."""
    import case
    if shown is None and stop in SHOWN_FILES:
        p = pathlib.Path(reg) / SHOWN_FILES[stop]
        shown = p.read_text(encoding="utf-8") if p.is_file() else None
        if stop == "next flow":  # a session coming back offers the next flow in its say-back, newer than any offer
            said = said_back_since(reg, p.stat().st_mtime if p.is_file() else 0)
            shown = said if said is not None else shown
    if shown is None:
        shown = f"(not kept: the run keeps no copy of the message answered at the {stop} stop)"
    case.decide(reg, stop, shown, (words or "").strip(), source, test=test)
JUDGED = "judged"  # earlier-flows/<flow id>/judged/: a finished flow's judged rows, unit and lead tables


def row_key(table, r):
    """A row's name in its table: its key columns' values, joined by ' · ' (the first column's alone for most)."""
    cols = ROW_KEYS.get(table) or list(r)[:1]
    return " · ".join((r.get(c) or "").strip() for c in cols if (r.get(c) or "").strip())


def table_rows(reg, table):
    """(columns, rows) of a register table, or ((), []) when it is not there."""
    p = pathlib.Path(reg) / f"{table}.csv"
    if not p.is_file():
        return (), []
    with p.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return tuple(r.fieldnames or ()), list(r)


def keep_finished_flow(reg, done, others):
    """A copy of every row the map holds when the next flow begins, under earlier-flows/<the finished flow's id>/, so
    the done check can show none of them changed: in flows.csv, the finished flows' rows only. In a split run, also
    its unit tables (earlier-flows/<id>/judged/units/) and the merge's resolution of every row (merge/ids.csv), which
    every later merge reuses."""
    reg = pathlib.Path(reg)
    if (reg / layout.UNITS_CSV).is_file():
        import merge
        merge.write_record(reg)  # refused, before anything is written, unless the root is the merge's own output
    fid = record_key(reg, done)
    finished = {flow_id_of(reg, s) for s in list(others.values()) + [done]} - {""}
    out = reg / EARLIER / fid
    out.mkdir(parents=True, exist_ok=True)
    for table in KEPT_TABLES:
        p = reg / f"{table}.csv"
        if not p.is_file():
            continue
        if table != "flows":
            (out / p.name).write_bytes(p.read_bytes())
            continue
        cols, rows = table_rows(reg, table)
        with (out / p.name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(r for r in rows if (r.get("flow_id") or "").strip() in finished)
    keep_judged_rows(reg, fid)


def keep_judged_rows(reg, fid):
    """earlier-flows/<fid>/judged/: every judged table's rows as the finished flow leaves them, the record of which rows
    are a finished flow's (a later flow judges none of them): the unit tables (units/<unit>/), mapping's lead tables at
    the root, `capabilities` and `set-aside` included (judges.FLOW_TABLES), and the lead's own rows
    (merge/lead-rows/)."""
    reg = pathlib.Path(reg)
    out = reg / EARLIER / fid / JUDGED
    copies = []
    units = reg / layout.UNITS
    for folder in sorted(p for p in units.iterdir() if p.is_dir()) if units.is_dir() else []:
        for table in layout.UNIT_TABLES:  # files.csv is never judged nor kept
            copies.append((folder / f"{table}.csv", out / layout.UNITS / folder.name / f"{table}.csv"))
    copies.append((reg / layout.UNITS_CSV, out / layout.UNITS / "units.csv"))  # the list units.py keeps (units.baseline)
    import judges
    for table in judges.FLOW_TABLES:
        copies.append((reg / f"{table}.csv", out / f"{table}.csv"))
    for table in sorted(judges.MERGED):
        copies.append((reg / layout.LEAD_ROWS / f"{table}.csv", out / layout.LEAD_ROWS / f"{table}.csv"))
    for p, to in copies:
        if p.is_file():
            to.parent.mkdir(parents=True, exist_ok=True)
            to.write_bytes(p.read_bytes())


def _snapshot(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return tuple(r.fieldnames or ()), list(r)


def _gone(old, now_rows, table, fixes, fid, name, key_of, disputed_ok=None):
    """The rows of `old` not in `now_rows` as they were, nor as recorded corrections make them, nor recorded removed,
    nor (`disputed_ok`, a finished call of a unit) the same row with only `disputed: ` put before its operation by a
    re-read the merge's re-read check credits."""
    cols, old = old
    now, out = {}, []
    for row in now_rows:
        key = tuple(row.get(c) or "" for c in cols)
        now[key] = now.get(key, 0) + 1
    for row in old:
        key = tuple(row.get(c) or "" for c in cols)
        fixed = tuple(corrected(table, row, fixes, key_of(row)).get(c) or "" for c in cols)
        labelled = None
        if disputed_ok is not None and "operation" in cols and not (row.get("operation") or "").startswith("disputed:"):
            labelled = tuple(("disputed: " + (row.get(c) or "")) if c == "operation" else (row.get(c) or "")
                             for c in cols)
        hit = key if now.get(key) else fixed if now.get(fixed) else None
        if not hit and labelled and now.get(labelled) and disputed_ok(key_of(row)):
            hit = labelled
        if hit:
            now[hit] -= 1
        elif not removed(fixes, key_of(row)):
            out.append((name, row, fid))
    return out


def _resolved_calls(reg):
    """A test, once per register, whether merge.rereads resolves the call `<unit>/<row_id>` (read only when asked)."""
    got = {}

    def ok(call):
        if "calls" not in got:
            import merge
            got["calls"] = {c["call"] for c in merge.rereads(reg) if c["resolved"]}
        return call in got["calls"]
    return ok


def changed_rows(reg):
    """[(table, the row as it was, the finished flow's id)]: each row of a finished flow no longer in the map as it was,
    a correction or a removal recorded in corrections-applied.csv apart. A unit row of a split run is named
    `units/<unit>/<table>` and matched by its unit and row_id. The one change a finished unit row may take unrecorded
    is the `disputed: ` label on a call's operation, and only once the merge's re-read check resolves that call (an
    unmatched call's re-read, merge.py)."""
    reg = pathlib.Path(reg)
    out = []
    resolved = _resolved_calls(reg)
    for kept in sorted((reg / EARLIER).glob("*/")) if (reg / EARLIER).is_dir() else []:
        for snap in sorted(kept.glob("*.csv")):
            out += _gone(_snapshot(snap), table_rows(reg, snap.stem)[1], snap.stem,
                         applied_corrections(reg, snap.stem), kept.name, snap.stem,
                         lambda r, t=snap.stem: row_key(t, r))
        judged = kept / JUDGED / layout.UNITS
        for snap in sorted(judged.glob("*/*.csv")) if judged.is_dir() else []:
            unit, table = snap.parent.name, snap.stem
            out += _gone(_snapshot(snap), table_rows(reg / layout.UNITS / unit, table)[1], table,
                         applied_corrections(reg, table, unit), kept.name, f"{layout.UNITS}/{unit}/{table}",
                         lambda r: (r.get("row_id") or "").strip(),
                         (lambda rid, u=unit: resolved(f"{u}/{rid}")) if table == "calls" else None)
    return out


def applied_corrections(reg, table, unit=""):
    """The corrections applied to a table's rows (corrections-applied.csv), in the order applied: a root table's
    (`unit` blank), or one unit's table's in a split run."""
    return [r for r in table_rows(reg, "corrections-applied")[1]
            if r.get("table") == table and (r.get("unit") or "").strip() == unit]


def corrected(table, row, fixes, key=None):
    """`row` with every recorded correction to it applied, each where the cell still holds what it held before. A row
    is named by its key columns, or by `key` when given (a unit row's row_id)."""
    out, key = dict(row), row_key(table, row) if key is None else key
    for f in fixes:
        if f.get("row") == key and f.get("column") in out and out[f["column"]] == f.get("before"):
            out[f["column"]] = f.get("after", "")
    return out


def removed(fixes, key):
    """A removal of the row named `key` is recorded among `fixes`."""
    return any(f.get("row") == key and f.get("after") == REMOVED and not (f.get("column") or "").strip()
               for f in fixes)


def added_row(fixes, key):
    """{column: cell} of the unit row named `key` as its addition is recorded among `fixes` (the latest), or None."""
    for f in reversed(fixes):
        if f.get("row") != key or (f.get("column") or "").strip() or f.get("before"):
            continue
        try:
            got = json.loads(f.get("after") or "")
        except ValueError:
            continue
        if isinstance(got, dict):
            return {str(c): str(v or "") for c, v in got.items()}
    return None


def added_words(fixes, key):
    """The person's words recorded with the latest addition of the unit row named `key` (go.py --added), or '' (none
    recorded: an addition nobody stands behind)."""
    for f in reversed(fixes):
        if f.get("row") == key and not (f.get("column") or "").strip() and not f.get("before") \
                and f.get("after") != REMOVED:
            return (f.get("words") or "").strip()
    return ""


def _typed(text):
    return " ".join(str(text).split())


def person_said(reg, words, transcripts=None):
    """(True, searched) when `words` (whitespace collapsed) appear in text the person typed into a session after the
    go of the flow worked now, else (False, searched): a user turn of a main session's transcript (never a subagent's,
    whose first message is the lead's prompt), its own text only (no tool result, which can echo this script's own
    output; no meta line nor compact summary, which the session wrote). `searched` names the transcripts read, or the
    folders when none was there. The transcripts are Claude Code's, found as the reading check finds them
    (BFO_TRANSCRIPTS, else the workspace's project folders), or `transcripts` when given."""
    import judges  # it imports this module
    folders = [pathlib.Path(f) for f in judges._folders(reg, transcripts)]
    mains = [f for folder in folders for f in sorted(folder.rglob("*.jsonl"))
             if "subagents" not in f.parts[len(folder.parts):]]
    searched = [f.as_posix() for f in mains] or [f.as_posix() for f in folders]
    want, since = _typed(words), judges.go_given(reg)
    if not want:
        return False, searched
    for f in mains:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(d, dict) or d.get("type") != "user" or d.get("isMeta") \
                        or d.get("isCompactSummary") or d.get("isSidechain"):
                    continue
                m = d.get("message")
                content = m.get("content") if isinstance(m, dict) else None
                text = content if isinstance(content, str) else " ".join(
                    b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")
                if want not in _typed(text):
                    continue
                if since is not None:
                    try:
                        ts = str(d.get("timestamp") or "")
                        at = datetime.datetime.fromisoformat(ts.rstrip("Z"))
                        at = at.replace(tzinfo=datetime.timezone.utc) if ts.endswith("Z") and not at.tzinfo else at
                    except ValueError:
                        continue
                    if (at if at.tzinfo else at.astimezone()) <= since:
                        continue
                return True, searched
    return False, searched


def _not_said(words, searched):
    shown = ", ".join(searched[:5]) + (f" and {len(searched) - 5} more" if len(searched) > 5 else "")
    return (f"the words {words.strip()!r} are not in anything the person typed into a session after the go: searched "
            f"the person's turns in {shown or 'no transcript (none found)'}. Give their words exactly as they typed "
            "them; a change the session itself needs to a unit row goes to that unit's fixer (readers.py prompt "
            "<register> <unit> --mode stop --reason \"<what is wrong>\")")


def apply_correction(reg, cid, value=None, added=False, remove=False, words=None, transcripts=None):
    """A correction filed in corrections.csv (by a flow's re-read, or by any later step), applied to the map by script
    and recorded (corrections-applied.csv: which correction, the row, the column, what it held and holds, why, its
    source, when, and the unit), so a finished flow's row changes only so, and the freeze accepts exactly that
    change. One that removes a row removes it here (--removed), recorded with the row as it was. A correction naming a
    `unit` is to that unit's table in a split run, its row named by row_id.

    A unit row reaches the map only through a typed reader or fixer, or as the person states it. So every correction to a unit's table (a cell, a removal, an added row) is the person's
    route alone: it is refused without their words (`words`, recorded with it), and refused unless those words are in
    text the person typed into a session after the go (person_said, which names the transcripts it searched). A change
    the session itself finds a unit row needs is never made so: it goes to that unit's fixer (readers.py --mode
    stop). A unit row it adds is written here, by this script, from `value` (the row as one CSV line in the table's
    columns, its row_id the one the correction names), never by the lead; one already in the file is refused, since
    nothing but this script may have put it there. Its content is recorded (`after`, as JSON): provenance.py accepts
    that row as recorded and credits it to the person's words, with any later recorded correction to it, or as a
    later Edit the transcripts show changed it, and as nothing else; it is still judged, and its unit still owes the
    reading check. A root row it adds (a lead table's) is recorded with the person's words, checked the same way; a
    root cell correction (a lead table's, the session's own rows) takes words only when given, and checks them then."""
    reg = pathlib.Path(reg)
    cols, filed = table_rows(reg, "corrections")
    c = next((r for r in filed if (r.get("correction_id") or "").strip() == cid), None)
    if c is None:
        return f"no correction {cid} in {CORRECTIONS}"
    if (c.get("status") or "").strip() == "applied":
        return f"{cid} is applied already"
    table, column = (c.get("table") or "").strip(), (c.get("column") or "").strip()
    unit = (c.get("unit") or "").strip()
    now = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    rec = {"correction_id": cid, "table": table, "row": (c.get("row") or "").strip(), "column": column,
           "before": "", "after": "(a row added)", "why": c.get("why", ""), "source": c.get("source", ""),
           "applied_at": now, "unit": unit, "words": ""}
    if unit:
        if table not in layout.UNIT_TABLES:
            return f"{cid} names unit {unit}, whose tables are {', '.join(layout.UNIT_TABLES)}, not {table!r}"
        home = layout.unit_dir(reg, unit)
        if not (home / f"{table}.csv").is_file():
            return f"{cid} names units/{unit}/{table}.csv, which the register does not have"
    else:
        home = reg
        if remove and table in ("subjects", "participation") and (reg / layout.UNITS_CSV).is_file():
            return (f"in a split run {table}.csv is the merge's output: remove the unit row it comes from (a "
                    f"correction naming its unit and row_id), and the merge withdraws the map's row and records it")
    if remove and (value is not None or added):
        return "--removed takes no --value and no --added: it removes the row named, whole"
    if (added or unit) and not (words or "").strip():
        what = "--added" if added else "a correction to a unit's row"
        return (f"{what} is the person's route alone, and --words is required: their words on the change, word for "
                "word, as they typed them. A unit row you found missing or wrong yourself goes to that unit's fixer "
                "(readers.py prompt <register> <unit> --mode stop --reason \"<what is wrong>\"), never in by your hand")
    if (words or "").strip():
        said, searched = person_said(reg, words, transcripts)
        if not said:
            return _not_said(words, searched)
        rec["words"] = words.strip()
    if added and unit:  # this script writes the row, from the person's correction: never the lead
        tcols, trows = table_rows(home, table)
        if any(rec["row"] and (r.get("row_id") or "").strip() == rec["row"] for r in trows):
            return (f"units/{unit}/{table}.csv holds row_id {rec['row']!r} already: a row the person adds is written "
                    "by go.py --added alone, so a row put there by any other hand is not theirs to record")
        if value is None:
            return (f"--value is required: the row {cid} adds, as one CSV line in the columns of units/{unit}/"
                    f"{table}.csv ({','.join(tcols)})")
        cells = next(csv.reader([value]), [])
        if len(cells) != len(tcols):
            return (f"the row is {len(cells)} cell(s), and units/{unit}/{table}.csv has {len(tcols)} columns "
                    f"({','.join(tcols)})")
        new = dict(zip(tcols, cells))
        if (new.get("row_id") or "").strip() != rec["row"]:
            return f"the row's row_id is {new.get('row_id', '')!r}, and {cid} names {rec['row']!r}"
        with (home / f"{table}.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=tcols, lineterminator="\r\n")
            w.writeheader()
            w.writerows(trows + [new])
        rec.update(column="", before="", after=json.dumps(new, ensure_ascii=False))
    if not added:
        if value is None and not remove:
            return "--value is required: the cell's new value, as the correction proposes it"
        tcols, trows = table_rows(home, table)
        if not remove and column not in tcols:
            return f"{table}.csv has no column {column!r}"
        def flat(text):
            return " ".join(text.replace(" · ", " ").split()).lower()
        if unit:  # a unit row is named by its row_id, and nothing else
            hits = [r for r in trows if rec["row"] and (r.get("row_id") or "").strip() == rec["row"]]
        else:
            hits = [r for r in trows if rec["row"] and flat(row_key(table, r)) == flat(rec["row"])]  # the key, whole
        if not hits and not unit:  # else its key cells named among other words ("S03 step 1")
            words = [w for w in re.split(r"\s+", rec["row"]) if w and w.lower() not in {c.lower() for c in tcols}]
            hits = [r for r in trows if words and all(w in row_key(table, r).split(" · ") for w in words)]
        if len(hits) != 1:
            where = f"units/{unit}/{table}.csv" if unit else f"{table}.csv"
            how = "row_id" if unit else ", ".join(ROW_KEYS.get(table) or tcols[:1])
            return (f"{cid} names {'no row' if not hits else 'more than one row'} of {where} ({rec['row']!r}): "
                    f"name the row by its key columns ({how}) in {CORRECTIONS}")
        target = hits[0]
        key = (target.get("row_id") or "").strip() if unit else row_key(table, target)
        if remove:
            rec.update(row=key, column="", before=json.dumps(target, ensure_ascii=False), after=REMOVED)
            trows = [r for r in trows if r is not target]
        else:
            rec.update(row=key, before=target[column], after=value)
            target[column] = value
        with (home / f"{table}.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=tcols, lineterminator="\r\n")
            w.writeheader()
            w.writerows(trows)
    record_applied(reg, [rec])
    for r in filed:
        if (r.get("correction_id") or "").strip() == cid:
            r["status"] = "applied"
    with (reg / CORRECTIONS).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(filed)
    return rec


def record_applied(reg, recs):
    """Append records to corrections-applied.csv, keeping every record already there."""
    _, done = table_rows(reg, "corrections-applied")
    with (pathlib.Path(reg) / APPLIED).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=APPLIED_COLS, lineterminator="\r\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(done + list(recs))


def record_report(reg, fid):
    """A flow's report sent: recorded in its record, once its re-read has passed (a register mapped in units draws no
    sample: its findings are judged with its outputs)."""
    import reread
    reg = pathlib.Path(reg)
    s = next((x for x in load_all(reg) if flow_id_of(reg, x) == fid), None)
    if s is None:
        return f"no flow {fid} is started in this register"
    sheet = reread.sheet_for(reg, s)
    import run_status
    if load(reg).get("flow") == s.get("flow") and not run_status.outputs_hold(reg):
        return (f"the flow {s.get('flow', fid)}'s outputs are not done on the map as it is: run the done check, then "
                "send the report")
    if run_status.owes_sample(reg, s) and (not sheet.is_file() or not reread.check_sheet(reg.resolve(), sheet).passed):
        return (f"the flow {s.get('flow', fid)}'s re-read has not passed, and its report waits on it: finish the "
                "re-read, then send the report")
    import brief  # a report with flows left ends on the offer of the next flow
    if load(reg).get("flow") == s.get("flow") and brief.next_ready(reg) and not brief.next_flow_recommended(reg):
        return ("the first look found flows still to map, and the report ends on the offer of the next flow: render "
                "it with brief.py next --after, send it at the end of the report, then record the report")
    s["report_sent"] = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    cur = load(reg)
    if cur.get("flow") == s.get("flow"):
        save(reg, s)
    else:
        others = dict((read_raw(reg) or {}).get(OTHER_FLOWS) or {})
        others[s.get("flow", "")] = s
        save(reg, cur, others)
    return s


def earlier_rows_changed(reg):
    """Each row of a finished flow no longer in the map as it was, for the done check: '<table>.csv: <its id> of flow
    <id>'."""
    return [f"{t}.csv: {next(iter(r.values()), '')} of flow {fid}" for t, r, fid in changed_rows(reg)]


def alert_owners(reg):
    """{handle: the id of the flow that made the alert}: the flow its measure was proposed for (measures.csv
    `for_flow`), for every alert proposed. An alert on a part's measure is that flow's decision; a further flow that
    measures the same part has a measure row, and any alert, of its own."""
    reg = pathlib.Path(reg)
    made = {(r.get("handle") or "").strip(): (r.get("for_flow") or "").strip() for r in rows(reg / "measures.csv")}
    return {h: made[h] for h in ((r.get("handle") or "").strip() for r in rows(reg / "alerts.csv")
                                 if (r.get("alert") or "").strip().lower().startswith("yes"))
            if made.get(h)}


def reused(reg):
    """[(table, column, id, [the rows that share it])]: each id the map uses twice. A further flow's ids continue
    after the highest the map holds, so none is one an earlier flow already uses."""
    out = []
    for table, col in IDS:
        by = {}
        for r in table_rows(reg, table)[1]:
            v = (r.get(col) or "").strip()
            if v:
                by.setdefault(v, []).append(r)
        out += [(table, col, v, rs) for v, rs in by.items() if len(rs) > 1]
    return out


def reused_ids(reg):
    """Each id the map uses twice, for the done check: '<table>.csv: <column> <id> used twice'."""
    return [f"{t}.csv: {c} {v} used twice" for t, c, v, _ in reused(reg)]



def read_raw(reg):
    p = pathlib.Path(reg) / layout.SCOPE
    if not p.is_file():
        return None
    got = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(got, dict):
        raise ValueError(f"{p}: not a JSON object")
    return got


def load(reg):
    """The record of the flow worked now (its go, pick and review), or None when no go is recorded. A register holds
    flow after flow: the one worked now is at the top of scope.json and every other under `other_flows`, so a record
    an earlier release wrote, of one flow, is already in this form."""
    got = read_raw(reg)
    return None if got is None else {k: v for k, v in got.items() if k != OTHER_FLOWS}


def load_all(reg):
    """Every flow's record in this register: the others in the order they were started, then the one worked now."""
    got = read_raw(reg)
    if got is None:
        return []
    return [s for s in (got.get(OTHER_FLOWS) or {}).values() if isinstance(s, dict)] + [load(reg)]


def save(reg, s, others=None):
    """Write `s` as the record of the flow worked now, keeping every other flow's record (or `others`, when given)."""
    if others is None:
        others = (read_raw(reg) or {}).get(OTHER_FLOWS) or {}
    out = {k: v for k, v in s.items() if k != OTHER_FLOWS}
    if others:
        out[OTHER_FLOWS] = others
    write(pathlib.Path(reg), layout.SCOPE, json.dumps(out, indent=1) + "\n")


def flow_id_of(reg, s):
    """The id in flows.csv of the flow `s` records: the id bound at the pick, else the flow named so."""
    if not s:
        return ""
    if s.get("flow_id"):
        return s["flow_id"]
    name = (s.get("flow") or "").strip().lower()
    return next(((r.get("flow_id") or "").strip() for r in rows(pathlib.Path(reg) / "flows.csv")
                 if name and (r.get("name") or "").strip().lower() == name), "")


def record_key(reg, s):
    """The id a flow's records are kept under (earlier-flows/<id>/, `started_from`): its id in flows.csv, else its name
    made safe for a folder name; "" when there is no record."""
    if not s:
        return ""
    return flow_id_of(reg, s) or re.sub(r"[^A-Za-z0-9]+", "-", s.get("flow", "flow")).strip("-")


JUDGED_AS = "judged_as"  # the key a flow's verdicts were written under before the pick bound its id to another


def flow_key(reg, s):
    """The flow as a verdict file's `flow` names it: its record key (record_key), or, when the pick bound an id other
    than the key the flow was judged under (the walk named it afresh), that earlier key, so no verdict stops counting."""
    if not s:
        return ""
    return s.get(JUDGED_AS) or record_key(reg, s)


def stages_of(reg, s):
    """The stage ids in stages.csv of the flow `s` records: those of its flow id; failing that, every stage no other
    flow's pick names (a register of one flow, or one whose stages name no flow)."""
    known = [r["stage"].strip() for r in rows(pathlib.Path(reg) / "stages.csv") if (r.get("stage") or "").strip()]
    flow_of = {r["stage"].strip(): (r.get("flow") or "").strip() for r in rows(pathlib.Path(reg) / "stages.csv")
               if (r.get("stage") or "").strip()}
    fid = flow_id_of(reg, s)
    mine = [sid for sid in known if fid and flow_of[sid] == fid]
    if mine:
        return mine
    others = {sid for o in load_all(reg)[:-1] if o.get("flow") != (s or {}).get("flow") for sid in (o.get("depth") or {})}
    return [sid for sid in known if sid not in others]


def depth_all(reg):
    """{stage: depth} over every flow picked in this register (a stage belongs to one flow), or None when no flow's
    depth has been picked."""
    out = {}
    for s in load_all(reg):
        if isinstance(s.get("depth"), dict):
            out.update(s["depth"])
    return out or None


def record_of(reg, flow_id):
    """The record of the flow whose id in flows.csv is `flow_id`, or the one worked now when none matches."""
    return next((s for s in load_all(reg) if flow_id and flow_id_of(reg, s) == flow_id), None) or load(reg)


def run_finished(reg):
    """The flow worked now is finished, so the next can open: every phase before the last done or passed over, and
    the last passed over (the mapping skill run alone) or its done check passed on everything but the sampled re-read,
    on the map as it is. The re-read gates the run's DONE and its report, never the next flow. In a split run, a flow
    ended at the map is finished only while the split checks' verdict stored at its end holds (run_status
    .mapping_check_holds): no flow is finished unjudged, whichever way it ends."""
    import brief
    import run_status
    ph = brief.phases(pathlib.Path(reg))
    if not ph:
        return False
    last, before = ph[-1], ph[:-1]
    if any(s not in ("done", "not picked") for _, s in before):
        return False
    if last[1] == "not picked":
        return run_status.mapping_check_holds(reg)
    return run_status.outputs_hold(reg)


def split_unheld(reg):
    """For a refusal: why a split run's flow ended at the map is not finished on the map as it is now (its split
    checks, the units not judged named), or '' when that is not why."""
    import brief
    import run_status
    reg = pathlib.Path(reg)
    ph = brief.phases(reg)
    if not ph or ph[-1][1] != "not picked" or run_status.mapping_check_holds(reg):
        return ""
    why = run_status.split_reasons(reg)
    return (". Its split checks no longer hold on the map as it is: "
            + ("; ".join(why) if why else "something they cover changed since its end at the map")
            + "; end its mapping again (--mapping-ends) once they pass")


def flows_left(reg):
    """The flows the first look found, or the person added since, that no go in this register has started, in order."""
    o = pathlib.Path(reg) / layout.ORIENTATION
    found = [f.get("name") for f in (json.loads(o.read_text(encoding="utf-8-sig")).get("flows") or [] if o.is_file()
                                     else []) if f.get("name")]
    started = {s.get("flow") for s in load_all(reg)}
    return [n for n in found if n not in started]


def names(text):
    return [n.strip() for n in (text or "").split(",") if n.strip()]


def rows(p):
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def scope_line(s, reg=None):
    """RUN.md's Scope line: at the go, the flow and the go's words; after the pick, how far each stage goes by stage
    name, in plain words, with the pick's own words."""
    depth = s.get("depth") or {}
    if depth and reg is not None:
        import brief
        p = s.get("depth_picked") or {}
        return (f"- **Scope:** flow {s.get('flow', '')}; their pick after mapping: {brief.depth_said(reg, depth)}. "
                f"In their words: \"{p.get('words', '')}\" "
                f"({'a test pick, given by a test standing in for the person' if p.get('test') else 'the person'}, {p.get('given', '')})")
    stages = (", ".join(f"{k} {v}" for k, v in depth.items()) if depth else
              ", ".join(s.get("stage_ids") or []) or "not yet picked (after the flow is mapped)")
    return (f"- **Scope:** flow {s.get('flow', '')}; stages {stages}. In their words: \"{s.get('words', '')}\" "
            f"({'a test go, given by a test standing in for the person' if s.get('test') else 'the person'}, {s.get('given', '')})")


def write(reg, name, text):
    (reg / name).write_text(text, encoding="utf-8")


DEFAULT_JUDGES = 3  # the kit's default checks per finding, the count run_status.MEASURED_JUDGES is built for


def surveyed_services(reg):
    """The services survey.csv lists (kind `service`), as named there."""
    return [r["service"].strip() for r in rows(pathlib.Path(reg) / "survey.csv")
            if (r.get("kind") or "").strip() == "service" and (r.get("service") or "").strip()]


def got_after(gos, surveyed):
    """{service lower case} of `surveyed` that no go in `gos` named, in or out: its code was got after the go (an
    external dependency's, FILL-STEPS "The order", item 3), and it is in the flow's scope.
    Empty when a go records no `services_out` (written by every go since it was added)."""
    if not gos or any("services_out" not in s for s in gos):
        return set()
    named = {n.strip().lower() for s in gos for k in ("services_in", "services_out") for n in s.get(k) or []}
    return {n.lower() for n in surveyed if n.lower() not in named}


def services_read(reg, s=None):
    """{service lower case} the flow worked now reads (scope.json `services_in`, and every service surveyed after its
    go that it did not leave out), or None when the go names none (every unit is then read)."""
    s = load(reg) if s is None else s
    if not s or "services_in" not in s:
        return None
    took = {n.strip().lower() for n in s.get("services_in") or [] if n.strip()}
    return took | got_after([s], surveyed_services(reg))


def default_services(reg, surveyed, flow=None):
    """(in, out): the kit's own choice of which services to read for `flow`. A flow found that names its services
    (orientation.json `flows[].services`) reads those. Else the first look's recommendation for each service, which
    is written for the flow it recommends, applies to that flow only: any other flow reads every surveyed service.
    The person is shown it, never asked it."""
    o = reg / layout.ORIENTATION
    data = json.loads(o.read_text(encoding="utf-8-sig")) if o.is_file() else {}
    entry = next((f for f in data.get("flows") or [] if f.get("name") == (flow or "").strip()), None)
    named = [n.strip() for n in (entry or {}).get("services") or [] if n.strip()]
    if named:
        return [n for n in surveyed if n in named], [n for n in surveyed if n not in named]
    recommended = (data.get("recommendation") or {}).get("flow")
    if flow is not None and recommended and flow.strip() != recommended:
        return list(surveyed), []
    rec = {s.get("name"): s.get("recommend") for s in data.get("services") or []}
    return [n for n in surveyed if rec.get(n, "in") != "out"], [n for n in surveyed if rec.get(n) == "out"]


def record_go(reg, a):
    """The go after the first look: which flow comes first, and the person's words. Which services are read is the
    kit's to decide: the first look's recommendation, shown to the person and overridden only when the person says so
    (`--in`/`--out`). How many checks each finding gets is the kit's too: three, unless the person gives a number
    (`--judges`), written into run-settings.json for the judging and the done check to read."""
    if a.stages is not None:
        return ("the stages are no longer picked at the go: once the flow is mapped, the person picks how far each "
                "stage goes (go.py --depth)")
    surveyed = [r["service"].strip() for r in rows(reg / "survey.csv")
                if (r.get("kind") or "").strip() == "service" and (r.get("service") or "").strip()]
    if not surveyed:
        return "survey.csv has no service: run survey.py first"
    problems = []
    if a.inn is None and a.out is None:
        inn, out = default_services(reg, surveyed, a.flow)
    else:
        inn, out = names(a.inn), names(a.out)
        unknown = [n for n in inn + out if n not in surveyed]
        both = sorted(set(inn) & set(out))
        unnamed = [n for n in surveyed if n not in inn and n not in out]
        problems = ([f"not a service in survey.csv: {', '.join(unknown)}"] if unknown else []) + \
                   ([f"named both in and out: {', '.join(both)}"] if both else []) + \
                   ([f"named neither in nor out: {', '.join(unnamed)}"] if unnamed else [])
    judges = DEFAULT_JUDGES if a.judges is None else a.judges
    if judges < 1:
        problems.append("--judges must be 1 or more: every finding that cites code is checked")
    required = (("--flow", a.flow),) if getattr(a, "page", False) else (("--flow", a.flow), ("--words", a.words))
    for flag, v in required:  # from the page, the tick is the answer and words are optional
        if not (v or "").strip():
            problems.append(f"{flag} is required")
    remains = {}
    o = reg / layout.ORIENTATION
    if o.is_file() and not problems:
        found = json.loads(o.read_text(encoding="utf-8-sig")).get("flows") or []
        flow = next((f for f in found if f.get("name") == a.flow.strip()), None)
        if flow is None:
            problems.append(f"not a flow found: {a.flow.strip()} (found: {', '.join(f.get('name', '') for f in found)})")
        else:
            remains = {"flows": [f.get("name") for f in found if f is not flow], "services_left_out": out}
    if problems:
        return "; ".join(problems)
    cur, others = load(reg), dict((read_raw(reg) or {}).get(OTHER_FLOWS) or {})
    finished = cur is not None and run_finished(reg)
    name = a.flow.strip()
    if name in others or (finished and cur.get("flow") == name):
        return (f"the flow {name} is mapped and finished already, and a flow is never mapped twice in one register: "
                "to take a stage of it further, record the new pick with --depth")
    if cur and not finished and cur.get("flow") == name and under_way(reg, cur):
        return (f"the flow {name} is under way: its go is recorded and its mapping has begun, so there is no go to "
                "record again; carry on from the first phase that is not done")
    if cur and not finished and cur.get("flow") != name and under_way(reg, cur):
        return (f"the flow {cur.get('flow')} is still under way: its mapping has begun and its phases are not all "
                "done. Finish it, through its done check and report (or, run with the mapping skill alone, its end at "
                "the map: --mapping-ends), and the next flow is then offered; nothing of it is lost when the next "
                "one starts" + split_unheld(reg))
    if remains.get("flows"):  # what remains after this flow: none the register has started already
        started = set(others) | ({cur.get("flow")} if finished else set())
        remains["flows"] = [n for n in remains["flows"] if n not in started]
    s = {"flow": a.flow.strip(), "services_in": inn, "services_out": out,
         "stage_ids": [], "words": a.words.strip(),
         "given": a.given or datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "test": a.test,
         "remains": remains or {"services_left_out": out}, IN_UNITS: True}
    if finished:  # the flow worked until now is done: it is kept whole, and this go starts the next flow
        others[cur.get("flow", "")] = cur
        s["started_from"] = record_key(reg, cur)
        import merge
        unkept = merge.record_problems(reg)
        if unkept:
            return ("the finished flow's merge cannot be kept for the next flow to reuse (" + "; ".join(unkept) + ")")
    p = reg / layout.SETTINGS
    settings = json.loads(p.read_text(encoding="utf-8-sig")) if p.is_file() else {}
    settings["judges"] = judges
    a.judges = judges
    write(reg, layout.SETTINGS, json.dumps(settings) + "\n")
    if finished:
        keep_finished_flow(reg, cur, others)
    save(reg, s, others)
    if finished:
        start_next_flow_in_run_md(reg, cur)
    record_in_run_md(reg, s)
    return s


MAPPING_ROWS = ("1 ", "2 ", "3 ")
AFTER_MAPPING = ("Pick of how far each stage goes", "4 ", "Review of the measures", "5a ", "Review of the alerts", "5b ", "6 ", "7 ")


def row_states(reg):
    """{row lead: status} for the run record's per-flow rows."""
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    out = {}
    for lead in PER_FLOW_ROWS:
        m = re.search(rf"^\| {re.escape(lead)}[^|]*\| ([^|]*)\|", text, re.M)
        if m:
            out[lead] = m.group(1).strip().lower()
    return out


def under_way(reg, s):
    """The flow `s` records has begun past its go: its pick is recorded, a phase after the go is done, or its moves
    are written."""
    fid = flow_id_of(reg, s)
    return (s.get("depth") is not None or any(v in ("done", "not picked") for k, v in row_states(reg).items()
                                              if k != "The go on the plan")
            or bool(fid and any((r.get("flow") or "").strip() == fid for r in table_rows(reg, "lifecycle")[1])))


def mapping_ends(reg, flow_id):
    """The end of the mapping skill run alone, at the map: the flow's id bound (as the map inspection names it), and
    the phases after mapping set not picked, so the flow counts finished and the next flow can be offered. Refused
    until the go is recorded and phases 1 to 3 are done, for an id not in flows.csv, and while an id is used twice or
    a finished flow's row is changed: the done check of a run that ends at the map. In a split run it is refused, too,
    until the split checks pass (every unit's rows judged, the merge, every unmatched call re-read), and their verdict
    is then stored with the fingerprint of the map, its units and its verdict files. Refused, last, while the map's
    drawing would refuse the register (run_status.undrawable)."""
    if load(reg) is None:
        return "no go is recorded: the mapping skill's run begins with the go"
    states = row_states(reg)
    if any(states.get(k) != "done" for k in MAPPING_ROWS):
        return "the map is not done: phases 1 to 3 are done first"
    if flow_id not in {(r.get("flow_id") or "").strip() for r in rows(pathlib.Path(reg) / "flows.csv")}:
        return f"not a flow in flows.csv: {flow_id or '(none given)'}; give the flow's id, as the map inspection names it"
    wrong = reused_ids(reg) + [f"{c}: changed or gone since that flow was finished" for c in earlier_rows_changed(reg)]
    if wrong:
        return ("the map breaks the rules for a further flow (" + "; ".join(wrong) + "): put each finished flow's row "
                "back as it was (a correction goes in corrections.csv) and give each new row an id after the highest")
    import run_status
    if run_status.in_units(reg):  # a go this kit recorded: no flow is finished without units.csv and every row judged
        unjudged = run_status.store_mapping_check(reg, flow_id)
        if unjudged:
            return ("the split run's checks do not pass, and no flow is finished unjudged (" + "; ".join(unjudged)
                    + "): judge every unit's rows, merge, re-read each unmatched call, then end the mapping again")
    import run_status  # the done check's own verdict on a map left mapped only
    owed = run_status.questions_owed_mapped_only(pathlib.Path(reg))
    if owed:
        return ("the map does not answer what the done check asks of a flow left mapped only (view questions not "
                "answered: " + "; ".join(owed) + "): answer each in the register, or write its gap with the reason")
    refused = run_status.undrawable(pathlib.Path(reg))  # the drawing's own check: a map it refuses is not done
    if refused:
        return run_status.cannot_draw_reason(refused) + ": put each right, then end the mapping again"
    record_flow_id(reg, flow_id)
    # Run alone, the pick of how far each stage goes is never asked: the request asked for the map only. That answer
    # is recorded as data (every stage of the flow mapped only, from the request's words), so the done check sees a
    # pick, and owes a mapped-only stage nothing past the map.
    s = load(reg)
    if s.get("depth") is None and stages_of(reg, s):
        s["depth"] = {sid: "none" for sid in stages_of(reg, s)}
        s["depth_picked"] = {"words": (s.get("words") or "").strip(),
                             "given": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
                             "test": bool(s.get("test")), "from_request": True}
        save(reg, s)
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8")
    for lead in AFTER_MAPPING:
        text = re.sub(rf"^(\| {re.escape(lead)}[^|]*\| )[^|]*\|", r"\1not picked |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")
    return load(reg)


EARLIER_FLOWS = "## Earlier flows in this register"
FLOW_LINES = ("Go", "Scope", "Depth picked", "Measures reviewed", "Alerts reviewed")
PER_FLOW_ROWS = ("The go on the plan", "1 ", "2 ", "3 ", "Pick of how far each stage goes", "4 ",
                 "Review of the measures", "5a ",
                 "Review of the alerts", "5b ", "6 ", "7 ")


def start_next_flow_in_run_md(reg, done):
    """RUN.md when the next flow starts: the finished flow's Go, Scope, Depth picked and Alerts reviewed lines kept,
    word for word, under *Earlier flows in this register*; those lines blank again for the next flow; and every phase
    from the go on to do again, as each is done once per flow. Phase 0 (the first look, over the whole capability)
    stays done."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    kept = []
    for label in FLOW_LINES:
        m = re.search(rf"^- \*\*{re.escape(label)}:\*\*.*(?:\n  .*)*$", text, re.M)
        if m:
            kept.append(m.group(0))
            if label in ("Depth picked", "Measures reviewed", "Alerts reviewed"):
                text = text[:m.start()] + f"- **{label}:** _blank until the person answers for this flow._" + text[m.end():]
    block = f"\n### {done.get('flow', '')}\n\n" + "\n".join(kept) + "\n"
    if EARLIER_FLOWS in text:
        head, rest = text.split(EARLIER_FLOWS, 1)
        nxt = rest.find("\n## ")
        text = (head + EARLIER_FLOWS + (rest.rstrip("\n") + "\n" + block if nxt < 0 else
                                        rest[:nxt].rstrip("\n") + "\n" + block + rest[nxt:]))
    else:
        intro = (f"{EARLIER_FLOWS}\n\nEach flow this register has finished, with its go, its pick and its review "
                 "as they were recorded. Its pages and its rows in the tables stay in this register.\n" + block)
        at = text.find("\n## Sources")
        text = text.rstrip("\n") + "\n\n" + intro if at < 0 else text[:at] + "\n\n" + intro + text[at:]
    for lead in PER_FLOW_ROWS:
        text = re.sub(rf"^(\| {re.escape(lead)}[^|]*\| )[^|]*\|[^|]*\|[^|]*\|", r"\1to do | | |", text, count=1,
                      flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


def record_in_run_md(reg, s):
    """RUN.md's Go and Scope lines, the go row done and the first reading phase doing; nothing when there is no RUN.md."""
    p = reg / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    who = "a test go, given by a test standing in for the person" if s.get("test") else "the person"
    text = re.sub(r"^- \*\*Go:\*\*.*$", lambda m: f"- **Go:** {s['words']} ({who}, {s['given']})", text, count=1,
                  flags=re.M)
    text = re.sub(r"^- \*\*Scope:\*\*.*(?:\n  .*)*$", lambda m: scope_line(s), text, count=1, flags=re.M)
    text = re.sub(r"^(\| The go on the plan \| )[^|]*\|", r"\1done |", text, count=1, flags=re.M)
    text = proved_by(text, "The go on the plan", GO_PROOF)
    text = re.sub(r"^(\| 1 The case and its lifecycle \| )to do \|", r"\1doing |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


ALERT_COLS = ("handle", "alert", "guards", "counted_moves")


def alert_fingerprint(reg, flow_id=None):
    """A short hash of one flow's alert choices in alerts.csv: each proposed alert's handle, basis, the expectation it
    guards and the moves it counts. The flow is the measure's: its stage, or its step's, read from measures.csv. A
    measure's own columns do not change it, and nor does another flow's alert. `flow_id` None: the flow worked now."""
    import hashlib
    reg = pathlib.Path(reg)
    s = load(reg) or {}
    fid = flow_id if flow_id is not None else flow_id_of(reg, s)
    mine = set(stages_of(reg, s if flow_id is None else {"flow_id": flow_id}))
    step_stage = {(r.get("step") or "").strip(): (r.get("stage") or "").strip() for r in rows(reg / "steps.csv")}

    owners = alert_owners(reg)
    measure = {(r.get("handle") or "").strip(): r for r in rows(reg / "measures.csv")}

    def of_flow(a):
        r = measure.get((a.get("handle") or "").strip(), {})
        stage = (r.get("stage") or "").strip() or step_stage.get((r.get("step") or "").strip(), "")
        if stage:
            return stage in mine
        made = owners.get((a.get("handle") or "").strip())
        return made == fid if made else (r.get("flow") or "").strip() in ("", fid)
    chosen = sorted("\t".join((r.get(c) or "").strip() for c in ALERT_COLS) for r in rows(reg / "alerts.csv")
                    if (r.get("alert") or "").strip().lower().startswith("yes") and of_flow(r))
    return hashlib.sha256("\n".join(chosen).encode("utf-8")).hexdigest()[:12]


def review_state(reg):
    """(the review row exists in RUN.md, it is done). A register whose run record has no such row is from before
    the alerts were reviewed apart, and is not held to it."""
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    m = re.search(r"^\| Review of the alerts \| ([^|]*)\|", text, re.M)
    return bool(m), bool(m) and m.group(1).strip().lower() == "done"


def review_line(reg, line, row):
    """RUN.md's *Alerts reviewed* line set to `line`, and the review row to `row`; nothing when there is no RUN.md."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    if re.search(r"^- \*\*Alerts reviewed:\*\*", text, re.M):
        text = re.sub(r"^- \*\*Alerts reviewed:\*\*.*(?:\n  .*)*$", lambda m: line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    text = re.sub(r"^(\| Review of the alerts \| )[^|]*\|", rf"\g<1>{row} |", text, count=1, flags=re.M)
    if row == "done":
        text = re.sub(r"^(\| 5b [^|]*\| )to do \|", r"\1doing |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


def reset_review(reg):
    """The alerts were written again: any earlier review no longer covers them."""
    s = load(reg)
    if s and s.pop("alerts_reviewed", None) is not None:
        save(reg, s)
    if review_state(reg)[0]:
        review_line(reg, "- **Alerts reviewed:** _blank until the person answers on the alerts as now proposed._",
                    "doing")


def record_alerts_shown(reg):
    """The fingerprint of the alerts as the review message showed them, kept until the person's answer on them."""
    s = load(reg)
    if s is None:  # no go recorded (an earlier run): there is no scope to keep it in
        return
    s["alerts_shown"] = alert_fingerprint(reg)
    save(reg, s)


def record_review(reg, a):
    if not (a.words or "").strip():
        return "--words is required: their answer on the alerts, word for word"
    if a.decision not in ("go", "changes"):
        return ("--decision is required: go when they accept the alerts and say go on to the runbooks, changes when "
                "they ask for any change")
    who = "a test review, given by a test standing in for the person" if a.test else "the person"
    given = a.given or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    s = load(reg) or {}
    if a.decision == "changes":
        s.pop("alerts_reviewed", None)
        save(reg, s)
        review_line(reg, f"- **Alerts reviewed:** changes asked: {a.words.strip()} ({who}, {given}). The alerts are "
                         "changed and shown again before any runbook.", "to do")
        p = reg / "RUN.md"
        if p.is_file():  # the alerts are reworked now: the run's, not the person's, until it shows them again
            p.write_text(re.sub(r"^(\| 5a [^|]*\| )[^|]*\|", r"\1doing |", p.read_text(encoding="utf-8"), count=1,
                                flags=re.M), encoding="utf-8", newline="\n")
        return s
    shown = s.get("alerts_shown")
    if shown and shown != alert_fingerprint(reg):
        return ("the alerts have changed since they were shown to the person, so their go does not cover them. Show "
                "them the alerts again (brief.py alerts) and record their answer on what they saw")
    s["alerts_reviewed"] = {"words": a.words.strip(), "test": a.test, "alerts": shown or alert_fingerprint(reg),
                            "given": given}
    save(reg, s)
    review_line(reg, f"- **Alerts reviewed:** {a.words.strip()} ({who}, {given})", "done")
    return s


# The person's review of the measures (phase 4's stop, before any alert is chosen): one per flow, with a snapshot of
# the flow's own rows of proposing the measures' tables taken at their go, so the done check names a later change.
MEASURES_TABLES = ("measures", "expectations", "measure-gaps")
# measure-gaps.csv is shared and owned by question: these are mapping's and the
# runbook step's; every other question is proposing the measures' own, so its rows are in the snapshot
OTHER_STEPS_GAPS = ("step: timeouts", "stage: cannot be undone", "stage: other outcomes", "step: trigger",
                    "part: operations", "part: depends on", "step: moves", "alert: its own tests")
MEASURES_ROW = "Review of the measures"


def measures_step_row(table, r):
    """A row proposing the measures writes: every row of measures.csv and expectations.csv, and the rows of
    measure-gaps.csv whose question is not another step's."""
    return table != "measure-gaps" or (r.get("question") or "").strip() not in OTHER_STEPS_GAPS


FOR_FLOW = "for_flow"  # measures.csv: the flow the row was proposed for, written by proposing the measures (MEASURES-STEPS.md) on every row


def measures_owners(reg):
    """{handle: the flow it was proposed for}, as each measures.csv row records it in `for_flow`. A part two flows
    measure has a row for each. Rows that record none (a register no migration has reached) are left out."""
    return {(r.get("handle") or "").strip(): (r.get(FOR_FLOW) or "").strip()
            for r in rows(pathlib.Path(reg) / "measures.csv")
            if (r.get("handle") or "").strip() and (r.get(FOR_FLOW) or "").strip()}


def inferred_for_flow(reg):
    """{handle: flow id}: where a measure sat before `for_flow` was recorded, for reconcile.py --migrate to write
    once: its stage's flow (or its step's stage's), else its `flow`, else the flow whose kept copy first held it (by
    when each flow's go was given), else the flow worked now, else the register's one flow with stages."""
    reg = pathlib.Path(reg)
    stage_flow = {(r.get("stage") or "").strip(): (r.get("flow") or "").strip() for r in rows(reg / "stages.csv")}
    step_stage = {(r.get("step") or "").strip(): (r.get("stage") or "").strip() for r in rows(reg / "steps.csv")}
    kept = {}
    for s in sorted(load_all(reg), key=lambda x: str(x.get("given") or "")):
        fid = flow_id_of(reg, s)
        for r in rows(reg / EARLIER / fid / "measures.csv") if fid else []:
            kept.setdefault((r.get("handle") or "").strip(), fid)
    now = flow_id_of(reg, load(reg) or {})
    single = {f for f in stage_flow.values() if f}
    fallback = now or (single.pop() if len(single) == 1 else "")
    out = {}
    for r in rows(reg / "measures.csv"):
        h = (r.get("handle") or "").strip()
        stage = (r.get("stage") or "").strip() or step_stage.get((r.get("step") or "").strip(), "")
        out[h] = stage_flow.get(stage) or (r.get("flow") or "").strip() or kept.get(h) or fallback
    return out


def measures_rows(reg, flow_id=None):
    """{table: {row key: row}}: the rows of proposing the measures that are the flow's own. A measure is the flow's it
    was proposed for (`for_flow`); an expectation, by its stage's flow, else its `flow`; a gap, by the stage of the
    element it is about (a stage, a step, an expectation, a measure), else, on a part or an operation, it belongs
    to each flow whose coverage list asks that element and question. A row none of these place is the flow worked
    now's. Nothing is read from when a flow's go was given. `flow_id` None: the flow worked now."""
    reg = pathlib.Path(reg)
    now = flow_id_of(reg, load(reg) or {})
    fid = flow_id or now
    stage_flow = {(r.get("stage") or "").strip(): (r.get("flow") or "").strip() for r in rows(reg / "stages.csv")}
    mine = set(stages_of(reg, {"flow_id": fid}))
    step_stage = {(r.get("step") or "").strip(): (r.get("stage") or "").strip() for r in rows(reg / "steps.csv")}
    exps = {(r.get("expectation_id") or "").strip(): r for r in rows(reg / "expectations.csv")}
    meas = {(r.get("handle") or "").strip(): r for r in rows(reg / "measures.csv")}
    flows = {(r.get("flow_id") or "").strip() for r in rows(reg / "flows.csv")}
    owners = measures_owners(reg)
    asked = {}  # (element, question): the flows whose coverage list asks it, read only for a gap on a part

    def askers(key):
        if not asked:
            import contextlib
            import io
            import flow_outputs as fo
            with contextlib.redirect_stdout(io.StringIO()):
                R = fo.load(reg)
                for f in [x for x in flows if x and any(v == x for v in stage_flow.values())]:
                    for r in fo.receipt(R, f):
                        asked.setdefault((r["element"], r["question"]), set()).add(f)
            asked.setdefault(None, set())  # read once, even where nothing is asked
        return asked.get(key, set())

    def of_flow(table, r):
        if table == "measures" and owners.get((r.get("handle") or "").strip()):
            return owners[(r.get("handle") or "").strip()] == fid
        if table == "measure-gaps":
            el = (r.get("element") or "").strip()
            if el in exps:
                return of_flow("expectations", exps[el])
            if el in meas:
                return of_flow("measures", meas[el])
            stage = el if el in stage_flow else step_stage.get(el, "")
            col = el if el in flows else ""
            if not stage and not col:
                who = askers((el, (r.get("question") or "").strip()))
                if who:
                    return fid in who
        else:
            stage = (r.get("stage") or "").strip() or step_stage.get((r.get("step") or "").strip(), "")
            col = (r.get("flow") or "").strip()
        if stage:
            return stage_flow.get(stage) == fid if stage_flow.get(stage) else stage in mine
        return col == fid if col else fid == now
    return {table: {row_key(table, r): r for r in table_rows(reg, table)[1]
                    if row_key(table, r) and measures_step_row(table, r) and of_flow(table, r)}
            for table in MEASURES_TABLES}


def measures_snapshot(reg, flow_id=None):
    """{table: {row key: a digest of the row}}: the flow's own rows of proposing the measures, as kept at its go."""
    def digest(r):
        cells = {c: (v or "").strip() for c, v in r.items() if c}
        return hashlib.sha256(json.dumps(cells, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
    return {t: {k: digest(r) for k, r in got.items()} for t, got in measures_rows(reg, flow_id).items()}


def measures_fingerprint(reg, flow_id=None):
    """A short hash of the flow's snapshot as it is now: what the review message showed."""
    return hashlib.sha256(json.dumps(measures_snapshot(reg, flow_id), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def measures_changed(reg, flow_id=None):
    """Each of the flow's rows of proposing the measures changed, added or gone since the person's go on them, as
    '<table>.csv <row>: changed|added|gone since the review of the measures'; [] when no go is recorded."""
    reg = pathlib.Path(reg)
    fid = flow_id or flow_id_of(reg, load(reg) or {})
    was = ((record_of(reg, fid) or {}).get("measures_reviewed") or {}).get("rows")
    if was is None:
        return []
    now = measures_snapshot(reg, fid)
    out = []
    for t in MEASURES_TABLES:
        a, b = was.get(t) or {}, now.get(t) or {}
        out += [f"{t}.csv {k}: {'changed' if k in b else 'gone'} since the review of the measures"
                for k in a if a[k] != b.get(k)]
        out += [f"{t}.csv {k}: added since the review of the measures" for k in b if k not in a]
    return out


def measures_review_state(reg):
    """(the measures review row exists in RUN.md, it is done). A register whose run record has no such row is from
    before the measures were reviewed apart, and is not held to it."""
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    m = re.search(rf"^\| {MEASURES_ROW} \| ([^|]*)\|", text, re.M)
    return bool(m), bool(m) and m.group(1).strip().lower() == "done"


def set_row(text, lead, status, only_from=None):
    """RUN.md's text with the row `lead` set to `status`, only where it now holds one of `only_from` when given."""
    now = "|".join(re.escape(x) for x in only_from) if only_from else "[^|]*"
    return re.sub(rf"^(\| {re.escape(lead)}[^|]*\| )(?:{now}) \|" if only_from else
                  rf"^(\| {re.escape(lead)}[^|]*\| )[^|]*\|", rf"\g<1>{status} |", text, count=1, flags=re.M)


def measures_review_line(reg, line, row, after=()):
    """RUN.md's *Measures reviewed* line set to `line`, the review row to `row`, then each (lead, status, only_from)
    of `after`; nothing when there is no RUN.md."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    if re.search(r"^- \*\*Measures reviewed:\*\*", text, re.M):
        text = re.sub(r"^- \*\*Measures reviewed:\*\*.*(?:\n  .*)*$", lambda m: line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    text = set_row(text, MEASURES_ROW, row)
    for lead, status, only_from in after:
        text = set_row(text, lead, status, only_from)
    for lead, proof in PROOFS.items():
        text = proved_by(text, lead, proof)
    p.write_text(text, encoding="utf-8", newline="\n")


GO_PROOF = "scope.json; the Go and Scope lines under Plan and go"  # what proves the go row done


# What proves a phase of proposing the measures done, written in RUN.md's "Proved by" cell when the go sets it done
# and the cell is still blank (a run's own words there are kept), so a done phase never leaves it blank.
PROOFS = {"4 ": "expectations.csv, measures.csv, measure-gaps.csv, each picked stage's MEASURES.md; the measures "
                "inspection (check_measures.py)",
          MEASURES_ROW: "measures-review.md (what the person was shown); their words under *Measures reviewed*"}


def proved_by(text, lead, proof):
    """RUN.md's text with the row `lead`'s "Proved by" cell set to `proof`, only when the row is done and the cell
    blank."""
    return re.sub(rf"^(\| {re.escape(lead)}[^|]*\| done \|)\s*\|", lambda m: f"{m.group(1)} {proof} |", text, count=1,
                  flags=re.M)


def reset_measures_review(reg):
    """The flow worked now's measures were proposed again: an earlier review no longer covers them, and the next go
    retakes the snapshot. A review row the pick leaves out stays so."""
    s = load(reg)
    if s and ("measures_reviewed" in s or "measures_shown" in s):
        s.pop("measures_reviewed", None)
        s.pop("measures_shown", None)
        save(reg, s)
    p = pathlib.Path(reg) / "RUN.md"
    if measures_review_state(reg)[0] and not re.search(rf"^\| {MEASURES_ROW} \| not picked \|",
                                                       p.read_text(encoding="utf-8"), re.M):
        measures_review_line(reg, "- **Measures reviewed:** _blank until the person answers on the measures as now "
                                  "proposed._", "to do")


def record_measures_shown(reg):
    """The fingerprint of the flow worked now's measures as the review message showed them, kept until the answer."""
    s = load(reg)
    if s is None:
        return
    s["measures_shown"] = measures_fingerprint(reg)
    save(reg, s)


def measures_requests(reg, status="open"):
    """The rows of corrections.csv that ask proposing the measures for a change (they name one of its tables), with
    this status; every one when `status` is None."""
    return [r for r in table_rows(reg, "corrections")[1] if (r.get("table") or "").strip() in MEASURES_TABLES
            and (status is None or (r.get("status") or "").strip() == status)]


def back_to_measures(reg, ids):
    """A later step (the runbooks, or choosing the alerts) needs a measure proposing the measures did not write: it
    has filed each request in corrections.csv, and the run goes back to phase 4 and the person's review of the
    measures. The rows of the phases after it stay as they are, so after the go the run goes on where it was; an
    alert review is asked again only if an alert changes (its fingerprint)."""
    s = load(reg)
    if s is None:
        return "no go is recorded: the run begins with the go"
    if not ids:
        return "name the correction or corrections that ask proposing the measures for a change"
    filed = {(r.get("correction_id") or "").strip(): r for r in table_rows(reg, "corrections")[1]}
    for cid in ids:
        r = filed.get(cid)
        if r is None:
            return f"{cid}: no correction with this id in corrections.csv: file the request there first"
        if (r.get("table") or "").strip() not in MEASURES_TABLES:
            return (f"{cid} is about {r.get('table') or 'no table'}, not one of proposing the measures' tables "
                    f"({', '.join(MEASURES_TABLES)}): a correction to the map is mapping's, taken up when it runs")
        if (r.get("status") or "").strip() != "open":
            return f"{cid} is not open (status {r.get('status') or 'blank'}): only an open request is taken back"
        if not (r.get("proposed") or "").strip():
            return f"{cid} says nothing in proposed: say what to measure, at which part, and why"
    if not s.get("measures_reviewed"):
        return ("the measures are before their review: proposing the measures takes the request up now, before the "
                "person sees them; there is no later step to come back to")
    was = s["measures_reviewed"]
    s.pop("measures_reviewed", None)
    s.pop("measures_shown", None)
    s["measures_asked"] = {"corrections": ids, "earlier_go": was.get("words", ""),
                           "given": datetime.datetime.now().astimezone().isoformat(timespec="minutes")}
    save(reg, s)
    measures_review_line(reg, "- **Measures reviewed:** _asked again: a later step needs what proposing the measures "
                              f"did not write ({', '.join(ids)} in corrections.csv). Blank until the person answers on "
                              f"the measures as now proposed. Their earlier go: {was.get('words', '')}._", "to do",
                         (("4 ", "doing", None),))
    return s


def record_measures_review(reg, a):
    """The person's answer on the measures: `go` keeps the flow's snapshot; `changes` sends the measures back."""
    if not (a.words or "").strip():
        return "--words is required: their answer on the measures, word for word"
    if a.decision not in ("go", "changes"):
        return ("--decision is required: go when they accept the measures and say go on, changes when they ask for "
                "any change")
    s = load(reg)
    if s is None:
        return "no go is recorded: the run begins with the go"
    if s.get("measures_reviewed"):
        # the review is open only on the first pass, or once proposing the measures is run again (go.py
        # --back-to-measures, flow_outputs.py --measures, a new pick): a change made by a later step clears only so
        return ("the measures already have the person's go, so this review is closed. A later step that needs a "
                "measure asks for it: file it in corrections.csv and take the run back with go.py "
                "--back-to-measures <correction id>; then proposing the measures (the measures skill) takes it up and the "
                "review opens again")
    who = "a test review, given by a test standing in for the person" if a.test else "the person"
    given = a.given or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    if a.decision == "changes":
        s.pop("measures_reviewed", None)
        save(reg, s)
        measures_review_line(reg, f"- **Measures reviewed:** changes asked: {a.words.strip()} ({who}, {given}). The "
                                  "measures are changed and shown again before any alert.", "to do",
                             (("4 ", "doing", None),))
        return s
    still = [(r.get("correction_id") or "").strip() for r in measures_requests(reg)]
    if still:
        return (f"{', '.join(still)} in corrections.csv ask proposing the measures for a change and are still open: "
                "take each up (write the row, and set its status to taken up) or turn it down (status turned down, "
                "the reason in how-made.csv), then show the person the measures again (brief.py measures)")
    shown = s.get("measures_shown")
    if not shown:
        return ("the measures have not been shown to the person: show them (brief.py measures) and record their "
                "answer on what they saw")
    if shown != measures_fingerprint(reg):
        return ("the measures have changed since they were shown to the person, so their go does not cover them. Show "
                "them the measures again (brief.py measures) and record their answer on what they saw")
    s["measures_reviewed"] = {"words": a.words.strip(), "test": a.test, "given": given, "measures": shown,
                              "rows": measures_snapshot(reg)}
    s.pop("measures_asked", None)
    save(reg, s)
    measures_review_line(reg, f"- **Measures reviewed:** {a.words.strip()} ({who}, {given})", "done",
                         (("4 ", "done", None), ("5a ", "doing", ("to do",))))
    return s


def record_stage_ids(reg, ids):
    s = load(reg)
    if s is None:
        return "no scope.json: record the go first"
    known = {(r.get("stage") or "").strip() for r in rows(reg / "stages.csv")} - {""}
    bad = [i for i in ids if i not in known]
    if not ids or bad:
        return f"not a stage in stages.csv: {', '.join(bad) or '(none given)'}"
    s["stage_ids"] = ids
    save(reg, s)
    return s


def record_flow_id(reg, flow_id):
    """The id of the flow the pick is for, as the session names it at the pick (brief.py depth), so the run finds its
    flow by id once the walk has named it afresh. Nothing is written for an id not in flows.csv, or before the
    go has made scope.json."""
    s = load(reg)
    known = {(r.get("flow_id") or "").strip() for r in rows(pathlib.Path(reg) / "flows.csv")}
    if s is None or flow_id not in known:
        return
    was = flow_key(reg, s)
    s["flow_id"] = flow_id
    if was and was not in known:  # judged under the name the go gave it, as a slug: those verdicts keep counting
        s[JUDGED_AS] = was
    save(reg, s)


DEPTHS = ("none", "measure", "alerting", "runbooks")  # each needs the one before it; none is mapped only


def pick_state(reg):
    """(the run record has the pick row, it is done). A register whose run record has no such row is from before
    mapping and measuring were picked apart, and is not held to it."""
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    m = re.search(r"^\| Pick of how far each stage goes \| ([^|]*)\|", text, re.M)
    return bool(m), bool(m) and m.group(1).strip().lower() == "done"


def measures_reopen(reg, s, before, depth):
    """Whether a new pick opens the review of the measures again: on a first pick; when a stage is measured that was
    not before (its measures are still to be proposed); or when the flow's measures changed since the person's go on
    them (the snapshot their go kept). Taking stages already measured on to alerts or runbooks, with the measures
    as reviewed, keeps the review closed."""
    if not before:
        return True
    if depth == before:
        return False
    newly = [sid for sid, d in depth.items() if d != "none" and before.get(sid, "none") == "none"]
    was = (s.get("measures_reviewed") or {}).get("rows")
    return bool(newly) or was is None or was != measures_snapshot(reg, flow_id_of(reg, s))


def mark_the_pick(reg, depth, line, before=None, picked=None, reopen=None):
    """RUN.md after the person's pick: its line, the pick row done, and the phases the pick leaves out set `not picked`, so the
    run record says what this run will not do and no phase is left waiting."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    values = set(depth.values())
    measured = values - {"none"}
    alerting = values & {"alerting", "runbooks"}
    text = p.read_text(encoding="utf-8")
    if re.search(r"^- \*\*Depth picked:\*\*", text, re.M):
        text = re.sub(r"^- \*\*Depth picked:\*\*.*(?:\n  .*)*$", lambda m: line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    s = load(reg)
    if s is not None:  # the Scope line now names the stages with their depth
        line_now = scope_line(dict(s, depth=depth, depth_picked=picked or s.get("depth_picked")), reg)
        text = re.sub(r"^- \*\*Scope:\*\*.*(?:\n  .*)*$", lambda m: line_now, text, count=1, flags=re.M)

    def row(lead, status):
        return re.sub(rf"^(\| {re.escape(lead)}[^|]*\| )[^|]*\|", rf"\g<1>{status} |", text, count=1, flags=re.M)
    def raised_to(levels):  # a stage this pick takes to one of `levels` that was below them before
        return any(d in levels and (before or {}).get(sid) not in levels for sid, d in depth.items())
    text = row("Pick of how far each stage goes", "done")
    # the flow's pages change: they are drawn, checked and reported again; a flow ended at the map has no pick
    # before, and its check and report were passed over, so a pick that measures anything reopens them too
    if (before and depth != before) or (measured and not before):
        text = row("6 ", "to do")
        text = row("7 ", "to do")
    if reopen is None:
        reopen = not before or depth != before
    if reopen or not measured:
        text = row("4 ", "doing" if measured else "not picked")
    if reopen:  # the measures are proposed again, so the person reviews them again
        if measured and not re.search(rf"^\| {MEASURES_ROW} \|", text, re.M):
            # a run record from before the measures had their own review has no row for it: without one the stop
            # cannot be recorded, and the run would pass it by with nothing said to be waiting on the person
            text = re.sub(r"^(\| 4 [^\n]*\n)", rf"\g<1>| {MEASURES_ROW} | to do | | |\n", text, count=1, flags=re.M)
        text = row("Review of the measures", "to do" if measured else "not picked")
    # work done stays done unless a stage now owes it again; a stage raised only to measure owes no alert review
    if raised_to({"alerting", "runbooks"}) or not alerting:
        for lead in ("5a ", "Review of the alerts"):
            text = row(lead, "to do" if alerting else "not picked")
    if raised_to({"runbooks"}) or "runbooks" not in values:
        text = row("5b ", "to do" if "runbooks" in values else "not picked")
    p.write_text(text, encoding="utf-8", newline="\n")


def record_depth(reg, text, a=None):
    """How far each stage goes, once the stages are cut: `ST2=measure,ST3=runbooks`; a stage not named is mapped
    only (none). An empty choice is a map-only run. The person's words are required: this is a hold point, as the go is."""
    if a is not None and not getattr(a, "page", False) and not (a.words or "").strip():
        return "--words is required: their answer on how far each stage goes, word for word"
    s = load(reg) or {}
    if not [r for r in rows(reg / "stages.csv") if (r.get("stage") or "").strip()]:
        return "stages.csv has no stage: the stages are cut in mapping, before this choice"
    named = {pair.partition("=")[0].strip() for pair in names(text)}
    owner = next((o for o in load_all(reg)[:-1] if named & set(stages_of(reg, o))), None)
    if owner is not None:  # a stage of a flow finished earlier: taken further only between flows
        if not run_finished(reg):
            return (f"the flow {s.get('flow', '')} is under way: finish it first, through its done check and report; "
                    f"then {owner.get('flow', '')} can be taken further" + split_unheld(reg))
        import merge
        unkept = merge.record_problems(reg)
        if unkept:
            return ("the finished flow's merge cannot be kept for the next flow to reuse (" + "; ".join(unkept) + ")")
        s = take_up_again(reg, owner)
    known = stages_of(reg, s)  # this flow's stages: another flow's pick is that flow's, and is never changed here
    if not known:
        return f"stages.csv has no stage of the flow {s.get('flow', '')}: its stages are cut in mapping, before this choice"
    depth = {sid: "none" for sid in known}
    for pair in names(text):
        sid, _, value = pair.partition("=")
        sid, value = sid.strip(), value.strip().lower()
        if sid not in known:
            return f"not a stage of this flow in stages.csv: {sid} (its stages: {', '.join(known)})"
        if value not in DEPTHS:
            return f"{sid}: {value or 'nothing'} is not one of {', '.join(DEPTHS)}"
        depth[sid] = value
    before = s.get("depth") or {}
    lowered = [f"{sid} from {before[sid]} to {d}" for sid, d in depth.items()
               if before.get(sid) in DEPTHS and DEPTHS.index(d) < DEPTHS.index(before[sid])]
    if lowered:
        return ("taking a stage less far than already picked is not supported yet (" + "; ".join(lowered) +
                "): the pages already written for it would stay. Name each stage at least as far as before; taking "
                "a stage further is allowed")
    reopen = measures_reopen(reg, s, before, depth)
    if reopen:  # phase 4 runs again: the review of the measures is open again
        s.pop("measures_reviewed", None)
        s.pop("measures_shown", None)
    s["depth"] = depth
    if a is not None:
        given = a.given or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
        s["depth_picked"] = {"words": a.words.strip(), "given": given, "test": a.test}
        asked = getattr(a, "from_request", False)  # their request said it before mapping: recorded, not asked again
        if asked:
            s["depth_picked"]["from_request"] = True
        who = "a test pick, given by a test standing in for the person" if a.test else "the person"
        mark_the_pick(reg, depth, f"- **Depth picked:** {'from their request: ' if asked else ''}{a.words.strip()} "
                      f"({who}, {given})", before, s["depth_picked"], reopen)
    save(reg, s)
    return s


def take_up_again(reg, owner):
    """A flow finished earlier made the one worked now again, to take it further: the flow just finished is kept as
    the next flow's start keeps it (its record, a copy of every row, its lines in RUN.md), and the earlier flow's go
    and scope lines come back, with its mapping and the work its earlier pick needed done. Its new pick then sets
    what it needs again. The time it is taken up again is recorded (`taken_up`): its go stays its own, earlier one,
    and provenance.py counts only the sessions after the later of the two."""
    cur, others = load(reg), dict((read_raw(reg) or {}).get(OTHER_FLOWS) or {})
    others[cur.get("flow", "")] = cur
    others.pop(owner.get("flow", ""), None)
    owner = dict(owner, taken_up=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
    keep_finished_flow(reg, cur, others)
    save(reg, owner, others)
    start_next_flow_in_run_md(reg, cur)
    record_in_run_md(reg, owner)
    reached = set((owner.get("depth") or {}).values())
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8")
    for lead, status in (("1 ", "done"), ("2 ", "done"), ("3 ", "done"),
                         ("Review of the measures", "done" if reached - {"none"} else "not picked"),
                         ("5a ", "done" if reached & {"alerting", "runbooks"} else "not picked"),
                         ("Review of the alerts", "done" if reached & {"alerting", "runbooks"} else "not picked"),
                         ("5b ", "done" if "runbooks" in reached else "not picked")):
        text = re.sub(rf"^(\| {re.escape(lead)}[^|]*\| )[^|]*\|", rf"\g<1>{status} |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")
    return load(reg)


def add_flow(reg, name, words, given=None, test=False):
    """A flow the first look missed, added at the offer of the next flow with the person's words, so it can be picked
    like any other. Only between flows; refused for a name the map already has."""
    name = (name or "").strip()
    cur = load(reg)
    if cur is None or not run_finished(reg):
        return "a flow is added at the offer of the next flow, once the flow worked now is finished"
    o = pathlib.Path(reg) / layout.ORIENTATION
    got = json.loads(o.read_text(encoding="utf-8-sig")) if o.is_file() else {}
    found = got.setdefault("flows", [])
    if not name or name.lower() in {(f.get("name") or "").lower() for f in found}:
        return f"{name or 'a flow with no name'} is not a new flow: it is in the list already"
    given = given or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    found.append({"name": name, "what": f"added by {'a test' if test else 'the person'}: {(words or '').strip()}",
                  "added": {"words": (words or "").strip(), "given": given, "test": test}})
    o.write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    p = pathlib.Path(reg) / "RUN.md"
    if p.is_file():
        who = "a test, standing in for the person" if test else "the person"
        p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + f"\n- **Flow added:** {name}: \"{(words or '').strip()}\""
                     f" ({who}, {given})\n", encoding="utf-8", newline="\n")
    return {"flow": name}


def ticked(value):
    """The ticks a page sent for one item: a checkbox group's list, or one value (a radio, a select), as a list."""
    if value is None or value == "":
        return []
    return [str(v) for v in value if str(v)] if isinstance(value, list) else [str(value)]


PICK_MILESTONES = ("Mapped", "Measures defined", "Alerts defined")
NEXT_TASK = "Choose the next flow to map"  # depth.py's open choice once a flow is finished  # the milestones whose choice the kit records
TALK_KEY, TALK_WORDS = "talk:", "talk-words:"  # the page's topics to talk about (home.py names them so)


def topics_of(got):
    """The page's topics to talk about, in the order sent: (milestone, what), each ticked label and each drop-down's
    words, verbatim; nothing for an unticked box or empty words."""
    out = []
    for k, v in got.items():
        if k.startswith(TALK_WORDS):
            out += [(k[len(TALK_WORDS):], f'"{w.strip()}"') for w in ticked(v) if w.strip()]
        elif k.startswith(TALK_KEY):
            out += [(k[len(TALK_KEY):].split(":", 1)[0], label) for label in ticked(v)]
    return out


def topics_line(topics):
    return "; ".join(f"{m}: {what}" for m, what in topics)


def record_topics(reg, topics, given, test):
    """The topics, verbatim with the time, in the run record, RUN.md: for the session to talk about, never a pick."""
    given = given or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    p = reg / "RUN.md"
    if p.is_file():
        who = "a test, given by a test standing in for the person" if test else "the person"
        line = f"- **Topics to talk about:** {topics_line(topics)} ({who}, {given})"
        p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\n" + line + "\n", encoding="utf-8", newline="\n")


def record_note(reg, milestone, got, given, test):
    """Their words, and any ticks, on a milestone with no pick open (one other teams do, such as Instrumented):
    recorded verbatim with the milestone and the time in the run record, RUN.md, and in scope.json once the go has
    made it. No pick is made and no depth changes: the session reads them and replies."""
    given = given or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    words = got.get("words") if isinstance(got.get("words"), str) else ""
    ticks = {k: v for k, v in got.items() if k not in ("milestone", "words", "choice_id")}
    note = {"milestone": milestone, "words": words, "ticks": ticks, "given": given, "test": test}
    s = load(reg)
    if s is not None:  # before the go there is no scope.json, and none is made here: the go makes it
        s.setdefault("notes", []).append(note)
        save(reg, s)
    p = reg / "RUN.md"
    if p.is_file():
        who = "a test, given by a test standing in for the person" if test else "the person"
        asked = "; ".join(f"{k}: {', '.join(ticked(v)) or 'nothing ticked'}" for k, v in ticks.items())
        line = (f"- **Note on {milestone}:** \"{words}\" ({who}, {given})" + (f". Ticked: {asked}" if asked else ""))
        p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\n" + line + "\n", encoding="utf-8", newline="\n")
    return argparse.Namespace(milestone=milestone, words=words, given=given, scoped=s is not None)


def from_answers(reg, path, test=False):
    """The person's picks from the page (ask-on-a-page's answers file: page, submittedAt, answers), checked against
    the open choice in depth.json now, and recorded exactly as --flow or --depth records them, their words verbatim.
    Returns the Namespace to record with and which, or the refusal."""
    import depth
    try:
        body = json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
        got = body["answers"]
        if not isinstance(got, dict):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        return f"{path} is not an answers file: it needs an `answers` object, as the page sends it"
    topics = topics_of(got)
    got = {k: v for k, v in got.items() if not k.startswith((TALK_KEY, TALK_WORDS))}
    said = (got.get("words") or "").strip() if isinstance(got.get("words"), str) else ""
    if not said and not any(ticked(v) for k, v in got.items() if k not in ("choice_id", "words", "milestone")):
        # nothing for the open choice: a Done in another drop-down, or a page with no choice open
        if not topics:
            return "nothing ticked and no words, so these answers say nothing"
        return "topics", argparse.Namespace(topics=topics, given=body.get("submittedAt"))
    c = depth.build(reg)["open_choice"]
    named = got.get("milestone")
    if named and (c is None or named != c["milestone"]):
        if named in PICK_MILESTONES and got.get("choice_id"):
            return (f"these answers pick at {named}, which is not waiting on a pick now (the page was drawn before "
                    "the run moved on). Draw the page again from depth.json")
        return "note", record_note(reg, named, got, body.get("submittedAt"), test)
    if c is None:
        return "nothing is waiting on a pick from the page now, so these answers cover nothing"
    if not c["items"]:  # never record a pick from a choice that showed the person nothing
        return "the open choice offers nothing to pick, so these answers cover nothing"
    if got.get("choice_id") != c["choice_id"]:
        return ("the choice has changed since the page was drawn, so these answers do not cover it (page "
                f"{got.get('choice_id') or 'none'}, now {c['choice_id']}). Draw the page again from depth.json and "
                "ask again")
    words = got.get("words")
    words = words if isinstance(words, str) else ""
    a = argparse.Namespace(flow=None, inn=None, out=None, stages=None, judges=None, words=words,
                           given=body.get("submittedAt"), test=test, depth=None, topics=topics)
    offered = {i["key"]: i for i in c["items"]}
    unknown = [k for k in got if k not in ("choice_id", "words", "milestone", "add") and k not in offered]
    if c["milestone"] == "Mapped":
        if unknown:
            return f"not a flow on the page: {', '.join(unknown)}"
        bad = [f"{k}: {v}" for k in offered for v in ticked(got.get(k)) if v != depth.FLOW_OPT]
        if bad:
            return f"not a tick the page offers: {'; '.join(bad)}"
        picked = [k for k in offered if ticked(got.get(k))]
        add = got.get("add").strip() if isinstance(got.get("add"), str) else ""
        if add and c["task"] == NEXT_TASK:  # a flow the first look missed: added, then picked unless another is ticked
            if len(picked) > 1:
                return f"tick at most one flow to map next ({len(picked)} ticked)"
            a.add, a.flow = add, picked[0] if picked else add
            return "add", a
        if len(picked) != 1:
            return f"tick exactly one flow to map first ({len(picked)} ticked)"
        a.flow = picked[0]
        return "flow", a
    if c["milestone"] == "Measures defined":
        order = list(depth.DEPTH_OPTS)
        problems = [f"not a stage on the page: {k}" for k in unknown]
        pairs = []
        for k in offered:
            value = got.get(k)
            ticks = ticked(value)
            bad = [t for t in ticks if t not in order]
            if bad:
                problems.append(f"{k}: not a tick the page offers: {', '.join(bad)}")
                continue
            if not ticks:
                continue  # no tick: mapped only
            furthest = max(order.index(t) for t in ticks)
            if isinstance(value, list):  # the ticked values: every one up to the furthest, as ticking a later
                # milestone includes the earlier ones; a single value (not a list) is the furthest alone
                missing = [order[i] for i in range(furthest) if order[i] not in ticks]
                if missing:
                    problems.append(f"{k}: {order[furthest]} without {missing[-1]}; each milestone includes the "
                                    "ones before it")
            pairs.append(f"{k}={depth.DEPTH_OPTS[order[furthest]]}")
        if problems:
            return "; ".join(problems)
        if not pairs:  # words and no tick: no pick is recorded from the page; the words are a topic
            return "topics", argparse.Namespace(topics=topics + [(c["milestone"], f'"{words.strip()}"')],
                                                given=body.get("submittedAt"), ask=True)
        a.depth = ",".join(pairs)
        return "depth", a
    return ("the reviews of the measures and of the alerts are not taken from a page: record their answer with "
            "go.py --measures-reviewed or --alerts-reviewed --decision go|changes --words")


RECORDED = pathlib.Path("answers") / ".recorded"  # one line per answers file taken: its content's sha256


def answers_key(path):
    try:
        return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def taken_before(reg, key):
    try:
        return key in (reg / RECORDED).read_text(encoding="utf-8").split()
    except OSError:
        return False


def mark_taken(reg, key):
    (reg / RECORDED).parent.mkdir(exist_ok=True)
    with open(reg / RECORDED, "a", encoding="utf-8", newline="\n") as f:
        f.write(key + "\n")


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if "--answers" in argv:  # the person's picks from the page, recorded as --flow or --depth records them
        i = argv.index("--answers")
        rest = argv[:i] + argv[i + 2:]
        test = "--test" in rest
        rest = [x for x in rest if x != "--test"]
        if len(rest) != 1 or i + 1 >= len(argv) or not pathlib.Path(rest[0]).is_dir():
            print("Usage: python go.py <register folder> --answers <answers file> [--test]", file=sys.stderr)
            return 2
        reg = pathlib.Path(rest[0])
        run_lock.guard(reg)
        key = answers_key(argv[i + 1])
        if key and taken_before(reg, key):
            print("REFUSED: these answers were recorded already, so they are not the person's latest. If nothing "
                  "newer has arrived, ask the question in the chat. Nothing written.", file=sys.stderr)
            return 2
        try:  # the say-back's Start or correction is not a pick: its own script records it
            said_back = "say_back" in json.loads(pathlib.Path(argv[i + 1]).read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            said_back = False
        if said_back:
            print("REFUSED: these are the person's answer to what the run said back, not a pick: record them with "
                  f'python say_back.py answer "{reg}" --answers "{argv[i + 1]}". Nothing written.', file=sys.stderr)
            return 2
        got = from_answers(reg, argv[i + 1], test)
        if isinstance(got, str):
            print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
            return 2
        how, a = got
        if how == "topics":
            record_topics(reg, a.topics, a.given, test)
            mark_taken(reg, key)
            import depth
            depth.write_quietly(reg)
            print("Written: topics to talk about, in RUN.md; no pick recorded.")
            print(f"You asked to talk about: {topics_line(a.topics)}")
            if getattr(a, "ask", False):
                print("Nothing was ticked, so no pick was recorded: ask the person in the chat how far each stage "
                      "goes, and record their answer with --depth.")
            return 0
        args = [str(reg), "--words", a.words] + (["--given", a.given] if a.given else []) + (["--test"] if test else [])
        if how == "add":
            added = add_flow(reg, a.add, a.words or "added on the page", a.given, test)
            if isinstance(added, str):
                print(f"REFUSED: {added}. Nothing written.", file=sys.stderr)
                return 2
            record_decision(reg, "add flow", a.words or "added on the page", "page", test)
            how = "flow"
        if how == "note":
            mark_taken(reg, key)
            print(f"Written: their words on {a.milestone}, in RUN.md" + (f" and {layout.SCOPE}" if a.scoped else "")
                  + "; no pick recorded. Read them and reply.")
            import depth
            depth.write_quietly(reg)
            return 0
        rc = main(args + ["--page"] + (["--flow", a.flow] if how == "flow" else ["--depth", a.depth]))
        if rc == 0:
            mark_taken(reg, key)
        if rc == 0 and a.topics:
            record_topics(reg, a.topics, a.given, test)
            print(f"You asked to talk about: {topics_line(a.topics)}")
        return rc
    ap = argparse.ArgumentParser(prog="go.py", description=__doc__.split("\n")[0])
    ap.add_argument("reg")
    ap.add_argument("--flow")
    ap.add_argument("--in", dest="inn")
    ap.add_argument("--out")
    ap.add_argument("--stages")
    ap.add_argument("--judges", type=int)
    ap.add_argument("--words")
    ap.add_argument("--given")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--stage-ids")
    ap.add_argument("--alerts-reviewed", action="store_true")
    ap.add_argument("--measures-reviewed", action="store_true")
    ap.add_argument("--back-to-measures", metavar="ID,...")
    ap.add_argument("--decision")
    ap.add_argument("--depth")
    ap.add_argument("--mapping-ends", metavar="FLOW_ID")
    ap.add_argument("--add-flow", metavar="NAME")
    ap.add_argument("--apply-correction", metavar="ID")
    ap.add_argument("--value")
    ap.add_argument("--added", action="store_true")
    ap.add_argument("--removed", action="store_true")
    ap.add_argument("--transcripts", metavar="DIR")  # --apply-correction: where the person's words are looked for
    ap.add_argument("--report-sent", metavar="FLOW_ID")
    ap.add_argument("--page", action="store_true", help=argparse.SUPPRESS)  # from the page: ticks alone answer
    ap.add_argument("--source", choices=("chat", "page", "request"), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    source = a.source or ("page" if a.page else "chat")
    reg = pathlib.Path(a.reg)
    if not reg.is_dir():
        print(f"not a folder: {reg}", file=sys.stderr)
        return 2
    run_lock.guard(reg)
    if a.add_flow is not None and not (a.words or "").strip():
        print("REFUSED: --words is required: the person's words on the flow they add, word for word. Nothing "
              "written.", file=sys.stderr)
        return 2
    if a.apply_correction is not None:
        got = apply_correction(reg, a.apply_correction, a.value, a.added, a.removed, a.words, a.transcripts)
        if isinstance(got, str):
            print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
            return 2
        if (a.words or "").strip():
            record_decision(reg, "correction", a.words, source, a.test,
                            shown="(no message: the person stated this change to the map themselves)")
        where = f"units/{got['unit']}/{got['table']}" if got["unit"] else got["table"]
        print(f"Written: {got['correction_id']} {'removed from' if a.removed else 'applied to'} {where}.csv "
              f"{got['row']}, recorded in {APPLIED}")
        return 0
    if a.back_to_measures is not None:
        got = back_to_measures(reg, names(a.back_to_measures))
        if isinstance(got, str):
            print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
            return 2
        import brief
        import depth
        depth.write_quietly(reg)
        print("Written: back to proposing the measures (phase 4) for " + ", ".join(names(a.back_to_measures)) +
              ", in RUN.md. Take each request up in proposing the measures (the measures skill), show the person the measures again (brief.py measures), "
              "and after their go the run goes on where it was")
        print("Status line for your reply:")
        print(brief.status(reg))
        return 0
    if a.report_sent is not None:
        got = record_report(reg, a.report_sent)
        if isinstance(got, str):
            print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
            return 2
        print(f"Written: the report of {got.get('flow')} sent, in {layout.SCOPE}")
        return 0
    got = (add_flow(reg, a.add_flow, a.words, a.given, a.test) if a.add_flow is not None else
           mapping_ends(reg, a.mapping_ends) if a.mapping_ends is not None else
           record_review(reg, a) if a.alerts_reviewed else
           record_measures_review(reg, a) if a.measures_reviewed else
           record_depth(reg, a.depth, a) if a.depth is not None else
           record_stage_ids(reg, names(a.stage_ids)) if a.stage_ids is not None else record_go(reg, a))
    if isinstance(got, str):
        print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
        return 2
    if a.mapping_ends is None and a.stage_ids is None:  # every other path here records an answer of the person's
        stop = ("add flow" if a.add_flow is not None else "alerts review" if a.alerts_reviewed else
                "measures review" if a.measures_reviewed else "depth" if a.depth is not None else
                "next flow" if len(load_all(reg)) > 1 else "flow")
        record_decision(reg, stop, a.words, source, a.test,
                        shown=f"(the request, word for word) {a.words}" if source == "request" else None)
    import depth  # the page's next state: depth.json follows every record
    depth.write_quietly(reg)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.depth is not None:
        print(f"Written: how far each stage goes, in {layout.SCOPE}: " +
              ", ".join(f"{k} {v}" for k, v in got["depth"].items()))
        import brief
        print("Status line for your reply:")
        print(brief.status(reg))
        return 0
    if a.add_flow is not None:
        print(f"Written: the flow {got['flow']} added to the flows to map, with their words; pick it with --flow")
        return 0
    if a.mapping_ends is not None:
        import brief
        print("Written: the phases after mapping, not picked, in RUN.md: this flow is finished")
        print("Status line for your reply:")
        print(brief.status(reg))
        return 0
    if a.alerts_reviewed or a.measures_reviewed:
        import brief
        print(f"Written: the review of the {'alerts' if a.alerts_reviewed else 'measures'}, in {layout.SCOPE} and "
              "RUN.md")
        print("Status line for your reply:")
        print(brief.status(reg))
        return 0
    print(f"Written: {layout.SCOPE}" + ("" if a.stage_ids is not None else f" and {layout.SETTINGS} (judges {a.judges})"))
    print("The scope, as recorded in RUN.md where there is one:")
    print(scope_line(got))
    import brief
    print("Status line for your reply:")
    print(brief.status(reg))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
