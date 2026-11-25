"""Upgrade a register in place to one part per deployable, store or outside system, each named by its own identifiers.
Run as `python reconcile.py --upgrade-identity <register> --backup <folder>`, after --migrate.

Unlike --migrate, this CHANGES CONTENT, and records every change it makes in corrections-applied.csv (id
`identity-<n>`; the merge's own as `merge-<n>`), so the finished-flow check (go.changed_rows) passes on every finished
flow. It refuses without a backup: it copies the register to --backup first, a folder outside the register that does
not exist yet.

Steps:
1. Back up the register.
2. Read identity (identity.py): configuration and deployment files only, into identity/.
3. A split run (units/units.csv): merge (merge.py), which folds the units' rows of one deployable into one part, and a
   store by its address or the deployable's one store; a judgment fold in identity/merges.csv is applied the same way.
   Each folded id stays an alias in merge/part-ids.csv. Then the tables the merge does not write are re-pointed
   through the alias map: merge/lead-rows/, measures.csv `subject_id` and `taken_at`, failure-modes.csv `part`,
   measure-gaps.csv `element` and agent-system.csv `agent` (a key column: the first row on a new key is corrected on
   its old key, each further one removed), lifecycle.csv `carried_by` and `needs` (the `S04 name` form).
   A register with no units (one read by a single reader): each application component is named by its deployable's
   identifiers, and the root identifiers.csv is written; two rows of one deployable are listed for judgment, not folded.
4. Rename: measures.csv `counted_at` and lifecycle.csv text are rewritten only where a cell holds an old full name
   exactly (counted_at: its text before the first comma). Prose (runbooks, stage pages, how-made notes) is listed as
   stale, never rewritten.
5. Judgments: the parts no rule could place (outside systems and stores with no resolved address) and the workloads no
   image matched are written to identity/judge-prompt.md, for ONE agent launch that decides each as a draft and
   records its basis and evidence (identity/merges.csv, identity/judged-identifiers.csv). Then
   `reconcile.py --upgrade-identity <register> --after-judgments --backup <new folder>` applies them (a split run
   only) the same way, every change recorded. A
   person's correction in review (go.py --apply-correction, table `merges`, row = the candidates) undoes a merge at the
   next merge and stands through every later upgrade.
6. Report: part counts before and after, the judgments to review, the cells rewritten and the stale prose.
"""
import datetime
import json
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import go  # noqa: E402
import identity  # noqa: E402
import merge  # noqa: E402
import register_layout as layout  # noqa: E402
import tables  # noqa: E402

SRC = "reconcile.py --upgrade-identity"
REPOINT = {"measures": ("subject_id", "taken_at"), "failure-modes": ("part",)}
KEYED = {"measure-gaps": "element", "agent-system": "agent"}
LEAD_CELLS = ("subject_id", "from_id", "to_id", "part_of")


def parts(rows):
    return [r for r in rows if r.get("kind") == "element" and r.get("level") in ("component", "external dependency")]


class Recorder:
    def __init__(self, reg):
        self.reg, self.recs = reg, []

    def add(self, table, row, column, before, after, why, words=""):
        self.recs.append({"table": table, "row": row, "column": column, "before": before, "after": after,
                          "why": why, "source": SRC, "words": words})

    def flush(self):
        if not self.recs:
            return
        have = len([r for r in go.table_rows(self.reg, "corrections-applied")[1]
                    if (r.get("correction_id") or "").startswith("identity-")])
        now = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
        go.record_applied(self.reg, [dict(k, correction_id=f"identity-{have + i}", applied_at=now, unit="")
                                     for i, k in enumerate(self.recs, 1)])
        self.recs = []


def map_id(value, alias):
    """A cell naming a part (`S12`, or `S12 name` in lifecycle's form), through the alias map."""
    m = re.match(r"^(S\d+)\b(.*)$", value or "", re.S)
    if m and m.group(1) in alias:
        return alias[m.group(1)] + m.group(2)
    return value


def rewrite(reg, table, fn):
    p = reg / f"{table}.csv"
    cols, rows = tables.table(p)
    if not cols:
        return
    rows2 = fn(rows)
    if rows2 is not None:
        tables.write(p, list(cols), rows2)


