#!/usr/bin/env python3
"""Render a design-for-operations run as one self-contained HTML page.

Usage:
    python render_run.py <run-directory> [output.html]

Reads only the run's own outputs: observation.json (required) and stages.json
(optional, supplies classification and citations). No network, no third-party
package, no CLI on PATH.

The page prints what the run's files say and nothing more. Where a cell carries no
value it prints the run's own stated reason for the absence. A reason shared by most
stages is stated once above the table instead of on every row.

Section order is declared once in ORDER and the nav derives from it. The order runs
subject first: a finding is a deviation from something, so the something is established
before any stage is named.
"""
import json
import sys
from collections import Counter
from html import escape
from pathlib import Path

LABELS = ["extracted", "proposed", "gapped", "ratified"]

ORDER = [
    ("outline", "The flow"),
    ("who", "Who depends on it"),
    ("findings", "What it found"),
    ("realise", "How each stage is realised"),
    ("flow", "What could be watched"),
    ("human", "Waiting on a person"),
    ("trust", "How to read this"),
]


ENTRY_KINDS = {"inbound_route", "message_subscription", "message_consumer"}

# Plain-language display for a fact kind. The raw kind stays visible beside it.
ACTION_LABELS = {
    "inbound_route": "takes a request",
    "message_consumer": "consumes an event",
    "message_subscription": "subscribes to an event",
    "message_publisher": "publishes an event",
    "durable_write": "writes to storage",
    "durable_read": "reads from storage",
    "outbound_http": "calls another system",
    "background_trigger": "runs on a schedule",
    "env_read": "reads configuration",
    "config_ref": "reads configuration",
    "client_binding": "binds a client",
}
# The two kinds that constitute doing work rather than relaying it.
WORK_KINDS = {"durable_write", "outbound_http"}


def load(run_dir):
    obs_path = run_dir / "observation.json"
    if not obs_path.exists():
        sys.exit(f"no observation.json in {run_dir} — this renderer reads a finished run")
    obs = json.loads(obs_path.read_text(encoding="utf-8"))
    stages_path = run_dir / "stages.json"
    stages = json.loads(stages_path.read_text(encoding="utf-8")) if stages_path.exists() else None
    fb_path = run_dir / "fact-base.json"
    facts = []
    if fb_path.exists():
        fb = json.loads(fb_path.read_text(encoding="utf-8"))
        facts = list(fb.get("facts") or [])
    return obs, stages, facts


def protocol_of(fact):
    """How the stage is entered, read off the rule that matched it."""
    rule = str(fact.get("rule", "")).lower()
    if fact.get("kind") in ("message_subscription", "message_consumer"):
        return "event"
    if "grpc" in rule:
        return "gRPC"
    if "route" in rule or "endpoint" in rule:
        return "HTTP"
    return "inbound"


def cited_lines(stage_extra):
    """{file: {line, ...}} exactly as the stage cites them."""
    cited = {}
    for c in stage_extra.get("citations", []) or []:
        path, _, lines = str(c).rpartition(":")
        if not path:
            continue
        try:
            cited.setdefault(path, set()).update(int(n) for n in lines.split(","))
        except ValueError:
            continue
    return cited


def entry_points(stage_extra, facts):
    """Entry-point facts whose file and line the stage itself cites. Never a guess."""
    cited = cited_lines(stage_extra)
    found, seen = [], set()
    for f in facts:
        if f.get("kind") not in ENTRY_KINDS:
            continue
        if f.get("line") in cited.get(f.get("file"), ()):
            key = (protocol_of(f), f.get("in_type"))
            if key not in seen:
                seen.add(key)
                found.append(f)
    return found


def relay_only_components(stage, facts):
    """Components of this stage in which every extracted action moves a message.

    Scoped to the component rather than the cited file: a write one hop from the
    entry file is still the component doing work, so file scope over-reports.
    """
    out = []
    for comp in stage.get("components", []) or []:
        kinds = {f.get("kind") for f in facts if f.get("service") == comp}
        if kinds and not (kinds & WORK_KINDS):
            out.append(comp)
    return out


