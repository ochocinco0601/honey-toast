"""Reading the map's record: its tables as rows, and the few readings of a row that the inspection and the pages share.

The map's own inspection (check_map.py) reads the record through this module, never through the page builder
(flow_outputs.py), so a change to the pages cannot change what the inspection finds."""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from capability_views import read_csv, join_alerts, alert_columns_left  # noqa: E402
import go  # noqa: E402

TABLES = ["about", "flows", "capabilities", "stages", "steps", "subjects", "participation", "measures", "lifecycle",
          "failure-modes", "remedies", "step-impact", "case-attributes", "agent-system", "measure-gaps", "sources",
          "expectations", "alerts"]
PRODUCT_NAMES = "product-names.csv"  # in the register: name, source (where the name is written so)


def cell(v):
    """A register value made safe for a markdown table cell: a pipe would end the cell."""
    return (v or "").replace("|", "\\|").replace("\n", " ")


def norm(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def vouched_products(rows):
    """The product names the register declares that the check may accept: each with a source, one word, and holding
    no dot, underscore, backtick or slash, so no declaration can let a code identifier through."""
    return {n for r in rows for n in [norm(r.get("name"))]
            if n and norm(r.get("source")) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\-]*", n)}


# files.csv `not read` reasons that say a read was blocked or failed, not that the file was skipped on purpose
# (generated code, over the reading budget, ran out of room, read in part, off this stage's path)
FAILED_READ = re.compile(r"block|hook|filter|denied|permission|fail|error|refus|could not|cannot|unable", re.I)
NAMED = 10  # files named in the unread line; the rest counted


def unread_files(reg):
    """The files of the system's code that the survey (survey.csv, column unread_files) or the code reader (the fact
    base's unread_files) could not read, each once. A register made before either listed them has none."""
    import json
    reg = pathlib.Path(reg)
    found = []
    for r in read_csv(reg / "survey.csv"):
        for x in (r.get("unread_files") or "").split("; "):
            x = x.strip()
            if x:
                found.append(x.rsplit(" (", 1)[0] if x.endswith(")") else x)  # "path (reason)"
    try:
        base = json.loads((reg / "fact-base.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        base = {}
    for u in (base.get("unread_files") or []) if isinstance(base, dict) else []:
        f = u.get("file") if isinstance(u, dict) else u
        if f:
            found.append(str(f))
    units = reg / "units"
    for p in sorted(units.glob("*/files.csv")) if units.is_dir() else []:  # a reader's or mapping agent's files
        for r in read_csv(p):  # only a read that was blocked or failed; one skipped on purpose is said where it is
            if (r.get("status") or "").strip() == "not read" and FAILED_READ.search(r.get("reason") or ""):
                found.append((r.get("path") or "").strip())
    found = [f for f in found if f]
    out = []
    for f in (f.replace(chr(92), "/").strip("/") for f in found):
        # the survey and the code reader may name one file from different folders: a path that ends the other is one
        if not any(f == g or f.endswith("/" + g) or g.endswith("/" + f) for g in out):
            out.append(f)
    return out


def unread_line(reg):
    """One plain line for the person when any file of the code could not be read: how many, and what it may cost;
    else the empty string."""
    n = len(unread_files(reg))
    if not n:
        return ""
    return (f"{n} file{'s' if n > 1 else ''} of the system's code could not be read, so mapping may have missed "
            f"code in {'those files' if n > 1 else 'that file'}.")


def unread_named(reg):
    """The files unread_line counts, named, for the map's inspection report (the brief's prose names no file):
    "" when there are none."""
    files = unread_files(reg)
    if not files:
        return ""
    more = f", and {len(files) - NAMED} more" if len(files) > NAMED else ""
    return "Not read: " + ", ".join(f"`{f}`" for f in files[:NAMED]) + more + "."


def load(reg):
    reg = pathlib.Path(reg)
    R = {t: [{k: cell(v) for k, v in r.items()} for r in read_csv(reg / f"{t}.csv")] for t in TABLES}
    R["_alert_columns_left"] = alert_columns_left(reg)
    join_alerts(R["measures"], R["alerts"])  # each measure carries its alert, if chosen, from alerts.csv
    R["hop-failures"] = read_csv(HERE / "method" / "hop-failures.csv")
    R["measure-forms"] = read_csv(HERE / "method" / "measure-forms.csv")
    R["agent-questions"] = read_csv(HERE / "method" / "agent-questions.csv")
    R["impact"] = read_csv(HERE / "method" / "impact.csv") if (HERE / "method" / "impact.csv").exists() else []
    R["products"] = vouched_products(read_csv(reg / PRODUCT_NAMES))
    R["corrections"] = read_csv(reg / "corrections.csv")  # later stages' requests to mapping; not part of the map
    R["alert_owners"] = go.alert_owners(reg)  # an alert a finished flow made is that flow's, never a further flow's
    R["_name"] = reg.name
    return R


def split_top(text, seps=";"):
    """Split on separators that are not inside parentheses."""
    out, depth, cur = [], 0, ""
    for ch in text or "":
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        if ch in seps and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [x for x in out if x]


def strip_parens(text):
    out, depth = "", 0
    for ch in text or "":
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif not depth:
            out += ch
    return out


def state(s):
    s = (s or "").strip()
    if s.startswith("(none)"):
        return "(none)"
    return re.split(r"\s+\(", s)[0].strip()


def resolve(token, subj):
    t = token.strip()
    m = re.match(r"([A-Z]\d+)\b", t)
    if m and m.group(1) in subj:
        return m.group(1)
    low = t.lower()
    for sid, s in subj.items():
        if s.get("kind") == "element" and (s["name"].lower() == low or state(s["name"]).lower() == low):
            return sid
    first = low.split()[0] if low.split() else ""
    hits = [sid for sid, s in subj.items() if s.get("kind") == "element" and s["name"].lower().split()[:1] == [first]]
    return hits[0] if len(hits) == 1 else None


def parts(text, subj, unresolved):
    out = []
    text = strip_parens(text)
    # a part's own name may hold a comma ("anyone, the code checks no identity"): taken whole before the split
    for sid, s in subj.items():
        name = (s.get("name") or "").strip()
        if s.get("kind") == "element" and ("," in name or ";" in name):
            hit = re.search(r"(?<![^\s;,])" + re.escape(name) + r"(?![^\s;,])", text, re.I)
            if hit:
                if sid not in out:
                    out.append(sid)
                text = text[:hit.start()] + text[hit.end():]
    for tok in split_top(text, ";,"):
        sid = resolve(tok, subj)
        if sid and sid not in out:
            out.append(sid)
        elif not sid:
            unresolved.append(tok)
    return out


# ---------------------------------------------------------------- an AI agent's decisions (mapping, Step 7)

def listed(text):
    """The `;`-separated values of a cell, each with its spacing made even."""
    return [norm(x) for x in (text or "").split(";") if norm(x)]


def decision_class(p, col="decision_point"):
    """`yes` or `no` from a participation row's `decision_point` cell (or its `reply_decision_point`), or None when it
    is not classed."""
    m = re.match(r"\s*(yes|no)\s*:", p.get(col) or "")
    return m.group(1) if m else None


def chain_findings(R):
    """The agent-system.csv rows classed wrongly: ("not an action", row, value) for a `decision_point` set on a row
    that is not an action of the chain, ("neither", row, value) for an action's that is neither `yes:` nor `no:`."""
    for a in R["agent-system"]:
        v = norm(a.get("decision_point"))
        if v and a.get("element") != "action":
            yield "not an action", a, v
        elif v and not decision_class(a):
            yield "neither", a, v


def chain_failures(R):
    """An agent-system.csv action row's `decision_point` is blank, `yes:` or `no:`; any other row leaves it blank."""
    err = []
    for kind, a, v in chain_findings(R):
        if kind == "not an action":
            err.append(f"agent-system.csv {a.get('agent')} {a.get('id')}: decision_point is set on a {a.get('element')} "
                       "row; only an action of the agent's chain is classed")
        else:
            err.append(f"agent-system.csv {a.get('agent')} {a.get('id')}: class it in decision_point, `yes:` where a later "
                       "call of the chain relies on what this model call writes, `no:` or blank where not, and why "
                       f"(got {v!r})")
    return err


def agent_rows(R, flow_id):
    subj = {s["subject_id"]: s for s in R["subjects"]}
    stages = {st["stage"] for st in R["stages"] if st["flow"] == flow_id}
    step_ids = [s["step"] for s in R["steps"] if s["stage"] in stages]
    return [p for p in R["participation"] if p["step"] in step_ids and p.get("involvement") in ("performs", "supports")
            and subj.get(p["subject_id"], {}).get("part_kind") == "LLM agent"]


def point_key(p, op):
    return f"{p['subject_id']} {op}" if op else f"{p['subject_id']} at step {p['step']}"


def class_findings(R, flow_id):
    """The agent rows of a flow classed wrongly: ("reply", row) for a reply not classed, ("tool", row) for a tool not
    classed, and ("both ways", row, operation, {class: [steps]}) for one agent's tool classed yes and no."""
    seen, first = {}, {}
    for p in agent_rows(R, flow_id):
        if not decision_class(p, "reply_decision_point"):
            yield "reply", p
        c = decision_class(p)
        if not c:
            yield "tool", p
            continue
        for op in listed(p.get("operation")) or [None]:
            seen.setdefault(point_key(p, op), {}).setdefault(c, []).append(p["step"])
            first.setdefault(point_key(p, op), (p, op))
    for key, by in seen.items():
        if len(by) > 1:
            yield "both ways", *first[key], by


def class_failures(R, flow_id):
    """An agent's participation row says whether its tool is a decision point: `yes:` or `no:` and why.
    A row not classed fails, and so does one agent's tool classed both ways, since the point is the agent and tool.
    Its reply is classed the same way, in `reply_decision_point`, on every agent row."""
    err = []
    for kind, p, *more in class_findings(R, flow_id):
        if kind == "reply":
            err.append(f"participation.csv {p['subject_id']} step {p['step']}: class the agent's reply in "
                       f"reply_decision_point, `yes:` where the person relies on it, as when it reports or explains a "
                       f"result, `no:` where it only confirms or asks, or replies to no person here, and why "
                       f"(got {p.get('reply_decision_point') or 'nothing'!r})")
        elif kind == "tool":
            err.append(f"participation.csv {p['subject_id']} step {p['step']}: class its tool as a decision point "
                       f"in decision_point, `yes:` where the agent chooses a value that becomes the case's outcome or "
                       f"a person's basis for it, `no:` where it records what a person stated or asked, and why "
                       f"(got {p.get('decision_point') or 'nothing'!r})")
        else:
            op, by = more
            err.append(f"participation.csv {point_key(p, op)}: classed yes at step {', '.join(by['yes'])} and no at step "
                       f"{', '.join(by['no'])}; a decision point is the agent and its tool, so class it one way")
    return err