def repoint(reg, alias, rec, notes):
    """The tables the merge does not write, re-pointed through the alias map, each change recorded."""
    for table, cols in REPOINT.items():
        def fn(rows, table=table, cols=cols):
            for r in rows:
                for c in cols:
                    new = map_id(r.get(c, ""), alias)
                    if c in r and new != r[c]:
                        rec.add(table, go.row_key(table, r), c, r[c], new, f"{r[c]} folded into {new}")
                        notes.append(f"{table}.csv {go.row_key(table, r)}: {c} {r[c]} -> {new}")
                        r[c] = new
            return rows
        rewrite(reg, table, fn)

    def life(rows):
        for r in rows:
            for c in ("carried_by", "needs"):
                if c not in r:
                    continue
                new = "; ".join(map_id(x.strip(), alias) for x in r[c].split(";")) if r[c] else r[c]
                if new != r[c]:
                    rec.add("lifecycle", go.row_key("lifecycle", r), c, r[c], new, "a part folded")
                    notes.append(f"lifecycle.csv {go.row_key('lifecycle', r)}: {c} re-pointed")
                    r[c] = new
        return rows
    rewrite(reg, "lifecycle", life)
    for table, col in KEYED.items():
        def keyed(rows, table=table, col=col):
            out, landed = [], set()
            for r in rows:
                new = map_id(r.get(col, ""), alias)
                if new == r.get(col, ""):
                    landed.add(go.row_key(table, r))
                    out.append(r)
                    continue
                old_key, r2 = go.row_key(table, r), dict(r, **{col: new})
                if go.row_key(table, r2) in landed:
                    rec.add(table, old_key, "", json.dumps(r, ensure_ascii=False), go.REMOVED,
                            f"{r[col]} folded into {new}: the same row as one already there")
                    notes.append(f"{table}.csv {old_key}: removed, the same as {go.row_key(table, r2)}")
                    continue
                rec.add(table, old_key, col, r[col], new, f"{r[col]} folded into {new}")
                notes.append(f"{table}.csv {old_key}: {col} -> {new}")
                landed.add(go.row_key(table, r2))
                out.append(r2)
            return out
        rewrite(reg, table, keyed)
    lead = reg / layout.LEAD_ROWS
    for name in ("subjects.csv", "participation.csv"):
        p = lead / name
        cols, rows = tables.table(p)
        changed = False
        for r in rows:
            for c in LEAD_CELLS:
                if c in r and r[c] in alias:
                    if name == "subjects.csv" and c != "subject_id":
                        rec.add("subjects", r.get("subject_id", ""), c, r[c], alias[r[c]], "a part folded")
                    r[c], changed = alias[r[c]], True
        if changed:
            tables.write(p, list(cols), rows)


def renamed_text(reg, renames, rec, notes):
    """counted_at and lifecycle text, rewritten only where a cell holds an old full name exactly."""
    def counted(rows):
        for r in rows:
            seg, sep, rest = (r.get("counted_at") or "").partition(",")
            if seg.strip() in renames:
                new = renames[seg.strip()] + sep + rest
                rec.add("measures", go.row_key("measures", r), "counted_at", r["counted_at"], new,
                        "the component's name, as its deployment states it")
                notes.append(f"measures.csv {go.row_key('measures', r)}: counted_at {seg.strip()!r} -> "
                             f"{renames[seg.strip()]!r}")
                r["counted_at"] = new
        return rows
    rewrite(reg, "measures", counted)

    def life(rows):
        for r in rows:
            for c in ("carried_by", "needs"):
                cells = [x.strip() for x in (r.get(c) or "").split(";")]
                new = []
                for x in cells:
                    m = re.match(r"^(S\d+) (.+)$", x)
                    new.append(f"{m.group(1)} {renames[m.group(2)]}" if m and m.group(2) in renames else x)
                text = "; ".join(new) if r.get(c) else r.get(c, "")
                if c in r and text != r[c]:
                    rec.add("lifecycle", go.row_key("lifecycle", r), c, r[c], text, "a part renamed")
                    notes.append(f"lifecycle.csv {go.row_key('lifecycle', r)}: {c} renamed")
                    r[c] = text
        return rows
    rewrite(reg, "lifecycle", life)


