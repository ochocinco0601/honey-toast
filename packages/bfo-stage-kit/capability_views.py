"""Draws the design-for-operations views of one capability from its register.

    python capability_views.py REGISTER [--out PAGE] [--check] [--open STAGES] [--fails PART]

REGISTER is a folder of tables in the shape of register-template/ (defined in register-template/REGISTER.md).
The method's closed lists are read from method/ beside this file. Writes one HTML page; with --check, only lists
what in the register points nowhere or sits outside the closed lists. Python standard library only.

The views are design-time: what the capability is, what carries each step, where it could be seen and where it
cannot. Nothing here reads or shows a live value.
"""
import argparse
import csv
import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
METHOD = HERE / "method"

TABLES = ["about", "capabilities", "flows", "stages", "steps", "subjects", "participation", "agent-system",
          "measures", "step-impact", "case-attributes", "how-made", "sources"]
COUNTED_ON = ("cases", "events", "requests", "resources", "runs")
LEVELS = ("component", "external dependency", "")
RECOVERY = ("moves on", "stranded", "not created", "")
AGENT_ELEMENTS = ("run", "step", "part", "dependency")
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


def load(reg):
    reg = pathlib.Path(reg)
    malformed = []
    R = {t: read_csv(reg / f"{t}.csv", malformed) for t in TABLES}
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
    caps = unique("capabilities", "capability_id")
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
    ext = {r["subject_id"] for r in R["subjects"] if r.get("level") == "external dependency"}
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
        if r.get("cause") and r["cause"] not in subj:
            err.append(f"step-impact.csv {r.get('step')}: cause {r['cause']} is not a subject")
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
                if own.get(p) != "part":
                    err.append(f"agent-system.csv {r['id']}: performed_by {p} is not one of agent {a}'s parts")
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
    return err, warn


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
            M["step"][p["step"]].setdefault("_way", []).append((p["subject_id"], p.get("way", "")))
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
    M["impact"] = {}
    for r in R["step-impact"]:
        M["impact"].setdefault(r["step"], []).append(r)
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


def other_ways(M, part_id, step_id):
    """The ways a step is still carried when a part fails. A participation row's `way` lists the ways of carrying the
    step it belongs to (`form; chat`); blank means every way needs it. Empty: the step stops."""
    s = M["step"].get(step_id, {})
    rows = s.get("_way", [])
    hit = [ids(w) for sid, w in rows if sid == part_id]
    if not hit:  # not in the step itself: it hurts the ways of the parts that call it there
        callers = {c for c, ds in M["uses"].items() if part_id in ds}
        hit = [ids(w) for sid, w in rows if sid in callers]
    if not hit or any(not h for h in hit):
        return []
    every = {x for _, w in rows for x in ids(w)}
    return sorted(every - {x for h in hit for x in h})


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


def default_failing(M):
    """An external dependency an AI agent calls, where there is one; else the component in the most steps."""
    for d in M["deps"]:
        if any(d["subject_id"] in M["uses"].get(a["subject_id"], ()) for a in M["agents"]):
            return d["subject_id"]
    counts = {}
    for s in M["step"].values():
        for sid, inv in s["_parts"]:
            if inv in ("performs", "supports") and sid in {c["subject_id"] for c in M["comps"]}:
                counts[sid] = counts.get(sid, 0) + 1
    if not counts:
        return None
    order = [c["subject_id"] for c in M["comps"]]
    return max(counts, key=lambda k: (counts[k], -order.index(k)))


def find_part(M, name):
    parts = M["comps"] + M["deps"] + [k for ks in M.get("dep_parts", {}).values() for k in ks]
    for s in parts:
        if name in (s["subject_id"], s.get("name")):
            return s["subject_id"]
    raise SystemExit(f"--fails {name!r} is not a component or external dependency; one of: "
                     + ", ".join(s.get("name", "") for s in parts))


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


def esc(s):
    return html.escape(str(s or ""), quote=True)


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
        if self.sel:
            return f'<g class="sel" tabindex="0" role="button" {self.sel}>{out}</g>'
        return out


def name_lines(text, width, cls="sx", max_lines=2):
    return [(t, cls) for t in wrap(text, width, 15 if cls == "t" else 12, max_lines)]


def sub_lines(text, width, max_lines=2):
    return [(t, "sub") for t in wrap(text, width, 12, max_lines)]


def owner_mark(mid):
    def m(x, y, box):
        # the owner line is the box's last line; the hatch sits in front of its words
        n = len(box.lines) - 1
        yy = y + 17 + LH * n - 10
        return f'<rect x="{x + 10:g}" y="{yy:g}" width="11" height="11" rx="1" class="bx" style="fill:url(#own-{mid});stroke:var(--g500)"/>'
    return m


def owner_text(s):
    o, r = s.get("owner", ""), s.get("responder", "")
    when = lambda d: f" ({d})" if d else ""
    if o and r:
        return f"owner {o}{when(s.get('owner_as_of'))}; responder {r}{when(s.get('responder_as_of'))}", False
    if o:
        return f"owner {o}{when(s.get('owner_as_of'))}; responder not assessed", False
    if r:
        return f"owner not assessed; responder {r}", False
    return "owner, responder: not assessed", True


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
            f'<line x1="12" y1="24" x2="{width - 12}" y2="24" class="rule" style="stroke-width:.8"/>')
    klass = f' class="{cls}"' if cls else ""
    return (f'<svg{klass} viewBox="0 0 {width} {height + 40:g}" role="img" aria-label="{esc(aria)}">'
            + head + '<g transform="translate(0,30)">' + "".join(parts) + "</g></svg>")


# ---------------------------------------------------------------- the business map: map, reports, reach

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


