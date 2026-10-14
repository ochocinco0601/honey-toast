"""Reconcile an earlier register with this run's new one: match rows by content, class each old row by its citation,
and check each code citation against the files the new walk read. The earlier register is only read, never written.

Usage: python reconcile.py <earlier register> <new register> [--workspace <folder>] [--out <file>]

The workspace is the folder every citation starts from (default: two levels above the new register, as for
bfo-work/<application>/). The report goes to <new register>/reconciliation-<earlier folder name>.md unless --out says.

Only the walk tables are reconciled: flows, lifecycle, stages, steps, subjects, participation, set-aside,
expectations. Rows are matched by what they say: a step's name, a move's states, a part's name without the trailing
"(repository)" an earlier kit put in it, a relationship's two ends and operation. A row whose id is also in the new
register is matched on it only where the two rows name the same thing, because ids belong to one register.

Each old row is classed by its citation, and field by field where a field carries its own:
- `asked:` in the row's citation, or a table whose old how-made.csv row was done by a person: the whole row is carried
  forward cited to the original; where it differs from the new row, a disagreement for a person to settle (the new
  walk does not overrule a person). `asked:` in one field (or in its `<field>_source`) backs that field only, and the
  rest of the row is checked as below;
- `proposed:` with no other citation: dropped, since the new walk proposes afresh;
- a document: what `sources.csv` records as kind `document`, a `§` or a web address. A claim field citing one is
  re-opened in that document, with the cited section beside the claim;
- a file and line: where the new register has the row and says otherwise, a disagreement (the new row stands).
  Where it lacks the row, the file is looked for in the repositories the new walk read, under any path: a citation
  into a clone outside the workspace is re-rooted to the repository of the same name or remote, and never opened where
  it points. Found with the line in range: unchecked, not added (that the line exists does not say it supports the
  row). Missing file or line out of range: not supported by the code. In a repository the new walk never read: not
  assessed;
- no citation at all: not supported by its source.
Matched rows are counted per table, not listed. Every unchecked code-cited row, and every matched one the new row
disagrees with, is printed with its claim beside its cited lines and a blank verdict and
reason, for the model to judge one row at a time; this script never judges whether a line says what a row claims.
Old Step 11 work (stage-<id> folders, failure-modes.csv, remedies.csv) is listed as not carried."""
import argparse
import csv
import pathlib
import re
import sys

KEYS = {
    "flows.csv": ("name",),
    "lifecycle.csv": ("from_state", "move", "to_state"),
    "stages.csv": ("name",),
    "steps.csv": ("name",),
    "subjects.csv": ("name",),
    "participation.csv": ("subject_id", "step"),
    "set-aside.csv": ("item",),
    "expectations.csv": ("party", "stage", "expectation"),
}
CLAIMS = {
    "flows.csv": ("case", "starts_at", "ends_at", "expectation_of", "promise"),
    "lifecycle.csv": ("travels_by", "carried_by", "timing", "if_not", "irreversible"),
    "stages.csv": ("entry", "exit", "promise"),
    "steps.csv": ("right_outcome",),
    "subjects.csv": ("kind", "level", "part_kind", "repository", "owner", "responder"),
    "participation.csv": ("involvement", "operation"),
    "set-aside.csv": ("kind", "why"),
    "expectations.csv": ("satisfied_when", "objective", "objective_source"),
}
IDS = {"flows.csv": "flow_id", "lifecycle.csv": "move_id", "stages.csv": "stage", "steps.csv": "step",
       "subjects.csv": "subject_id", "expectations.csv": "expectation_id"}