def stage_actions(stage_extra, facts):
    """Every application-level action found in a file this stage cites, by kind.

    Scoped to the cited file rather than the cited line: a stage cites its entry
    points, and the work it does sits on the lines after them. A fact in a file no
    stage cites is left unattributed rather than guessed at.
    """
    files = set(cited_lines(stage_extra))
    hits = [f for f in facts if f.get("file") in files]
    grouped = {}
    for f in hits:
        grouped.setdefault(f.get("kind"), []).append(f)
    return grouped


# What this renderer needs, which phase of the run owes it, and what its absence costs.
INPUTS = [
    {"file": "observation.json", "required": True, "owed_by": "Phase 7",
     "costs": "nothing can be rendered at all"},
    {"file": "stages.json", "required": False, "owed_by": "Phase 7",
     "costs": "stages lose their citations and their classification"},
    {"file": "fact-base.json", "required": False, "owed_by": "Phase 1",
     "costs": "no entry points, and the realised-actions view is empty"},
]


def check(run_dir):
    """Can this run be rendered, and what does the reader lose if not.

    Returns (ok, rows). Exit-code shaped on purpose: a claim that a run is
    renderable should be checkable by someone who did not make it.
    """
    run_dir = Path(run_dir)
    rows, ok = [], True
    for spec in INPUTS:
        row = dict(spec, state="present")
        if not (run_dir / spec["file"]).exists():
            row["state"] = "missing"
            if spec["required"]:
                ok = False
        rows.append(row)
    return ok, rows


def chip(label):
    return f'<span class="chip chip-{escape(str(label))}">{escape(str(label))}</span>' if label else ""


def common_reason(values):
    """The reason most rows give, when most of them give the same one."""
    stated = [v for v in values if v]
    if len(stated) < 2:
        return None
    top, n = Counter(stated).most_common(1)[0]
    return top if n * 2 > len(stated) else None


def cell(d, absent_word, suppress=None):
    """Render a {value,label,reason} cell without ever filling a blank."""
    if not isinstance(d, dict):
        return '<span class="muted">not stated</span>'
    value, label, reason = d.get("value"), d.get("label"), d.get("reason")
    if reason == suppress:
        reason = None
    if value not in (None, "", "unowned"):
        out = f'<span class="val">{escape(str(value))}</span> {chip(label)}'
    else:
        shown = "unowned" if value == "unowned" else absent_word
        out = f'<span class="absent">{escape(shown)}</span> {chip(label)}'
    if reason:
        out += f'<div class="reason">{escape(str(reason))}</div>'
    if d.get("would_close"):
        out += f'<div class="reason"><b>Closed by:</b> {escape(str(d["would_close"]))}</div>'
    return out


def disposition(sig):
    if not isinstance(sig, dict):
        return '<span class="muted">no signal cell</span>'
    if sig.get("producible") == "no":
        return '<span class="disp disp-none">nothing emits this</span>'
    if sig.get("watched") is True:
        return '<span class="disp disp-watched">emitted and watched</span>'
    if sig.get("producible") == "yes":
        return '<span class="disp disp-unwatched">could be emitted</span>'
    return '<span class="disp disp-unknown">not stated</span>'


def wrap(text, width, max_lines=3):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:width - 1] + "…"
    return lines


def stage_state(stage, extra):
    """Three states, because two of them are different findings.

    A stage no code implements ("absence") is not the same as a stage the code
    carries but nothing can measure. Collapsing them tells a reader the bank
    cannot watch its financial-crime screening, when in fact it has none.
    """
    if (extra or {}).get("classification") == "absence":
        return "absent"
    sig = stage.get("signal") if isinstance(stage.get("signal"), dict) else {}
    return "blind" if sig.get("producible") == "no" else "ok"


STATE_FOOT = {"absent": "no code does this", "blind": "nothing can see this", "ok": ""}


