"""The sponsor's page of a split run: how the run is planned and how it is going, for steering, never a sign-off.

    python run_page.py <reg>          writes <reg>/run.html

It reads only the files split-run-formats.md names under "What run_page.py reads": RUN.md, PLAN.md,
run-settings.json, units/units.csv, job/jobs.csv, job/lock.json, judging/judgements.csv, merge/unmatched-calls.csv,
merge/summary.json, and whether views.html exists. Any of them may be missing, empty or half written (the job runner
redraws the page while it writes); the page then says that part is not there yet, and never fails. Once every step in
jobs.csv is done it also runs the kit's done check (run_status.py, which reads the whole register and the session
transcripts): the run is finished only when that check says DONE, and otherwise the page names its reasons.

The page is written ready to publish as a claude.ai Artifact: no document wrapper (the publish adds it), its title
first and named after the register folder so it stays the same from the first draw on, the kit's colour tokens
(page_style.py) in light and dark with a toggle, everything inline. From the top: one health line (waiting for the go,
running, stopped on a named problem, not finished with the done check's reasons, finished) with when the page was drawn and when the run last changed; the plan in
brief; every unit and each of its steps; the run's own steps (the merge, a re-read per unmatched call); the counts of
rows and calls; the link to the map once it is drawn."""
import datetime as dt
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run isolated (-I), the folder is not on the path
import page_style as ps  # noqa: E402
import settings as run_settings  # noqa: E402
import tables  # noqa: E402
import register_layout as layout  # noqa: E402

E = html.escape
OUT = layout.RUN_HTML
NOT_YET = "not there yet"
COMPLETE = "Draft complete, for your review"  # the run state once the done check says DONE: a draft, not accepted
UNIT_STEPS = ("read", "judge", "fix")
STEP_WORDS = {"read": "Read the code", "judge": "Judges check each row", "fix": "Fix flagged rows",
              "merge": "Merge into one map", "reread": "Re-read the call"}
WORD_STEP = {v: k for k, v in STEP_WORDS.items()}
STATES = ("to do", "running", "done", "blocked")
NOT_STARTED = "not started"  # a step the job list does not hold yet
NO_STEP = "—"  # a step the item does not have: jobs.csv has a later step of it and none of this one
FLOW = "flow"  # the unit that is the lead's own flow-level tables at the register's root
FLOW_WORDS = "The flow itself: the lead's own tables (the order, its lifecycle, stages and steps)"


# ---------------------------------------------------------------- reading the run's files, each perhaps missing

def _text(p):
    try:
        return p.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def _json(p):
    t = _text(p)
    try:
        v = json.loads(t) if t else None
    except ValueError:
        return None
    return v if isinstance(v, dict) else None


