"""Draws the design-for-operations views of one capability from its register.

    python capability_views.py REGISTER [--out PAGE] [--check] [--open STAGES]

REGISTER is a folder of tables in the shape of register-template/ (defined in register-template/REGISTER.md).
The method's closed lists are read from method/ beside this file. Writes one HTML page; with --check, only lists
what in the register points nowhere or sits outside the closed lists. Python standard library only.

The views are design-time: what the capability is, what carries each step, where it could be seen and where it
cannot. Nothing here reads or shows a live value.
"""
import argparse
import csv
import html
import json
import pathlib
import re
from types import SimpleNamespace
import sys

HERE = pathlib.Path(__file__).resolve().parent
METHOD = HERE / "method"

TABLES = ["about", "capabilities", "flows", "stages", "steps", "subjects", "participation", "agent-system",
          "measures", "step-impact", "case-attributes", "how-made", "sources"]
COUNTED_ON = ("cases", "events", "requests", "resources", "runs")
LEVELS = ("component", "external dependency", "")
RECOVERY = ("moves on", "stranded", "not created", "")
AGENT_ELEMENTS = ("run", "operation", "agent part", "dependency")
DONE_BY = ("tool", "model drafting", "person confirming", "by hand")
SOURCE_KINDS = ("code", "document", "person", "tool output")
CITE = re.compile(r"\.\w{1,8}:\s?\d|asked:|§|https?://")
SOURCE_COLS = ("source", "source_ref", "basis", "activity")


# ---------------------------------------------------------------- reading

def read_csv(path, malformed=None):
    """Rows as dicts. A row with more fields than the header is kept without the extras and noted in `malformed`."""
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            extra = r.pop(None, None)
            if extra and malformed is not None:
                malformed.append(f"{path.name} line {reader.line_num}: {len(reader.fieldnames) + len(extra)} fields where the "
                                 f"header has {len(reader.fieldnames)}; quote a value that holds a comma")
            rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items()})
    return rows


def ids(v):
    return [x.strip() for x in re.split(r"[;,]", v or "") if x.strip()]


def register_columns(doc=None):
    """{table: {column: optional}} from the column tables of register-template/REGISTER.md: the one definition of a
    register, which the template's headers are tested against and --check compares every table with. A column is
    optional where its description begins `Optional`."""
    doc = doc or HERE / "register-template" / "REGISTER.md"
    out, table = {}, None
    for line in doc.read_text(encoding="utf-8").splitlines():
        m = re.match(r"###\s+([\w-]+)\.csv\b", line)
        if m:
            table = out.setdefault(m.group(1), {})
            continue
        if line.startswith("## "):
            table = None
        if table is None or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "Column" or not cells[0].strip("-"):
            continue
        for name in cells[0].split(","):
            table[name.strip().strip("`")] = cells[1].startswith("Optional")
    return out


# A column the definition no longer holds, with what to do about it, said instead of the plain undefined warning.
RETIRED = {
    ("about", "delivering_application"): "about.csv: the delivering_application column is retired; remove it, since a "
    "component is now any deployable the flow runs through whose code the run can get (FILL-STEPS Step 5)",
    ("participation", "way"): "participation.csv: the way column is retired and no longer read; remove it, since no "
    "view draws the route a row belonged to",
    ("step-impact", "cause"): "step-impact.csv: the cause column is retired and no longer read; remove it, since "
    "failure effects are out of the views (what can stop each move goes in failure-modes.csv)",
}


def headers(reg, tables):
    """{table: its header} for each table file the register has; a file with no header row reads as no columns."""
    out = {}
    for t in tables:
        p = reg / f"{t}.csv"
        if p.exists():
            with p.open(encoding="utf-8-sig", newline="") as f:
                out[t] = [c.strip() for c in next(csv.reader(f), [])]
    return out


def column_failures(R, said=()):
    """(errors, warnings) comparing each table's header with the definition: one error per table naming the defined
    columns it lacks (optional ones aside), one warning per table naming the columns defined nowhere. A column an
    earlier message in `said` already names is left to that message."""
    err, warn = [], []
    for t, have in R.get("_columns", {}).items():
        defined = R["_defined"].get(t, {})
        miss = [c for c, optional in defined.items() if not optional and c not in have
                and not any(s.startswith(f"{t}.csv has no {c} column") for s in said)]
        if miss:
            err.append(f"{t}.csv has no {', '.join(miss)} column{'s' if len(miss) > 1 else ''}, which "
                       f"register-template/REGISTER.md defines (a register made with an earlier version of this kit): add "
                       f"each from register-template/{t}.csv, in its place, and fill it as FILL-STEPS says; a blank cell "
                       "reads as not assessed")
        extra = []
        for c in have:
            if (t, c) in RETIRED:
                warn.append(RETIRED[(t, c)])
            elif c and c not in defined:
                extra.append(c)
        if extra:
            warn.append(f"{t}.csv: {', '.join(extra)} {'are' if len(extra) > 1 else 'is'} not a column "
                        "register-template/REGISTER.md defines, and nothing reads it; remove it, or move what it holds "
                        "into the defined column it belongs in")
    return err, warn


def load(reg):
    reg = pathlib.Path(reg)
    malformed = []
    R = {t: read_csv(reg / f"{t}.csv", malformed) for t in TABLES}
    R["_defined"] = register_columns()
    R["_columns"] = headers(reg, R["_defined"])
    R["_malformed"] = malformed
    R["_name"] = reg.name
    R["_path"] = reg
    R["method"] = {m: read_csv(METHOD / f"{m}.csv") for m in ("layers", "part-kinds", "agent-questions", "involvement",
                                                            "impact", "measure-forms")}
    return R


def layer_of(R, v):
    w = (v or "").strip().lower()
    for r in R["method"]["layers"]:
        names = [r["layer"].lower()] + [a.strip().lower() for a in ids(r["also_written"])]
        if w in names:
            return r["layer"]
    return None


def short_layer(layer):
    return {"business health": "health", "business impact": "impact"}.get(layer, layer)


# ---------------------------------------------------------------- the check

def check(R):
    """(errors, warnings): what points nowhere or sits outside the closed lists; rows with no citation."""
    err, warn = list(R.get("_malformed", [])), []
    kinds = {r["part_kind"]: r["family"] for r in R["method"]["part-kinds"]}
    inv = {r["involvement"] for r in R["method"]["involvement"]}
    cats = {r["impact_category"] for r in R["method"]["impact"]}
    aq = {r["agent_question"] for r in R["method"]["agent-questions"]}

    def unique(table, col):
        seen = set()
        for r in R[table]:
            v = r.get(col, "")
            if not v:
                err.append(f"{table}.csv: a row has no {col}")
            elif v in seen:
                err.append(f"{table}.csv: {col} {v} appears twice")
            seen.add(v)
        return seen

    if len(R["about"]) != 1 or not R["about"][0].get("system"):
        err.append("about.csv: needs exactly one row, with system")
    caps =unique("capabilities", "capability_id")
    flows = unique("flows", "flow_id")
    stages = unique("stages", "stage")
    steps = unique("steps", "step")
    subj = unique("subjects", "subject_id")
    unique("measures", "handle")
    for r in R["capabilities"]:
        if r.get("parent") and r["parent"] not in caps:
            err.append(f"capabilities.csv {r['capability_id']}: parent {r['parent']} is not a capability")
    for r in R["flows"]:
        if not ids(r.get("delivers")):
            warn.append(f"flows.csv {r['flow_id']}: delivers no capability")
        for c in ids(r.get("delivers")):
            if c not in caps:
                err.append(f"flows.csv {r['flow_id']}: delivers {c}, which is not a capability")
    for r in R["stages"]:
        if r.get("flow") not in flows:
            err.append(f"stages.csv {r['stage']}: flow {r.get('flow')!r} is not a flow")
        if not (r.get("order") or "").isdigit():
            err.append(f"stages.csv {r['stage']}: order {r.get('order')!r} is not a number")
    for r in R["steps"]:
        if r.get("stage") not in stages:
            err.append(f"steps.csv {r['step']}: stage {r.get('stage')!r} is not a stage")
        if r.get("business_subject") and r["business_subject"] not in subj:
            err.append(f"steps.csv {r['step']}: business_subject {r['business_subject']} is not a subject")
        q = r.get("qualifier", "")
        if q and not q.startswith(("partial:", "stub:")):
            err.append(f"steps.csv {r['step']}: qualifier must start with 'partial:' or 'stub:'")
    for r in R["subjects"]:
        sid = r["subject_id"]
        if r.get("kind") not in ("element", "relationship"):
            err.append(f"subjects.csv {sid}: kind must be element or relationship")
        if r.get("level", "") not in LEVELS:
            err.append(f"subjects.csv {sid}: level {r['level']!r} is not one of component, external dependency, blank")
        pk = r.get("part_kind", "")
        if pk not in kinds:
            err.append(f"subjects.csv {sid}: part_kind {pk!r} is not in method/part-kinds.csv")
        if r.get("kind") == "relationship":
            for c in ("from_id", "to_id"):
                if r.get(c) not in subj:
                    err.append(f"subjects.csv {sid}: {c} {r.get(c)!r} is not a subject")
            for h in ids(r.get("step_hint")):
                if h not in steps:
                    err.append(f"subjects.csv {sid}: step_hint {h} is not a step")
        elif r.get("level") and kinds.get(pk) in ("case", "interaction", "person"):
            err.append(f"subjects.csv {sid}: a {pk} has no level")
    parts = [r for r in R["subjects"] if r.get("kind") == "element" and r.get("level") in ("component", "external dependency")]
    if parts and "purpose" not in R["subjects"][0]:
        err.append("subjects.csv has no purpose column (a register made before it was added): add it after name, and "
                   "write for each part what it does in this flow, in one sentence, cited (FILL-STEPS Step 5)")
    elif parts:
        for r in parts:
            if not r.get("purpose"):
                err.append(f"subjects.csv {r['subject_id']}: no purpose; write what this part does in this flow, in one "
                           "sentence, cited")
    comps = [r for r in parts if r.get("level") == "component"]
    if comps and "repository" not in R["subjects"][0]:
        err.append("subjects.csv has no repository column (a register made before it was added, or one that kept each "
                   "repository inside name): add it after application_id, as in the template, move each repository out "
                   "of name into it, and fill it for every component from its build or deployment definition "
                   "(FILL-STEPS Step 5)")
    elif comps:
        for r in comps:
            if r.get("repository"):
                continue
            sid, src = r["subject_id"], r.get("source", "")
            said = " ".join(r.get(c) or "" for c in ("name", "purpose", "source")).lower()
            if r.get("band") == "technology" and re.search(r"\bno repository\b", src, re.I):
                continue  # a system component no repository defines, as its source says
            if re.search(r"not separately built|no (?:build|deployable) of its own|in[- ]process", said):
                err.append(f"subjects.csv {sid}: a component with no repository that is not separately built; it is "
                           "not a component, since a component is a deployable. Remove its subjects.csv row and "
                           "describe it in agent-system.csv as an agent part inside its parent component's run "
                           "(FILL-STEPS Steps 5 and 7)")
            elif r.get("band") == "technology":
                err.append(f"subjects.csv {sid}: a system component with no repository; shared infrastructure a parent "
                           "component's deployment provisions (a database, a cache, a broker) takes the repository "
                           "that defines it, with the path to the definition (`repo: path`); `not built here:` and "
                           "the image for one run from someone else's image; or, where no repository defines it, "
                           "leave it blank and say so in source, with where it was looked for")
            else:
                err.append(f"subjects.csv {sid}: a component with no repository; write the repository it is built "
                           "from, from its build or deployment definition, or `not built here:` and the image for one "
                           "run from someone else's image. A part whose code can't be had is an external dependency, "
                           "with repository blank")
    ext ={r["subject_id"] for r in R["subjects"] if r.get("level") == "external dependency"}
    by_id = {r.get("subject_id"): r for r in R["subjects"]}
    for r in R["subjects"]:
        po = r.get("part_of")
        if not po:
            continue
        if r.get("level") != "external dependency":
            err.append(f"subjects.csv {r['subject_id']}: part_of is only for a part of an outside service (level external dependency)")
        elif po not in ext:
            err.append(f"subjects.csv {r['subject_id']}: part_of {po} is not an external dependency")
        elif by_id[po].get("part_of"):
            err.append(f"subjects.csv {r['subject_id']}: part_of {po} is itself a part; a part's part_of is the outside service")
    placed = {}
    for r in R["subjects"]:
        if r.get("kind") != "relationship" or not r.get("sequence"):
            continue
        sid, hints = r.get("subject_id"), ids(r.get("step_hint"))
        items = ids(r.get("sequence"))
        if len(items) == 1 and ":" not in items[0]:
            pairs = [(h, items[0]) for h in hints]
        else:
            pairs = [tuple(x.strip() for x in it.split(":", 1)) if ":" in it else ("", it) for it in items]
        for st, o in pairs:
            if not o.isdigit():
                err.append(f"subjects.csv {sid}: sequence {o!r} is not a number")
            elif st not in hints:
                err.append(f"subjects.csv {sid}: sequence names step {st or '(none)'}, which is not in its step_hint")
            elif (st, o) in placed:
                err.append(f"subjects.csv {sid}: sequence {o} in step {st} is also {placed[(st, o)]}'s; "
                           "calls with no strict order between them are left unnumbered")
            else:
                placed[(st, o)] = sid
    if R.get("_path") and not (pathlib.Path(R["_path"]) / "sources.csv").exists():
        warn.append("sources.csv is missing: list each source with the pass that read it (FILL-STEPS, Before you start)")
    for r in R["participation"]:
        if r.get("subject_id") not in subj:
            err.append(f"participation.csv: subject {r.get('subject_id')!r} is not a subject")
        if r.get("step") not in steps:
            err.append(f"participation.csv: step {r.get('step')!r} is not a step")
        if r.get("involvement") not in inv:
            err.append(f"participation.csv {r.get('subject_id')} at {r.get('step')}: involvement {r.get('involvement')!r} is not one of {sorted(inv)}")
    for r in R["measures"]:
        h = r["handle"]
        if r.get("subject_id") not in subj:
            err.append(f"measures.csv {h}: subject {r.get('subject_id')!r} is not a subject")
        if r.get("step") and r["step"] not in steps:
            err.append(f"measures.csv {h}: step {r['step']} is not a step")
        if not layer_of(R, r.get("layer")):
            err.append(f"measures.csv {h}: layer {r.get('layer')!r} is not in method/layers.csv")
        if r.get("counted_on") not in COUNTED_ON:
            err.append(f"measures.csv {h}: counted_on {r.get('counted_on')!r} is not one of {', '.join(COUNTED_ON)}")
        if r.get("exists", "") not in ("yes", "no", ""):
            err.append(f"measures.csv {h}: exists must be yes or no")
        if r.get("flow") and r["flow"] not in flows:
            err.append(f"measures.csv {h}: flow {r['flow']} is not a flow")
        if r.get("agent_question") and r["agent_question"] not in aq:
            err.append(f"measures.csv {h}: agent_question {r['agent_question']!r} is not in method/agent-questions.csv")
        if layer_of(R, r.get("layer")) in ("business health", "business impact") and r.get("counted_on") != "cases":
            warn.append(f"measures.csv {h}: a business measure counts cases, not {r.get('counted_on')}")
    for r in R["step-impact"]:
        if r.get("step") not in steps:
            err.append(f"step-impact.csv: step {r.get('step')!r} is not a step")
        if r.get("impact_category") not in cats:
            err.append(f"step-impact.csv {r.get('step')}: impact_category {r.get('impact_category')!r} is not in method/impact.csv")
        if r.get("recovery", "") not in RECOVERY:
            err.append(f"step-impact.csv {r.get('step')}: recovery must be 'moves on', 'stranded', 'not created' or blank")
    for r in R["case-attributes"]:
        if r.get("flow") not in flows:
            err.append(f"case-attributes.csv {r.get('attribute')}: flow {r.get('flow')!r} is not a flow")
    case_flows = {}
    stage_flow = {r["stage"]: r.get("flow") for r in R["stages"]}
    for r in R["steps"]:
        if r.get("business_subject"):
            case_flows.setdefault(r["business_subject"], set()).add(stage_flow.get(r.get("stage")))
    for r in R["measures"]:
        sid = r.get("subject_id", "")
        if kinds.get(next((x.get("part_kind") for x in R["subjects"] if x["subject_id"] == sid), "")) == "case" \
                and not r.get("step") and not r.get("flow") and len(case_flows.get(sid, ())) > 1:
            warn.append(f"measures.csv {r['handle']}: its case {sid} is shared by several flows; name the flow it "
                        "measures in `flow`, or it is counted for none")
    agents = {r["subject_id"] for r in R["subjects"] if kinds.get(r.get("part_kind")) == "agent"}
    by_agent = {}
    for r in R["agent-system"]:
        a = r.get("agent")
        if a not in agents:
            err.append(f"agent-system.csv {r.get('id')}: agent {a!r} is not a subject whose part_kind is an agent kind")
        if r.get("element") not in AGENT_ELEMENTS:
            err.append(f"agent-system.csv {r.get('id')}: element must be one of {', '.join(AGENT_ELEMENTS)}")
        by_agent.setdefault(a, []).append(r)
    for a, rows_ in by_agent.items():
        own = {r["id"]: r.get("element") for r in rows_}
        if len(own) != len(rows_):
            err.append(f"agent-system.csv: agent {a} repeats an id")
        if sum(1 for r in rows_ if r.get("element") == "run") != 1:
            err.append(f"agent-system.csv: agent {a} needs exactly one run")
        for r in rows_:
            for p in ids(r.get("performed_by")):
                if own.get(p) != "agent part":
                    err.append(f"agent-system.csv {r['id']}: performed_by {p} is not one of agent {a}'s agent parts")
            for p in ids(r.get("uses")):
                if own.get(p) != "dependency":
                    err.append(f"agent-system.csv {r['id']}: uses {p} is not one of agent {a}'s dependencies")
            for s in ids(r.get("serves_business_step")):
                if s not in steps:
                    err.append(f"agent-system.csv {r['id']}: serves_business_step {s} is not a step")
            for s in ids(r.get("subject_id")):
                if s not in subj:
                    err.append(f"agent-system.csv {r['id']}: subject_id {s} is not a subject")
    for a in sorted(agents - set(by_agent)):
        warn.append(f"subjects.csv {a}: an agent with no block in agent-system.csv; drawn on the map only")
    passes = set()
    for r in R["sources"]:
        if r.get("kind") not in SOURCE_KINDS:
            err.append(f"sources.csv {r.get('source_id')}: kind {r.get('kind')!r} is not one of {', '.join(SOURCE_KINDS)}")
        if not (r.get("pass") or "").isdigit():
            err.append(f"sources.csv {r.get('source_id')}: pass {r.get('pass')!r} is not a number")
        passes.add(r.get("pass"))
    for r in R["how-made"]:
        if R["sources"] and (r.get("pass") or "1") not in passes:
            err.append(f"how-made.csv step {r.get('step')}: pass {r.get('pass')} is not a pass in sources.csv")
        for x in ids(r.get("done_by")):
            if x not in DONE_BY:
                err.append(f"how-made.csv step {r.get('step')}: done_by {x!r} is not one of {', '.join(DONE_BY)}")
    for t in TABLES:
        for n, r in enumerate(R[t], 2):
            if t in ("about", "how-made", "sources"):
                continue
            if not any(r.get(c) for c in SOURCE_COLS) and not any(CITE.search(v) for v in r.values() if v):
                warn.append(f"{t}.csv line {n}: no citation")
    col_err, col_warn = column_failures(R, err)
    return col_err + err, col_warn + warn