def resource_store(reg, r, ident, rec, notes, renames, ids_rows):
    """A store the deployment runs as its own workload (`not built here: redis:alpine (manifest:118)`): named by that
    workload, the one whose image is the row's image (identity/unmatched.csv), and given the identifiers of the store a
    deployable reaches at that host."""
    m = re.search(r"not built here:\s*([^\s(]+)", r.get("repository") or "")
    if not m:
        return
    img = identity.norm_image(m.group(1))
    hits = {(w.get("workload") or "").strip(): w for w in tables.dicts(reg / identity.DIR / "unmatched.csv")
            if img and img in {identity.norm_image(x) for x in (w.get("image") or "").split(";")}}
    if len(hits) != 1:
        return
    name, w = next(iter(hits.items()))
    nm = (r.get("name") or "").strip()
    if name != nm:
        rec.add("subjects", r["subject_id"], "name", nm, name, "named as its deployment names its workload")
        notes.append(f"subjects.csv {r['subject_id']}: name {nm!r} -> {name!r}")
        renames[nm] = name
        r["name"] = name
    ids_rows.append({"subject_id": r["subject_id"], "operation": "", "attribute": "k8s.deployment.name",
                     "value": name, "source": w.get("source", ""), "basis": "rule: read"})
    for ref, xs in ident.items():
        if ref[1].startswith("store:") and identity.value(xs, "server.address") == name:
            for x in xs:
                ids_rows.append({"subject_id": r["subject_id"], "operation": "", **{
                    k: x.get(k, "") for k in ("attribute", "value", "source", "basis")}})
            break


def single_reader(reg, ident, rec, notes):
    """A register with no units: each application component named by its deployable's identifiers, and the root
    identifiers.csv written. Returns {old name: new name}."""
    cols, rows = tables.table(reg / "subjects.csv")
    deps = {d for d, ref in ident if not ref}
    renames, ids_rows, owner = {}, [], {}
    for r in rows:
        if r.get("kind") != "element" or r.get("level") != "component":
            continue
        nm = (r.get("name") or "").strip()
        cands = {nm.lower()} | {m.lower() for m in re.findall(r"\(([^()]+)\)", nm)}
        cands |= {(r.get("repository") or "").split(":")[-1].strip().rstrip("/").rsplit("/", 1)[-1].lower()}
        hit = None
        for d in deps:
            own = {d} | {(x.get("value") or "").lower() for x in ident[(d, "")]
                         if x.get("attribute") in ("k8s.deployment.name", "container.image.name")}
            if own & cands:
                hit = d
                break
        if hit is None and r.get("band") != "application":
            resource_store(reg, r, ident, rec, notes, renames, ids_rows)
            continue
        if hit is None:
            continue
        if r.get("band") == "application":
            if hit in owner:
                notes.append(f"JUDGMENT: subjects.csv {owner[hit]} and {r['subject_id']} are one deployable "
                             f"({hit}); fold them by a correction to subjects.csv (go.py --apply-correction), or keep them apart")
                continue
            owner[hit] = r["subject_id"]
            new = identity.part_name(ident[(hit, "")], hit)[0]
            if new != nm:
                rec.add("subjects", r["subject_id"], "name", nm, new, "named as its deployment states it")
                notes.append(f"subjects.csv {r['subject_id']}: name {nm!r} -> {new!r}")
                renames[nm] = new
                r["name"] = new
            refs = [(hit, "")]
        else:  # a store of that deployable: its one store of the kind, when there is exactly one
            cls = merge.STORE_KINDS.get((r.get("part_kind") or "").strip().lower())
            refs = [k for k, v in ident.items() if k[0] == hit and k[1].startswith("store:")
                    and identity.store_class(v) == cls]
            refs = refs if len(refs) == 1 else []
            new = identity.store_name(ident[refs[0]]) if refs else ""
            if new and new != nm:
                rec.add("subjects", r["subject_id"], "name", nm, new, "named by its address, as its configuration "
                        "states it")
                notes.append(f"subjects.csv {r['subject_id']}: name {nm!r} -> {new!r}")
                renames[nm] = new
                r["name"] = new
        for ref in refs:
            for x in ident[ref]:
                if x.get("attribute") != "custom: finding" or not ref[1]:
                    ids_rows.append({"subject_id": r["subject_id"], "operation": "", **{
                        k: x.get(k, "") for k in ("attribute", "value", "source", "basis")}})
    tables.write(reg / "subjects.csv", list(cols), rows)
    fixes = go.applied_corrections(reg, "identifiers")
    tables.write(reg / "identifiers.csv", merge.IDENT_COLS,
                 [go.corrected("identifiers", x, fixes) for x in ids_rows])
    return renames