def business_map(M, view, mid, opened=None, fails=None, select_steps=None, draw_parts=True, calls="click"):
    """view: 'map', 'reports', 'reach' or 'join' (the business row above an agent's own view).
    opened: the stage ids opened into their steps. fails: the failing part (reach). select_steps: for 'join',
    the business steps the agent serves; only their stages and flows are drawn."""
    styled = view in ("reports", "reach")
    M.setdefault("_seq_placed", {})[mid] = []
    reach_steps = steps_of(M, fails) if view == "reach" else set()
    M["_ways"] = {s: other_ways(M, fails, s) for s in reach_steps} if view == "reach" else {}
    M["_fails"] = fails
    if view == "reach":
        opened = {M["step"][s]["stage"] for s in reach_steps if s in M["step"]}
    if view == "join":
        opened = {M["step"][s]["stage"] for s in select_steps}
    opened = opened or set()
    flows = M["flows"]
    if view == "join":
        flows = [f for f in flows if any(st["stage"] in opened for st in f["_stages"])]
    e, keyrows = [], []
    marks_used = set()

    # ---- flows, stages and steps, one block per flow (a tidy tree: no two parents share a line)
    y = 44
    flow_boxes, stage_boxes, step_boxes, collapse_rows = [], {}, {}, []
    reached_flows = set()
    for f in flows:
        top = y
        stages = f["_stages"] if view != "join" else [st for st in f["_stages"] if st["stage"] in opened]
        for k, st in enumerate(stages):
            label = f'{st.get("order") or k + 1}. {st.get("name", "")}'
            lines = name_lines(label, SW - 20)
            if view == "reports":
                bm = [m for s in st["_steps"] for m in M["m_step"].get(s["step"], [])]
                lines += sub_lines("business measures on its steps: " + measure_summary(bm)[len("on record: "):] if bm else "business measures on its steps: none", SW - 20, 2)
            on = view != "reach" or st["stage"] in opened
            if view == "reach" and st["stage"] in opened:
                lines += [("cases would be located here", "sub")]
            if not any(carried(x) for x in st["_steps"]) and view != "join":
                lines[0] = (lines[0][0] + " · not assessed", lines[0][1])
                lines = name_lines(" ".join(t for t, c in lines if c == "sx"), SW - 20) + [x for x in lines if x[1] != "sx"]
                sb = Box(SX, SW, lines, na_style(mid))
                marks_used.add("na")
            else:
                sb = Box(SX, SW, lines, OPEN if st["stage"] in opened and view != "join" else "")
            sb.y, sb.on = y, on
            stage_boxes[st["stage"]] = sb
            block = sb.h
            if st["stage"] in opened:
                shown = st["_steps"]
                if view == "reach":
                    shown = [s for s in st["_steps"] if s["step"] in reach_steps]
                if view == "join":
                    shown = [s for s in st["_steps"] if s["step"] in select_steps]
                yy = y
                for i, s in enumerate(shown):
                    b = step_box(M, view, mid, s, st["_steps"].index(s) + 1, marks_used)
                    b.y, b.step_id = yy, s["step"]
                    if view != "join":
                        b.sel = f'data-step="{esc(s["step"])}"'
                    step_boxes[s["step"]] = b
                    yy += b.h + 8
                rest = len(st["_steps"]) - len(shown)
                if rest and view in ("reach", "join"):
                    na = sum(1 for s in st["_steps"] if s not in shown and not carried(s))
                    txt = f"+{rest} step{'s' if rest > 1 else ''} not on this path" + (f" ({na} not assessed)" if na else "")
                    collapse_rows.append((PX + 10, yy + 10, txt))
                    marks_used.add("collapse")
                    yy += 22
                block = max(block, yy - 8 - y)
            y += block + 8
        y -= 8
        lines = name_lines(f.get("name", ""), FW - 20, max_lines=3)
        fb = Box(FX, FW, lines)
        fb.y = max(top, (top + y) / 2 - fb.h / 2)
        fon = view == "map" or view == "reports" or (view == "reach" and any(st["stage"] in opened for st in f["_stages"]))
        if fon:
            reached_flows.add(f["flow_id"])
        fb.on = fon
        tags = []
        if view == "reports":
            tags = wrap(measure_summary(M["m_flow"].get(f["flow_id"], [])), FW + 20, 11, 3)
        if view == "reach" and fon:
            tags = ["would count: its own cases wrong", "or late, moving on or stranded,", "and cases still to reach", "the failure"]
        fb.tags = tags
        flow_boxes.append((f, fb, [stage_boxes[st["stage"]] for st in stages]))
        y = max(y, fb.y + fb.h + LH * len(tags) + 6) + 30
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
        lo, hi = min([fb.mid] + [b.mid for b in sbs]), max([fb.mid] + [b.mid for b in sbs])
        on_mids = [b.mid for b in sbs if b.on]
        e.append(faint(fb.on, f'<line x1="{FX + FW}" y1="{fb.mid:g}" x2="{tx}" y2="{fb.mid:g}" class="ln"{ln}/>'))
        if view == "reach" and fb.on and len(on_mids) < len(sbs):
            e.append(f'<g opacity="{FAINT}"><line x1="{tx}" y1="{lo:g}" x2="{tx}" y2="{hi:g}" class="ln"{ln}/></g>')
            a, b = min(on_mids + [fb.mid]), max(on_mids + [fb.mid])
            e.append(f'<line x1="{tx}" y1="{a:g}" x2="{tx}" y2="{b:g}" class="ln"{ln}/>')
        elif len(sbs) > 1 or abs(sbs[0].mid - fb.mid) > 1:
            e.append(faint(fb.on, f'<line x1="{tx}" y1="{lo:g}" x2="{tx}" y2="{hi:g}" class="ln"{ln}/>'))
        for b in sbs:
            e.append(faint(b.on, f'<line x1="{tx}" y1="{b.mid:g}" x2="{SX}" y2="{b.mid:g}" class="ln"{ln}/>'
                                 f'<circle cx="{tx}" cy="{b.mid:g}" r="2.4" class="hit"/>'))
            e.append(faint(b.on and view != "join", b.svg()))
    for sid, sb in stage_boxes.items():
        kids = [step_boxes[s["step"]] for s in M["stage"][sid]["_steps"] if s["step"] in step_boxes]
        if not kids:
            continue
        ln = SUM if styled else ' style="stroke:var(--clay)"'
        if view == "join":
            ln = ""
        tx = PX - 18
        lo, hi = min([sb.mid] + [k.mid for k in kids]), max([sb.mid] + [k.mid for k in kids])
        e.append(f'<line x1="{SX + SW}" y1="{sb.mid:g}" x2="{tx}" y2="{sb.mid:g}" class="ln"{ln}/>'
                 f'<line x1="{tx}" y1="{lo:g}" x2="{tx}" y2="{hi:g}" class="ln"{ln}/>')
        for k in kids:
            e.append(f'<line x1="{tx}" y1="{k.mid:g}" x2="{PX}" y2="{k.mid:g}" class="ln"{ln}/><circle cx="{tx}" cy="{k.mid:g}" r="2.4" class="hit"/>')
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

    def draw_cap(c, x, yy, w, depth):
        cid = c["capability_id"]
        mine = tree_flows(cid)
        on = view != "reach" or any(flow_boxes[g][1].on for g in mine)
        if view == "join":
            on = False
        cls = "t" if delivered.get(cid) else "sx"
        lines = name_lines(c.get("name", ""), w - 24, cls)
        names = [flow_boxes[g][0].get("name", "") for g in sorted(mine)]
        sub = ""
        if view == "reports":
            sub = f"coverage over {len(mine)} of its flows here" if mine else "none: a gap"
        elif view == "reach":
            hit = [flow_boxes[g][0].get("name", "") for g in sorted(mine) if flow_boxes[g][1].on]
            sub = ("reads " + ", ".join(hit) + "; counts kept per flow, not added") if hit else ""
        elif depth and not mine and view != "join":
            sub = "no flow here delivers it"
        elif depth:
            sub = "inside " + M["cap"].get(c.get("parent"), {}).get("name", "")
        lines += sub_lines(sub, w - 24, 3) if sub else []
        b = Box(x, w, lines, "" if mine else ' style="stroke:var(--g400)"', rx=8 if depth == 0 else 4)
        b.y = yy
        inner = yy + b.h + (2 if M["kids"].get(cid) else 0)
        parts = []
        for k in M["kids"].get(cid, []):
            h, p = draw_cap(k, x + 14, inner, w - 28, depth + 1)
            parts.append(p)
            inner += h + 8
        h = inner - yy + (6 if M["kids"].get(cid) else 0) if M["kids"].get(cid) else b.h
        b.h = h
        if delivered.get(cid):
            origins[cid] = (x + w, yy + 18)
        return h, faint(on, b.svg()) + "".join(parts)

    yy = 44
    for root in M["kids"].get("", []):
        h, p = draw_cap(root, CAPX, yy, CAPW, 0)
        cap_svg.append(p)
        yy += h + 10
    cap_bottom = yy
    e[:0] = cap_svg
    for cid, (x, yy_) in origins.items():
        for g in delivered[cid]:
            fb = flow_boxes[g][1]
            on = fb.on and view != "join"
            e.append(faint(on, f'<line x1="{x}" y1="{yy_:g}" x2="{FX}" y2="{fb.mid:g}" class="ln"{COUNT if styled else ""}/>'
                               f'<circle cx="{x}" cy="{yy_:g}" r="3" class="hit"/>'))

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
        if view == "reach":
            ffam = {fails} | {k["subject_id"] for k in M["dep_parts"].get(fails, [])}
            shown = [fails] if fails in comp_ids else sorted({c for c, ds in M["uses"].items() if ffam & ds and c in links},
                                                             key=comp_ids.index)
        else:
            shown = [c for c in comp_ids if c in links]
            for a in M["agents"]:  # an AI agent is always drawn: it is part of the capability or it is not
                if a["subject_id"] not in shown:
                    shown.append(a["subject_id"])
        hidden_c = len([c for c in M["comps"]]) - len([c for c in shown if c in {x["subject_id"] for x in M["comps"]}])
        boxes = []
        for sid in shown:
            s = M["subj"][sid]
            b = part_box(M, view, mid, s, marks_used, fails)
            ys = [lb.mid for lb, _ in links.get(sid, [])]
            b.target = sum(ys) / len(ys) if ys else body_bottom
            boxes.append((sid, b))
        boxes.sort(key=lambda t: t[1].target)
        cursor = 44
        for n, (sid, b) in enumerate(boxes, 1):
            b.y = max(b.target - b.h / 2, cursor)
            cursor = b.y + b.h + 12
            numbers[sid] = n
            if view == "map":
                b.lines[0] = (f"{M.get('_pagenum', {}).get(sid, n)} · {b.lines[0][0]}", b.lines[0][1])
        cbox = dict(boxes)
        for sid, b in boxes:
            ins = sorted(links.get(sid, []), key=lambda t: t[0].mid)
            for i, (lb, inv) in enumerate(ins):
                st = INFER if inv == "performs" else SUPPORT
                marks_used.add("perform" if inv == "performs" else "support")
                e.append(f'<line x1="{PX + PW}" y1="{lb.mid:g}" x2="{CX}" y2="{port(b, i, len(ins)):g}" class="ln link" '
                         f'data-step="{esc(lb.step_id)}" data-part="{esc(sid)}"{st}/>')
        for sid, b in boxes:
            b.sel = f'data-part="{esc(sid)}" data-steps="{esc(" ".join(direct_steps(M, sid, step_boxes)))}"'
            e.append(b.svg())
        part_bottom = max([body_bottom] + [b.y + b.h for _, b in boxes])
        # external dependencies: beside the components that call them, or the steps they take part in directly
        dep_ids = [d["subject_id"] for d in M["deps"]]
        dshown = []
        for d in dep_ids:
            fam_ids = {d} | {k["subject_id"] for k in M["dep_parts"].get(d, [])}
            callers = [c for c in cbox if fam_ids & M["uses"].get(c, set())]
            direct = [step_boxes[s] for s in step_boxes if any(sid in fam_ids for sid, _ in M["step"][s]["_parts"])]
            if view == "reach":
                if fails in fam_ids:
                    dshown.append((d, callers, []))
                continue
            if callers or direct:
                dshown.append((d, callers, direct))
        hidden_d = len(dep_ids) - len(dshown)
        dboxes = []
        for d, callers, direct in dshown:
            s = M["subj"][d]
            b = dep_box(M, view, s, callers, direct, numbers)
            ys = [cbox[c].mid for c in callers] or [x.mid for x in direct]
            b.target = sum(ys) / len(ys) if ys else part_bottom
            dboxes.append((d, b, callers))
        dboxes.sort(key=lambda t: t[1].target)
        n = len(boxes)
        for d, b, _ in dboxes:
            for sid, bx_ in [(d, b)] + b.kids:
                n += 1
                numbers[sid] = n
        if view == "map":  # one number per part for the whole page: the overview's, where it has been drawn
            if opened is not None and set(opened) >= set(M["stage"]) and "_pagenum" not in M:
                M["_pagenum"] = dict(numbers)
            page_n = M.get("_pagenum", {})
            numbers = {sid: page_n.get(sid, n_) for sid, n_ in numbers.items()}
            for d, b, _ in dboxes:
                for sid, bx_ in [(d, b)] + b.kids:
                    bx_.lines[0] = (f"{numbers[sid]} · {bx_.lines[0][0]}", bx_.lines[0][1])
        if view == "map":  # a step's carriers by number, so a step can be read without following its lines
            for s, lb in step_boxes.items():
                ns = sorted({numbers[sid] for sid, _ in M["step"][s]["_parts"] if sid in numbers})
                if ns:
                    lb.extra = f'<text x="{PX + PW - 8}" y="{lb.y + 17:g}" text-anchor="end" {TAG}>{esc(", ".join(map(str, ns)))}</text>'
                    marks_used.add("numbers")
        cursor = 44
        for d, b, callers in dboxes:
            b.y = max(b.target - b.h / 2, cursor)
            cursor = b.y + b.h + 12
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
            reach = steps_of(M, d)
            kids = " ".join(k for k, _ in b.kids)
            head.sel = (f'data-part="{esc(d)}" data-steps="{esc(" ".join(x for x in M["step"] if x in step_boxes and x in reach))}"'
                        + (f' data-children="{esc(kids)}"' if kids else ""))
            e.append(head.svg())
            for kid, kb in b.kids:
                kr = steps_of(M, kid)
                kb.sel = (f'data-part="{esc(kid)}" data-parent="{esc(d)}" '
                          f'data-steps="{esc(" ".join(x for x in M["step"] if x in step_boxes and x in kr))}"')
                e.append(kb.svg())
            marks_used.add("dep")
        part_bottom = max([part_bottom] + [b.y + b.h for _, b, _ in dboxes])
        e.append(call_arcs(M, mid, cbox, calls, marks_used))
        if hidden_c:
            e.append(f'<text x="{CX}" y="{part_bottom + 20:g}" class="s" style="font-size:12px;font-style:italic">'
                     f'+{hidden_c} other component{"s" if hidden_c > 1 else ""} not drawn</text>')
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
        cols += [(CX, "COMPONENT"), (DX, "EXTERNAL DEPENDENCY")]
        rels += [(CX, "carried out by"), (DX, "depends on")]
    head = [f'<text x="{x}" y="22" class="k">{k}</text>' for x, k in cols]
    head += [f'<text x="{x - 12}" y="22" class="r" text-anchor="end" style="font-size:12px">{r} →</text>' for x, r in rels]

    # ---- key
    rows = []
    e = [("".join(b.svg() for b in step_boxes.values()) if x is STEPS_SLOT else x) for x in e]
    if view == "join":
        return head + e, max(body_bottom, cap_bottom), [f.get("name") for f, _, _ in flow_boxes]
    if styled:
        rows += [(f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{SUM}/>', "first-hand: adds up, step to stage to flow"),
                 (f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{COUNT}/>', "counted, not added: a capability's flows"),
                 (f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{INFER}/>', "inferred: performs, depends on")]
    else:
        rows += [('<line x1="12" y1="0" x2="52" y2="0" class="ln"/>', "line: the relation named above the columns"),
                 (f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{INFER}/>', "dotted: performs the step")]
    if "support" in marks_used:
        rows.append((f'<line x1="12" y1="0" x2="52" y2="0" class="ln"{SUPPORT}/>', "grey dashes: supports or records the step"))
    rows += [('<rect x="12" y="-9" width="40" height="18" rx="3" class="bx"/><rect x="20" y="-4" width="24" height="8" rx="2" class="bx"/>',
              "inside a box: a capability within one"),
             (f'<rect x="12" y="-8" width="26" height="16" rx="2" class="bx"{OPEN}/><line x1="38" y1="0" x2="52" y2="0" class="ln" style="stroke:var(--clay)"/>',
              "orange: a stage opened into its steps")]
    if any(not M["kids"].get(c["capability_id"]) and not tree_flows(c["capability_id"]) for c in M["caps"]):
        rows.append(('<rect x="14" y="-8" width="36" height="16" rx="2" class="bx" style="stroke:var(--g400)"/>',
                     "grey outline: a capability no flow here delivers"))
    rows.append(('<circle cx="32" cy="0" r="2.4" class="hit"/>', "dot: where a line branches to each child"))
    if "na" in marks_used:
        rows.append((f'<rect x="14" y="-8" width="36" height="16" rx="2" class="bx"{na_style(mid)}/>', "hatched: not assessed, nothing found carrying it"))
    if "part" in marks_used:
        rows.append(('<rect x="14" y="-8" width="36" height="16" rx="2" class="bx"/><rect x="14" y="-8" width="5" height="16" style="fill:var(--slate)"/>',
                     "solid bar: partial or stub, as named"))
    if "agent" in marks_used:
        rows.append((f'<rect x="14" y="-8" width="36" height="16" rx="3" class="bx"{HEAVY}/>', "heavy box: an AI agent, a part like any other; its own view follows"))
    if any(k.startswith("call-") for k in marks_used):
        shown = "always shown" if calls == "all" else "shown when either end is clicked"
        rows.append(('<path d="M14 6 C40 6, 40 -6, 14 -6" fill="none" style="stroke:var(--g600);stroke-width:1.3"/>',
                     f"arc with an arrow: one component calls another; {shown}"))
    if "call-seq" in marks_used:
        rows.append(('<text x="26" y="4" style="font-family:var(--sans);font-size:12px;font-weight:700;fill:var(--clay-d)">1 2</text>',
                     "orange numbers: calls that always run one after another, in this order, on one way of the step"))
    if "call-proposed" in marks_used:
        rows.append(('<circle cx="20" cy="0" r="3.2" style="fill:var(--paper);stroke:var(--g600);stroke-width:1.4"/>'
                     '<line x1="23" y1="0" x2="52" y2="0" style="stroke:var(--g600);stroke-width:1.3"/>',
                     "hollow dot: a drafted call, read from the code by an AI assistant; no tool confirmed it"))
    if "call-unordered" in marks_used:
        rows.append(('<text x="26" y="4" style="font-family:var(--sans);font-size:12px;font-weight:700;fill:var(--clay-d)">~</text>',
                     "orange ~: in a step whose calls are ordered, a call with no single place in that order (repeated per item, or its place not read)"))
    if "call-start" in marks_used:
        rows.append(('<line x1="12" y1="0" x2="52" y2="0" style="stroke:var(--g600);stroke-width:1.3;stroke-dasharray:7 2 1.5 2"/>',
                     "dash-dot call: made only at start-up, in no step"))
    if "call-handoff" in marks_used:
        rows.append(('<line x1="12" y1="0" x2="52" y2="0" style="stroke:var(--clay);stroke-width:1.6"/>',
                     "orange call: a handoff, the two parts have different owners"))
    if "call-unknown" in marks_used:
        rows.append(('<line x1="12" y1="0" x2="52" y2="0" style="stroke:var(--g500);stroke-width:1.2;stroke-dasharray:3 2"/>',
                     "grey dashed call: owners not assessed, so whether it is a handoff is not known"))
    if "dep" in marks_used:
        rows.append(('<rect x="14" y="-8" width="36" height="16" rx="2" class="bx" style="stroke-dasharray:8 4"/>', "dashed box: external, run by someone else"))
    if "person" in marks_used:
        rows.append(('<rect x="14" y="-8" width="36" height="16" rx="8" class="bx"/>', "round box: a person who carries out the step"))
    if "owner" in marks_used:
        rows.append((f'<rect x="14" y="-6" width="12" height="12" rx="1" class="bx" style="fill:url(#own-{mid});stroke:var(--g500)"/>',
                     "small hatch: owner and responder not assessed"))
    if "numbers" in marks_used:
        rows.append((f'<text x="14" y="4" {TAG}>2, 5</text>', "numbers at a step's right: every part carrying it, as numbered, an external dependency in it directly included"))
    if view == "reports":
        rows.append((f'<text x="14" y="4" {TAG}>on</text>', "grey text: what that box reports, and what is on record"))
    if view == "reach":
        rows.append((f'<text x="14" y="4" {TAG}>impact</text>', "grey text: what reaches that box"))
        rows.append((f'<g opacity="{FAINT}"><rect x="14" y="-8" width="36" height="16" rx="2" class="bx"/></g>', "faint: off the failing part's path"))
    if "collapse" in marks_used:
        rows.append(('<text x="14" y="4" class="s" style="font-size:12px;font-style:italic">+N</text>', "italic +N: not drawn here, counted"))
    ky = cap_bottom + 56
    ksvg, kbot = key_block(rows, 12, ky)
    bottom = max(body_bottom, part_bottom, kbot, cap_bottom)
    return head + e + [ksvg], bottom, [f.get("name") for f, _, _ in flow_boxes]


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
    return (f'<text x="{x:g}" y="{y:g}"{anchor} class="{cls} seq" {ends} data-steps="{esc(step)}" data-seq="{esc(seq)}" '
            f'style="font-family:var(--sans);font-size:12px;font-weight:700;fill:var(--clay-d)">{esc(seq)}</text>')


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
        title = f'{M["subj"][r["from_id"]].get("name")} calls {M["subj"][r["to_id"]].get("name")}' + (" at start-up" if start else "")
        pm, pdef = proposed_marker(mid, used) if proposed([r]) else ("", "")
        if pm:
            title += " (drafted: no tool confirmed it)"
            out.append(pdef)
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


def step_box(M, view, mid, s, n, used):
    q = s.get("qualifier", "")
    suffix = ""
    style, marks = "", []
    if not carried(s):
        suffix, style = " · not assessed", na_style(mid)
        used.add("na")
    elif q:
        marks.append(lambda x, y, b: f'<rect x="{x:g}" y="{y:g}" width="5" height="{b.h:g}" style="fill:var(--slate)"/>')
        used.add("part")
    carriers = {sid for sid, _ in s["_parts"]}
    room = PW - 20 - (text_w(", ".join(["00"] * len(carriers)), 12) + 12 if view == "map" and carriers else 0)
    lines = [(t, "sx") for t in wrap(f"{s['step']}. {s.get('name', '')}{suffix}", PW - 20, 12, 3, first=room)]
    if q and carried(s):
        lines += [(t, "sx") for t in wrap(q, PW - 20, 12, 8)]
    if view == "reports":
        lines += sub_lines(measure_summary(M["m_at_step"].get(s["step"], [])), PW - 20, 1)
    if view == "reach":
        rows = M["impact"].get(s["step"], [])
        other = M.get("_ways", {}).get(s["step"])
        mine = [r for r in rows if r.get("cause") == M.get("_fails")]
        if other:
            hurt = sorted({x for _, w in s.get("_way", []) for x in ids(w)} - set(other))
            line = ((f'only {" and ".join(hurt)}-way cases are hurt' if hurt else "only cases on another way are hurt")
                    + f'; the {", ".join(other)} way still carries it' + ("" if mine else "; impact not assessed"))
            lines += sub_lines(line, PW - 20, 2)
        elif not mine:
            mine = [r for r in rows if not r.get("cause")]
        if mine:
            for imp in mine[:4]:
                rec = imp.get("recovery") or "recovery not assessed"
                lines += sub_lines(f'impact: {imp.get("impact_category")}, {imp.get("unit")}; {rec}', PW - 20, 2)
            if len(mine) > 4:
                lines += [(f"+{len(mine) - 4} more costs in step-impact.csv", "sub")]
        elif not other:
            lines += [("impact: not assessed for this cause" if rows else "impact: not assessed", "sub")]
    return Box(PX, PW, lines, style, title=s.get("name") + suffix, marks=marks)


def part_box(M, view, mid, s, used, fails=None):
    fam = M["family"](s)
    kind = s.get("part_kind", "")
    lines = name_lines(s.get("name", ""), CW - 20, max_lines=2)
    style, marks, rx = "", [], 3
    if fam == "agent":
        style = HEAVY
        used.add("agent")
    if fam == "person":
        rx = 8
        used.add("person")
    if view == "reports":
        kset = M["kinds"].get(kind, {}).get("set_to_ask", "")
        lines += sub_lines(f"{kind}: {kset}" if kset else kind, CW - 20, 2)
        lines += sub_lines(measure_summary(M["m_part"].get(s["subject_id"], [])), CW - 20, 2)
    elif view == "reach":
        lines += [("fails: the cause" if s["subject_id"] == fails else "calls the failing part", "sub")]
        txt, na = owner_text(s)
        lines += [(t, "subi" if na else "sub") for t, _ in sub_lines(txt, CW - 36 if na else CW - 20, 2)]
        if na:
            marks.append(owner_mark(mid))
            used.add("owner")
    else:
        lines += [(kind, "sub")]
        txt, na = owner_text(s)
        lines += [(t, "subi" if na else "sub") for t, _ in sub_lines(txt, CW - 36 if na else CW - 20, 2)]
        if na:
            marks.append(owner_mark(mid))
            used.add("owner")
        if fam == "agent" and not any(s["subject_id"] == sid for st in M["step"].values() for sid, _ in st["_parts"]):
            lines += [("takes part in no step on record", "sub")]
    return Box(CX, CW, lines, style, rx=rx, marks=marks, title=s.get("name"))


def dep_box(M, view, s, callers, direct, numbers):
    lines = name_lines(s.get("name", ""), DW - 20, max_lines=2)
    who = s.get("owner") or "not assessed"
    lines += sub_lines(f"run by: {who}", DW - 20, 1)
    if view == "reach" and s["subject_id"] == M.get("_fails"):
        lines += [("fails: the cause", "sub")]
    calls_in = [r for r in M["R"]["subjects"] if r.get("kind") == "relationship" and r.get("to_id") == s["subject_id"]]
    if calls_in and not any(ids(r.get("step_hint")) for r in calls_in):
        lines += [("called only at start-up", "sub")]
    if view == "reports":
        lines += sub_lines(measure_summary(M["m_part"].get(s["subject_id"], [])), DW - 20, 2)
    elif not callers and direct:
        lines += sub_lines("takes part in a step directly", DW - 20, 1)
    if s.get("map_link"):
        lines += [("its owner's own map ↗", "link")]
    b = Box(DX, DW, lines, ' style="stroke-dasharray:8 4"', title=s.get("name"))
    b.link = s.get("map_link", "")
    b.kids = []
    for k in M.get("dep_parts", {}).get(s["subject_id"], []):
        kl = name_lines(k.get("name", ""), DW - 40, max_lines=2) + sub_lines(f'run by: {k.get("owner") or "not assessed"}', DW - 40, 1)
        if view == "reach" and k["subject_id"] == M.get("_fails"):
            kl += [("fails: the cause", "sub")]
        if view == "reports":
            kl += sub_lines(measure_summary(M["m_part"].get(k["subject_id"], [])), DW - 40, 2)
        if k.get("map_link"):
            kl += [("its owner's own map ↗", "link")]
        kb = Box(DX + 10, DW - 20, kl, ' style="stroke-dasharray:4 3"', title=k.get("name"))
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


def figure_map(M, view, mid, opened=None, fails=None, calls="click"):
    parts, bottom, flows = business_map(M, view, mid, opened=opened, fails=fails, calls=calls)
    head_h = 0
    if view == "reports":
        h, head_h = reports_head()
        parts = h + [f'<g transform="translate(0,{head_h})">'] + parts + ["</g>"]
    axis = {"map": "COLUMNS ARE LEVELS · EACH ONE CONTAINS, OR IS CARRIED OUT BY, THE NEXT",
            "reports": "COLUMNS ARE LEVELS · WHAT A MEASURE IS COUNTED ON  —  BANDS ARE LAYERS · THE QUESTION IT ASKS",
            "reach": "FROM A FAILING PART UP TO THE CASES IT HURTS · INFERRED TO THE STEP, FIRST-HAND ABOVE IT"}[view]
    return wrap_svg(aria_map(M, view, opened, fails), VW, bottom + head_h + 10, [defs(mid)] + parts, axis,
                    "fade-links" if view == "map" else "")


def aria_map(M, view, opened, fails):
    flows = ", ".join(f.get("name", "") for f in M["flows"])
    if view == "reach":
        name = M["subj"][fails].get("name")
        hit = sorted({M["stage"][M["step"][s]["stage"]].get("name", "") for s in steps_of(M, fails) if s in M["step"]})
        return f"{M['system']}: where a failure of {name} reaches. The stages holding a step it takes part in: {', '.join(hit)}."
    op = ", ".join(x.get("name", "") for x in M["stage"].values() if x["stage"] in (opened or ()))
    return (f"{M['system']}: the flows {flows}; opened into steps: {op}; components and external dependencies "
            f"that carry those steps" + (", with what each reports and what is on record" if view == "reports" else "") + ".")


# ---------------------------------------------------------------- an AI agent as its own system

def figure_agent(M, agent, mid):
    rows = M["agent_rows"].get(agent["subject_id"], [])
    el = lambda w: [r for r in rows if r.get("element") == w]
    run = (el("run") or [{}])[0]
    steps, parts, deps = el("step"), el("part"), el("dependency")
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
    title = f'{agent.get("name", "")} · {agent.get("part_kind", "")} · drawn as its own system of interest'.upper()
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
    own = M["m_part"].get(agent["subject_id"], [])
    calls = [m for r in M["R"]["subjects"] if r.get("kind") == "relationship" and r.get("from_id") == agent["subject_id"]
             for m in M["R"]["measures"] if m.get("subject_id") == r["subject_id"]]
    ms = own + [dict(m, _layer=layer_of(M["R"], m.get("layer")) or "") for m in calls if m not in own]
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
    ("Component", "A deployable part of the system that performs or supports a step. An AI agent is one."),
    ("External dependency", "Something the system relies on and does not run."),
]


def words(M, opened):
    caps = [c for c in M["caps"] if c.get("parent")] or M["caps"]
    st = next((x for x in M["stage"].values() if x["stage"] in opened), None) or next(iter(M["stage"].values()), {})
    f = next((x for x in M["flows"] if x["flow_id"] == st.get("flow")), M["flows"][0] if M["flows"] else {})
    step = next((s for s in st.get("_steps", []) if carried(s)), {}) if st else {}
    comp = "; ".join(dict.fromkeys([c.get("name") for c in M["comps"][:1] + M["agents"][:1]]))
    ex = [caps[0].get("name", "") if caps else "", f.get("name", ""), st.get("name", ""), step.get("name", ""), comp,
          M["deps"][0].get("name", "") if M["deps"] else "none in the register"]
    trs = "".join(f"<tr><th>{w}</th><td>{d}</td><td class=\"ex\">{esc(e)}</td></tr>" for (w, d), e in zip(WORDS, ex))
    ways = sorted({w for s_ in M["step"].values() for _, wv in s_.get("_way", []) for w in ids(wv)})
    status = [("Case", "One instance going through a flow, from its start to its end: what the business measures count.",
               f.get("case", "")),
              ("Way", "One route by which a step is carried out, where there is more than one. A step still happens "
                      "while any one of its ways is whole.", ", ".join(ways) or "this register has one way per step"),
              ("On record", "A measure the register holds: proposed, or emitted by the code today. Never a reading.", ""),
              ("Not assessed", "Looked for in the sources examined and not found, or not looked at. Never a finding "
                               "that it is absent.", "")]
    trs += "".join(f"<tr><th>{w}</th><td>{d}</td><td class=\"ex\">{esc(e)}</td></tr>" for w, d, e in status)
    return ('<section class="words"><h2>The words</h2><table><thead><tr><th>Level</th><th>What it means</th>'
            f'<th>Example, from this register</th></tr></thead><tbody>{trs}</tbody></table></section>')


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
svg.fade-links .ln.link[data-step]{opacity:.35}
svg.fade-links.picked .ln.link[data-step]:not(.off){opacity:1}
svg .call{display:none}
svg .call.on,svg .call.shown{display:inline}
p.hint{font-size:13px;color:var(--g500);margin:0 0 8px}
"""

SCRIPT = """<script>
(function () {
  var clears = [];
  document.querySelectorAll('svg').forEach(function (svg) {
    var cur = null;
    function clear() {
      cur = null;
      svg.classList.remove('picked');
      svg.querySelectorAll('.off').forEach(function (x) { x.classList.remove('off'); });
      svg.querySelectorAll('.shown').forEach(function (x) { x.classList.remove('shown'); });
    }
    clears.push(clear);
    function pick(g) {
      var key = g.dataset.step ? 's:' + g.dataset.step : 'p:' + g.dataset.part;
      if (key === cur) { clear(); return; }
      clear(); cur = key;
      svg.classList.add('picked');
      var links = Array.prototype.slice.call(svg.querySelectorAll('.link'));
      var lit = new Set(), steps = new Set(), parts = new Set();
      var own = function (x) { return (x.dataset.steps || '').split(' ').filter(Boolean); };
      if (g.dataset.step) {
        var s = g.dataset.step; steps.add(s);
        links.forEach(function (l) { if (!l.dataset.dep && l.dataset.step === s) { lit.add(l); parts.add(l.dataset.part); } });
        svg.querySelectorAll('g.sel[data-part]').forEach(function (x) { if (own(x).indexOf(s) >= 0) parts.add(x.dataset.part); });
        svg.querySelectorAll('.call, .link[data-dep]').forEach(function (c) {  // the step's calls, in order
          if ((c.dataset.steps || '').split(' ').indexOf(s) < 0) return;
          if (c.classList.contains('call')) { c.classList.add('shown'); parts.add(c.dataset.from); parts.add(c.dataset.to); }
          else { lit.add(c); parts.add(c.dataset.part); parts.add(c.dataset.dep); }
        });
      } else {
        var p = g.dataset.part, callers = [];
        var family = [p].concat((g.dataset.children || '').split(' ').filter(Boolean));
        family.forEach(function (x) { parts.add(x); });
        if (g.dataset.parent) parts.add(g.dataset.parent);
        svg.querySelectorAll('g.sel[data-part]').forEach(function (x) { if (family.indexOf(x.dataset.part) > 0) own(x).forEach(function (s) { steps.add(s); }); });
        own(g).forEach(function (s) { steps.add(s); });
        links.forEach(function (l) {
          if (l.dataset.dep) {
            if (l.dataset.part === p) { lit.add(l); parts.add(l.dataset.dep); }
            else if (family.indexOf(l.dataset.dep) >= 0) { lit.add(l); parts.add(l.dataset.part); callers.push(l.dataset.part); }
          } else if (l.dataset.part === p) { lit.add(l); steps.add(l.dataset.step); }
        });
        svg.querySelectorAll('.call').forEach(function (c) {
          if (c.classList.contains('seq')) return;
          if (c.dataset.from === p || c.dataset.to === p) {
            c.classList.add('shown'); parts.add(c.dataset.from === p ? c.dataset.to : c.dataset.from);
          }
        });
      }
      svg.querySelectorAll('.call').forEach(function (c) { if (!c.classList.contains('shown')) c.classList.add('off'); });
      svg.querySelectorAll('g.sel').forEach(function (x) {
        var on = x.dataset.step ? steps.has(x.dataset.step) : parts.has(x.dataset.part);
        if (!on) x.classList.add('off');
      });
      links.forEach(function (l) { if (!lit.has(l)) l.classList.add('off'); });
    }
    svg.addEventListener('click', function (ev) {
      if (svg.dataset.dragged) { delete svg.dataset.dragged; return; }
      var g = ev.target.closest('g.sel');
      if (g) pick(g); else clear();
    });
    svg.addEventListener('keydown', function (ev) {
      var g = ev.target.closest && ev.target.closest('g.sel');
      if (g && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); pick(g); }
    });
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') clears.forEach(function (c) { c(); }); });
  // zoom and pan inside each figure, so a large map reads on a laptop; the page itself never scrolls sideways
  document.querySelectorAll('.fig').forEach(function (fig) {
    var svg = fig.querySelector('svg'); if (!svg) return;
    var base = svg.getAttribute('viewBox').split(' ').map(Number), vb = base.slice();
    function set() { svg.setAttribute('viewBox', vb.join(' ')); }
    function zoom(f, cx, cy) {
      var w = Math.min(base[2], Math.max(base[2] / 12, vb[2] * f)), h = w * base[3] / base[2];
      cx = cx === undefined ? vb[0] + vb[2] / 2 : cx; cy = cy === undefined ? vb[1] + vb[3] / 2 : cy;
      vb = [cx - (cx - vb[0]) * w / vb[2], cy - (cy - vb[1]) * h / vb[3], w, h]; clamp(); set();
    }
    function clamp() {
      vb[0] = Math.max(base[0], Math.min(vb[0], base[0] + base[2] - vb[2]));
      vb[1] = Math.max(base[1], Math.min(vb[1], base[1] + base[3] - vb[3]));
    }
    function user(ev) { var r = svg.getBoundingClientRect(); return [vb[0] + (ev.clientX - r.left) * vb[2] / r.width, vb[1] + (ev.clientY - r.top) * vb[3] / r.height]; }
    var sel = fig.querySelector('[data-zoom="selection"]');
    fig.querySelectorAll('[data-zoom]').forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.zoom;
        if (k === 'in') zoom(1 / 1.5); else if (k === 'out') zoom(1.5); else if (k === 'fit') { vb = base.slice(); set(); }
        else {
          var r = svg.getBoundingClientRect(), lo = [Infinity, Infinity], hi = [-Infinity, -Infinity];
          svg.querySelectorAll('g.sel:not(.off)').forEach(function (g) {
            var q = g.getBoundingClientRect();
            [[q.left, q.top], [q.right, q.bottom]].forEach(function (pt) {
              var u = [vb[0] + (pt[0] - r.left) * vb[2] / r.width, vb[1] + (pt[1] - r.top) * vb[3] / r.height];
              lo = [Math.min(lo[0], u[0]), Math.min(lo[1], u[1])]; hi = [Math.max(hi[0], u[0]), Math.max(hi[1], u[1])];
            });
          });
          if (lo[0] === Infinity) return;
          var pad = 40, w = Math.max(hi[0] - lo[0] + 2 * pad, (hi[1] - lo[1] + 2 * pad) * base[2] / base[3]);
          w = Math.min(base[2], w); var h = w * base[3] / base[2];
          vb = [(lo[0] + hi[0]) / 2 - w / 2, (lo[1] + hi[1]) / 2 - h / 2, w, h]; clamp(); set();
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
      drag.moved = true; vb[0] = drag.vb[0] - dx * vb[2] / r.width; vb[1] = drag.vb[1] - dy * vb[3] / r.height; clamp(); set();
    });
    window.addEventListener('pointerup', function () { if (drag && drag.moved) svg.dataset.dragged = '1'; drag = null; });
  });
})();
</script>"""

ZOOM = ('<div class="zoom"><button type="button" data-zoom="in" aria-label="Zoom in">+</button>'
        '<button type="button" data-zoom="out" aria-label="Zoom out">&minus;</button>'
        '<button type="button" data-zoom="fit">Fit</button>'
        '<button type="button" data-zoom="selection" disabled>Zoom to selection</button></div>')

HINT_CLICK = ('Click a step or a part to keep only what it connects to; the other steps and parts fade. '
              'Click it again, click empty space or press Escape to clear.')
HINT_NUM = ('<p class="hint">The lines from steps to parts are light until you click: the numbers at a step name its parts. '
            + HINT_CLICK + '</p>')
HINT = '<p class="hint">' + HINT_CLICK + '</p>'


def page(M, opened, fails, reg_label, build_cmd, checked=(0, 0)):
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
    failing = [fails] if fails else []
    if not fails:
        failing = [a["subject_id"] for a in M["agents"][:1]] + [d for d in [default_failing(M)] if d]
        failing = list(dict.fromkeys(failing))
    for i, fp in enumerate(failing):
        fname = M["subj"][fp].get("name")
        is_dep = fp in {d["subject_id"] for d in M["deps"]}
        why = ""
        if not fails:
            why = (" (an external dependency an AI agent calls)" if is_dep and M["agents"] else
                   " (the capability's AI agent)" if fp in {a["subject_id"] for a in M["agents"]} else
                   " (the component that performs or supports the most steps)")
        reached = ("the stages holding a step it takes part in, or a step its callers' calls to it are made in"
                   if is_dep else "the stages holding a step it takes part in")
        sections.append(section(n, f"Where a failure reaches: {fname} fails",
                                "If this part fails, whose cases are hurt, where, and do they recover?",
                                figure_map(M, "reach", f"m{3 + i}", fails=fp),
                                f"{fname} fails{why}. Only {reached} are opened, and only those steps drawn; the rest of each stage is "
                                "one line. The production readiness review's failure-mode question."))
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
              "step, where it could be seen and where it cannot, and whose cases a failure would hurt. They hold no live "
              "values.")
    return (head + "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{esc(M['system'])} design views</title>\n<style>{CSS}</style></head><body><main>"
            f"<h1>{esc(M['system'])}: design-for-operations views</h1><p class=\"lede\">{lede}</p>"
            + "".join(sections) + "</main>" + SCRIPT + "</body></html>\n")


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
    ap.add_argument("--fails", help="the failing part on the reach view, by name or id (default: the AI agent and an external dependency it "
                                     "calls, each in its own view; with no agent, the component in the most steps)")
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
    fails = find_part(M, a.fails) if a.fails else None
    out = pathlib.Path(a.out) if a.out else HERE / "out" / f"{R['_name']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = "python capability_views.py " + " ".join(argv if argv is not None else sys.argv[1:])
    out.write_text(page(M, opened, fails, pathlib.Path(a.register).as_posix(), cmd, (len(err), len(warn))), encoding="utf-8")
    if warn:
        print(f"{len(warn)} warnings; --check lists them")
    if not fails:
        chosen = list(dict.fromkeys([a["subject_id"] for a in M["agents"][:1]] + [d for d in [default_failing(M)] if d]))
        names = ", ".join(M["subj"][c].get("name", c) for c in chosen)
        print(f"failing part drawn by default: {names}; to draw another, pass --fails NAME")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