# ---------------------------------------------------------------- the model

def model(R):
    kinds = {r["part_kind"]: r for r in R["method"]["part-kinds"]}
    M = dict(R=R, kinds=kinds)
    M["system"] = R["about"][0].get("system", R["_name"])
    M["subj"] = {s["subject_id"]: s for s in R["subjects"]}
    fam = lambda s: kinds.get(s.get("part_kind", ""), {}).get("family", "")
    M["family"] = fam
    els = [s for s in R["subjects"] if s.get("kind") == "element"]
    M["comps"] = [s for s in els if s.get("level") == "component"]
    M["ext"] = {s["subject_id"] for s in els if s.get("level") == "external dependency"}
    M["deps"] = [s for s in els if s.get("level") == "external dependency" and s.get("part_of") not in M["ext"]]
    M["dep_parts"] = {}
    for x in els:
        if x.get("level") == "external dependency" and x.get("part_of") in M["ext"]:
            M["dep_parts"].setdefault(x["part_of"], []).append(x)
    M["persons"] = [s for s in els if fam(s) == "person"]
    M["agents"] = [s for s in M["comps"] if fam(s) == "agent"]
    M["caps"] = R["capabilities"]
    M["cap"] = {c["capability_id"]: c for c in R["capabilities"]}
    M["kids"] = {}
    for c in R["capabilities"]:
        M["kids"].setdefault(c.get("parent", ""), []).append(c)
    M["flows"] = [dict(f, _stages=[]) for f in R["flows"]]
    fl = {f["flow_id"]: f for f in M["flows"]}
    M["stage"] = {}
    for s in sorted(R["stages"], key=lambda s: int(s["order"]) if s.get("order", "").isdigit() else 0):
        s = dict(s, _steps=[])
        M["stage"][s["stage"]] = s
        if s.get("flow") in fl:
            fl[s["flow"]]["_stages"].append(s)
    M["step"] = {}
    for s in R["steps"]:
        s = dict(s, _parts=[])
        M["step"][s["step"]] = s
        if s.get("stage") in M["stage"]:
            M["stage"][s["stage"]]["_steps"].append(s)
    for p in R["participation"]:
        if p.get("step") in M["step"] and p.get("subject_id") in M["subj"]:
            M["step"][p["step"]]["_parts"].append((p["subject_id"], p.get("involvement", "")))
    M["flow_of_stage"] = {s["stage"]: s.get("flow") for s in R["stages"]}
    # what each component calls among the external dependencies, from the interaction rows
    M["uses"] = {}
    for r in R["subjects"]:
        if r.get("kind") == "relationship" and r.get("to_id") in M["ext"]:
            M["uses"].setdefault(r.get("from_id"), set()).add(r["to_id"])
    # measures: a case subject with no step measures its flow; an interaction's measure belongs to what it calls
    flows_of_case = {}
    for s in M["step"].values():
        if s.get("business_subject"):
            flows_of_case.setdefault(s["business_subject"], set()).add(M["flow_of_stage"].get(s.get("stage")))
    M["m_flow"], M["m_step"], M["m_part"], M["m_at_step"] = {}, {}, {}, {}
    for m in R["measures"]:
        m = dict(m, _layer=layer_of(R, m.get("layer")) or "")
        sid = m.get("subject_id", "")
        s = M["subj"].get(sid, {})
        if m.get("step"):
            M["m_at_step"].setdefault(m["step"], []).append(m)
        if fam(s) == "case":
            if m.get("step"):
                M["m_step"].setdefault(m["step"], []).append(m)
            elif m.get("flow"):
                M["m_flow"].setdefault(m["flow"], []).append(m)
            elif len(flows_of_case.get(sid, ())) == 1:  # a case shared by several flows names its flow, or counts for none
                M["m_flow"].setdefault(next(iter(flows_of_case[sid])), []).append(m)
        elif s.get("kind") == "relationship":
            M["m_part"].setdefault(s.get("to_id"), []).append(m)
        else:
            M["m_part"].setdefault(sid, []).append(m)
    M["agent_rows"] = {}
    for r in R["agent-system"]:
        M["agent_rows"].setdefault(r.get("agent"), []).append(r)
    return M


def carried(step):
    return bool(step["_parts"])


def steps_of(M, part_id):
    """The steps a part takes part in. An external dependency also reaches the steps its callers' calls to it are
    made in (the interactions' step_hint). A call that names no step is made at start-up and reaches none."""
    out = {s["step"] for s in M["step"].values() for sid, _ in s["_parts"] if sid == part_id}
    for kid in M.get("dep_parts", {}).get(part_id, []):  # a dependency fails with all of its own parts
        out |= steps_of(M, kid["subject_id"])
    if part_id in M.get("ext", ()):
        calls = [r for r in M["R"]["subjects"] if r.get("kind") == "relationship" and r.get("to_id") == part_id]
        out |= {h for r in calls for h in ids(r.get("step_hint")) if h in M["step"]}  # a call with no step: start-up
    return out


def relations(M):
    """Step -> every part that takes part in it; component -> its steps and the external dependencies it calls;
    dependency -> the components that call it and the steps it reaches (its own, and those its calls are made in);
    inside each agent, a dependency reaches the steps its users perform."""
    rel = {}

    def link(a, b):
        rel.setdefault(a, set()).add(b)

    for s in M["step"].values():
        for sid, _ in s["_parts"]:
            link("s:" + s["step"], "p:" + sid)
            link("p:" + sid, "s:" + s["step"])
    for c, ds in M["uses"].items():
        for d in ds:
            link("p:" + c, "p:" + d)
            link("p:" + d, "p:" + c)
    carriers = {c["subject_id"] for c in M["comps"] + M["persons"]}
    for r in M["R"]["subjects"]:  # a component and the components it calls, one hop either way
        ends = (r.get("from_id"), r.get("to_id"))
        if r.get("kind") == "relationship" and ends[0] in carriers and ends[1] in carriers and ends[0] != ends[1]:
            link("p:" + ends[0], "p:" + ends[1])
            link("p:" + ends[1], "p:" + ends[0])
    for d in M["ext"]:  # a dependency reaches the steps its callers' calls to it are made in
        for st in steps_of(M, d):
            link("p:" + d, "s:" + st)
            link("s:" + st, "p:" + d)
    for parent, kids in M["dep_parts"].items():  # a dependency and its own parts, and who calls them
        for k in kids:
            link("p:" + parent, "p:" + k["subject_id"])
            link("p:" + k["subject_id"], "p:" + parent)
            for c, ds in M["uses"].items():
                if k["subject_id"] in ds:
                    link("p:" + parent, "p:" + c)
    reach = carriers | set(M["ext"])
    for r in M["R"]["subjects"]:  # a step reaches both ends of the calls made in it
        ends = (r.get("from_id"), r.get("to_id"))
        if r.get("kind") == "relationship" and ends[0] in reach and ends[1] in reach:
            for h in ids(r.get("step_hint")):
                for x in ends:
                    link("s:" + h, "p:" + x)
    for rows in M["agent_rows"].values():
        for r in rows:
            for p in ids(r.get("performed_by")):
                link("s:" + r["id"], "p:" + p)
                link("p:" + p, "s:" + r["id"])
            for d in ids(r.get("uses")):
                link("p:" + r["id"], "p:" + d)
                link("p:" + d, "p:" + r["id"])
    for rows in M["agent_rows"].values():
        for r in rows:
            for d in ids(r.get("uses")):
                for st in [x for x in rel.get("p:" + r["id"], ()) if x.startswith("s:")]:
                    link("p:" + d, st)
                    link(st, "p:" + d)
    return {k: sorted(v) for k, v in rel.items()}



def chain(M):
    """What a click on each box lights: the chain through it, up to the capabilities and down to the external
    dependencies. Capability, flow, stage and step are walked as a tree both ways. Below a step, and around a part,
    the one-hop neighbourhood of `relations` holds, so a step does not light every call its parts make elsewhere."""
    rel = relations(M)
    down, up = {}, {}

    def edge(a, b):
        down.setdefault(a, set()).add(b)
        up.setdefault(b, set()).add(a)

    for parent, kids in M["kids"].items():
        for k in kids:
            if parent in M["cap"]:
                edge("c:" + parent, "c:" + k["capability_id"])
    for f in M["flows"]:
        for c in ids(f.get("delivers")):
            if c in M["cap"]:
                edge("c:" + c, "f:" + f["flow_id"])
        for st in f["_stages"]:
            edge("f:" + f["flow_id"], "g:" + st["stage"])
            for s in st["_steps"]:
                edge("g:" + st["stage"], "s:" + s["step"])

    def walk(k, g):
        seen, todo = set(), [k]
        while todo:
            for n in g.get(todo.pop(), ()):
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        return seen

    out = {}
    for k in set(down) | set(up) | set(rel):
        lit = walk(k, up) | walk(k, down)
        if k.startswith("p:"):
            near = set(rel.get(k, ()))
            lit |= near
            for s in [x for x in near if x.startswith("s:")]:
                lit |= walk(s, up)
        else:
            lit |= {p for s in lit | {k} if s.startswith("s:") for p in rel.get(s, ()) if p.startswith("p:")}
        out[k] = sorted(lit - {k})
    return out


def chain_data(M):
    """The chain as JSON the page's click script reads."""
    return ('<script type="application/json" id="chain-data">'
            + json.dumps(chain(M), separators=(",", ":"), sort_keys=True).replace("</", "<" + chr(92) + "/") + "</script>")


def default_opened(M):
    """Per flow, one stage opened: among the stages an AI agent takes part in where there are any, the one with the
    most steps carried out (the first on a tie). An agent is a part of the capability, so it is on the first view."""
    agents = {a["subject_id"] for a in M["agents"]}
    out = set()
    for f in M["flows"]:
        if not f["_stages"]:
            continue
        with_agent = [st for st in f["_stages"] if any(sid in agents for s in st["_steps"] for sid, _ in s["_parts"])]
        cands = with_agent or f["_stages"]
        best = max(cands, key=lambda st: (sum(1 for s in st["_steps"] if carried(s)), -cands.index(st)))
        out.add(best["stage"])
    return out


def parse_open(M, spec):
    if not spec:
        return default_opened(M)
    chosen = {}
    default = default_opened(M)
    for tok in [x.strip().lower() for x in spec.split(",") if x.strip()]:
        hit = [st for st in M["stage"].values() if tok in (st["stage"].lower(), st.get("name", "").lower())]
        if not hit:
            raise SystemExit(f"--open {tok!r} is not a stage; one of: "
                             + ", ".join(f'{s["stage"]} ({s.get("name")})' for s in M["stage"].values()))
        chosen.setdefault(hit[0].get("flow"), set()).add(hit[0]["stage"])
    out = {s for s in default if M["flow_of_stage"].get(s) not in chosen}
    for v in chosen.values():
        out |= v
    return out


# ---------------------------------------------------------------- drawing primitives

VW = 1760
CAPX, CAPW = 12, 300
FX, FW = 344, 200
SX, SW = 580, 250
PX, PW = 866, 362
CX, CW = 1266, 244
DX, DW = 1540, 210
LH = 14
TAG = 'class="s" style="font-size:12px"'
SUB = 'class="s" style="font-size:12px"'
SUM = ' style="stroke:var(--slate);stroke-width:2.2"'
COUNT = ' style="stroke-dasharray:5 4"'
INFER = ' style="stroke-dasharray:1.5 3"'
SUPPORT = ' style="stroke-dasharray:6 3;stroke:var(--g400)"'
OPEN = ' style="stroke:var(--clay);stroke-width:2"'
HEAVY = ' style="stroke:var(--slate);stroke-width:2.4"'
FAINT = ".2"
FOLDED = ' style="fill:var(--ivory);stroke-opacity:.45;stroke-dasharray:2 2"'  # a folded line: click to open


def esc(s):
    return html.escape(str(s or ""), quote=True)


def tog_svg(x, y, key, opened):
    """The ▸ or ▾ that starts a line: its own control (WAI-ARIA disclosure), so opening or closing never changes the pick."""
    return (f'<g class="tog" tabindex="0" role="button" aria-expanded="{"true" if opened else "false"}" '
            f'aria-label="{"Collapse" if opened else "Expand"}" data-open="{esc(key)}">'
            f'<rect x="{x + 2:g}" y="{y + 2:g}" width="22" height="22" style="fill:transparent;stroke:none"/></g>')