JUDGE_PROMPT = "identity/judge-prompt.md"
JUDGED_IDENTIFIERS = "identity/judged-identifiers.csv"
JUDGED_DONE = "identity/judged.done"


def cases(reg):
    """(the parts no rule could place, the workloads no image matched): what the one judging agent decides."""
    reg = pathlib.Path(reg)
    subj = tables.dicts(reg / "subjects.csv")
    keyed = {r.get("subject_id"): r.get("key", "") for r in tables.dicts(reg / merge.PART_IDS)}
    ident = identity.load(reg) or {}
    resolved_ext = {ref for (d, ref), rows in ident.items() if ref.startswith("external:") and identity.resolved(rows)}
    cands = []
    for r in subj:
        if r.get("kind") != "element" or r.get("level") not in ("component", "external dependency"):
            continue
        if r.get("level") == "external dependency" and not any(r.get("name") == ref[len("external:"):] or
                                                               (r.get("source") or "").find(ref) >= 0
                                                               for ref in resolved_ext):
            cands.append(r)
        elif (r.get("band") or "") == "technology" and (keyed.get(r["subject_id"]) or "").startswith("row|"):
            cands.append(r)
    return cands, tables.dicts(reg / identity.DIR / "unmatched.csv")


def judge_prompt(reg, only=None, mark=False, workspace=None):
    """The one agent launch the judgments owe: the parts no rule could place, for the model to
    judge as a draft, each decision written with its basis and evidence. Returns the number of candidates. `only`: the
    ids and workloads to list (run control lists those not handed over before); `mark`: the prompt ends by telling the
    agent to write JUDGED_DONE last, which run control reads as its finish, in place of the hand command."""
    reg = pathlib.Path(reg)
    cands, unmatched = cases(reg)
    if only is not None:
        cands = [r for r in cands if r["subject_id"] in only]
        unmatched = [w for w in unmatched if (w.get("workload") or "") in only]
    done = {(m.get("candidates") or "").strip() for m in merge.judged_merges(reg)}
    lines = [
        "# Identity judgments for this register (a draft; the person corrects it in review)",
        "",
        "You judge which of the parts below are one real thing. Everything you write is a draft: decide each case on",
        "the evidence, as a careful engineer would, and record your basis so a reviewer can find and correct it.",
        "",
        "Read each candidate's cited lines (its `source`) in the workspace. Then, for each set of candidates that are",
        "one outside system, one store or one broker (the same client, the same host and path, the same schema and",
        "tables, the same secret's name), append one row to `identity/merges.csv`:",
        "`candidates` (the map ids, `;`-joined), `decision` `merge`, `basis` `judgment`, `evidence` (`file:line` and",
        "what it shows, never a password, token or key value), `what_would_change_it`. Where two look alike but are not one thing, write `decision` `apart`",
        "the same way. A shared gateway host alone is never evidence that two systems are one.",
        "",
        "Never change or remove a row already in `identity/merges.csv`, nor decide again a set already there: those",
        f"are decided ({len(done)} so far) and a person's correction to one stands.",
        "",
        "For each workload in the second table, decide which deployable it runs, from its image, name and manifest, and",
        "append a row to `identity/judged-identifiers.csv` (columns `deployable,ref,attribute,value,source,basis`):",
        "`k8s.deployment.name` (or `custom: <kind> name`), the workload's name, its manifest `file:line`, basis",
        "`judgment: <evidence>`; or, when it runs none, nothing.",
        "",
    ] + ([
        f"The register is `{reg.resolve().as_posix()}`; every `identity/` path above is in it."
        + (f" Each `source` is a path in `{pathlib.Path(workspace).as_posix()}`." if workspace else ""),
        "",
        f"Write nothing else, except, LAST, once every row above is written: the file `{JUDGED_DONE}` (one line,",
        "`done`). Without it your judgments count as not done.",
    ] if mark else [
        "Write nothing else. When done, the session runs",
        "`reconcile.py --upgrade-identity <register> --after-judgments --backup <new folder>`.",
    ]) + [
        "",
        "## Parts no rule placed",
        "",
        "| id | name | part_kind | source |",
        "|---|---|---|---|",
    ]
    lines += [f"| {r['subject_id']} | {r.get('name', '')} | {r.get('part_kind', '')} | {r.get('source', '')} |"
              for r in cands]
    lines += ["", "## Workloads no image matched", "", "| workload | image | source | candidates |", "|---|---|---|---|"]
    lines += [f"| {w.get('workload', '')} | {w.get('image', '')} | {w.get('source', '')} | {w.get('candidates', '')} |"
              for w in unmatched]
    (reg / JUDGE_PROMPT).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not (reg / JUDGED_IDENTIFIERS).is_file():
        tables.write(reg / JUDGED_IDENTIFIERS, identity.COLS, [])
    return len(cands) + len(unmatched)