CITE = ("source", "source_ref", "basis", "activity")
# A file and its lines: `path:41`, `path:41-60`, `path:79-83, 101-103`. The path keeps a drive letter.
CODE = re.compile(r"((?:[A-Za-z]:)?[\w.~\-/\\]+\.[A-Za-z0-9]+):(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?(?![\w./-]))*)")
PATHLIKE = re.compile(r"(?:[A-Za-z]:)?[\w.~\-/\\]+\.[A-Za-z][A-Za-z0-9]*")
SHOWN = 20  # lines shown per cited range
SECTIONS = (
    ("added_candidates", "Unchecked: not added (the new register lacks them and the cited code line exists, but "
                         "nothing here says the line supports the row)"),
    ("unsupported", "Not supported by the code or by any citation"),
    ("not_assessed", "Not assessed (cited to a repository the new walk never read)"),
    ("disagreements", "Disagreements (code-cited; the new row stands)"),
    ("carry_forward_person", "Carried forward from a person (cite the original person or record, never this register)"),
    ("disagreements_for_a_person", "Disagreements for a person to settle (a person-backed old row and the new walk)"),
    ("reopen_in_document", "Re-open in the document (carry forward cited to the document only if it says so)"),
    ("dropped_proposed", "Dropped (proposed: rows; the new walk proposes afresh)"),
    ("to_judge", "Claims beside their cited lines (for each row, write a verdict: supported, not supported or not "
                 "assessed, and the reason)"),
)


def norm(v):
    return re.sub(r"[^a-z0-9]+", " ", (v or "").lower()).strip()


def table(reg, name):
    p = reg / name
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def citations(text):
    """[(path, [(first, last), ...])] for every file-and-line citation in a cell."""
    out = []
    for m in CODE.finditer(text or ""):
        spans = []
        for part in m.group(2).split(","):
            a, _, b = part.strip().partition("-")
            spans.append((int(a), int(b or a)))
        out.append((m.group(1).replace("\\", "/"), spans))
    return out


def folders(ws):
    return sorted(p.name for p in ws.iterdir() if p.is_dir()) if ws and ws.is_dir() else []


def repositories(reg, ws=None):
    """{name or remote: (workspace folder, commit)} for every repository a register's sources.csv says it read.
    A release-1 sources.csv has no repository column: a workspace folder counts where a code source's description
    names it."""
    out = {}
    for r in table(reg, "sources.csv"):
        m = re.search(r"\bHEAD ([0-9a-f]{7,40})", r.get("what") or "")
        commit = (r.get("commit") or "").strip() or (m.group(1) if m else "")
        named = [(r.get("repository") or "").strip()]
        if not named[0]:
            if (r.get("kind") or "").strip().lower() != "code":
                continue
            text = r.get("what") or ""
            named = [f for f in folders(ws) if re.search(rf"(?<![\w.-]){re.escape(f)}(?![\w.-])", text)]
        for n in named:
            out[n] = (n, commit)
            remote = (r.get("remote") or "").strip().rstrip("/")
            if remote:
                out.setdefault(re.sub(r"\.git$", "", re.split(r"[/:]", remote)[-1]), (n, commit))
    return out


def documents(*regs):
    """Paths the registers' sources.csv record as kind `document`."""
    out = set()
    for reg in regs:
        for r in table(reg, "sources.csv"):
            if (r.get("kind") or "").strip().lower() == "document":
                out.update(m.group(0).replace("\\", "/") for m in PATHLIKE.finditer(r.get("what") or ""))
    return out


def is_doc(path, docs):
    p = path.replace("\\", "/")
    return any(p == d or p.endswith("/" + d) for d in docs)


def backing(text, docs):
    """What a cell rests on: person, proposed, document, code, or None (nothing of its own)."""
    t = (text or "").strip()
    if not t:
        return None
    if "asked:" in t.lower():
        return "person"
    if t.lower().startswith("proposed:"):
        return "proposed"
    if any(not is_doc(p, docs) for p, _ in citations(t)):
        return "code"
    if any(is_doc(m.group(0), docs) for m in PATHLIKE.finditer(t)) or re.search(r"§|https?://", t):
        return "document"
    return None


def plain(name, repos):
    """A part's name without the trailing "(repository)" an earlier kit put in it."""
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", name or "")
    return m.group(1) if m and m.group(2).strip().lower() in repos else (name or "")


class Names:
    """A register's id-to-name lookups, for keys that go through another table."""

    def __init__(self, reg, repos):
        def look(name, idcol, col="name"):
            return {r.get(idcol, ""): r.get(col, "") for r in table(reg, name)}
        self.repos = repos
        self.subjects = {k: plain(v, repos) for k, v in look("subjects.csv", "subject_id").items()}
        self.steps = look("steps.csv", "step")
        self.stages = look("stages.csv", "stage")