def toggle(b, key, opened):
    b.marks.append(lambda x, y, _b: tog_svg(x, y, key, opened))


def steps_said(st, k, n_out, glyph="▸"):
    n_step = len(st["_steps"]) - n_out
    return f'{glyph} Stage {st.get("order") or k + 1}: {n_step} step{"" if n_step == 1 else "s"}' + (
        f', {n_out} outcome{"" if n_out == 1 else "s"}' if n_out else "")


def text_w(s, fs=12):
    return len(s) * fs * 0.54


def wrap(s, width, fs=12, max_lines=2, first=None):
    """Greedy word wrap to a pixel width (the first line to `first` where given, leaving room beside it); the last
    line is cut at a word and marked with an ellipsis."""
    first = width if first is None else first
    words, lines, cur = [], [], ""
    per = max(4, int(width / (fs * 0.54)))
    for w in (s or "").split():  # a word longer than the line (a path) is broken into pieces that fit
        words += [w[i:i + per] for i in range(0, len(w), per)]
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(t, fs) <= (first if not lines else width) or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lines = lines or [""]
    if len(lines) > max_lines:
        last = " ".join(lines[max_lines - 1:])
        room = first if max_lines == 1 else width
        while text_w(last + "…", fs) > room and " " in last:
            last = last.rsplit(" ", 1)[0]
        lines = lines[:max_lines - 1] + [last.rstrip(" ,;:") + "…"]
    return lines


def faint(on, s):
    return s if on else f'<g opacity="{FAINT}">{s}</g>'


def tree(ends, s):
    """A line of the capability-to-step tree, named by the boxes it joins, so a click can fade it with them."""
    return f'<g class="tree" data-ends="{esc(ends)}">{s}</g>'


def defs(mid):
    return (f'<defs><pattern id="na-{mid}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="6" height="6" style="fill:var(--paper)"/><line x1="0" y1="0" x2="0" y2="6" style="stroke:var(--g300);stroke-width:2"/></pattern>'
            f'<pattern id="own-{mid}" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="4" height="4" style="fill:var(--paper)"/><line x1="0" y1="0" x2="0" y2="4" style="stroke:var(--g500);stroke-width:1.6"/></pattern></defs>')


def na_style(mid):
    return f' style="fill:url(#na-{mid});stroke:var(--g400);stroke-dasharray:2 2"'


class Box:
    """A box of text lines: (text, cls) where cls is 'sx' (name), 't' (title) or 'sub' (grey)."""

    def __init__(self, x, w, lines, style="", rx=3, title=None, marks=None):
        self.x, self.w, self.lines, self.style, self.rx, self.title = x, w, lines, style, rx, title
        self.marks = marks or []  # extra svg drawn relative to the box: callables (x, y) -> svg
        self.h = 26 + sum(18 if c == "t" else LH for _, c in lines[1:]) + (4 if lines and lines[0][1] == "t" else 0)
        self.y = 0
        self.sel, self.extra = "", ""  # sel: data attributes that make the box clickable

    @property
    def mid(self):
        return self.y + self.h / 2

    def svg(self):
        tt = f"<title>{esc(self.title)}</title>" if self.title else ""
        out = f'<rect x="{self.x:g}" y="{self.y:g}" width="{self.w:g}" height="{self.h:g}" rx="{self.rx}" class="bx"{self.style}>{tt}</rect>'
        y = self.y + (21 if self.lines and self.lines[0][1] == "t" else 17)
        for text, cls in self.lines:
            attr = {"sx": 'class="sx"', "t": 'class="t"', "sub": SUB, "subi": SUB, "link": SUB}[cls]
            t_ = f'<text x="{self.x + (26 if cls == "subi" else 10):g}" y="{y:g}" {attr}>{esc(text)}</text>'
            if cls == "link":
                t_ = f'<a href="{esc(self.link)}" target="_blank" rel="noopener">{t_.replace("fill", "x") if False else t_}</a>'
            out += t_
            y += 18 if cls == "t" else LH
        for m in self.marks:
            out += m(self.x, self.y, self)
        out += self.extra
        if self.sel:  # a folded line stays clickable; a part or step picked lights it when its chain runs into what it holds, else fades it
            return f'<g class="sel{" folded" if getattr(self, "folded", False) else ""}" tabindex="0" role="button" {self.sel}>{out}</g>'
        return out


def name_lines(text, width, cls="sx", max_lines=2):
    return [(t, cls) for t in wrap(text, width, 15 if cls == "t" else 12, max_lines)]


def sub_lines(text, width, max_lines=2):
    return [(t, "sub") for t in wrap(text, width, 12, max_lines)]


def key_block(rows, x, y, width=262):
    """Rows of (mark svg drawn around y=0, label). Returns svg and its bottom."""
    out = [f'<text x="{x}" y="{y - 22:g}" class="k">KEY</text>']
    for mark, label in rows:
        lines = wrap(label, width, 12, 3)
        out.append(f'<g transform="translate(0,{y:g})">{mark}</g>')
        for n, ln in enumerate(lines):
            out.append(f'<text x="{x + 48}" y="{y + 4 + LH * n:g}" class="sx">{esc(ln)}</text>')
        y += 10 + LH * len(lines)
    return "".join(out), y


def wrap_svg(aria, width, height, parts, axis, cls=""):
    head = (f'<text x="12" y="16" class="k" style="fill:var(--slate)">{esc(axis)}</text>'
            f'<line x1="12" y1="24" x2="{width - 12}" y2="24" class="rule" style="stroke-width:.8"/>') if axis else ""
    klass = f' class="{cls}"' if cls else ""
    return (f'<svg{klass} viewBox="0 0 {width} {height + 40:g}" role="img" aria-label="{esc(aria)}">'
            + head + '<g transform="translate(0,30)">' + "".join(parts) + "</g></svg>")


# ---------------------------------------------------------------- the business map: map, reports, join

REPORT_COLS = [  # what each level is, what it counts on, and what it can report
    (CAPX, "what the business is able to do", "its flows", ["its own measure is coverage;", "health, derived from its flows"],
     ["its flows' counts, kept per flow"], []),
    (FX, "one case's path, start to end", "each case", ["cases started, finished, still open;", "finished on time and right"],
     ["cases wrong or late,", "by stake; moving on or stranded"], []),
    (SX, "one ordered stretch of a flow", "each case, entry to exit", ["cases in it now; age of the oldest;", "time to get through"],
     ["cases wrong or late, located here;", "projected: cases still upstream"], []),
    (PX, "one act with an outcome", "one event per case", ["did it happen for this case,", "and was what it produced right"],
     ["cases where it did not happen,", "or produced the wrong outcome"], []),
    (CX, "a deployable part of the system", "requests, runs, resources", [], [],
     ["by its kind's set, named on each box;", "every part: metrics, events, logs, traces"]),
    (DX, "relied on, run by someone else", "calls, from the calling side", [], [],
     ["the same sets from the calling side:", "available, duration, errors, timeouts"]),
]


def measure_summary(ms):
    if not ms:
        return "on record: none"
    by = {}
    for m in ms:
        by[short_layer(m["_layer"])] = by.get(short_layer(m["_layer"]), 0) + 1
    in_code = sum(1 for m in ms if m.get("exists") == "yes")
    s = "on record: " + ", ".join(f"{v} {k}" for k, v in by.items())
    return s + (f"; {in_code} emitted by the code" if in_code else "; all proposed")