def apply(reg, notes):
    """Steps 3-4: fold (merge, or name a single reader's parts), re-point and rename, every change recorded."""
    reg = pathlib.Path(reg)
    before = parts(tables.dicts(reg / "subjects.csv"))
    ident = identity.load(reg) or {}
    rec = Recorder(reg)
    old_names = {r["subject_id"]: (r.get("name") or "").strip() for r in before}
    split = (reg / layout.UNITS_CSV).is_file()
    if split:
        merge.merge(reg)
        alias = {r["subject_id"]: r["alias_of"] for r in tables.dicts(reg / merge.PART_IDS)
                 if (r.get("alias_of") or "").strip()}
        repoint(reg, alias, rec, notes)
        rec.flush()
        merge.merge(reg)
        now = {r["subject_id"]: (r.get("name") or "").strip() for r in parts(tables.dicts(reg / "subjects.csv"))}
        pairs = [(old_names[s], now[s]) for s in old_names if s in now and now[s] != old_names[s]]
        pairs += [(old_names[was], now[sid]) for was, sid in sorted(alias.items())
                  if was in old_names and sid in now and old_names[was] != now[sid]]
        news = {}
        for old, new in pairs:
            news.setdefault(old, set()).add(new)
        renames = {old: next(iter(ns)) for old, ns in news.items() if len(ns) == 1}
        notes += [f"JUDGMENT: the old name {old!r} became {sorted(ns)}; text naming it is left as it is"
                  for old, ns in sorted(news.items()) if len(ns) > 1]
        notes += [f"folded: {was} into {sid}" for was, sid in sorted(alias.items(), key=lambda x: merge.id_num(x[0]))
                  if was in old_names]
    else:
        renames = single_reader(reg, ident, rec, notes)
    renamed_text(reg, renames, rec, notes)
    rec.flush()
    if split:
        merge.merge(reg)
    return before


def undone_repoints(reg, live):
    """A fold undone (a person's correction) restores the part's row, never the cells the upgrade moved off it: each
    such re-point, listed for the person to move back or keep."""
    out = []
    for r in go.table_rows(reg, "corrections-applied")[1]:
        m = re.match(r"^(S\d+)\b", r.get("before") or "")
        if (r.get("correction_id") or "").startswith("identity-") and m and m.group(1) in live \
                and not (r.get("after") or "").startswith(m.group(1)) and (r.get("column") or "") != "name":
            out.append(f"JUDGMENT: {r['correction_id']} moved {r.get('table')}.csv {r.get('row')} {r.get('column')} "
                       f"off {m.group(1)}, a part again since its fold was undone; move it back by a correction, or "
                       "keep it on " + (r.get("after") or "")[:12])
    return out