def flow_outline_svg(stages, by_order, rulings):
    """The flow drawn as its stages. Only the stages that carry a finding are marked."""
    if not stages:
        return '<p class="muted">no stages to draw</p>'
    ruled = {r.get("stage") for r in rulings.values()}
    M, BW, BH, GX, GY, PER = 16, 206, 74, 40, 54, 4
    rows = (len(stages) + PER - 1) // PER
    width = M * 2 + PER * BW + (PER - 1) * GX
    height = M * 2 + rows * BH + (rows - 1) * GY
    s = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
         f'role="img" aria-label="the flow and its stages">'
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
         'markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#8c9bab"/></marker></defs>']
    pos = {}
    for i, st in enumerate(stages):
        r, c = divmod(i, PER)
        x, y = M + c * (BW + GX), M + r * (BH + GY)
        pos[i] = (x, y)
        kind = stage_state(st, by_order.get(st.get("order")))
        s.append(f'<rect class="box box-{kind}" x="{x}" y="{y}" width="{BW}" height="{BH}" rx="7"/>')
        s.append(f'<circle class="bc bc-{kind}" cx="{x + 21}" cy="{y + 21}" r="13"/>')
        s.append(f'<text class="bn" x="{x + 21}" y="{y + 25}" text-anchor="middle">'
                 f'{escape(str(st.get("order", i + 1)))}</text>')
        for j, line in enumerate(wrap(st.get("name", ""), 24)):
            s.append(f'<text class="bt" x="{x + 41}" y="{y + 18 + j * 14}">{escape(line)}</text>')
        foot = STATE_FOOT[kind] or ("nothing can see this" if st.get("order") in ruled else "")
        if foot:
            s.append(f'<text class="bs bs-{kind}" x="{x + 12}" y="{y + BH - 10}">'
                     f"{escape(foot)}</text>")
    for i in range(len(stages) - 1):
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        if y1 == y2:
            s.append(f'<line class="arr" x1="{x1 + BW + 4}" y1="{y1 + BH // 2}" '
                     f'x2="{x2 - 8}" y2="{y2 + BH // 2}" marker-end="url(#ah)"/>')
        else:
            elbow = min(x1 + BW + 10, width - 4)
            back, mid = 6, y1 + BH + GY // 2
            s.append(f'<polyline class="arr" fill="none" points="'
                     f'{x1 + BW + 4},{y1 + BH // 2} {elbow},{y1 + BH // 2} {elbow},{mid} '
                     f'{back},{mid} {back},{y2 + BH // 2} {x2 - 4},{y2 + BH // 2}" '
                     f'marker-end="url(#ah)"/>')
    s.append("</svg>")
    return "".join(s)