def key(names, name, row):
    if name == "participation.csv":
        return (norm(names.subjects.get(row.get("subject_id"), row.get("subject_id"))),
                norm(names.steps.get(row.get("step"), row.get("step"))))
    if name == "subjects.csv" and (row.get("kind") or "").strip().lower() == "relationship":
        return ("relationship", norm(names.subjects.get(row.get("from_id"), row.get("from_id"))),
                norm(names.subjects.get(row.get("to_id"), row.get("to_id"))), norm(row.get("operation")))
    if name == "subjects.csv":
        return (norm(plain(row.get("name"), names.repos)),)
    if name == "expectations.csv":
        return (norm(row.get("party")), norm(names.stages.get(row.get("stage"), row.get("stage"))),
                norm(row.get("expectation")))
    return tuple(norm(row.get(c)) for c in KEYS[name])


def same_thing(a, b):
    """Whether two keys name the same thing: a relationship's two ends agree; otherwise at least half the words
    are shared."""
    if a[:1] == ("relationship",) or b[:1] == ("relationship",):
        return a[:3] == b[:3]
    wa, wb = set(" ".join(a).split()), set(" ".join(b).split())
    return bool(wa | wb) and len(wa & wb) * 2 >= len(wa | wb)


def person_tables(reg):
    """Tables an old how-made.csv row says a person confirmed or wrote by hand."""
    out = set()
    for r in table(reg, "how-made.csv"):
        if re.search(r"person|by hand", r.get("done_by", ""), re.I):
            out.update(n for n in KEYS if n in r.get("came_out", ""))
    return out


def row_kind(name, row, confirmed, docs):
    cites = " ".join(row.get(c) or "" for c in CITE)
    every = " ".join(v or "" for v in row.values() if isinstance(v, str))
    if "asked:" in cites.lower():
        return "person"
    if cites.strip().lower().startswith("proposed:") and not CODE.search(every):
        return "proposed"
    if name in confirmed:
        return "person"
    b = backing(cites, docs)
    if b in ("code", "document"):
        return b
    if CODE.search(every):
        return "code"
    if cites.strip() and "proposed:" not in cites.lower():
        return "document"
    if "proposed:" in every.lower():
        return "proposed"
    return "none"


def field_backing(row, docs):
    """{field: backing} for the fields that carry their own citation; `<field>_source` backs `<field>`."""
    out = {}
    for c, v in row.items():
        if not isinstance(c, str) or c in CITE:
            continue
        b = backing(row.get(f"{c}_source"), docs) or backing(v, docs)
        if b:
            out[c] = b
    return out


def differs(name, old, new, only=None, skip=()):
    out = []
    for c in CLAIMS[name]:
        if (only is not None and c not in only) or c in skip:
            continue
        a, b = (old.get(c) or "").strip(), (new.get(c) or "").strip()
        if a and b and not a.lower().startswith("proposed:") and norm(a) != norm(b):
            out.append(f"{c}: earlier `{a}`, new `{b}`")
    return out


def resolve(path, ws, reads):
    """(file or None, workspace folder or None, note). A path outside the workspace is never opened: it is re-rooted
    to the read repository named in it."""
    p = path.replace("\\", "/")
    root = str(ws).replace("\\", "/").rstrip("/") + "/"
    if p.lower().startswith(root.lower()):
        p = p[len(root):]
    absolute = bool(re.match(r"[A-Za-z]:/|/", p))
    parts = [s for s in p.split("/") if s not in ("", ".")]
    if not parts:
        return None, None, ""
    if not absolute:
        if parts[0] in reads:
            f = ws.joinpath(reads[parts[0]][0], *parts[1:])
            return (f if f.is_file() else None), reads[parts[0]][0], ""
        for folder, _ in sorted(set(reads.values())):
            if ws.joinpath(folder, *parts).is_file():
                return ws.joinpath(folder, *parts), folder, ""
    missing = None
    for i, seg in enumerate(parts):
        if seg in reads:
            folder = reads[seg][0]
            f = ws.joinpath(folder, *parts[i + 1:])
            where = "cited outside the workspace" if absolute else "cited under another folder"
            note = f"{where}, re-rooted to {folder}/{'/'.join(parts[i + 1:])}"
            if f.is_file():
                return f, folder, note
            missing = missing or (None, folder, note)
    return missing or (None, None, "")