def close(reg, before, notes):
    after = parts(tables.dicts(reg / "subjects.csv"))
    notes.insert(1, f"parts: {len(before)} before, {len(after)} after")
    judged = merge.judged_merges(reg)
    notes.append(f"judgments to review: {len(judged)} in identity/merges.csv, and every identifier whose basis "
                 "starts `judgment`")
    notes += undone_repoints(reg, {r.get("subject_id") for r in after})
    stale = sorted(p.name for p in reg.glob("stage-*") if p.is_dir())
    if stale:
        notes.append("stale prose, regenerate with the kit's page commands (never rewritten): " + ", ".join(stale))
    return notes


def back_up(reg, backup):
    """The register copied to `backup`, a new folder outside it, before anything changes (the run lock left out, so a
    restored copy is never locked). Refuses (ValueError) without one."""
    if not backup:
        raise ValueError("refused: --backup <folder> is required; the upgrade changes content")
    backup = pathlib.Path(backup).resolve()
    if backup.exists() or reg in backup.parents or backup == reg:
        raise ValueError(f"refused: the backup {backup} must be a new folder outside the register")
    import run_lock
    shutil.copytree(reg, backup, ignore=lambda d, names: [n for n in names if n == run_lock.LOCK and pathlib.Path(d)
                                                          == reg])
    return backup


def upgrade(reg, backup, read_identity=True, workspace=None):
    """Upgrade one register in place; returns the report's lines. Refuses (ValueError) without a backup. Ends by
    writing identity/judge-prompt.md, the one agent launch the judgments owe, when there is anything to judge."""
    reg = pathlib.Path(reg).resolve()
    notes = [f"backup: {back_up(reg, backup)}"]
    if read_identity:
        rows, unmatched = identity.write(reg, workspace)
        notes.append(f"identity: {len(rows)} identifier row(s); {len(unmatched)} workload(s) left for the model "
                     "to join (identity/unmatched.csv)")
    before = apply(reg, notes)
    n = judge_prompt(reg)
    if n and not (reg / layout.UNITS_CSV).is_file():
        notes.append(f"NEXT: {n} case(s) no rule could place, listed in {JUDGE_PROMPT}. This register has no units, so "
                     "--after-judgments applies nothing here: record each fold as a correction to subjects.csv "
                     "(go.py --apply-correction), with its basis")
    elif n:
        notes.append(f"NEXT: {n} case(s) no rule could place. Launch one agent with the prompt in {JUDGE_PROMPT} "
                     "(it writes its judgments, each with its basis and evidence, into identity/), then run "
                     "reconcile.py --upgrade-identity <register> --after-judgments --backup <new folder>")
    return close(reg, before, notes)


def after_judgments(reg, backup):
    """The model's judgments applied, as a draft: the same fold, re-pointing and renaming, every change recorded.
    Refuses (ValueError) without a new backup folder, and on a register with no units, whose fold reads no judgment."""
    reg = pathlib.Path(reg).resolve()
    if not (reg / layout.UNITS_CSV).is_file():
        raise ValueError("refused: this register was read by a single reader (no units/units.csv), and the upgrade "
                         "applies no judgment to it; record each merge in identity/merges.csv as a correction to "
                         "subjects.csv by hand (go.py --apply-correction), with its basis")
    notes = [f"backup: {back_up(reg, backup)}",
             "judgments applied from identity/merges.csv and identity/judged-identifiers.csv"]
    before = apply(reg, notes)
    return close(reg, before, notes)


def main(argv):
    argv = list(argv)
    backup = ws = None
    for flag in ("--backup", "--workspace"):
        if flag in argv:
            i = argv.index(flag)
            val = argv[i + 1] if i + 1 < len(argv) else None
            del argv[i:i + 2]
            backup, ws = (val, ws) if flag == "--backup" else (backup, val)
    after = "--after-judgments" in argv
    argv = [a for a in argv if a != "--after-judgments"]
    if len(argv) != 1:
        print(__doc__)
        return 2
    import run_lock  # the register is written by one run at a time
    run_lock.refuse_unless_register(argv)
    run_lock.guard(argv[0])
    try:
        notes = after_judgments(argv[0], backup) if after else upgrade(argv[0], backup, workspace=ws)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    print("\n".join(notes))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