CSS = """
:root {
  --extracted:#2e7d32; --proposed:#1565c0; --gapped:#b35309; --ratified:#6a1b9a;
  --ink:#16202b; --dim:#5b6b7c; --line:#dfe4ea; --bg:#eef1f5; --card:#fff;
}
* { box-sizing:border-box; margin:0; padding:0; }
body { font:15px/1.55 -apple-system,'Segoe UI',Roboto,sans-serif; color:var(--ink); background:var(--bg); }
header { background:#1f2d3d; color:#eef1f5; padding:26px 32px; }
header h1 { font-size:1.5rem; }
header .what { color:#c7d4e0; font-size:.92rem; margin-top:8px; max-width:78ch; }
header .run { color:#7d90a5; font-size:.8rem; margin-top:12px; font-family:ui-monospace,Consolas,monospace; }
nav { position:sticky; top:0; background:#fff; border-bottom:1px solid var(--line); padding:0 32px;
      display:flex; gap:22px; flex-wrap:wrap; z-index:9; box-shadow:0 1px 4px rgba(0,0,0,.05); }
nav a { padding:12px 0; color:var(--dim); text-decoration:none; font-size:.88rem; font-weight:500;
        border-bottom:3px solid transparent; }
nav a:hover { color:var(--ink); border-bottom-color:#c3cdd8; }
main { padding:26px 32px 60px; max-width:1080px; }
section { margin-bottom:34px; }
h2 { font-size:1.15rem; margin-bottom:6px; }
h2 .n { color:var(--dim); font-weight:400; font-size:.9rem; margin-left:8px; }
.lede { color:var(--dim); font-size:.9rem; margin-bottom:14px; max-width:70ch; }
.card { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px 18px; margin-bottom:12px; }
.chip { display:inline-block; padding:1px 8px; border-radius:10px; font-size:.7rem; font-weight:700;
        text-transform:uppercase; letter-spacing:.03em; color:#fff; vertical-align:2px; }
.chip-extracted { background:var(--extracted); } .chip-proposed { background:var(--proposed); }
.chip-gapped { background:var(--gapped); } .chip-ratified { background:var(--ratified); }
.legend { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:10px; }
.legend div { font-size:.84rem; color:var(--dim); }
.finding { border-left:5px solid #c0392b; }
.finding h3 { font-size:1.02rem; margin-bottom:8px; }
.finding .fact { font-size:1rem; margin-bottom:8px; }
.finding .pos { color:var(--dim); font-size:.88rem; margin-bottom:8px; }
.gapcard { border-left:5px solid var(--gapped); }
.gapcard h3 { font-size:1.02rem; margin-bottom:8px; }
table { width:100%; border-collapse:collapse; background:#fff; font-size:.87rem;
        border:1px solid var(--line); border-radius:8px; overflow:hidden; }
th { background:#33475b; color:#eef1f5; text-align:left; padding:9px 12px; font-size:.75rem;
     text-transform:uppercase; letter-spacing:.04em; }
td { padding:11px 12px; border-bottom:1px solid #eceff2; vertical-align:top; }
tr:last-child td { border-bottom:none; }
.ord { color:var(--dim); font-weight:700; font-family:ui-monospace,Consolas,monospace; }
.stage-name { font-weight:600; }
.why { font-size:.84rem; color:#4a5a6a; margin-top:4px; font-style:italic; }
.comp { font-family:ui-monospace,Consolas,monospace; font-size:.75rem; color:#33475b;
        background:#eef1f5; padding:1px 5px; border-radius:3px; display:inline-block;
        overflow-wrap:anywhere; max-width:100%; }
.cite { font-family:ui-monospace,Consolas,monospace; font-size:.73rem; color:var(--dim);
        margin-top:5px; word-break:break-all; }
.reason { font-size:.8rem; color:var(--dim); margin-top:5px; max-width:60ch; }
.absent { color:var(--gapped); font-weight:600; font-style:italic; }
.muted { color:#9aa7b4; font-style:italic; }
.val { font-weight:600; }
.disp { display:inline-block; padding:2px 9px; border-radius:4px; font-size:.75rem; font-weight:700; }
.disp-none { background:#fdecea; color:#a5281b; }
.disp-watched { background:#e6f4ea; color:#1b6b34; }
.disp-unwatched { background:#eef1f5; color:#42586e; }
.disp-unknown { background:#eceff2; color:#5b6b7c; }
.signame { font-size:.87rem; font-weight:600; margin-top:6px; }
table.fixed { table-layout:fixed; }
.acts { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:10px 18px;
        margin-top:10px; }
.act { font-size:.86rem; }
.actn { display:inline-block; min-width:20px; text-align:center; color:#fff; background:#33475b;
        border-radius:3px; padding:0 5px; margin-right:6px;
        font:700 .78rem ui-monospace,Consolas,monospace; }
.kind { font:.7rem ui-monospace,Consolas,monospace; color:#9aa7b4; margin-left:5px; }
.entry { font-size:.84rem; margin-top:6px; overflow-wrap:anywhere; }
.entry:first-child { margin-top:0; }
.proto { display:inline-block; font:700 .68rem ui-monospace,Consolas,monospace; color:#42586e;
         background:#eef1f5; border-radius:3px; padding:1px 6px; margin-right:5px;
         text-transform:uppercase; letter-spacing:.04em; }
.svgwrap { background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px;
           overflow-x:auto; margin-bottom:10px; }
.svgwrap svg { max-width:100%; height:auto; display:block; }
rect.box { stroke-width:1.5; }
rect.box-ok { fill:#fff; stroke:#cfd8e2; }
rect.box-blind { fill:#fdecea; stroke:#c0392b; }
rect.box-absent { fill:#f4f5f7; stroke:#8c9bab; stroke-dasharray:5 4; }
circle.bc-ok { fill:#33475b; } circle.bc-blind { fill:#c0392b; }
circle.bc-absent { fill:#8c9bab; }
text.bn { font:700 12px ui-monospace,Consolas,monospace; fill:#fff; }
text.bt { font:12px -apple-system,'Segoe UI',sans-serif; fill:var(--ink); }
text.bs { font:700 9.5px -apple-system,'Segoe UI',sans-serif; text-transform:uppercase;
          letter-spacing:.05em; }
text.bs-blind { fill:#a5281b; } text.bs-absent { fill:#5b6b7c; }
text.bs-ok { fill:#a5281b; }
.finding ul { margin:6px 0 0 20px; } .finding li { font-size:.88rem; margin-bottom:5px; }
.arr { stroke:#8c9bab; stroke-width:1.5; }
.key { font-size:.8rem; color:var(--dim); display:flex; gap:20px; flex-wrap:wrap; }
.key i { display:inline-block; width:22px; height:12px; border-radius:3px; border:1.5px solid;
         margin-right:7px; vertical-align:-1px; }
.shared { background:#fff8e8; border:1px solid #f0dcb4; border-left:4px solid var(--gapped);
          border-radius:6px; padding:9px 13px; margin-bottom:10px; font-size:.83rem; color:#6b5730;
          max-width:78ch; }
.who { margin-bottom:12px; } .who b { display:block; }
footer { padding:20px 32px 40px; color:var(--dim); font-size:.8rem; max-width:80ch; }
"""