def excerpt(f, spans):
    """(lines shown, problem or "") for the cited spans of a file. Only the first line cited decides: a later span
    past the end (often a line of another file, after a comma) is shown as a note."""
    text = f.read_text(encoding="utf-8", errors="replace").splitlines()
    shown, problems = [], []
    for n, (a, b) in enumerate(spans):
        if a > len(text) or a < 1:
            if n == 0:
                problems.append(f"has {len(text)} lines, not {a}")
            else:
                shown.append(f"(note: the file has {len(text)} lines, not {a})")
            continue
        if b > len(text):
            shown.append(f"(note: the file has {len(text)} lines, not {b})")
            b = len(text)
        last = min(b, a + SHOWN - 1)
        shown += [f"{n}: {text[n - 1]}" for n in range(a, last + 1)]
        if last < b:
            shown.append(f"... {b - last} more lines to {b}: open the file")
    return shown, "; ".join(problems)


def section(f, text):
    """The lines of a document under the heading the citation names, or its first lines."""
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    named = [norm(s) for s in re.split(r"[,;]", text) if norm(s)]
    for i, line in enumerate(lines):
        h = re.match(r"^(#+)\s*(.*)", line)
        if h and any(n and n in norm(h.group(2)) for n in named):
            end = next((j for j in range(i + 1, len(lines))
                        if re.match(rf"^#{{1,{len(h.group(1))}}}\s", lines[j])), len(lines))
            return lines[i:min(end, i + SHOWN)]
    return lines[:SHOWN]


def doc_cited(text, ws, reads, docs):
    """The documents a cell cites, each with the section or lines it names."""
    out = []
    for m in PATHLIKE.finditer(text or ""):
        d = m.group(0).replace("\\", "/")
        if not is_doc(d, docs):
            continue
        f = ws / d if (ws / d).is_file() else resolve(d, ws, reads)[0]
        if f is None:
            out.append(f"`{d}`: not found in the workspace")
            continue
        rest = (text[m.end():].split(")")[0]).lstrip(":, ")
        spans = next((s for p, s in citations(text) if p == d), None)
        body = excerpt(f, spans)[0] if spans else section(f, rest)
        out.append("\n".join([f"`{d}`" + (f" ({rest})" if rest and not spans else "")] + body))
    if not out and re.search(r"§|https?://", text or ""):
        out.append(f"`{text.strip()}`: open it where it says")
    return "\n".join(out)


def claim(row, skip):
    return "; ".join(f"{c}: {v}" for c, v in row.items()
                     if isinstance(c, str) and v and c not in ("source", "source_ref") and c not in skip)


def check(cites, ws, reads, old_reads):
    """[(verdict, why, cited lines)] for code citations, at the files the new walk read."""
    out = []
    for path, spans in cites:
        found, folder, note = resolve(path, ws, reads)
        where = ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in spans)
        if folder is None:
            out.append(("not_assessed", f"{path}:{where} is in no repository the new walk read", ""))
            continue
        commit = next((c for n, (fo, c) in reads.items() if fo == folder and c), "")
        if found is None:
            out.append(("unsupported", f"{path} does not exist at the new walk's commit"
                        + (f" ({note})" if note else ""), ""))
            continue
        lines, problem = excerpt(found, spans)
        if problem:
            out.append(("unsupported", f"{path} {problem}", ""))
            continue
        moved = old_reads.get(folder, ("", ""))[1]
        stale = (f"; the earlier register read {folder} at {moved}, the new walk at {commit}: re-locate the code "
                 "before judging") if moved and commit and not (moved.startswith(commit) or
                                                               commit.startswith(moved)) else ""
        rel = found.relative_to(ws).as_posix()
        head = f"`{path}:{where}`" + (f", {note}" if note else "") + (f", at {commit}" if commit else "") + \
               (f" ({rel})" if note else "")
        out.append(("added_candidates", f"{path}:{where} exists" + (f" ({note})" if note else "") + stale,
                    "\n".join([head] + lines)))
    return out