def _time(s):
    """An ISO time as an aware datetime (a trailing Z, or none, taken as UTC), or None."""
    try:
        t = dt.datetime.fromisoformat(str(s or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _when(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if t else NOT_YET


def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def scrub(s):
    """Check output as it may go on a published page: any absolute local path cut to what follows the user folder
    (and its work folder)."""
    s = re.sub(r"[A-Za-z]:[/\\]Users[/\\][^/\\\s]+[/\\](?:work[/\\])?", "", s or "")
    return re.sub(r"/(?:home|Users)/[^/\s]+/(?:work/)?", "", s)


def settings(reg):
    """The run's count settings as ints; a value that is not a whole number, or a file that cannot be read as
    settings, gives the default: the page never fails on a half-written file."""
    s = {k: v for k, v in run_settings.DEFAULTS.items() if isinstance(v, int)}
    try:
        got = run_settings.load(reg)
    except (OSError, ValueError):
        got = {}
    for k, v in got.items():
        if k in s and _int(v) is not None:
            s[k] = _int(v)
    return s


def _placeholder(v):
    v = v.strip()
    return not v or (v.startswith("_") and v.endswith("_"))


def run_field(md, name):
    """A top-level bullet `- **<name>:** ...` of RUN.md with its continuation lines, joined, or None when it is
    missing or still the template's placeholder."""
    if not md:
        return None
    m = re.search(r"^- \*\*" + re.escape(name) + r":\*\*(.*(?:\n(?![-#]|\s*$).*)*)", md, re.M)
    if not m:
        return None
    v = re.sub(r"\s+", " ", m.group(1)).strip()
    return None if _placeholder(v) else v


def plan_brief(md):
    """(the plan's headline, the flow it recommends) from PLAN.md, each None when not there. The headline is the
    bold summary paragraph straight under the plan's title, joined onto one line."""
    if not md:
        return None, None
    head = re.search(r"\A\s*#[^\n]*\n\s*\*\*(.+?)\*\*\s*(?:\n\s*\n|\Z)", md, re.S)
    flow = re.search(r"\*\*Recommended:\s*(.+?)\*\*", md)
    return ((re.sub(r"\s+", " ", head.group(1)).strip() if head else None),
            (flow.group(1).strip().rstrip(".") if flow else None))


def application(md, folder):
    """The application the run is of, for the page's title: the summary's lead before its colon ("Sock Shop: 10
    repositories ..."), else the plan title's after "Plan:" up to a comma, if three words or fewer; else the
    register folder's name. PLAN.md is written before the go, so the title holds from the first draw."""
    head, _ = plan_brief(md)
    t = re.match(r"\s*#\s*(?:Plan:\s*)?([^,\n]+)", md or "")
    for name in ((head or "").split(":")[0] if head and ":" in head else "", t.group(1) if t else ""):
        name = name.strip()
        if name and len(name.split()) <= 3:
            return name
    return folder


def counts(reg):
    """Rows and calls, from judgements.csv and the merge's summary. `written` is the map's row count, known only
    after the merge (None before); `put` is the rows put to the judges so far; `fixed` is a row flagged in an
    earlier round that passed when judged again."""
    j = tables.filled(reg / layout.JUDGEMENTS_CSV)
    s = _json(reg / layout.SUMMARY_JSON)
    c = {"written": _int((s or {}).get("rows")), "judgements": j is not None}
    states = [(r.get("state") or "").strip() for r in j or []]
    c["put"] = len(states)
    c["judged"] = sum(1 for x in states if x and x != "pending")
    for k in ("passed", "flagged", "disputed"):
        c[k] = states.count(k)
    c["fixed"] = sum(1 for r in j or []
                     if (r.get("state") or "").strip() == "passed" and (_int(r.get("round")) or 1) >= 2)
    c["summary"] = s if s and all(_int(s.get(k)) is not None for k in ("matched", "unmatched")) else None
    return c


# ---------------------------------------------------------------- the run's health

def done_check(reg):
    """The kit's done check (run_status.py) on the register: (done, the reasons it is not). It reads the transcripts
    and every table, so the page calls it only once every step is done."""
    import run_status
    return run_status.verdict(reg)


def health(now, go, jobs, lock, cfg, check=None):
    """(state word, sentence, [problems]) for the top line. Stopped wins: any blocked step, or the lead session's
    lock stale while steps are marked running. Then waiting for the go, running, and once every step is done,
    finished only when `check()` (the done check: (done, reasons)) says done; otherwise not finished, with its
    reasons."""
    problems = []
    for r in jobs or []:
        if (r.get("state") or "").strip() == "blocked":
            problems.append(f"{r.get('item')}, {STEP_WORDS.get(r.get('step'), r.get('step'))}: "
                            + (scrub(r.get("reason")) or "no reason given"))
    running = [r for r in jobs or [] if (r.get("state") or "").strip() == "running"]
    last = _time((lock or {}).get("last"))
    if running and last and now - last > dt.timedelta(minutes=cfg["lock_stale_minutes"]):
        mins = int((now - last).total_seconds() // 60)
        problems.append(f"The lead session {(lock or {}).get('session') or '(unnamed)'}: not heard from for "
                        f"{mins} minutes (the limit is {cfg['lock_stale_minutes']}), with {len(running)} steps "
                        "still marked running. A new lead session takes the run over and carries on.")
    if problems:
        return "Stopped", "The run is stopped on " + ("a named problem." if len(problems) == 1
                                                         else f"{len(problems)} named problems."), problems
    if not go:
        return "Waiting", "Waiting for your go on the plan. Nothing is read in depth until you give it.", []
    if not jobs:
        return "Running", "Your go is given; the job list is not there yet, so no step has started.", []
    if all((r.get("state") or "").strip() == "done" for r in jobs):
        try:
            done, reasons = check() if check else (False, ["the done check was not run"])
        except Exception as e:  # the page never fails; a check that cannot run is not a finished run
            done, reasons = False, [f"the done check could not be run ({type(e).__name__}: {scrub(str(e))})"]
        if done:
            # what the run produced is a draft for the person's review, never accepted
            return COMPLETE, (f"{COMPLETE}: every step of every unit has run, the map is merged, and the done check "
                              "says DONE: a draft for review, not accepted."), []
        return ("Not finished", "Every unit is read, judged and merged; not finished: the done check "
                                "(run_status.py) says NOT DONE, for these reasons.",
                [scrub(r) for r in reasons] or ["the done check gave no reason"])
    return "Running", "Running: the steps below are in hand.", []


def _by_key(jobs):
    return {(r.get("item") or "", r.get("step") or ""): r for r in jobs or []}


def summary_sentence(jobs):
    """Plain sentences naming the items stopped, running, to do and done (an item counts as its least finished
    step)."""
    by = {s: [] for s in STATES}
    for it in dict.fromkeys(r.get("item") for r in jobs or []):
        states = {(r.get("state") or "").strip() for r in jobs if r.get("item") == it}
        if "blocked" in states:
            by["blocked"].append(it)
        elif "running" in states:
            by["running"].append(it)
        elif states == {"done"}:
            by["done"].append(it)
        else:
            by["to do"].append(it)
    words = {"done": "Done", "running": "Running", "to do": "To do", "blocked": "Stopped"}
    return [f"{words[s]}: {', '.join(by[s])}." for s in ("blocked", "running", "to do", "done") if by[s]]


# ---------------------------------------------------------------- drawing

CSS = ps.CSS + """
/* the run page: a wide working column on the kit's tokens; the health band first, then plan, steps and counts */
html,body{background:var(--m-page)}
body{padding-left:max(16px, env(safe-area-inset-left, 0px));padding-right:max(16px, env(safe-area-inset-right, 0px))}
main.frame{background:var(--m-col);padding-block:16px 48px;padding-inline:20px}
@media (max-width:600px){main.frame{padding-inline:4px}}
table{font:inherit;color:inherit}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
#theme{font:13px var(--m-sans);color:var(--m-ink2);background:transparent;border:1px solid var(--m-line);
 border-radius:4px;padding:3px 10px;cursor:pointer}
#theme:focus-visible{outline:2px solid var(--m-acc);outline-offset:2px}
.health{border:1px solid var(--m-line);border-left:6px solid var(--h);border-radius:4px;padding:12px 16px;margin:8px 0 4px}
.health .state{font:700 20px/1.2 var(--m-sans);color:var(--h)}
.health p{margin:4px 0 0}.health ul{margin:6px 0 0;padding-left:20px}.health li{margin:0 0 4px;overflow-wrap:anywhere}
.h-run{--h:var(--m-acc)}.h-stop{--h:var(--m-bad)}.h-wait,.h-open{--h:var(--m-bus-s)}.h-done{--h:var(--m-ok)}
.when{font-size:13px;color:var(--m-ink2)}
.when b{font-weight:600;color:var(--m-ink)}
dl.brief{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:6px 0}
dl.brief dt{color:var(--m-ink2)}dl.brief dd{margin:0;min-width:0;overflow-wrap:anywhere}
@media (max-width:600px){dl.brief{grid-template-columns:1fr;gap:0}dl.brief dd{margin-bottom:8px}}
.scroll{overflow-x:auto;margin:6px 0 10px}
table.grid{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
table.grid th{text-align:left;font-weight:600;color:var(--m-ink2);border-bottom:2px solid var(--m-line);padding:6px 10px;white-space:nowrap}
table.grid td{border-bottom:1px solid var(--m-line);padding:6px 10px;vertical-align:top}
.item{font-weight:600;font-family:var(--m-mono);font-size:13px}
.sub{display:block;color:var(--m-ink2);font-size:13px;max-width:44ch}
.pill{display:inline-block;font-size:13px;line-height:1.3;padding:1px 8px;border-radius:10px;border:1px solid var(--p);color:var(--p);white-space:nowrap}
.s-done{--p:var(--m-ok)}.s-running{--p:var(--m-acc);font-weight:600}.s-blocked{--p:var(--m-bad);font-weight:600}
.s-todo,.s-not{--p:var(--m-ink3)}
.why{display:block;font-size:13px;color:var(--m-bad);max-width:46ch;overflow-wrap:anywhere;margin-top:3px}
.tries{display:block;font-size:13px;color:var(--m-ink3)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:6px 0 4px}
.tile{border:1px solid var(--m-line);border-radius:4px;padding:8px 12px;min-width:0}
.tile .n{font:700 22px/1.2 var(--m-sans);font-variant-numeric:tabular-nums}
.tile .l{font-size:13px;color:var(--m-ink2)}
.note{font-size:13px;color:var(--m-ink2);margin:2px 0 8px}
.missing{color:var(--m-ink3);font-style:italic}
"""

SCRIPT = """<script>
(function(){var r=document.documentElement,b=document.getElementById('theme');
function cur(){return r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}
function show(){b.textContent=cur()==='dark'?'Light theme':'Dark theme'}
try{var s=localStorage.getItem('run-page-theme');if(s==='dark'||s==='light')r.dataset.theme=s}catch(e){}
show();b.addEventListener('click',function(){var t=cur()==='dark'?'light':'dark';r.dataset.theme=t;
try{localStorage.setItem('run-page-theme',t)}catch(e){}show()});})();
</script>"""


def pill(state):
    cls = {"done": "s-done", "running": "s-running", "blocked": "s-blocked", "to do": "s-todo"}.get(state, "s-not")
    return f'<span class="pill {cls}">{E(state)}</span>'


def cell(r, step, none=False):
    """One step's cell: its state, how often it was tried when more than once, and a stopped step's reason. `none`:
    the item has no such step (no line for it in jobs.csv, while it has a later step), shown as a dash."""
    if not r:
        if none:
            return f'<td data-step="{E(step)}"><span class="pill s-not" title="no such step">{NO_STEP}</span></td>'
        return f'<td data-step="{E(step)}">{pill(NOT_STARTED)}</td>'
    state = (r.get("state") or "").strip() or "to do"
    out = pill(state)
    tries = _int(r.get("tries")) or 0
    if tries > 1:
        out += f'<span class="tries">tried {tries} times</span>'
    if state in ("blocked", "to do") and (r.get("reason") or "").strip():
        out += f'<span class="why">{E(scrub(r.get("reason")))}</span>'
    return f'<td data-step="{E(step)}">{out}</td>'


def missing(what):
    return f'<span class="missing">{E(what)}: {NOT_YET}</span>'


def _n(v):
    return f"{v:,}" if isinstance(v, int) else E(str(v or ""))


def units_table(units, jobs):
    """Every unit (units.csv order, then any unit only the job list has) by its read, judge and fix steps."""
    J = _by_key(jobs)
    names = [u.get("unit") for u in units or []]
    for it, _ in J:
        if it not in names and it != "run" and not it.startswith("call:"):
            names.append(it)
    if not names:
        return f'<p>{missing("The list of reading units")}</p>'
    U = {u.get("unit"): u for u in units or []}
    head = "".join(f"<th>{E(STEP_WORDS[s])}</th>" for s in UNIT_STEPS)
    rows = []
    for n in names:
        u = U.get(n, {})
        lines, files = _int(u.get("lines")), _int(u.get("files"))
        if n == FLOW:
            size = FLOW_WORDS
        elif n not in U:
            size = "added by the run; not in the list of units"
        elif lines == 0:
            size = f"configuration only, {_n(files)} files" if files is not None else "configuration only"
        elif lines is not None:
            size = f"{_n(lines)} lines in {_n(files)} files"
        else:
            size = "size not recorded"
        dep = E(u.get("deployable") or "")
        sub = f'<span class="sub">{dep}{" · " if dep else ""}{size}</span>'
        has = [(n, s) in J for s in UNIT_STEPS]
        rows.append(f'<tr><td><span class="item">{E(n)}</span>{sub}</td>'
                    + "".join(cell(J.get((n, s)), STEP_WORDS[s], none=not has[i] and any(has[i + 1:]))
                              for i, s in enumerate(UNIT_STEPS)) + "</tr>")
    return (f'<div class="scroll"><table class="grid steps" id="units"><thead><tr><th>Unit</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def run_table(jobs, unmatched):
    """The run's own steps: the merge, then one re-read per unmatched call."""
    J = _by_key(jobs)
    why = {f"call:{r.get('call')}": r for r in unmatched or []}
    items = [k for k in J if k[0] == "run" or k[0].startswith("call:")]
    if not any(k[0] == "run" for k in items):
        items.insert(0, ("run", "merge"))
    rows = []
    for it, step in items:
        if it == "run":
            sub = "All units' rows put into one map, and every call between units matched on both sides"
        else:
            u = why.get(it)
            sub = (f"{u.get('from_unit')} calls {u.get('to_unit') or 'another part'}: {u.get('operation')}. "
                   f"Unmatched because {u.get('why')}" if u else "A call between units the merge could not match")
        rows.append(f'<tr><td><span class="item">{E(it)}</span><span class="sub">{E(scrub(sub))}</span></td>'
                    f'<td>{E(STEP_WORDS.get(step, step))}</td>' + cell(J.get((it, step)), "State") + "</tr>")
    return (f'<div class="scroll"><table class="grid steps" id="run-steps"><thead><tr><th>Item</th><th>Step</th>'
            f'<th>State</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def parse_back(cells):
    """{(item, step): state} from the page's step cells as a reader sees them ({(item, column heading): state}),
    steps the job list does not hold yet left out: the page's account of jobs.csv, for comparing with it. In the
    run's own table the merge is the run's only step and an unmatched call's only step is its re-read."""
    out = {}
    for (item, col), state in cells.items():
        if state in (NOT_STARTED, NO_STEP):
            continue
        step = ("merge" if item == "run" else "reread") if col == "State" else WORD_STEP.get(col, col)
        out[(item, step)] = state
    return out


def tile(n, label):
    return f'<div class="tile"><div class="n">{n}</div><div class="l">{E(label)}</div></div>'


def counts_html(c, views):
    if not c["judgements"] and c["written"] is None:
        rows = f'<p>{missing("The judges’ verdicts")}</p>'
    else:
        written = _n(c["written"]) if c["written"] is not None else _n(c["put"])
        wl = ("rows in the merged map" if c["written"] is not None
              else "rows put to the judges so far (the map's full count comes with the merge)")
        rows = ('<div class="tiles">' + tile(written, wl) + tile(_n(c["judged"]), "judged by every judge this round")
                + tile(_n(c["passed"]), "passed: every judge says the code says it")
                + tile(_n(c["flagged"]), "flagged, waiting to be fixed and judged again")
                + tile(_n(c["fixed"]), "fixed: flagged once, passed when judged again")
                + tile(_n(c["disputed"]), "disputed: still flagged after the last round, marked on the map")
                + "</div>")
        if not c["judgements"]:
            rows += f'<p>{missing("The judges’ verdicts")}</p>'
    s = c["summary"]
    if s:
        def k(key):
            return _int(s.get(key))
        calls = ('<div class="tiles">' + tile(_n(k("calls")), "calls between units")
                 + tile(_n(k("matched")), f"{k('matched')} matched on both sides")
                 + tile(_n(k("unmatched")), f"{k('unmatched')} unmatched, each re-read")
                 + tile(_n(k("found_by_reader")), f"{k('found_by_reader')} found by the code reader")
                 + tile(_n(k("proposed")), f"{k('proposed')} proposed: found only by reading")
                 + "</div>")
    else:
        calls = f'<p>{missing("Calls between units, counted by the merge")}</p>'
    link = ('<p><a href="views.html">Open the map so far</a></p>' if views
            else f'<p>{missing("The map, drawn after the merge")}</p>')
    return (f'<h2 class="sec">Rows checked</h2>{rows}'
            '<p class="note">Every row a reader writes is checked against its cited code by independent judges; a '
            'flagged row is fixed and judged again.</p>'
            f'<h2 class="sec">Calls between units</h2>{calls}{link}')


def render(reg, now=None, done_check=done_check):
    """The page for the run in folder `reg`, as drawn at `now` (an aware datetime; the current time if None).
    `done_check(reg)` gives (done, reasons); it is the kit's done check unless a test gives another."""
    reg = pathlib.Path(reg)
    now = now or dt.datetime.now(dt.timezone.utc)
    run_md, plan_md = _text(reg / "RUN.md"), _text(reg / "PLAN.md")
    cfg = settings(reg)
    units = tables.filled(reg / layout.UNITS_CSV)
    jobs = tables.filled(reg / layout.JOBS_CSV)
    lock = _json(reg / layout.LOCK_JSON)
    unmatched = tables.filled(reg / layout.UNMATCHED_CSV)
    go = run_field(run_md, "Go")
    state, sentence, problems = health(now, go, jobs, lock, cfg, lambda: done_check(reg))
    cls = {"Stopped": "h-stop", "Waiting": "h-wait", COMPLETE: "h-done", "Not finished": "h-open"}.get(state, "h-run")
    changed = max((t for t in (_time(r.get("updated")) for r in jobs or []) if t), default=None)
    lead = (f'; lead session <b>{E(str(lock.get("session") or ""))}</b>, last heard from '
            f'<b>{_when(_time(lock.get("last")))}</b>' if lock else "")
    say = summary_sentence(jobs)
    band = (f'<section class="health {cls}" aria-label="Health"><div class="state">{E(state)}</div><p>{E(sentence)}</p>'
            + (f'<ul>{"".join(f"<li>{E(p)}</li>" for p in problems)}</ul>' if problems else "")
            + (f'<p>{" ".join(E(x) for x in say)}</p>' if say else "")
            + f'<p class="when">Page drawn <b>{_when(now)}</b>; the run last changed '
            f'<b>{_when(changed)}</b>{lead}.</p></section>')

    head, rec = plan_brief(plan_md)
    flow = run_field(run_md, "Flow")
    scope = run_field(run_md, "Scope")
    flow_html = (E(flow) if flow else (f'{E(rec)} <span class="missing">(recommended in the plan; the go names it)</span>'
                                       if rec else missing("The flow")))
    services = list(dict.fromkeys(u.get("deployable") for u in units or [] if u.get("deployable")))
    readers = [u for u in units or [] if u.get("unit") != FLOW]
    lines = sum(_int(u.get("lines")) or 0 for u in readers)
    plus = " plus the flow" if len(readers) < len(units or []) else ""
    reading = (f'{len(readers)} reading units{plus}, {lines:,} lines of code in all; each unit read in full by one '
               f'reader (at most {cfg["unit_lines"]:,} lines a unit)' if units else missing("The list of units"))
    brief = (
        '<dl class="brief">'
        f'<dt>Plan</dt><dd>{E(head) if head else missing("PLAN.md")}</dd>'
        f'<dt>{"Flow" if go else "Flow (your decision at the go)"}</dt><dd>{flow_html}</dd>'
        f'<dt>Services</dt><dd>{E(", ".join(services)) if services else missing("The list of units")}</dd>'
        f'<dt>Reading units</dt><dd>{reading}</dd>'
        f'<dt>{"Your pick of how far each stage goes" if scope and "their pick after mapping" in scope else "Scope given at the go"}'
        f'</dt><dd>{E(scope) if scope else "not yet given"}</dd>'
        f'<dt>Settings</dt><dd>{cfg["judges"]} judges a row, {cfg["judge_rounds"]} rounds at most, '
        f'{cfg["parallel"]} readers at once</dd></dl>')

    app = application(plan_md, reg.name)
    body = (f'<main class="frame"><div class="top"><h1>The run of {E(app)}</h1>'
            '<button type="button" id="theme">Dark theme</button></div>'
            f'{band}'
            f'<h2 class="sec">The plan in brief</h2>{brief}'
            '<h2 class="sec">Units and their steps</h2>'
            '<p class="note">Each unit is part of the code, read in full by one reader; its rows are then checked by '
            'the judges, and any flagged row is fixed.</p>'
            f'{units_table(units, jobs)}'
            f'<h2 class="sec">The run’s own steps</h2>{run_table(jobs, unmatched)}'
            + ("" if jobs else f'<p>{missing("The job list")}</p>')
            + counts_html(counts(reg), (reg / "views.html").is_file())
            + "</main>")
    return (f'<title>{E(app)} run</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            f"<style>{CSS}</style>\n{body}\n{SCRIPT}\n")


def main(argv):
    if len(argv) != 1:
        print("python run_page.py <register folder>")
        return 2
    reg = pathlib.Path(argv[0])
    if not reg.is_dir():
        print(f"no such folder: {reg}")
        return 2
    (reg / OUT).write_text(render(reg), encoding="utf-8")
    print(reg / OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