def render(run_dir, out_path=None):
    run_dir = Path(run_dir)
    obs, stages_doc, entry_facts = load(run_dir)
    by_order = {s.get("order"): s for s in (stages_doc or {}).get("stages", [])}

    flow = obs.get("business_process_flow", "unnamed business process flow")
    subject = obs.get("subject", "")
    run_id = obs.get("run", run_dir.name)
    stages = obs.get("stages", [])
    rulings = obs.get("rulings", {}) or {}
    ba = obs.get("business_account") or {}
    why = ba.get("why_a_business_names_each_stage") or {}
    tb = obs.get("too_broken")
    unowned = [s for s in stages
               if isinstance(s.get("owner"), dict) and s["owner"].get("value") in (None, "unowned")]
    owner_stated_above = bool(unowned) and len(unowned) == len(stages)
    absent = [s for s in stages
              if stage_state(s, by_order.get(s.get("order"))) == "absent"]
    inv = obs.get("source_inventory") or {}

    parts = {}

    def build(sid):
        parts[sid] = []
        return parts[sid].append

    # --- The flow: the subject, and the anomaly, in one picture -------------
    a = build("outline")
    a('<h2>The flow<span class="n">what this business process is made of</span></h2>')
    a('<div class="lede">The parts of the flow, in the order the business works in. Each box is a '
      'stage &mdash; something a business person would name and would care about if it stopped.</div>')
    a('<div class="svgwrap">' + flow_outline_svg(stages, by_order, rulings) + "</div>")
    a('<div class="key"><span><i style="background:#fff;border-color:#cfd8e2"></i>'
      'something could be watched here</span>'
      '<span><i style="background:#fdecea;border-color:#c0392b"></i>'
      'the code does this, and nothing emits anything to watch</span>')
    if absent:
        a('<span><i style="background:#f4f5f7;border-color:#8c9bab;border-style:dashed"></i>'
          "the business named it; no code does it</span>")
    a("</div>")

    # --- Who depends on it: the stakes, before the problem -------------------
    a = build("who")
    a("<h2>Who depends on it</h2>")
    a(f'<div class="lede">Drafted from how this kind of business works. {chip(ba.get("label"))}</div>')
    a('<div class="card">')
    for w in ba.get("who_depends", []) or []:
        st = ", ".join(str(x) for x in (w.get("stages") or []))
        a(f'<div class="who"><b>{escape(str(w.get("party", "")))}</b>'
          f'{escape(str(w.get("expects", "")))}'
          + (f'<div class="reason">stages {escape(st)}</div>' if st else "") + "</div>")
    if ba.get("source"):
        a(f'<div class="reason"><b>Drafted from:</b> {escape(str(ba["source"]))}</div>')
    a("</div>")

    # --- What it found: now a stage number means something -------------------
    a = build("findings")
    a("<h2>What it found</h2>")
    for key, r in rulings.items():
        num = r.get("stage")
        st = next((s for s in stages if s.get("order") == num), {})
        sig = st.get("signal") if isinstance(st.get("signal"), dict) else {}
        a(f'<div class="card finding"><h3>Stage {escape(str(num))} &mdash; '
          f'{escape(str(st.get("name", "")))}</h3>')
        if sig.get("reason"):
            a(f'<div class="fact">{escape(str(sig["reason"]))}</div>')
        if sig.get("producible_source"):
            a(f'<div class="cite">{escape(str(sig["producible_source"]))}</div>')
        a(f'<div class="pos">{escape(str(r.get("position", "")))} {chip(r.get("label"))}</div>')
        bits = []
        if r.get("would_ratify"):
            bits.append(f'Needs a yes from {escape(str(r["would_ratify"]))}')
        bits.append(escape(str(key)))
        a('<div class="reason">' + " &middot; ".join(bits) + "</div></div>")
    if absent:
        n = len(absent)
        a(f'<div class="card finding"><h3>{n} stage{"" if n == 1 else "s"} the business named '
          f'that no code implements</h3>')
        a('<div class="fact">These are not stages nothing can watch. They are steps the drafted '
          "business account expects and the extraction found no code for at all.</div><ul>")
        for s in absent:
            reason = (s.get("signal") or {}).get("reason", "")
            a(f'<li><b>{escape(str(s.get("order")))} {escape(str(s.get("name", "")))}</b>'
              + (f' &mdash; {escape(str(reason))}' if reason else "") + "</li>")
        a("</ul></div>")
    if tb:
        a('<div class="card gapcard"><h3>How much broken is too much</h3>'
          + cell(tb, "no number") + "</div>")
    if owner_stated_above:
        a('<div class="card gapcard"><h3>Ownership</h3>'
          '<div class="fact">No stage in this flow has a named owner.</div>'
          f'<div class="reason">{escape(str(unowned[0]["owner"].get("reason", "")))}</div></div>')

    # --- How each stage is realised: the application process view ------------
    a = build("realise")
    a('<h2>How each stage is realised<span class="n">'
      'the application-level actions inside each stage</span></h2>')
    a('<div class="lede">A separate view, answering a different question: not what the business '
      'does, but which application actions carry it out. Every action below was found in a file '
      'the stage itself cites; actions in files no stage cites are left unattributed rather than '
      'guessed at.</div>')
    if not entry_facts:
        a('<div class="card"><b>This run carries no fact base, so this view is empty.</b>'
          '<div class="reason">Phase 1 produces it. Run <code>--check</code> on this run to see '
          "which inputs are missing and which phase owes each.</div></div>")
    for s in stages if entry_facts else []:
        extra = by_order.get(s.get("order"), {})
        grouped = stage_actions(extra, entry_facts)
        a(f'<div class="card"><b><span class="ord">{escape(str(s.get("order", "")))}</span> '
          f'{escape(str(s.get("name", "")))}</b>')
        if not grouped:
            a('<div class="reason"><span class="muted">no extracted action falls in a file this '
              "stage cites</span></div></div>")
            continue
        a('<div class="acts">')
        for kind, fs in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
            label = ACTION_LABELS.get(kind, str(kind).replace("_", " "))
            a(f'<div class="act"><span class="actn">{len(fs)}</span> {escape(label)} '
              f'<span class="kind">{escape(str(kind))}</span>'
              f'<div class="cite">{escape(str(fs[0].get("file")))}:'
              + ", ".join(escape(str(f.get("line"))) for f in fs[:8])
              + ("&hellip;" if len(fs) > 8 else "") + "</div></div>")
        a("</div>")
        for comp in relay_only_components(s, entry_facts):
            a(f'<div class="reason"><b>Nothing in <code>{escape(str(comp))}</code> writes to '
              "storage or calls another system</b> &mdash; every extracted action in it is a "
              "message arriving or leaving</div>")
        a("</div>")

    # --- What could be watched: the evidence table ---------------------------
    shared_healthy = common_reason([s["healthy"].get("reason") for s in stages
                                    if isinstance(s.get("healthy"), dict)])
    shared_owner = common_reason([s["owner"].get("reason") for s in stages
                                  if isinstance(s.get("owner"), dict)])
    a = build("flow")
    a('<h2>What could be watched<span class="n">stage by stage, and the code it comes from</span></h2>')
    a('<div class="lede">The order is drafted from how this kind of business works, and stays a '
      'draft. Reading source establishes that a step <em>can</em> hand to the next, never that it '
      'always does.</div>')
    banners = [("No target, on most stages", shared_healthy)]
    if not owner_stated_above:
        banners.append(("No owner, on most stages", shared_owner))
    for heading, shared in banners:
        if shared:
            a(f'<div class="shared"><b>{heading}:</b> {escape(str(shared))}</div>')
    show_entry = bool(entry_facts)
    columns = [("Signal", 17), ("Stage", 21), ("Runs on", 11)]
    if show_entry:
        columns.append(("Entered by", 22))
    columns += [("Target", 18), ("Owner", 11)]
    total = sum(w for _, w in columns)
    a('<table class="fixed"><tr>' + "".join(
        f'<th style="width:{w * 100.0 / total:.1f}%">{escape(name)}</th>'
        for name, w in columns) + "</tr>")
    for s in stages:
        extra = by_order.get(s.get("order"), {})
        sig = s.get("signal") if isinstance(s.get("signal"), dict) else {}
        nm = sig.get("display_name") or sig.get("name")
        a("<tr>")
        a("<td>" + disposition(sig)
          + (f'<div class="signame">{escape(str(nm))}</div>' if nm else "")
          + (f'<div class="cite">{escape(str(sig["producible_source"]))}</div>'
             if sig.get("producible_source") else "") + "</td>")
        a(f'<td><span class="ord">{escape(str(s.get("order", "")))}</span> '
          f'<span class="stage-name">{escape(str(s.get("name", "")))}</span>')
        wtext = why.get(str(s.get("order")))
        if wtext:
            a(f'<div class="why">{escape(str(wtext))}</div>')
        for c in extra.get("citations", []) or []:
            a(f'<div class="cite">{escape(str(c))}</div>')
        a("</td>")
        comps = " ".join(f'<span class="comp">{escape(str(c))}</span>'
                         for c in s.get("components", []) or [])
        a(f'<td>{comps or "<span class=muted>not stated</span>"}</td>')
        if show_entry:
            entries = entry_points(extra, entry_facts)
            a("<td>" + ("".join(
                f'<div class="entry"><span class="proto">{escape(protocol_of(f))}</span> '
                f'{escape(str(f.get("in_type", "")))}</div>'
                f'<div class="cite">{escape(str(f.get("file")))}:{escape(str(f.get("line")))}</div>'
                for f in entries) or '<span class="muted">not stated</span>') + "</td>")
        a(f'<td>{cell(s.get("healthy"), "no target", shared_healthy)}</td>')
        a(f'<td>{cell(s.get("owner"), "unowned", shared_owner)}</td>')
        a("</tr>")
    a("</table>")

    # --- Waiting on a person: the ask ---------------------------------------
    a = build("human")
    a("<h2>Waiting on a person</h2>")
    a('<div class="lede">What a named human has to settle before any of this can be acted on.</div>'
      '<div class="card"><table><tr><th>What</th><th>Who</th></tr>')
    rows = 0
    for key, r in rulings.items():
        st = next((s for s in stages if s.get("order") == r.get("stage")), {})
        a(f'<tr><td>Rule on stage {escape(str(r.get("stage")))}, '
          f'{escape(str(st.get("name", "")))}</td>'
          f'<td>{escape(str(r.get("would_ratify", "not stated")))}</td></tr>')
        rows += 1
    if tb and tb.get("would_close"):
        a('<tr><td>Set how much broken is too much</td>'
          f'<td>{escape(str(tb["would_close"]))}</td></tr>')
        rows += 1
    if unowned:
        a(f'<tr><td>Name an owner for {len(unowned)} stages</td>'
          f'<td>whoever runs this estate</td></tr>')
        rows += 1
    if not rows:
        a('<tr><td colspan="2"><span class="muted">nothing recorded</span></td></tr>')
    a("</table></div>")

    # --- How to read this: reference ----------------------------------------
    a = build("trust")
    a('<h2>How to read this</h2><div class="card">')
    bits = [f"{escape(k.replace('_', ' '))} &mdash; {escape(str(v))}"
            for k, v in inv.items() if k not in ("label", "source")]
    if bits:
        a('<div class="reason" style="margin-bottom:14px"><b>What this run could reach:</b> '
          + "; ".join(bits) + "</div>")
    a('<div class="legend">')
    for k in LABELS:
        desc = (obs.get("labels", {}) or {}).get(k, "")
        a(f'<div>{chip(k)} {escape(str(desc))}</div>')
    a("</div></div>")

    nav = "".join(f'<a href="#{sid}">{escape(label)}</a>' for sid, label in ORDER)
    body = "".join(f'<section id="{sid}">' + "".join(parts[sid]) + "</section>"
                   for sid, _ in ORDER)

    page = (
        "<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n"
        f"     Source: {run_dir.as_posix()}/observation.json (+ stages.json)\n"
        f"     Build: python view/render_run.py {run_dir.as_posix()}\n-->\n"
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(str(flow))} &mdash; what can be seen</title>"
        f"<style>{CSS}</style></head><body>"
        "<header>"
        f"<h1>{escape(str(flow))}</h1>"
        '<div class="what">A design for operations run reads a codebase and works out what one '
        "business process flow actually does, which code runs each part of it, and what could be "
        "watched. Every claim below carries a label saying how it was established.</div>"
        f'<div class="run">run: {escape(str(run_id))} &nbsp;&middot;&nbsp; '
        f"subject: {escape(str(subject))} &nbsp;&middot;&nbsp; {len(stages)} stages</div>"
        "</header>"
        f"<nav>{nav}</nav><main>{body}</main>"
        "<footer>Generated from this run&rsquo;s files: <code>observation.json</code>"
        f'{" and <code>stages.json</code>" if stages_doc else ""}.</footer>'
        "</body></html>"
    )

    out = Path(out_path) if out_path else run_dir / "READ-THIS-RUN.html"
    out.write_text(page, encoding="utf-8")
    return out, len(stages), len(rulings)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(f"usage: {sys.argv[0]} [--check] <run-directory> [output.html]")
    if args[0] == "--check":
        if len(args) < 2:
            sys.exit(f"usage: {sys.argv[0]} --check <run-directory>")
        ok, rows = check(args[1])
        for r in rows:
            mark = {"present": "ok  ", "missing": "MISS"}[r["state"]]
            need = "required" if r["required"] else "optional"
            print(f"{mark} {r['file']:<26} {need:<9} owed by {r['owed_by']}")
            if r["state"] != "present":
                print(f"       without it: {r['costs']}")
        print("renderable" if ok else "NOT renderable")
        sys.exit(0 if ok else 1)
    o, n, f = render(args[0], args[1] if len(args) > 1 else None)
    print(f"wrote {o}")
    print(f"  stages: {n}   findings: {f}")