def reconcile(old, new, ws):
    report = {k: [] for k, _ in SECTIONS}
    report["not_carried"] = []
    report["matched"] = {}
    reads, old_reads, confirmed = repositories(new, ws), repositories(old, ws), person_tables(old)
    repos = {n.lower() for n in list(reads) + list(old_reads) + folders(ws)}
    docs = documents(old, new)
    old_names, new_names = Names(old, repos), Names(new, repos)
    for name in KEYS:
        idcol = IDS.get(name)
        new_rows, by_id = {}, {}
        for r in table(new, name):
            new_rows.setdefault(key(new_names, name, r), []).append(r)
            if idcol and r.get(idcol):
                by_id[r[idcol]] = r
        for row in table(old, name):
            k = key(old_names, name, row)
            candidates = new_rows.get(k, [])
            match = min(candidates, key=lambda n: len(differs(name, row, n))) if candidates else None
            if match is None and idcol and row.get(idcol) in by_id and \
                    same_thing(k, key(new_names, name, by_id[row[idcol]])):
                match = by_id[row[idcol]]
            kind = row_kind(name, row, confirmed, docs)
            fields = field_backing(row, docs)
            item = {"table": name, "row": row, "why": ""}
            if match:
                report["matched"][name] = report["matched"].get(name, 0) + 1
            if kind == "person":
                person = [c for c in CLAIMS[name] if row.get(c)] + [c for c in CITE if row.get(c)]
            else:
                person = [c for c, b in fields.items() if b == "person"]
            if person:
                report["carry_forward_person"].append(dict(item, fields=[(c, row[c]) for c in person]))
                d = differs(name, row, match, only=person) if match else []
                if d:
                    report["disagreements_for_a_person"].append(dict(item, why="; ".join(d)))
            if kind == "person":
                continue
            if kind == "proposed":
                report["dropped_proposed"].append(item)
                continue
            docf = [c for c in CLAIMS[name] if fields.get(c) == "document" and c not in person and
                    (match is None or norm(row.get(c)) != norm(match.get(c)))]
            if docf:
                report["reopen_in_document"].append(dict(
                    item, fields=[(c, row[c]) for c in docf], verdict="", reason="",
                    cited="\n".join(doc_cited(row[c], ws, reads, docs) for c in docf)))
            skip = set(person) | {c for c, b in fields.items() if b == "document"}
            if match:
                d = differs(name, row, match, skip=skip)
                if d:
                    report["disagreements"].append(dict(item, why="; ".join(d)))
            text = " ".join(row.get(c) or "" for c in CITE)
            cites = [c for c in citations(text) if not is_doc(c[0], docs)] or \
                [c for f, v in row.items() if isinstance(f, str) and f not in skip
                 for c in citations(v) if not is_doc(c[0], docs)]
            if kind == "code" and cites:
                verdicts = check(cites, ws, reads, old_reads)
                lines = "\n".join(v[2] for v in verdicts if v[2])
                if match:
                    if lines and d:
                        report["to_judge"].append(dict(
                            item, match="matched a new row that says otherwise",
                            claim=claim(row, skip), cited=lines, verdict="", reason="",
                            why="; ".join(w for v, w, _ in verdicts if v != "added_candidates")))
                    continue
                order = ("unsupported", "not_assessed", "added_candidates")
                worst = min((v for v, _, _ in verdicts), key=order.index)
                report[worst].append(dict(item, why="; ".join(w for _, w, _ in verdicts)))
                if worst == "added_candidates":
                    report["to_judge"].append(dict(item, match="not in the new register", claim=claim(row, skip),
                                                   cited=lines, verdict="", reason="", why=""))
                continue
            if match or docf or person:
                continue
            if kind == "document":
                report["reopen_in_document"].append(dict(
                    item, fields=[], verdict="", reason="", cited=doc_cited(text, ws, reads, docs) or text.strip()))
            else:
                report["unsupported"].append(dict(item, why="no citation"))
    report["to_judge"].sort(key=lambda i: i["match"] != "not in the new register")
    for p in sorted(old.glob("stage-*")):
        if p.is_dir():
            report["not_carried"].append(f"{p.name}/ (alerts and runbook: re-derive in that stage's own run)")
    for name in ("failure-modes.csv", "remedies.csv"):
        n = len(table(old, name))
        if n:
            report["not_carried"].append(f"{name}: {n} rows (Step 11 work is re-derived, never carried)")
    return report