def business_map(M, view, mid, opened=None, select_steps=None, draw_parts=True, calls="click", key=True, fold=None):
    """view: 'map', 'reports' or 'join' (the business row above an agent's own view).
    opened: the stage ids opened into their steps. select_steps: for 'join', the business steps the agent serves;
    only their stages and flows are drawn. The key's rows, (mark svg, label), are kept in M["_key_rows"][mid];
    key=False leaves the key out of the drawing, for a page that shows it beside the map instead.
    fold: a folded map (a degree-of-interest tree): "" folds every capability group and every stage's steps to one
    line that says how much it holds; "c:<group>" opens that group; "o:<stage>" opens that stage's steps; "f:<flow>"
    opens the flow's chain and folds the other flows, groups and parts to one line each; "g:<stage>" opens the stage's
    steps and folds its neighbours; "g:<stage>^" is that map with the stage's own steps folded to their line. On a flow or stage: "+flows", "+groups", "+parts" or "+deps" opens that one line of
    others under a ▾ header; "~<group>,<group>" folds those of its groups. Every ▸ and ▾ names the map it opens."""
    styled = view == "reports"
    M.setdefault("_seq_placed", {})[mid] = []
    if view == "join":
        opened = {M["step"][s]["stage"] for s in select_steps}
    opened = opened or set()
    flows = M["flows"]
    folding = fold is not None
    focus, more, shut = fold or "", "", set()
    if "+" in focus:
        focus, more = focus.split("+", 1)
    elif "~" in focus:
        focus, s_ = focus.split("~", 1)
        shut = set(s_.split(","))
    tucked = focus.startswith("g:") and focus.endswith("^")  # the stage in focus, its own steps folded: nothing else moves
    focus = focus[:-1] if tucked else focus
    fkey = focus + ("^" if tucked else "")
    tail = "+" + more if more else ("~" + ",".join(sorted(shut)) if shut else "")  # the other lines' state, kept by a steps toggle
    lit = ({focus} | set(chain(M).get(focus, []))) if focus[:2] in ("f:", "g:") else None
    fold_stages, fold_steps, fold_lines, step_heads = set(), {}, [], []

    def other_line(x):  # an "N other ..." line: ▸ opens it under a ▾ header; ▾ folds it back to the focus
        return (fkey, True) if more == x else (fkey + "+" + x if not more else "all", False)

    def unshut(cid):
        rest = sorted(shut - {cid})
        return fkey + ("~" + ",".join(rest) if rest else "")

    def shutting(cid):
        s_ = shut | {cid} if len(shut) < 3 else {cid}
        return fkey + "~" + ",".join(sorted(s_))
    if folding:
        opened = {focus[2:]} if focus[:2] in ("g:", "o:") and not tucked else set()
        if lit is not None:
            fid = focus[2:] if focus.startswith("f:") else M["flow_of_stage"].get(focus[2:])
            flows = [f for f in M["flows"] if f["flow_id"] == fid]
            if focus.startswith("g:"):
                fold_stages = {st["stage"] for st in flows[0]["_stages"]} - {focus[2:]}
    if view == "join":
        flows = [f for f in flows if any(st["stage"] in opened for st in f["_stages"])]
    e, keyrows = [], []
    marks_used = set()

    # ---- flows, stages and steps, one block per flow (a tidy tree: no two parents share a line)
    y = 44
    flow_boxes, stage_boxes, step_boxes, collapse_rows = [], {}, {}, []
    all_open = set(M["stage"]) <= set(opened)  # orange marks the opened stage only when some are left closed
    others = [f for f in M["flows"] if f not in flows] if folding and view != "join" else []
    for f in flows + (others if more == "flows" else []):
        top = y
        if more == "flows" and f is others[0]:
            ob = Box(FX, FW, [(f'▾ {len(others)} other flow{"" if len(others) == 1 else "s"}', "sx")], FOLDED)
            ob.y = top
            fold_lines.append((ob,) + other_line("flows") + ("",))
            y = top = y + ob.h + 12
        stages = f["_stages"] if view != "join" else [st for st in f["_stages"] if st["stage"] in opened]
        for k, st in enumerate(stages):
            label = f'Stage {st.get("order") or k + 1}: {st.get("name", "")}'
            lines = name_lines(label, SW - 20)
            if view == "reports":
                bm = [m for s in st["_steps"] for m in M["m_step"].get(s["step"], [])]
                lines += sub_lines("business measures on its steps: " + measure_summary(bm)[len("on record: "):] if bm else "business measures on its steps: none", SW - 20, 2)
            on = True
            if not any(carried(x) for x in st["_steps"]) and view != "join":
                lines[0] = (lines[0][0] + " · not assessed", lines[0][1])
                lines = name_lines(" ".join(t for t, c in lines if c == "sx"), SW - 20) + [x for x in lines if x[1] != "sx"]
                sb = Box(SX, SW, lines)
            else:
                sb = Box(SX, SW, lines)
            folded = st["stage"] in fold_stages
            if folded:  # a neighbour of the stage in focus: one folded line, unfaded by the stage's own click; a click opens it
                sb = Box(SX, SW, name_lines("▸ " + label, SW - 20, max_lines=1), FOLDED)
                toggle(sb, "g:" + st["stage"], False)
            sb.y, sb.on, sb.node, sb.folded = y, on, "g:" + st["stage"], folded
            if view != "join":
                sb.sel = f'data-node="{esc(sb.node)}"' + (f' data-open="{esc(sb.node)}"' if folding else "")
            stage_boxes[st["stage"]] = sb
            block = sb.h
            if folding and st["stage"] not in opened and st["stage"] not in fold_stages:  # its steps, folded to one line
                n_out = sum(1 for s in st["_steps"] if is_outcome(M, s["step"]))
                fb_ = Box(PX, PW, [(steps_said(st, k, n_out), "sx")], FOLDED)
                fb_.y, fb_.folded, fb_.sel = y, True, f'data-node="{esc(sb.node)}" data-open="{esc(sb.node)}"'
                toggle(fb_, focus + tail if tucked and sb.node == focus else ("o:" if lit is None else "g:") + st["stage"], False)
                fold_steps[st["stage"]] = fb_
                block = max(block, fb_.h)
            if st["stage"] in opened:
                shown = st["_steps"]
                if view == "join":
                    shown = [s for s in st["_steps"] if s["step"] in select_steps]
                yy = y
                if folding:  # the opened steps keep their one line above them, now a ▾ that folds them again
                    hb = Box(PX, PW, [(steps_said(st, k, sum(1 for s in st["_steps"] if is_outcome(M, s["step"])), "▾"), "sx")])
                    hb.y, hb.sel = y, f'data-node="{esc(sb.node)}"'
                    toggle(hb, "load" if focus.startswith("o:") else focus + "^" + tail, True)
                    step_heads.append(hb)
                    yy += hb.h + 8
                for i, s in enumerate(shown):
                    b = step_box(M, view, mid, s, st["_steps"].index(s) + 1, marks_used)
                    b.y, b.step_id = yy, s["step"]
                    if view != "join":
                        b.sel = f'data-step="{esc(s["step"])}"'
                    step_boxes[s["step"]] = b
                    yy += b.h + 8
                rest = len(st["_steps"]) - len(shown)
                if rest and view == "join":
                    na = sum(1 for s in st["_steps"] if s not in shown and not carried(s))
                    txt = f"+{rest} step{'s' if rest > 1 else ''} not on this path" + (f" ({na} not assessed)" if na else "")
                    collapse_rows.append((PX + 10, yy + 10, txt))
                    marks_used.add("collapse")
                    yy += 22
                block = max(block, yy - 8 - y)
            y += block + 8
        y -= 8
        lines = name_lines(f.get("name", ""), FW - 20, max_lines=3)
        if not f["_stages"]:
            lines += sub_lines("not broken into stages in the register", FW - 20, 2)
        fb = Box(FX, FW, lines)
        fb.y = max(top, (top + y) / 2 - fb.h / 2)
        fb.node = "f:" + f["flow_id"]
        if view != "join":
            fb.sel = f'data-node="{esc(fb.node)}"' + (f' data-open="{esc(fb.node)}"' if folding else "")
        fb.on = view in ("map", "reports")
        tags = []
        if view == "reports":
            tags = wrap(measure_summary(M["m_flow"].get(f["flow_id"], [])), FW + 20, 11, 3)
        fb.tags = tags
        flow_boxes.append((f, fb, [stage_boxes[st["stage"]] for st in stages]))
        y = max(y, fb.y + fb.h + LH * len(tags) + 6) + 30
    if others and more != "flows":
        n = len(others)
        ob = Box(FX, FW, [(f'▸ {n} other flow{"" if n == 1 else "s"}', "sx")], FOLDED)
        ob.y = y
        fold_lines.append((ob,) + other_line("flows") + (" ".join(["f:" + o["flow_id"] for o in others]
                                                                   + ["g:" + st["stage"] for o in others for st in o["_stages"]]),))
        y += ob.h + 30
    body_bottom = y - 30

    # ---- draw flows, stages, steps and their tree lines
    for f, fb, sbs in flow_boxes:
        ln = SUM if styled else ""
        e.append(faint(fb.on, fb.svg()))
        for n, t in enumerate(fb.tags):
            e.append(f'<text x="{FX}" y="{fb.y + fb.h + 14 + LH * n:g}" {TAG}>{esc(t)}</text>')
        if not sbs:
            continue
        tx = SX - 18
        e.append(tree(fb.node, faint(fb.on, f'<line x1="{FX + FW}" y1="{fb.mid:g}" x2="{tx}" y2="{fb.mid:g}" class="ln"{ln}/>')))
        for b in sbs:  # each stage's own stretch of the trunk, so a click lights only the stretch to its stages
            e.append(tree(fb.node if b.folded else f"{fb.node} {b.node}", faint(b.on, f'<line x1="{tx}" y1="{fb.mid:g}" x2="{tx}" y2="{b.mid:g}" class="ln"{ln}/>'
                                                              f'<line x1="{tx}" y1="{b.mid:g}" x2="{SX}" y2="{b.mid:g}" class="ln"{ln}/>'
                                                              f'<circle cx="{tx}" cy="{b.mid:g}" r="2.4" class="hit"/>')))
            e.append(faint(b.on and view != "join", b.svg()))
    for sid, b in fold_steps.items():
        sb = stage_boxes[sid]
        e.append(tree(sb.node, f'<line x1="{SX + SW}" y1="{b.mid:g}" x2="{PX}" y2="{b.mid:g}" class="ln"/>'))
        e.append(b.svg())
    e += [hb.svg() for hb in step_heads]
    for sid, sb in stage_boxes.items():
        kids = [step_boxes[s["step"]] for s in M["stage"][sid]["_steps"] if s["step"] in step_boxes]
        if not kids:
            continue
        ln = SUM if styled else ""
        tx = PX - 18
        e.append(tree(sb.node, f'<line x1="{SX + SW}" y1="{sb.mid:g}" x2="{tx}" y2="{sb.mid:g}" class="ln"{ln}/>'))
        for k in kids:
            e.append(tree(f"{sb.node} s:{k.step_id}", f'<line x1="{tx}" y1="{sb.mid:g}" x2="{tx}" y2="{k.mid:g}" class="ln"{ln}/>'
                                                      f'<line x1="{tx}" y1="{k.mid:g}" x2="{PX}" y2="{k.mid:g}" class="ln"{ln}/>'
                                                      f'<circle cx="{tx}" cy="{k.mid:g}" r="2.4" class="hit"/>'))
    e.append(STEPS_SLOT)
    for x, yy, txt in collapse_rows:
        e.append(f'<text x="{x}" y="{yy:g}" class="s" style="font-size:12px;font-style:italic">{esc(txt)}</text>')

    # ---- capabilities: nested boxes, each delivered by the flows that name it
    delivered = {}
    for gi, (f, fb, _) in enumerate(flow_boxes):
        for c in ids(f.get("delivers")):
            delivered.setdefault(c, []).append(gi)

    def tree_flows(cid):
        out = set(delivered.get(cid, []))
        for k in M["kids"].get(cid, []):
            out |= tree_flows(k["capability_id"])
        return out

    origins = {}
    cap_svg = []
    by_any = {c for f in M["flows"] for c in ids(f.get("delivers"))}  # a folded map draws fewer flows than deliver

    def members(cid):
        return [cid] + [m for k in M["kids"].get(cid, []) for m in members(k["capability_id"])]

    def draw_cap(c, x, yy, w, depth):
        cid = c["capability_id"]
        mine = tree_flows(cid)
        if folding:
            mine = {1} if any(m in by_any for m in members(cid)) else set()
        on = view != "join"
        if depth == 0 and folding and cid not in groups_open:  # a group folded to one line: how much it holds
            mem = members(cid)
            none = sum(1 for m in mem if m not in by_any)
            count = (f'{len(mem)} · delivered by no flow' if none == len(mem) and len(mem) > 1 else
                     f'{len(mem)} capabilit{"y" if len(mem) == 1 else "ies"}' + (" · delivered by no flow" if none == len(mem)
                                                                               else f" · {none} delivered by no flow" if none else ""))
            b = Box(x, w, name_lines("▸ " + c.get("name", ""), w - 24, max_lines=1) + sub_lines(count, w - 24, 1), FOLDED, rx=8)
            b.y, b.folded, b.sel = yy, True, f'data-node="c:{esc(cid)}" data-open="c:{esc(cid)}"'
            toggle(b, unshut(cid) if cid in shut else "c:" + cid, False)
            return b.h, b.svg()
        cls = "t" if delivered.get(cid) or (folding and cid in by_any) else "sx"
        head = depth == 0 and folding and view != "join"  # an opened group keeps its line, now a ▾ that folds it again
        lines = name_lines(("▾ " if head else "") + c.get("name", ""), w - 24, cls)
        sub = ""
        if view == "reports":
            sub = f"coverage over {len(mine)} of its flows here" if mine else "none: a gap"
        elif depth and not mine and view != "join":
            sub = "no flow here delivers it"
        elif depth:
            sub = "inside " + M["cap"].get(c.get("parent"), {}).get("name", "")
        lines += sub_lines(sub, w - 24, 3) if sub else []
        b = Box(x, w, lines, rx=8 if depth == 0 else 4)
        b.y = yy
        if view != "join":
            b.sel = f'data-node="c:{esc(cid)}"'
        if head:
            toggle(b, "load" if focus.startswith("c:") else shutting(cid), True)
        kids = M["kids"].get(cid, [])
        if lit is not None:  # what the flow in focus does not deliver folds to one line in its group
            if depth == 0:
                skipped.clear()
            skipped.extend(m for k in kids if "c:" + k["capability_id"] not in lit for m in members(k["capability_id"]))
            kids = [k for k in kids if "c:" + k["capability_id"] in lit]
        inner = yy + b.h + (2 if kids or (depth == 0 and skipped) else 0)
        parts = []
        for k in kids:
            h, p = draw_cap(k, x + 14, inner, w - 28, depth + 1)
            parts.append(p)
            inner += h + 8
        if depth == 0 and lit is not None and skipped:
            n, none = len(skipped), sum(1 for m in skipped if m not in by_any)
            ob = Box(x + 14, w - 28, [(f"▸ {n} delivered by no flow" if none == n else f"▸ {n} not delivered by this flow", "sx")]
                     + (sub_lines(f"{none} delivered by no flow", w - 52, 1) if 0 < none < n else []), FOLDED)
            ob.y = inner
            parts.append(f'<g class="fold" tabindex="0" role="button" aria-expanded="false" data-open="c:{esc(cid)}" '
                         f'data-holds="{esc(" ".join("c:" + m for m in skipped))}">{ob.svg()}</g>')
            inner += ob.h + 8
            kids = kids or [None]
        h = inner - yy + (6 if kids else 0) if kids else b.h
        b.h = h
        if delivered.get(cid):
            origins[cid] = (x + w, yy + 18)
        return h, faint(on, b.svg()) + "".join(parts)

    roots = M["kids"].get("", [])
    skipped = []
    groups_open = set()
    if focus.startswith("c:"):
        groups_open = {focus[2:]}
    elif lit is not None:
        groups_open = {r["capability_id"] for r in roots if "c:" + r["capability_id"] in lit} - shut
    elif not folding:
        groups_open = {r["capability_id"] for r in roots}
    yy = 44
    for root in roots:
        if lit is not None and root["capability_id"] not in groups_open | shut:
            continue
        h, p = draw_cap(root, CAPX, yy, CAPW, 0)
        cap_svg.append(p)
        yy += h + 10
    rest_g = [r for r in roots if r["capability_id"] not in groups_open | shut]
    n = len(rest_g)
    if lit is not None and n:
        ob = Box(CAPX, CAPW, [(f'{"▾" if more == "groups" else "▸"} {n} other group{"" if n == 1 else "s"}', "sx")]
                 + sub_lines(f'this flow delivers none of {"its" if n == 1 else "their"} capabilities', CAPW - 24, 1), FOLDED, rx=8)
        ob.y = yy
        fold_lines.append((ob,) + other_line("groups") + (" ".join("c:" + m for r in rest_g for m in members(r["capability_id"])),))
        yy += ob.h + 10
        if more == "groups":
            for root in rest_g:
                h, p = draw_cap(root, CAPX, yy, CAPW, 0)
                cap_svg.append(p)
                yy += h + 10
    cap_bottom = yy
    e[:0] = cap_svg
    for cid, (x, yy_) in origins.items():
        for g in delivered[cid]:
            fb = flow_boxes[g][1]
            on = fb.on and view != "join"
            e.append(tree(f"c:{cid} {fb.node}", faint(on, f'<line x1="{x}" y1="{yy_:g}" x2="{FX}" y2="{fb.mid:g}" class="ln"{COUNT if styled else ""}/>'
                                                          f'<circle cx="{x}" cy="{yy_:g}" r="3" class="hit"/>')))

    # ---- components and external dependencies, each placed beside what it connects to
    part_bottom = body_bottom
    hidden_c = hidden_d = 0
    numbers = {}
    if draw_parts and view != "join":
        comp_ids = [c["subject_id"] for c in M["comps"]] + [p["subject_id"] for p in M["persons"]]
        links = {}
        for s, b in step_boxes.items():
            for sid, inv in M["step"][s]["_parts"]:
                if sid in comp_ids:
                    links.setdefault(sid, []).append((b, inv))
        for st_id, b in fold_steps.items():  # a stage's folded steps: one line to each part that carries one of them
            seen = set()
            for s in M["stage"][st_id]["_steps"]:
                for sid, inv in s["_parts"]:
                    if sid in comp_ids and sid not in seen:
                        seen.add(sid)
                        links.setdefault(sid, []).append((SimpleNamespace(mid=b.mid, step_id=s["step"]), inv))
        everywhere = {sid for st in M["step"].values() for sid, _ in st["_parts"]}
        shown = [c for c in comp_ids if (c in everywhere if folding else c in links)]
        for a in M["agents"]:  # an AI agent is always drawn: it is part of the capability or it is not
            if a["subject_id"] not in shown:
                shown.append(a["subject_id"])
        hidden_c = len([c for c in M["comps"]]) - len([c for c in shown if c in {x["subject_id"] for x in M["comps"]}])
        other_c, extra_c = 0, []
        if lit is not None:
            other_c = len(shown)
            off_c = [c for c in shown if "p:" + c not in lit]
            extra_c = off_c if more == "parts" else []
            shown = [c for c in shown if "p:" + c in lit]
            other_c -= len(shown)
        boxes = []
        for sid in shown:
            s = M["subj"][sid]
            b = part_box(M, view, mid, s, marks_used)
            ys = [lb.mid for lb, _ in links.get(sid, [])]
            b.target = sum(ys) / len(ys) if ys else body_bottom
            boxes.append((sid, b))
        boxes.sort(key=lambda t: t[1].target)
        cursor = 44
        for n, (sid, b) in enumerate(boxes, 1):
            b.y = max(b.target - b.h / 2, cursor)
            cursor = b.y + b.h + 12
        part_line = None
        if other_c:  # the parts off the focus: one line, or opened under it as a ▾ header
            part_line = Box(CX, CW, [(f'{"▾" if more == "parts" else "▸"} {other_c} other part{"" if other_c == 1 else "s"}', "sx")], FOLDED)
            part_line.y = max([44] + [b.y + b.h + 12 for _, b in boxes])
            fold_lines.append((part_line,) + other_line("parts") + (" ".join("p:" + c for c in off_c),))
            cursor = part_line.y + part_line.h + 12
            for sid in extra_c:
                b = part_box(M, view, mid, M["subj"][sid], marks_used)
                b.y = cursor
                cursor = b.y + b.h + 12
                boxes.append((sid, b))
        cbox = dict(boxes)
        for sid, b in boxes:
            ins = sorted(links.get(sid, []), key=lambda t: t[0].mid)
            for i, (lb, inv) in enumerate(ins):
                st = INFER if styled else ""  # one line style: which parts perform and which support is said per part on click
                e.append(f'<line x1="{PX + PW}" y1="{lb.mid:g}" x2="{CX}" y2="{port(b, i, len(ins)):g}" class="ln link" '
                         f'data-step="{esc(lb.step_id)}" data-part="{esc(sid)}"{st}/>')
        for sid, b in boxes:
            b.sel = f'data-part="{esc(sid)}" data-steps="{esc(" ".join(direct_steps(M, sid, step_boxes)))}"'
            e.append(b.svg())
        part_bottom = max([body_bottom] + [b.y + b.h for _, b in boxes] + ([part_line.y + part_line.h] if part_line else []))
        # external dependencies: beside the components that call them, or the steps they take part in directly
        dep_ids = [d["subject_id"] for d in M["deps"]]
        dshown, extra_d, off_d = [], [], []
        reached = 0
        for d in dep_ids:
            fam_ids = {d} | {k["subject_id"] for k in M["dep_parts"].get(d, [])}
            callers = [c for c in cbox if fam_ids & M["uses"].get(c, set())]
            direct = [step_boxes[s] for s in step_boxes if any(sid in fam_ids for sid, _ in M["step"][s]["_parts"])]
            direct += [b for st_id, b in fold_steps.items()
                       if any(sid in fam_ids for s in M["stage"][st_id]["_steps"] for sid, _ in s["_parts"])]
            if folding and (fam_ids & everywhere or any(fam_ids & M["uses"].get(c, set()) for c in comp_ids)):
                reached += 1
                if lit is not None and "p:" + d not in lit:
                    off_d.append(d)
                    if more == "deps":
                        extra_d.append((d, callers, direct))
                    continue
            if callers or direct:
                dshown.append((d, callers, direct))
        hidden_d = len(dep_ids) - (reached if folding else len(dshown))
        other_d = reached - len(dshown) if lit is not None else 0
        dboxes = []
        for d, callers, direct in dshown:
            s = M["subj"][d]
            b = dep_box(M, view, s, callers, direct, numbers)
            ys = [cbox[c].mid for c in callers] or [x.mid for x in direct]
            b.target = sum(ys) / len(ys) if ys else part_bottom
            dboxes.append((d, b, callers))
        dboxes.sort(key=lambda t: t[1].target)
        cursor = 44
        for d, b, callers in dboxes:
            b.y = max(b.target - b.h / 2, cursor)
            cursor = b.y + b.h + 12
        dep_line = None
        if other_d > 0:  # the dependencies off the focus: one line, or opened under it as a ▾ header
            dep_line = Box(DX, DW, [(f'{"▾" if more == "deps" else "▸"} {other_d} other', "sx")], FOLDED)
            dep_line.y = max([44] + [b.y + b.h + 12 for _, b, _ in dboxes])
            fold_lines.append((dep_line,) + other_line("deps") + (" ".join("p:" + x for x in off_d),))
            cursor = dep_line.y + dep_line.h + 12
            for d, callers, direct in extra_d:
                b = dep_box(M, view, M["subj"][d], callers, direct, numbers)
                b.y = cursor
                cursor = b.y + b.h + 12
                dboxes.append((d, b, callers))
        for d, b, callers in dboxes:
            ky = b.y + b.head_h
            for _, kb in b.kids:
                kb.y = ky
                ky += kb.h + 6
            head = Box(b.x, b.w, b.lines, b.style, title=b.title)
            head.y, head.h, head.link = b.y, b.h, b.link
            targets = [(d, head)] + b.kids
            for tid, tb in targets:
                ins = []
                for c in sorted(callers, key=lambda c: cbox[c].mid):
                    calls_ = [r for r in M["R"]["subjects"] if r.get("kind") == "relationship"
                              and r.get("from_id") == c and r.get("to_id") == tid]
                    if calls_:
                        ins.append((c, calls_))
                for i, (c, calls_) in enumerate(ins):
                    hints = sorted({h for r in calls_ for h in ids(r.get("step_hint"))})
                    y2 = port(tb, i, len(ins)) if tid != d else port(Box(b.x, b.w, b.lines), 0, 1) - b.h / 2 + b.head_h / 2 + b.y if False else (
                        port(tb, i, len(ins)) if tid != d else b.y + b.head_h * (i + 1) / (len(ins) + 1))
                    pm, pdef = proposed_marker(mid, marks_used) if proposed(calls_) else ("", "")
                    e.append(pdef + f'<line x1="{CX + CW}" y1="{cbox[c].mid:g}" x2="{DX if tid == d else tb.x}" y2="{y2:g}" class="ln link" '
                             f'data-part="{esc(c)}" data-dep="{esc(tid)}" data-steps="{esc(" ".join(hints))}"'
                             + f'{INFER if styled else ""}{pm}/>')
                    for h in hints:
                        marks = []
                        for r in calls_:
                            if order_mark(M, r, h) and order_mark(M, r, h) not in marks:
                                marks.append(order_mark(M, r, h))
                        for seq in marks:
                            marks_used.add("call-unordered" if seq == "~" else "call-seq")
                            sy = free_y(M, mid, CX + CW + 15, (cbox[c].mid + y2) / 2 - 3, seq)
                            e.append(seq_label(CX + CW + 15, sy, "call",
                                               f'data-from="{esc(c)}" data-to="{esc(tid)}"', h, seq))
            dsteps = steps_of(M, d)
            kids = " ".join(k for k, _ in b.kids)
            head.sel = (f'data-part="{esc(d)}" data-steps="{esc(" ".join(x for x in M["step"] if x in step_boxes and x in dsteps))}"'
                        + (f' data-children="{esc(kids)}"' if kids else ""))
            e.append(head.svg())
            for kid, kb in b.kids:
                kr = steps_of(M, kid)
                kb.sel = (f'data-part="{esc(kid)}" data-parent="{esc(d)}" '
                          f'data-steps="{esc(" ".join(x for x in M["step"] if x in step_boxes and x in kr))}"')
                e.append(kb.svg())
            marks_used.add("dep")
        part_bottom = max([part_bottom] + [b.y + b.h for _, b, _ in dboxes] + ([dep_line.y + dep_line.h] if dep_line else []))
        e.append(call_arcs(M, mid, cbox, calls, marks_used))
        if hidden_c:
            e.append(f'<text x="{CX}" y="{part_bottom + 20:g}" class="s" style="font-size:12px;font-style:italic">'
                     f'+{hidden_c} other part{"s" if hidden_c > 1 else ""} not drawn</text>')
        if hidden_d:
            e.append(f'<text x="{DX}" y="{part_bottom + 20:g}" class="s" style="font-size:12px;font-style:italic">'
                     f'+{hidden_d} external dependenc{"ies" if hidden_d > 1 else "y"} not drawn</text>')
        if hidden_c or hidden_d:
            marks_used.add("collapse")
            part_bottom += 26
        n_calls = M.get("_calls_missing", 0)
        if n_calls:
            e.append(f'<text x="{CX}" y="{part_bottom + 20:g}" class="s" style="font-size:12px;font-style:italic">'
                     f'+{n_calls} call{"s" if n_calls > 1 else ""} to or from parts not drawn here</text>')
            marks_used.add("collapse")
            part_bottom += 26

    # ---- column heads
    cols = [(CAPX, "CAPABILITY"), (FX, "INTENDED FLOW"), (SX, "STAGE"), (PX, "PROCESS STEP")]
    rels = [(FX, "delivered by"), (SX, "contains"), (PX, "contains")]
    if draw_parts and view != "join":
        cols += [(CX, "PART"), (DX, "EXTERNAL DEPENDENCY")]
        rels += [(CX, "carried out by"), (DX, "depends on")]
    head = [f'<text x="{x}" y="22" class="k">{k}</text>' for x, k in cols]
    head += [f'<text x="{x - 12}" y="22" class="r" text-anchor="end" style="font-size:12px">{r} →</text>' for x, r in rels]

    # ---- key
    rows = []
    e = [("".join(b.svg() for b in step_boxes.values()) if x is STEPS_SLOT else x) for x in e]
    e += [f'<g class="fold" tabindex="0" role="button" aria-expanded="{"true" if o else "false"}" data-open="{esc(k)}"'
          + (f' data-holds="{esc(h)}"' if h and not o else "") + f'>{b.svg()}</g>'
          for b, k, o, h in fold_lines]
    if view == "join":
        return head + e, max(body_bottom, cap_bottom), [f.get("name") for f, _, _ in flow_boxes]
    rows += KEY_ROWS  # two entries: everything else is written on the box, or said where it shows on click
    if styled:
        rows += [(f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{SUM}/>', "first-hand: adds up, step to stage to flow"),
                 (f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{COUNT}/>', "counted, not added: a capability's flows"),
                 (f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{INFER}/>', "inferred: performs, depends on"),
                 (f'<text x="14" y="4" {TAG}>on</text>', "grey text: what that box reports, and what is on record")]
    M.setdefault("_key_rows", {})[mid] = rows
    if not key:
        return head + e, max(body_bottom, part_bottom, cap_bottom), [f.get("name") for f, _, _ in flow_boxes]
    ky = cap_bottom + 56
    ksvg, kbot = key_block(rows, 12, ky)
    bottom = max(body_bottom, part_bottom, kbot, cap_bottom)
    return head + e + [ksvg], bottom, [f.get("name") for f, _, _ in flow_boxes]


KEY_ROWS = [('<rect x="14" y="-8" width="36" height="16" rx="3" class="bx"/>', "a box: one thing at its level"),
            ('<rect x="2" y="-7" width="18" height="14" rx="2" class="bx"/><line x1="20" y1="0" x2="34" y2="0" class="ln"/>'
             '<rect x="34" y="-7" width="18" height="14" rx="2" class="bx"/>'
             f'<g opacity="{FAINT}"><line x1="52" y1="0" x2="58" y2="0" class="ln"/><rect x="58" y="-7" width="6" height="14" class="bx"/></g>',
             "lit: the chain of what you clicked")]


def seq_for(r, step):
    """A call's place in the order of calls within one step: `sequence` is one number for every step it is in, or
    `step:order` pairs (`6:2; 8:1`) for a call made in several steps."""
    pairs = [x.split(":", 1) for x in ids(r.get("sequence"))]
    if len(pairs) == 1 and len(pairs[0]) == 1:
        return pairs[0][0] if step in ids(r.get("step_hint")) else ""
    return next((o[0].strip() for st, *o in pairs if o and st.strip() == step), "")


def numbered_steps(M):
    """The steps in which at least one call has a place in a strict order."""
    if "_numbered" not in M:
        rels = [r for r in M["R"]["subjects"] if r.get("kind") == "relationship"]
        M["_numbered"] = {h for r in rels for h in ids(r.get("step_hint")) if seq_for(r, h)}
    return M["_numbered"]


def order_mark(M, r, step):
    """A call's number in its step's strict order; `~` for a call in a numbered step whose place is not known."""
    return seq_for(r, step) or ("~" if step in numbered_steps(M) else "")


def proposed(rows):
    return any(r.get("source", "").lower().startswith("proposed") for r in rows)


def proposed_marker(mid, used):
    """The hollow dot that starts a proposed call, defined once per figure."""
    if "call-proposed" in used:
        return ' marker-start="url(#pr-' + mid + ')"', ""
    used.add("call-proposed")
    return (' marker-start="url(#pr-' + mid + ')"',
            f'<defs><marker id="pr-{mid}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7">'
            '<circle cx="5" cy="5" r="3.2" style="fill:var(--paper);stroke:var(--g600);stroke-width:1.4"/></marker></defs>')


def free_y(M, mid, x, y, text, end=False):
    """A y for a call-order number that keeps it clear of the numbers already placed in this figure."""
    w = len(text) * 12 * 6.2 / 11.5
    x0 = x - w if end else x
    placed = M.setdefault("_seq_placed", {}).setdefault(mid, [])
    while any(x0 < b[2] and b[0] < x0 + w and y - 11 < b[3] and b[1] < y + 3 for b in placed):
        y += 13
    placed.append((x0, y - 11, x0 + w, y + 3))
    return y


def seq_label(x, y, cls, ends, step, seq, anchor=""):
    """A call's order number, with what it means as its title: said where it shows, not in the key."""
    return (f'<g><title>{esc(SEQ_SAYS[seq == "~"])}</title>'
            f'<text x="{x:g}" y="{y:g}"{anchor} class="{cls} seq" {ends} data-steps="{esc(step)}" data-seq="{esc(seq)}" '
            f'style="font-family:var(--sans);font-size:12px;font-weight:700;fill:var(--clay-d)">{esc(seq)}</text></g>')


SEQ_SAYS = ("this call's place among calls that always run one after another, in this order, on one way of the step",
            "in a step whose calls are ordered, a call with no single place in that order (repeated per item, or its place not read)")


def call_arcs(M, mid, cbox, calls, used):
    """Each call between two drawn components, as an arc with an arrow on the right of the component column: shown
    when either end is clicked, or always (calls="all"). Different owners make it a handoff; blank owners, unknown."""
    carriers = {c["subject_id"] for c in M["comps"] + M["persons"]}
    rels = [r for r in M["R"]["subjects"] if r.get("kind") == "relationship" and r.get("from_id") != r.get("to_id")
            and r.get("from_id") in carriers and r.get("to_id") in carriers]
    rows = [r for r in rels if r["from_id"] in cbox and r["to_id"] in cbox]
    M["_calls_missing"] = sum(1 for r in rels if (r["from_id"] in cbox) != (r["to_id"] in cbox))
    if not rows:
        return ""
    rows.sort(key=lambda r: abs(cbox[r["from_id"]].mid - cbox[r["to_id"]].mid))
    out = [f'<defs><marker id="ar-{mid}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">'
           f'<path d="M0,0 L8,4 L0,8 z" style="fill:var(--g600)"/></marker></defs>']
    x0 = CX + CW
    for k, r in enumerate(rows):
        a, b = cbox[r["from_id"]], cbox[r["to_id"]]
        oa, ob = M["subj"][r["from_id"]].get("owner", ""), M["subj"][r["to_id"]].get("owner", "")
        kind = "handoff" if oa and ob and oa != ob else ("same" if oa and ob else "unknown")
        used.add("call-" + kind)
        style = {"handoff": "stroke:var(--clay);stroke-width:1.6", "same": "stroke:var(--g600);stroke-width:1.3",
                 "unknown": "stroke:var(--g500);stroke-width:1.2;stroke-dasharray:3 2"}[kind]
        ya, yb = a.y + a.h * 0.35, b.y + b.h * 0.65
        bx = x0 + 8 + min(18, 3 * k)
        cls = f'call{" on" if calls == "all" else ""} {kind}'
        start = not ids(r.get("step_hint"))
        if start:
            used.add("call-start")
            style += ";stroke-dasharray:7 2 1.5 2"
        title = f'{M["subj"][r["from_id"]].get("name")} calls {M["subj"][r["to_id"]].get("name")}' + (" at start-up, in no step" if start else "")
        pm, pdef = proposed_marker(mid, used) if proposed([r]) else ("", "")
        if pm:
            title += " (drafted: no tool confirmed it)"
            out.append(pdef)
        title += {"handoff": "; a handoff: the two parts have different owners", "same": "",  # the arc says what it is where it shows
                  "unknown": "; owners not assessed, so whether it is a handoff is not known"}[kind]
        hints = " ".join(ids(r.get("step_hint")))
        ends = f'data-from="{esc(r["from_id"])}" data-to="{esc(r["to_id"])}"'
        attrs = f'{ends} data-steps="{esc(hints)}"'
        out.append(f'<path d="M{x0} {ya:g} C{bx} {ya:g}, {bx} {yb:g}, {x0 + 1} {yb:g}" fill="none" class="{cls}" '
                   f'{attrs} style="{style}" marker-end="url(#ar-{mid})"{pm}><title>{esc(title)}</title></path>')
        for h in ids(r.get("step_hint")):
            seq = order_mark(M, r, h)
            if seq:
                used.add("call-unordered" if seq == "~" else "call-seq")
                sy = free_y(M, mid, bx - 1, (ya + yb) / 2 + 4, seq, end=True)
                out.append(seq_label(bx - 1, sy, f"call {kind}", ends, h, seq, ' text-anchor="end"'))
    return "".join(out)


def direct_steps(M, sid, drawn):
    """The drawn steps a part takes part in itself, in register order."""
    return [s for s in M["step"] if s in drawn and any(x == sid for x, _ in M["step"][s]["_parts"])]


def port(b, i, n):
    """Where the i-th of n lines enters a box: spread down its left edge in the order they arrive."""
    if n == 1:
        return b.mid
    return b.y + 6 + (b.h - 12) * (i + 0.5) / n


STEPS_SLOT = object()


def plain_qualifier(q):
    """A qualifier as a reader new to the method reads it: no source citations or lifecycle codes, plain words."""
    q = re.sub(r"\s*\((?:[^()]*?(?:/|\.\w{1,5}:\d|\.py\b|\.md\b|\bL\d+\b)[^()]*?)\)", "", q)
    q = re.sub(r"^stub:", "simulated:", q.strip())
    return re.sub(r"\s{2,}", " ", q)


def is_outcome(M, sid):
    return M.get("_step_label", {}).get(sid, "").endswith(" outcome")


def outcome_short(name):
    """An outcome's name on its box: the register's sentence without its subject ("The parcel is
    delivered" -> "delivered"), since the label before it already says how the case ends."""
    m = re.match(r"(?:The|A|An) (?:\S+ ){0,3}?(?:is|are) (.+)$", name or "")
    return m.group(1) if m else (name or "")


def step_title(M, sid, short=False):
    """A process step as the reader sees it: "Step 3.1: …" for an act inside its stage, "Expected outcome: …" or
    "Other outcome: …" for a way the stage ends; short=True gives an outcome its short name, for its box on the
    map. A page that does not number its steps keeps the register's id."""
    name = M["step"].get(sid, {}).get("name", "")
    label = M.get("_step_label", {}).get(sid)
    if short and is_outcome(M, sid):
        name = outcome_short(name)
    return f"{label}: {name}" if label else f"{sid}. {name}"


def kind_label(M, s):
    """A part's kind as the page names it: a part of the agent family is an "AI agent", whatever the register calls it."""
    return "AI agent" if M["family"](s) == "agent" else s.get("part_kind", "")


def step_box(M, view, mid, s, n, used):
    q = s.get("qualifier", "")
    suffix = ""
    style, marks = "", []
    if not carried(s):
        suffix = " · not assessed"
    full = ""
    if q and carried(s):  # the box carries the qualifier's kind word; its full words are in the tooltip and the panel
        q = re.sub(r"\bas step (\d+)\b(?!\.\d)", lambda m: "as " + (f"\u201c{outcome_short(M['step'][m.group(1)].get('name', ''))}\u201d"
                   if m.group(1) in M["step"] and is_outcome(M, m.group(1)) else m.group(0)), q)
        full = plain_qualifier(q)
        suffix = " \u00b7 " + full.split(":", 1)[0].strip()  # "partial" or "simulated"
    lines = [(t, "sx") for t in wrap(f"{step_title(M, s['step'], short=True)}{suffix}", PW - 20, 12, 3)]
    if view == "reports":
        lines += sub_lines(measure_summary(M["m_at_step"].get(s["step"], [])), PW - 20, 1)
    b = Box(PX, PW, lines, style, title=step_title(M, s["step"]) + (f"\n{full}" if full else suffix), marks=marks)
    return b


def part_box(M, view, mid, s, used):
    fam = M["family"](s)
    kind = s.get("part_kind", "")
    lines = name_lines(s.get("name", ""), CW - 20, max_lines=2)
    style, marks, rx = "", [], 3
    if view == "reports":
        kset = M["kinds"].get(kind, {}).get("set_to_ask", "")
        lines += sub_lines(f"{kind}: {kset}" if kset else kind, CW - 20, 2)
        lines += sub_lines(measure_summary(M["m_part"].get(s["subject_id"], [])), CW - 20, 2)
    else:
        lines += [(kind_label(M, s), "sub")]
        if fam == "agent" and not any(s["subject_id"] == sid for st in M["step"].values() for sid, _ in st["_parts"]):
            lines += [("takes part in no step on record", "sub")]
    return Box(CX, CW, lines, style, rx=rx, marks=marks, title=s.get("name"))


def dep_box(M, view, s, callers, direct, numbers):
    lines = name_lines(s.get("name", ""), DW - 20, max_lines=2)
    calls_in = [r for r in M["R"]["subjects"] if r.get("kind") == "relationship" and r.get("to_id") == s["subject_id"]]
    if calls_in and not any(ids(r.get("step_hint")) for r in calls_in):
        lines += [("called only at start-up", "sub")]
    if view == "reports":
        lines += sub_lines(measure_summary(M["m_part"].get(s["subject_id"], [])), DW - 20, 2)
    elif not callers and direct:
        lines += sub_lines("takes part in a step directly", DW - 20, 1)
    if s.get("map_link"):
        lines += [("the provider's own map ↗", "link")]
    b = Box(DX, DW, lines, title=s.get("name"))
    b.link = s.get("map_link", "")
    b.kids = []
    for k in M.get("dep_parts", {}).get(s["subject_id"], []):
        kl = name_lines(k.get("name", ""), DW - 40, max_lines=2)
        if view == "reports":
            kl += sub_lines(measure_summary(M["m_part"].get(k["subject_id"], [])), DW - 40, 2)
        if k.get("map_link"):
            kl += [("the provider's own map ↗", "link")]
        kb = Box(DX + 10, DW - 20, kl, title=k.get("name"))
        kb.link = k.get("map_link", "")
        b.kids.append((k["subject_id"], kb))
    b.head_h = b.h
    if b.kids:
        b.h += sum(kb.h + 6 for _, kb in b.kids) + 4
    return b


def reports_head():
    """The reports view's top: what each column is and counts on, then the business bands and the why band."""
    out = []
    band = 'fill="none" style="stroke:var(--g300);stroke-width:1.2"'
    out.append(f'<rect x="4" y="64" width="{PX + PW + 12 - 4}" height="62" rx="6" {band}/><text x="12" y="80" class="k">BUSINESS HEALTH LAYER · IS THE EXPECTATION MET?</text>')
    out.append(f'<rect x="4" y="134" width="{PX + PW + 12 - 4}" height="62" rx="6" {band}/><text x="12" y="150" class="k">BUSINESS IMPACT LAYER · FOR HOW MANY CASES IS IT NOT?</text>')
    out.append(f'<rect x="{CX - 12}" y="64" width="{DX + DW + 12 - CX + 12}" height="132" rx="6" {band}/><text x="{CX}" y="80" class="k">WHY · APPLICATION, TECHNOLOGY, AGENTIC LAYERS</text>')
    for x, is_, counted, health, impact, why in REPORT_COLS:
        out.append(f'<text x="{x}" y="36" class="sx">{esc(is_)}</text><text x="{x}" y="51" {SUB}>counted on: {esc(counted)}</text>')
        for y0, lines in ((96, health), (166, impact), (96, why)):
            for n, u in enumerate(lines):
                out.append(f'<text x="{x}" y="{y0 + 14 * n}" {SUB}>{esc(u)}</text>')
    return out, 210


def figure_map(M, view, mid, opened=None, calls="click"):
    parts, bottom, flows = business_map(M, view, mid, opened=opened, calls=calls)
    head_h = 0
    if view == "reports":
        h, head_h = reports_head()
        parts = h + [f'<g transform="translate(0,{head_h})">'] + parts + ["</g>"]
    axis = {"map": "COLUMNS ARE LEVELS · EACH ONE CONTAINS, OR IS CARRIED OUT BY, THE NEXT",
            "reports": "COLUMNS ARE LEVELS · WHAT A MEASURE IS COUNTED ON  —  BANDS ARE LAYERS · THE QUESTION IT ASKS"}[view]
    return wrap_svg(aria_map(M, view, opened), VW, bottom + head_h + 10, [defs(mid)] + parts, axis,
                    "fade-links" if view == "map" else "")


def aria_map(M, view, opened):
    flows = ", ".join(f.get("name", "") for f in M["flows"])
    op = ", ".join(x.get("name", "") for x in M["stage"].values() if x["stage"] in (opened or ()))
    return (f"{M['system']}: the flows {flows}; opened into steps: {op}; components and external dependencies "
            f"that carry those steps" + (", with what each reports and what is on record" if view == "reports" else "") + ".")


# ---------------------------------------------------------------- an AI agent as its own system

def agent_measures(M, agent):
    """The measures on record for an agent: its own, and those on the calls it makes."""
    own = M["m_part"].get(agent["subject_id"], [])
    calls = [m for r in M["R"]["subjects"] if r.get("kind") == "relationship" and r.get("from_id") == agent["subject_id"]
             for m in M["R"]["measures"] if m.get("subject_id") == r["subject_id"]]
    return own + [dict(m, _layer=layer_of(M["R"], m.get("layer")) or "") for m in calls if m not in own]


def figure_agent(M, agent, mid):
    rows = M["agent_rows"].get(agent["subject_id"], [])
    el = lambda w: [r for r in rows if r.get("element") == w]
    run = (el("run") or [{}])[0]
    steps, parts, deps = el("operation"), el("agent part"), el("dependency")
    served = [s for s in ids(run.get("serves_business_step")) if s in M["step"]]
    served += [x for r in steps for x in ids(r.get("serves_business_step")) if x in M["step"] and x not in served]
    served += [s["step"] for s in M["step"].values() if any(sid == agent["subject_id"] for sid, _ in s["_parts"]) and s["step"] not in served]
    e = [defs(mid)]
    top = 44
    if served:
        join, jbot, _ = business_map(M, "join", mid, select_steps=set(served), draw_parts=False)
        e += join
        top = jbot + 30
    else:
        e.append(f'<text x="{FX}" y="60" class="warn">the register names no business step this agent serves</text>')
        top = 90
    L, Rr = FX, VW - 20
    e.append(f'<line x1="{PX + 150}" y1="{top - 26:g}" x2="{PX + 150}" y2="{top + 0:g}" class="ln"{INFER}/>'
             f'<text x="{PX + 160}" y="{top - 8:g}" class="r" style="font-size:12px">performed or supported by</text>')
    ct = top + 50
    RX, TX, QX, DX2 = L + 20, SX, PX + 40, 1440
    TW, QW, DW2 = 268, 320, 290
    na = na_style(mid)
    used = set()
    # steps
    sboxes = []
    y = ct + 16
    for r in steps:
        lab = r.get("name", "")
        style = ""
        if not ids(r.get("performed_by")):
            lab += " · not assessed"
            style = na
            used.add("na")
        lines = name_lines(lab, TW - 20)
        sv = ids(r.get("serves_business_step"))
        if sv:
            fname = lambda x: next((f.get("name", "") for f in M["flows"] if f["flow_id"] == M["flow_of_stage"].get(M["step"][x].get("stage"))), "")
            names = [f'{M["step"][x].get("name", x)} ({fname(x)})' for x in sv if x in M["step"]]
            lines += sub_lines("serves: " + "; ".join(names), TW - 20, 9)
        b = Box(TX, TW, lines, style, title=r.get("what_it_is"))
        b.y, b.row = y, r
        b.sel = f'data-step="{esc(r["id"])}"'
        y += b.h + 10
        sboxes.append(b)
    steps_bot = y
    # parts, placed beside the steps they perform
    pboxes = []
    for r in parts:
        lab = r.get("name", "")
        style = ""
        if not ids(r.get("subject_id")):
            lab += " · not assessed"
            style = na
            used.add("na")
        lines = name_lines(lab, QW - 20) + sub_lines(r.get("what_it_is", ""), QW - 20, 2)
        b = Box(QX, QW, lines, style, title=r.get("source_ref"))
        b.sel = f'data-part="{esc(r["id"])}"'
        ys = [sb.mid for sb in sboxes if r["id"] in ids(sb.row.get("performed_by"))]
        b.target = sum(ys) / len(ys) if ys else steps_bot
        b.row = r
        pboxes.append(b)
    pboxes.sort(key=lambda b: b.target)
    cursor = ct + 16
    for b in pboxes:
        b.y = max(b.target - b.h / 2, cursor)
        cursor = b.y + b.h + 10
    pid = {b.row["id"]: b for b in pboxes}
    # dependencies, beside the parts that use them
    dboxes = []
    ext = {d["subject_id"] for d in M["deps"]}
    for r in deps:
        outside = not ids(r.get("subject_id")) or any(s in ext for s in ids(r.get("subject_id")))
        lines = name_lines(r.get("name", ""), DW2 - 20) + sub_lines(r.get("what_it_is", ""), DW2 - 20, 2)
        b = Box(DX2, DW2, lines, ' style="stroke-dasharray:8 4"' if outside else "", title=r.get("source_ref"))
        users_ = {x["id"] for x in parts if r["id"] in ids(x.get("uses"))}
        their = [x["id"] for x in steps if users_ & set(ids(x.get("performed_by")))]
        b.sel = f'data-part="{esc(r["id"])}" data-steps="{esc(" ".join(their))}"'
        users = [pb for pb in pboxes if r["id"] in ids(pb.row.get("uses"))]
        b.target = sum(u.mid for u in users) / len(users) if users else cursor
        b.users = users
        b.outside = outside
        b.row_id = r["id"]
        dboxes.append(b)
    dboxes.sort(key=lambda b: b.target)
    cursor_d = ct + 16
    for b in dboxes:
        b.y = max(b.target - b.h / 2, cursor_d)
        cursor_d = b.y + b.h + 10
    bottoms = [steps_bot] + [b.y + b.h for b in pboxes + dboxes]
    run_lines = name_lines(run.get("name", "One run"), 180) + sub_lines(run.get("what_it_is", ""), 180, 4)
    rb = Box(RX, 200, run_lines, title=run.get("source_ref"))
    first, last = (sboxes[0].mid, sboxes[-1].mid) if sboxes else (ct + 40, ct + 40)
    rb.y = max(ct + 16, (first + last) / 2 - rb.h / 2)
    bottoms.append(rb.y + rb.h)
    bot = max(bottoms) + 24
    title = f'{agent.get("name", "")} · {kind_label(M, agent)} · drawn as its own system of interest'.upper()
    e.append(f'<rect x="{L}" y="{top:g}" width="{Rr - L}" height="{bot - top:g}" rx="10" class="bx"{HEAVY}/>'
             f'<text x="{L + 16}" y="{top + 22:g}" class="k" style="fill:var(--slate)">{esc(title)}</text>'
             f'<text x="{Rr - 16}" y="{top + 22:g}" class="warn" text-anchor="end">still forming</text>')
    for x, k in [(RX, "RUN"), (TX, "ITS STEPS"), (QX, "ITS PARTS"), (DX2, "ITS DEPENDENCIES")]:
        e.append(f'<text x="{x}" y="{ct:g}" class="k">{k}</text>')
    for x, rel in [(TX, "contains"), (QX, "performed by"), (DX2, "depends on")]:
        e.append(f'<text x="{x - 12}" y="{ct:g}" class="r" text-anchor="end" style="font-size:12px">{rel} →</text>')
    e.append(rb.svg())
    if sboxes:
        tx = TX - 18
        e.append(f'<line x1="{RX + 200}" y1="{rb.mid:g}" x2="{tx}" y2="{rb.mid:g}" class="ln"/>'
                 f'<line x1="{tx}" y1="{min(first, rb.mid):g}" x2="{tx}" y2="{max(last, rb.mid):g}" class="ln"/>')
        for sb in sboxes:
            e.append(f'<line x1="{tx}" y1="{sb.mid:g}" x2="{TX}" y2="{sb.mid:g}" class="ln"/><circle cx="{tx}" cy="{sb.mid:g}" r="2.4" class="hit"/>')
    for sb in sboxes:
        for p in ids(sb.row.get("performed_by")):
            if p in pid:
                e.append(f'<line x1="{TX + TW}" y1="{sb.mid:g}" x2="{QX}" y2="{pid[p].mid:g}" class="ln link" '
                         f'data-step="{esc(sb.row["id"])}" data-part="{esc(p)}"{INFER}/>')
        e.append(sb.svg())
    for b in pboxes:
        e.append(b.svg())
    for b in dboxes:
        for u in b.users:
            e.append(f'<line x1="{QX + QW}" y1="{u.mid:g}" x2="{DX2}" y2="{b.mid:g}" class="ln link" '
                     f'data-part="{esc(u.row["id"])}" data-dep="{esc(b.row_id)}"{INFER}/>')
        e.append(b.svg())
    # what the agent can report: the method's questions, with what the register holds for each
    ms = agent_measures(M, agent)
    mt = bot + 30
    qs = M["R"]["method"]["agent-questions"]
    rowsvg = []
    yq = mt + 44
    for q in qs:
        got = [m for m in ms if m.get("agent_question") == q["agent_question"]]
        held = "; ".join(f'{m.get("measure")} ({"emitted by the code" if m.get("exists") == "yes" else "proposed"})' for m in got)
        mlines = wrap(held or "none on record", 760, 12, 3)
        rowsvg.append(f'<text x="{L + 16}" y="{yq:g}" class="sx">{esc(q["question"])}</text>')
        for n, ln in enumerate(mlines):
            rowsvg.append(f'<text x="{L + 480}" y="{yq + LH * n:g}" {SUB if not held else chr(99) + "lass=" + chr(34) + "sx" + chr(34)}>{esc(ln)}</text>')
        rowsvg.append(f'<text x="{Rr - 16}" y="{yq:g}" class="warn" text-anchor="end">{esc(q["status"])}</text>')
        yq += 10 + LH * len(mlines)
    other = [m for m in ms if not m.get("agent_question")]
    if other:
        txt = "also on record for it: " + "; ".join(f'{m.get("measure")} ({short_layer(m["_layer"])})' for m in other)
        for ln in wrap(txt, Rr - L - 32, 12, 2):
            rowsvg.append(f'<text x="{L + 16}" y="{yq:g}" {SUB}>{esc(ln)}</text>')
            yq += LH
        yq += 6
    mb = yq + 20
    e.append(f'<rect x="{L}" y="{mt:g}" width="{Rr - L}" height="{mb - mt:g}" rx="6" fill="none" style="stroke:var(--g300);stroke-width:1.2"/>'
             f'<text x="{L + 16}" y="{mt + 20:g}" class="k">AGENTIC LAYER · WHAT IT CAN REPORT, BENEATH THE STEP</text>'
             f'<text x="{L + 480}" y="{mt + 20:g}" class="k">ON RECORD IN THIS REGISTER</text>'
             f'<text x="{Rr - 16}" y="{mt + 20:g}" class="k" text-anchor="end">HOW SETTLED</text>')
    e += rowsvg
    krows = [(f'<g opacity="{FAINT}"><rect x="14" y="-8" width="36" height="16" rx="2" class="bx"/></g>', "faint: the business map, for place"),
             ('<rect x="14" y="-8" width="36" height="16" rx="2" class="bx"/>', "full strength, top row: the business steps it serves"),
             (f'<rect x="14" y="-8" width="36" height="16" rx="3" class="bx"{HEAVY}/>', "heavy box: the agent, its own system"),
             ('<line x1="12" y1="0" x2="52" y2="0" class="ln"/>', "line: contains"),
             (f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{INFER}/>', "dotted: performs, depends on, carried out by"),
             ('<rect x="14" y="-8" width="36" height="16" rx="2" class="bx" style="stroke-dasharray:8 4"/>', "dashed box: external, run by someone else")]
    if "na" in used:
        krows.append((f'<rect x="14" y="-8" width="36" height="16" rx="2" class="bx"{na}/>', "hatched: not assessed, looked for and not found"))
    krows.append(('<text x="14" y="4" class="warn" style="font-size:12px">still</text>', "orange italic: how settled the method's question is"))
    ksvg, kbot = key_block(krows, 12, top + 50, width=262)
    e.append(ksvg)
    height = max(mb, kbot) + 10
    aria = (f"{agent.get('name')} drawn as its own system: one run, {len(steps)} steps, {len(parts)} parts, "
            f"{len(deps)} dependencies; it serves business steps {', '.join(served) or 'none on record'}.")
    return wrap_svg(aria, VW, height, e, "TOP: THE BUSINESS STEPS IT SERVES, FAINT FOR PLACE · IN THE BOX: THE AGENT'S OWN LEVELS · STILL FORMING")


# ---------------------------------------------------------------- how this map was made

BY_STYLE = {"tool": "", "model drafting": ' style="stroke-dasharray:4 3"', "person confirming": HEAVY,
            "by hand": ' style="stroke-dasharray:1.5 2.5"'}


def figure_how_made(M, mid, checked, reg_label):
    """The register's own run (how-made.csv), then the check and the draw this page came from, as a workflow."""
    rows = [dict(r, _pass=r.get("pass") or "1") for r in M["R"]["how-made"]]
    rows.sort(key=lambda r: int(r["_pass"]) if r["_pass"].isdigit() else 0)
    err, warn = checked
    rows.append(dict(_pass="this page", step="check", name="For this page: check the register", went_in=f"the register ({reg_label})",
                     came_out=f"{err} errors, {warn} warnings", done_by="tool",
                     note="capability_views.py --check: ids that point nowhere, values outside the method's lists, rows with no citation"))
    rows.append(dict(_pass="this page", step="draw", name="For this page: draw the views", went_in="the register and the method's lists", came_out="this page",
                     done_by="tool", note="capability_views.py: fixed layout rules; nothing is typed in by hand"))
    SXc, IX, OX, BX = 12, 380, 840, 1240
    e = [f'<text x="{SXc}" y="22" class="k">STEP</text><text x="{IX}" y="22" class="k">WHAT WENT IN</text>'
         f'<text x="{OX}" y="22" class="k">WHAT CAME OUT</text><text x="{BX}" y="22" class="k">WHO DID IT</text>']
    y, prev, shown = 40, None, None
    srcs = M["R"]["sources"]
    for r in rows:
        if r["_pass"] != shown:
            shown = r["_pass"]
            src_lines = []
            if shown == "this page":
                head_ = "THIS PAGE"
            else:
                head_ = f"PASS {shown}"
                src_lines = [f'{x.get("source_id", "")} · {x.get("what")} ({x.get("kind")}, {x.get("as_of")})'
                             + (f' · {x.get("note")}' if x.get("note") else "") for x in srcs if x.get("pass") == shown]
                if not srcs:
                    ex = (M["R"]["about"] or [{}])[0].get("sources_examined", "")
                    src_lines = [f"sources examined: {ex}"] if ex else []
            hl = wrap(head_, VW - 40, 13.6, 2)
            y += 6
            for n_, ln in enumerate(hl):
                e.append(f'<text x="{SXc}" y="{y + 12 + LH * n_:g}" class="k" style="fill:var(--slate)">{esc(ln)}</text>')
            y += 14 + LH * len(hl)
            for sl in src_lines:
                for ln in wrap(sl, VW - 40, 12, 6):
                    e.append(f'<text x="{SXc}" y="{y + 10:g}" class="sx">{esc(ln)}</text>')
                    y += LH
            if src_lines:
                y += 6
            prev = None
        label = (f'{r.get("step")}. ' if str(r.get("step", "")).isdigit() else "") + r.get("name", "")
        b = Box(SXc, 330, name_lines(label, 310, max_lines=2))
        b.y = y
        cells = [wrap(r.get("went_in", ""), 430, 12, 4), wrap(r.get("came_out", ""), 370, 12, 4)]
        by = ids(r.get("done_by"))
        note = wrap(r.get("note", ""), 490, 12, 40)
        h = max(b.h, LH * max(len(cells[0]), len(cells[1])) + 12, 30 + LH * len(note))
        b.h = max(b.h, h - 8)
        if prev is not None:
            e.append(f'<line x1="{SXc + 30}" y1="{prev:g}" x2="{SXc + 30}" y2="{y:g}" class="ln" marker-end="url(#{mid})"/>')
        e.append(b.svg())
        for x0, lines in ((IX, cells[0]), (OX, cells[1])):
            for n, ln in enumerate(lines):
                e.append(f'<text x="{x0}" y="{y + 17 + LH * n:g}" class="sx">{esc(ln)}</text>')
        cx = BX
        for who in by:
            w = text_w(who, 12) + 16
            e.append(f'<rect x="{cx:g}" y="{y + 5:g}" width="{w:g}" height="20" rx="3" class="bx"{BY_STYLE.get(who, "")}/>'
                     f'<text x="{cx + 8:g}" y="{y + 19:g}" class="s" style="font-size:12px;fill:var(--slate)">{esc(who)}</text>')
            cx += w + 8
        for n, ln in enumerate(note):
            e.append(f'<text x="{BX}" y="{y + 42 + LH * n:g}" {SUB}>{esc(ln)}</text>')
        prev = y + b.h
        y += h + 14
    ky = y + 30
    krows = [(f'<rect x="12" y="-9" width="44" height="18" rx="3" class="bx"{BY_STYLE[k]}/>', t) for k, t in
             [("tool", "solid: a tool produced it"), ("model drafting", "dashed: an AI assistant drafted it from the sources"),
              ("person confirming", "heavy: a person checked and confirmed it"), ("by hand", "dotted: a person wrote it directly")]]
    ksvg, kbot = key_block(krows, 12, ky, width=520)
    e.append(ksvg)
    head = (f'<defs><marker id="{mid}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0,0 L8,4 L0,8 z" style="fill:var(--g600)"/></marker></defs>')
    return wrap_svg(f"How the register behind this page was made: {len(rows)} steps, from {reg_label}.", VW, kbot + 10,
                    [head] + e, "EACH STEP: WHAT WENT IN, WHAT CAME OUT, AND WHO DID IT")


# ---------------------------------------------------------------- the page

WORDS = [  # the controlled vocabulary for system and work-structure terms
    ("Capability", "What the business is able to do, named apart from how it is built. Covered by the flows that deliver it."),
    ("Intended flow", "One case's path from start to end, as designed."),
    ("Stage", "One ordered stretch of a flow, with an entry and an exit."),
    ("Process step", "One act inside a stage, with an outcome the business would recognise, that happened or did not."),
    ("Part", "A person or a component that carries out or supports a step. The field's term is participant."),
    ("Component", "A deployable part of the system that performs or supports a step. An AI agent is one."),
    ("External dependency", "Something the system relies on and does not run."),
]


OUTCOME_WORDS = [  # the ways a stage ends, drawn after its numbered steps
    ("Expected outcome", "A way a stage ends on its main path: the case leaves the stage as designed. Not numbered."),
    ("Other outcome", "Any other way a stage ends: an alternative or exception path out of it. Not numbered."),
]

AGENT_WORDS = [  # the levels of an AI agent seen as its own system
    ("Run", "One request an AI agent takes for one case, from taking it to its reply. The field's term is agent "
            "invocation.", "run"),
    ("Operation", "One act inside a run: a call to its model, a tool, or a check. Not a process step.", "operation"),
    ("Agent part", "A piece of the agent's own machinery: its model, the functions it may call, its guardrails or its orchestration.",
     "agent part"),
]


def cited(text):
    """Text with its bracketed citations moved behind a fold, so the reader sees the words first."""
    cites = [c for c in re.findall(r"\(([^()]*)\)", text) if CITE.search(c)]
    plain = re.sub(r"\s*\(([^()]*)\)", lambda m: "" if CITE.search(m.group(1)) else m.group(0), text)
    return esc(plain) + (f'<details class="src"><summary>Source</summary>{esc("; ".join(cites))}</details>' if cites else "")


def words(M, opened, folded=False):
    caps = [c for c in M["caps"] if c.get("parent")] or M["caps"]
    st = next((x for x in M["stage"].values() if x["stage"] in opened), None) or next(iter(M["stage"].values()), {})
    f = next((x for x in M["flows"] if x["flow_id"] == st.get("flow")), M["flows"][0] if M["flows"] else {})
    step = next((s for s in st.get("_steps", []) if carried(s)), {}) if st else {}
    comp = "; ".join(dict.fromkeys([c.get("name") for c in M["comps"][:1] + M["agents"][:1]]))
    part = "; ".join(x.get("name", "") for x in M["persons"][:1] + M["comps"][:1])
    ex = [caps[0].get("name", "") if caps else "", f.get("name", ""), st.get("name", ""), step.get("name", ""), part,
          comp, M["deps"][0].get("name", "") if M["deps"] else "none in the register"]
    trs = "".join(f"<tr><th>{w}</th><td>{d}</td><td class=\"ex\">{esc(e)}</td></tr>" for (w, d), e in zip(WORDS, ex))
    lab = M.get("_step_label", {})
    for w, d_ in OUTCOME_WORDS:
        e = next((M["step"][s].get("name", "") for s in lab if lab[s] == w and s in M["step"]), "")
        trs += f"<tr><th>{w}</th><td>{d_}</td><td class=\"ex\">{esc(e)}</td></tr>"
    rows = next((M["agent_rows"][a["subject_id"]] for a in M["agents"] if M["agent_rows"].get(a["subject_id"])), [])
    first = lambda el: next((r.get("name", "") for r in rows if r.get("element") == el), "")
    trs += "".join(f"<tr><th>{w}</th><td>{d}</td><td class=\"ex\">{esc(first(el))}</td></tr>" for w, d, el in AGENT_WORDS)
    status = [("Case", "One instance going through a flow, from its start to its end: what the business measures count.",
               re.split(r"[:;,(]", f.get("case", ""), maxsplit=1)[0].strip()),  # its name; where it is stored stays off the page
              ("On record", "A measure the register holds: proposed, or emitted by the code today. Never a reading.", ""),
              ("Not assessed", "Looked for in the sources examined and not found, or not looked at. Never a finding "
                               "that it is absent.", "")]
    trs += "".join(f"<tr><th>{w}</th><td>{d}</td><td class=\"ex\">{cited(e)}</td></tr>" for w, d, e in status)
    table = ('<table><thead><tr><th>Level</th><th>What it means</th>'
             f'<th>Example, from this register</th></tr></thead><tbody>{trs}</tbody></table>')
    if folded:  # one link at the top of a page, closed until the reader opens it
        return f'<details class="words glossary"><summary>Glossary</summary>{table}</details>'
    return f'<section class="words"><h2>Glossary</h2>{table}</section>'


CSS = """
:root{--ivory:#FAF9F5;--paper:#FFFFFF;--slate:#141413;--clay:#D97757;--clay-d:#B85C3E;--olive:#788C5D;
--g200:#DDD9CF;--g300:#C4BFB3;--g400:#9A958A;--g500:#736F66;--g600:#57544D;
--serif:ui-serif,Georgia,"Times New Roman",serif;--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,"SF Mono","Cascadia Mono",Consolas,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ivory:#1B1B19;--paper:#262624;--slate:#ECEAE3;--clay:#E08A6D;--clay-d:#E89A7E;
--g200:#3A3935;--g300:#4E4C47;--g400:#77736B;--g500:#A39F96;--g600:#C2BEB5}}
:root[data-theme="dark"]{--ivory:#1B1B19;--paper:#262624;--slate:#ECEAE3;--clay:#E08A6D;--clay-d:#E89A7E;
--g200:#3A3935;--g300:#4E4C47;--g400:#77736B;--g500:#A39F96;--g600:#C2BEB5}
html,body{background:var(--ivory)}
body{margin:0;color:var(--slate);font:15px/1.6 var(--sans)}
main{max-width:1800px;margin:0 auto;padding:24px 16px 64px}
h1{font-family:var(--serif);font-weight:500;font-size:28px;margin:8px 0 4px}
h2{font-family:var(--serif);font-weight:500;font-size:22px;margin:44px 0 6px;border-top:1px solid var(--g300);padding-top:20px}
p.lede,p.ask{max-width:68rem;color:var(--g600);margin:0 0 12px}
p.ask{font-style:italic}
figure{margin:0 0 20px}
.fig{position:relative;background:var(--paper);border:1px solid var(--g300);border-radius:6px;padding:12px;overflow:hidden}
.fig svg{display:block;width:100%;height:auto;touch-action:none;cursor:grab}
.zoom{position:absolute;top:8px;right:8px;display:flex;gap:4px;z-index:1}
.zoom button{font:12px var(--sans);color:var(--slate);background:var(--paper);border:1px solid var(--g400);border-radius:4px;padding:2px 8px;cursor:pointer}
.zoom button:focus-visible{outline:2px solid var(--clay)}
.zoom button[disabled]{opacity:.4;cursor:default}
figcaption{font-size:14px;color:var(--g600);margin-top:6px;max-width:68rem}
.words table{border-collapse:collapse;width:100%;max-width:68rem;font-size:15px;background:var(--paper);border:1px solid var(--g200)}
.words th,.words td{text-align:left;vertical-align:top;padding:8px 12px;border-top:1px solid var(--g200)}
.words thead th{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--g500);border-top:none}
.words tbody th{white-space:nowrap;font-weight:600}
.words td.ex{color:var(--g600)}
svg .bx{fill:var(--paper);stroke:var(--g500);stroke-width:1.4}
svg .t{font-family:var(--serif);font-size:15px;fill:var(--slate)}
svg .s{font-family:var(--sans);font-size:12.5px;fill:var(--g500)}
svg .r{font-family:var(--serif);font-style:italic;font-size:12.5px;fill:var(--g600)}
svg .k{font-family:var(--mono);font-size:12px;letter-spacing:.1em;fill:var(--g400)}
svg .warn{font-family:var(--serif);font-style:italic;font-size:13px;fill:var(--clay-d)}
svg .ln{stroke:var(--g600);stroke-width:1.4;fill:none}
svg .rule{stroke:var(--slate);stroke-width:1.3}
svg .hit{fill:var(--g600)}
svg .sx{font-family:var(--sans);font-size:12px;fill:var(--slate)}
svg g.sel{cursor:pointer}
svg g.sel:focus{outline:none}
svg g.sel:focus-visible rect.bx{stroke:var(--clay)}
svg .off{opacity:.1}
svg g.sel.folded.off{opacity:.35}
svg g.fold.off{opacity:.35}svg g.fold.held rect.bx{stroke-opacity:1!important;stroke-dasharray:none!important}
svg g.tog{cursor:pointer}svg g.tog:focus{outline:none}svg g.tog:focus-visible rect{stroke:var(--clay)!important;stroke-width:1.5px!important}
svg.reach g.sel.folded:not(.off) rect.bx{stroke-opacity:1!important;stroke-dasharray:none!important}
svg.fade-links .ln.link[data-step]{opacity:.35}
svg.fade-links.picked .ln.link[data-step]:not(.off){opacity:1}
svg.picked .link.off,svg.fade-links.picked .ln.link.off,svg.picked .tree.off{opacity:0}
svg .call{display:none}
svg .call.on,svg .call.shown{display:inline}
p.hint{font-size:13px;color:var(--g500);margin:0 0 8px}
"""

SCRIPT = """<script>
(function () {
  var clears = [], CHAIN = {};
  try { CHAIN = JSON.parse((document.getElementById('chain-data') || {}).textContent || '{}'); } catch (e) {}
  var nodeKey = function (x) { return x.dataset.node || (x.dataset.step ? 's:' + x.dataset.step : 'p:' + x.dataset.part); };
  document.querySelectorAll('svg').forEach(function (svg) {
    var cur = null;
    function clear() {
      cur = null; delete svg.dataset.cur;
      svg.classList.remove('picked'); svg.classList.remove('reach');
      svg.querySelectorAll('.off').forEach(function (x) { x.classList.remove('off'); });
      svg.querySelectorAll('g.fold.held').forEach(function (x) { var t = x.querySelector('text'); t.textContent = t.dataset.said; x.classList.remove('held'); });
      svg.querySelectorAll('.shown').forEach(function (x) { x.classList.remove('shown'); });
    }
    clears.push(clear);
    function pick(g) {  // the chain through the clicked box, up to the capabilities and down to the dependencies
      var key = nodeKey(g);
      if (key === cur) { clear(); return; }
      light(key);
    }
    function light(key) {
      clear(); cur = key; svg.dataset.cur = key;
      svg.classList.add('picked');
      var lit = new Set([key].concat(CHAIN[key] || []));
      var has = function (k) { return lit.has(k); };
      var inLit = function (x) {
        var s = (x.dataset.steps || '').split(' ').filter(Boolean);
        return !s.length || s.some(function (t) { return has('s:' + t); });
      };
      var reach = /^[ps]:/.test(key);  // a part or step picked: a folded line lights when the chain runs into what it holds, else fades
      svg.classList.toggle('reach', reach);  // a stage or flow picked folds its neighbours and leaves them unfaded
      svg.querySelectorAll(reach ? 'g.sel' : 'g.sel:not(.folded)').forEach(function (x) { if (!has(nodeKey(x))) x.classList.add('off'); });
      svg.querySelectorAll('g.fold[data-holds]').forEach(function (x) {  // a folded line holding lit boxes stays lit and says how many
        var n = x.dataset.holds.split(' ').filter(has).length, t = x.querySelector('text');
        if (n) { x.classList.add('held'); t.dataset.said = t.textContent; t.textContent += ' \u00b7 ' + n + ' lit'; }
        else if (reach) x.classList.add('off');
      });
      svg.querySelectorAll('.link').forEach(function (l) {
        var on = l.dataset.dep
          ? has('p:' + l.dataset.part) && has('p:' + l.dataset.dep) && (inLit(l) || key === 'p:' + l.dataset.part || key === 'p:' + l.dataset.dep)
          : has('s:' + l.dataset.step) && has('p:' + l.dataset.part);
        if (!on) l.classList.add('off');
      });
      svg.querySelectorAll('.tree').forEach(function (x) { if (!x.dataset.ends.split(' ').every(function (k) { return has(k); })) x.classList.add('off'); });
      svg.querySelectorAll('.call').forEach(function (c) {
        c.classList.add(has('p:' + c.dataset.from) && has('p:' + c.dataset.to) && inLit(c) ? 'shown' : 'off');
      });
    }
    svg.addEventListener('click', function (ev) {
      if (svg.dataset.dragged) { delete svg.dataset.dragged; return; }
      var g = ev.target.closest('g.sel');
      if (g) pick(g); else clear();
    });
    svg.addEventListener('mapswap', function () { if (cur) light(cur); });  // a folded map swapped in keeps the chain lit
    svg.addEventListener('keydown', function (ev) {
      var g = ev.target.closest && ev.target.closest('g.sel');
      if (g && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); g.dispatchEvent(new MouseEvent('click', {bubbles: true})); }  // every listener on a click hears the key too
    });
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') clears.forEach(function (c) { c(); }); });
  // zoom and pan inside each figure, so a large map reads on a laptop; the page itself never scrolls sideways.
  // base is the drawing's bounds; vb is the view, whose aspect is always the box's, so a frame taller than the drawing
  // is room to pan into. The drawing opens fitted to the frame's width, anchored top-left; nothing zooms by itself.
  document.querySelectorAll('.fig').forEach(function (fig) {
    var svg = fig.querySelector('svg'); if (!svg) return;
    svg.setAttribute('preserveAspectRatio', 'xMinYMin meet');
    function bounds() { return svg.getAttribute('viewBox').split(' ').map(Number); }
    var base = bounds(), vb = base.slice(), fitted = true;
    function aspect() { var r = svg.getBoundingClientRect(); return r.width > 0 && r.height > 0 ? r.height / r.width : 0; }  // 0 while hidden
    function set() { svg.setAttribute('viewBox', vb.join(' ')); }
    function clamp() {  // within the drawing; a view wider or taller than it sits at its top-left
      vb[0] = Math.max(base[0], Math.min(vb[0], base[0] + base[2] - vb[2]));
      vb[1] = Math.max(base[1], Math.min(vb[1], base[1] + base[3] - vb[3]));
    }
    function fit() { var a = aspect(); if (!a) return; vb = [base[0], base[1], base[2], base[2] * a]; fitted = true; set(); }
    function reshape() {  // the box changed size: keep the scale and the top-left, take the new aspect
      var a = aspect(); if (!a) return;
      if (fitted) { fit(); return; }
      vb[3] = vb[2] * a; clamp(); set();
    }
    svg.addEventListener('mapswap', function () {  // a folded map swapped in: the zoom and pan carry over, held to the new drawing
      base = bounds();
      if (fitted) { fit(); return; }
      vb[2] = Math.min(vb[2], base[2]); reshape();
    });
    fit();
    if (window.ResizeObserver) new ResizeObserver(reshape).observe(svg);
    function zoom(f, cx, cy) {
      var a = aspect(); if (!a) return;
      var w = Math.min(base[2], Math.max(base[2] / 12, vb[2] * f)), h = w * a;
      vb = [cx - (cx - vb[0]) * w / vb[2], cy - (cy - vb[1]) * h / vb[3], w, h]; fitted = false; clamp(); set();
    }
    function user(ev) { var r = svg.getBoundingClientRect(); return [vb[0] + (ev.clientX - r.left) * vb[2] / r.width, vb[1] + (ev.clientY - r.top) * vb[3] / r.height]; }
    function box(pick) {  // the selection's bounds in drawing units: the picked box, or every lit box; null if none
      var r = svg.getBoundingClientRect(), lo = [Infinity, Infinity], hi = [-Infinity, -Infinity], gs;
      if (pick) gs = svg.dataset.cur ? Array.prototype.filter.call(svg.querySelectorAll('g.sel'), function (g) { return nodeKey(g) === svg.dataset.cur; }) : [];
      else gs = svg.querySelector('.off') ? svg.querySelectorAll('g.sel:not(.off)') : [];
      Array.prototype.forEach.call(gs, function (g) {
        var q = g.getBoundingClientRect(); if (!q.width && !q.height) return;
        [[q.left, q.top], [q.right, q.bottom]].forEach(function (pt) {
          var u = [vb[0] + (pt[0] - r.left) * vb[2] / r.width, vb[1] + (pt[1] - r.top) * vb[3] / r.height];
          lo = [Math.min(lo[0], u[0]), Math.min(lo[1], u[1])]; hi = [Math.max(hi[0], u[0]), Math.max(hi[1], u[1])];
        });
      });
      return lo[0] === Infinity ? null : [lo, hi];
    }
    var picked = null;
    function anchor() {  // + and - zoom about the selection's centre, or about the frame's top-left, so nothing zooms out of view
      var b = picked = box(true) || box(false);
      return b ? [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2] : [vb[0], vb[1]];
    }
    function into(b) {  // a selection that fits the view is moved wholly into it
      if (!b) return;
      for (var i = 0; i < 2; i++) if (b[1][i] - b[0][i] <= vb[2 + i]) vb[i] = Math.min(Math.max(vb[i], b[1][i] - vb[2 + i]), b[0][i]);
      clamp(); set();
    }
    var sel = fig.querySelector('[data-zoom="selection"]');
    fig.querySelectorAll('[data-zoom]').forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.zoom, a;
        if (k === 'in') { a = anchor(); zoom(1 / 1.5, a[0], a[1]); into(picked); }
        else if (k === 'out') { a = anchor(); zoom(1.5, a[0], a[1]); into(picked); }
        else if (k === 'fit') fit();
        else {
          var s = box(false), A = aspect(); if (!s || !A) return;
          var lo = s[0], hi = s[1], pad = 40, w = Math.max(hi[0] - lo[0] + 2 * pad, (hi[1] - lo[1] + 2 * pad) / A);
          w = Math.min(base[2], w); var h = w * A;
          vb = [(lo[0] + hi[0]) / 2 - w / 2, (lo[1] + hi[1]) / 2 - h / 2, w, h]; fitted = false; clamp(); set();
        }
      });
    });
    new MutationObserver(function () { if (sel) sel.disabled = !svg.querySelector('.off'); })
      .observe(svg, {subtree: true, attributes: true, attributeFilter: ['class']});
    svg.addEventListener('wheel', function (ev) {
      if (!ev.ctrlKey) return; ev.preventDefault(); var u = user(ev); zoom(ev.deltaY < 0 ? 1 / 1.2 : 1.2, u[0], u[1]);
    }, {passive: false});
    var drag = null;
    svg.addEventListener('pointerdown', function (ev) { drag = {x: ev.clientX, y: ev.clientY, vb: vb.slice(), moved: false}; });
    svg.addEventListener('pointermove', function (ev) {
      if (!drag) return; var r = svg.getBoundingClientRect(), dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
      if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 5) return;
      drag.moved = true; fitted = false; vb[0] = drag.vb[0] - dx * vb[2] / r.width; vb[1] = drag.vb[1] - dy * vb[3] / r.height; clamp(); set();
    });
    window.addEventListener('pointerup', function () { if (drag && drag.moved) svg.dataset.dragged = '1'; drag = null; });
  });
})();
</script>"""

ZOOM = ('<div class="zoom"><button type="button" data-zoom="in" aria-label="Zoom in">+</button>'
        '<button type="button" data-zoom="out" aria-label="Zoom out">&minus;</button>'
        '<button type="button" data-zoom="fit">Fit</button>'
        '<button type="button" data-zoom="selection" disabled>Zoom to selection</button></div>')

HINT_CLICK = ('Click any box to light the chain through it: the flow and capabilities it belongs to above it, the parts it relies on below it. Capabilities are tied to a whole flow, so every stage and step of a flow lights the same capabilities. '
              'Click it again, click empty space or press Escape to clear.')
HINT_NUM = ('<p class="hint">The lines from steps to parts are light until you click. '
            + HINT_CLICK + '</p>')
HINT = '<p class="hint">' + HINT_CLICK + '</p>'


def page(M, opened, reg_label, build_cmd, checked=(0, 0)):
    overview = figure_map(M, "map", "m9", opened=set(M["stage"]), calls="all")
    sections = [words(M, opened)]
    flows = ", ".join(f.get("name", "") for f in M["flows"])
    op = ", ".join(f'{M["stage"][s].get("name")}' for s in sorted(opened, key=lambda s: list(M["stage"]).index(s)))
    n_na = sum(1 for s in M["step"].values() if not carried(s))
    sections.append(section(1, "The map", "Is this the capability, and what carries each step?",
                            figure_map(M, "map", "m1", opened=opened),
                            f"From the register: {len(M['flows'])} flow{'s' if len(M['flows']) != 1 else ''} ({flows}), "
                            f"{len(M['stage'])} stages, {len(M['step'])} steps, {n_na} of them not assessed. One stage per flow is opened into "
                            f"its steps ({op}): by default the one with the most steps carried out, among the stages an AI agent takes part in "
                            "where one does. Only the components and external dependencies that carry those steps are drawn; every stage is "
                            "opened in the overview at the foot of the page."))
    sections.append(section(2, "What each column reports", "Where could we see whether it works, and where are we blind?",
                            figure_map(M, "reports", "m2", opened=opened),
                            "Each part with the set its kind is asked and the measures on record for it. Business measures count cases. "
                            "On record means proposed in the register or emitted by the code today; nothing here is a reading."))
    n = 3
    if M["agents"]:
        for i, a in enumerate(M["agents"]):
            sections.append(section(n, f"{a.get('name')}: the AI agent as its own system",
                                    "What is the agent as a system, and what can it report about the steps it serves?",
                                    figure_agent(M, a, f"a{i}") if M["agent_rows"].get(a["subject_id"]) else
                                    '<p class="ask">The register names this agent but does not describe it as its own system (agent-system.csv).</p>',
                                    "Its run, steps, parts and dependencies from agent-system.csv; the questions in the bottom band are the "
                                    "method's, and the middle column is what this register holds for each."))
            n += 1
    else:
        sections.append(f'<section><h2>{n}. The AI agent</h2><p class="ask">The register names no AI agent in this capability.</p></section>')
        n += 1
    if M["R"]["how-made"]:
        sections.append(section(n, "How this map was made", "What went in, what came out, and who did each step?",
                                figure_how_made(M, "hm", checked, reg_label),
                                "From this register's how-made.csv, then the check and the draw that made this page. "
                                "To make a map for another capability, follow FILL-STEPS.md beside the program."))
    else:
        sections.append(f'<section><h2>{n}. How this map was made</h2><p class="ask">This register does not record how '
                        'it was made (how-made.csv). The check and the draw are the program\'s: '
                        f'{checked[0]} errors, {checked[1]} warnings.</p></section>')
    sections.append('<section class="overview"><h2>Overview: every stage opened</h2>'
                    '<p class="ask">Optional. The map with every stage opened into its steps, and every part that carries one.</p>' + HINT_NUM +
                    f'<figure><div class="fig">{ZOOM}{overview}</div><figcaption>From the register: every stage opened into its '
                    'steps, every part that carries a step, and every call between parts.</figcaption></figure></section>')
    about = M["R"]["about"][0]
    head = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n"
            f"     Source: {reg_label}\n"
            "     Builder: capability_views.py\n"
            f"     Build: {build_cmd}\n-->\n")
    lede = (f"Drawn from the register {esc(reg_label)}" + (f", as of {esc(about.get('as_of'))}" if about.get("as_of") else "")
            + ". These are design-time views for a production readiness review of one capability: what carries each "
              "step, what each part serves and relies on, and where it could be seen and where it cannot. They hold no "
              "live values.")
    return (head + "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{esc(M['system'])} design views</title>\n<style>{CSS}</style></head><body><main>"
            f"<h1>{esc(M['system'])}: design-for-operations views</h1><p class=\"lede\">{lede}</p>"
            + "".join(sections) + "</main>" + chain_data(M) + SCRIPT + "</body></html>\n")


def section(n, title, ask, fig, cap):
    hint = HINT_NUM if 'class="fade-links"' in fig[:200] else HINT if 'class="ln link"' in fig else ""
    inner = fig if fig.startswith("<p") else f'{hint}<figure><div class="fig">{ZOOM}{fig}</div><figcaption>{esc(cap)}</figcaption></figure>'
    return f'<section><h2>{n}. {esc(title)}</h2><p class="ask">{esc(ask)}</p>{inner}</section>'


def main(argv=None):
    ap = argparse.ArgumentParser(description="Draws the design-for-operations views of one capability from its register.")
    ap.add_argument("register", help="the register folder")
    ap.add_argument("--out", help="the page to write (default: out/<register folder name>.html beside this program)")
    ap.add_argument("--check", action="store_true", help="only check the register")
    ap.add_argument("--open", help="the stages the map opens, by id or name, comma-separated; each replaces its flow's default")
    a = ap.parse_args(argv)
    R = load(a.register)
    err, warn = check(R)
    if a.check or err:
        for w in warn:
            print("warning:", w)
        for x in err:
            print("error:", x)
        print(f"{len(err)} errors, {len(warn)} warnings")
        if err:
            return 1
        return 0
    M = model(R)
    opened = parse_open(M, a.open)
    out = pathlib.Path(a.out) if a.out else HERE / "out" / f"{R['_name']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = "python capability_views.py " + " ".join(argv if argv is not None else sys.argv[1:])
    out.write_text(page(M, opened, pathlib.Path(a.register).as_posix(), cmd, (len(err), len(warn))), encoding="utf-8")
    if warn:
        print(f"{len(warn)} warnings; --check lists them")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