def ident(r):
    if r.get("subject_id") and r.get("step") and not r.get("name"):
        return f"{r['subject_id']} in step {r['step']}"
    return next((r[c] for c in ("name", "move", "item", "expectation", "step", "subject_id") if r.get(c)), "?")


def block(i, head):
    out = [f"### {i['table']} `{ident(i['row'])}`" + (f" ({head})" if head else ""), ""]
    if i.get("claim"):
        out += [f"Claim: {i['claim']}", ""]
    if i.get("fields"):
        out += ["Claim: " + "; ".join(f"{c}: `{v}`" for c, v in i["fields"]), ""]
    if i.get("why"):
        out += [f"Note: {i['why']}", ""]
    out += ["Cited:", "", "```text", *(i.get("cited") or "(nothing to show)").splitlines(), "```", "",
            f"Verdict: {i.get('verdict', '')}".rstrip(), f"Reason: {i.get('reason', '')}".rstrip(), ""]
    return out


def render(old, new, report):
    lines = [f"# Reconciliation: {old} against {new}", "",
             "The earlier register was read, never written, and nothing in this report is added to the new "
             "register: it is a report for a person. Counts: " +
             ", ".join(f"{k.replace('_', ' ')} {len(report[k])}" for k, _ in SECTIONS) +
             f", not carried {len(report['not_carried'])}.", "",
             "## Matched (counted, not listed)", "",
             "The new walk has these rows. Where a matched row says otherwise, it is under Disagreements.", ""]
    lines += [f"- {t}: {n}" for t, n in sorted(report.get("matched", {}).items())] or ["- none"]
    lines.append("")
    for k, title in SECTIONS:
        lines += [f"## {title}", ""]
        if k in ("to_judge", "reopen_in_document"):
            for i in report[k]:
                lines += block(i, i.get("match", ""))
            lines.append("" if report[k] else "- none\n")
            continue
        for i in report[k]:
            r = i["row"]
            if k == "carry_forward_person":
                lines.append(f"- {i['table']} `{ident(r)}`: " + "; ".join(f"{c}: `{v}`" for c, v in i["fields"]) +
                             ". Carry each field as written, cited to the person or record it names.")
                continue
            cite = next((r[c] for c in CITE if r.get(c)), "")
            lines.append(f"- {i['table']} `{ident(r)}`" + (f" [{cite}]" if cite else "") +
                         (f": {i['why']}" if i["why"] else ""))
        lines.append("" if report[k] else "- none\n")
    lines += ["## Not carried (Step 11 work)", ""] + [f"- {s}" for s in report["not_carried"]] + \
             ([] if report["not_carried"] else ["- none"])
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--workspace")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    old, new = pathlib.Path(a.old).resolve(), pathlib.Path(a.new).resolve()
    if old == new:
        sys.exit("the earlier register and the new one are the same folder")
    for p in (old, new):
        if not p.is_dir():
            sys.exit(f"not a folder: {p}")
    ws = pathlib.Path(a.workspace).resolve() if a.workspace else new.parent.parent
    report = reconcile(old, new, ws)
    out = pathlib.Path(a.out) if a.out else new / f"reconciliation-{old.name}.md"
    if out.resolve().is_relative_to(old):
        sys.exit("refused: the report would be written into the earlier register")
    text = render(old, new, report)
    out.write_text(text, encoding="utf-8")
    print(text.splitlines()[2])
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
