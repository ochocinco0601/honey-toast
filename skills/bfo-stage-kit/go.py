"""Record the person's go on the plan as data the run follows: scope.json, and the judges count in run-settings.json.

Usage: python go.py <register folder> --flow "<the flow to start with>" --words "<their go, verbatim>"
                    [--in <service,...> --out <service,...>] [--judges N] [--given "<when>"] [--test]
       python go.py <register folder> --stage-ids <id,...>      once the stages are cut (Phase 2)
       python go.py <register folder> --depth "<id>=measure|alerting|runbooks,..."   how far each stage goes, once
                                                                  cut; a stage not named is mapped only
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
test standing in for the person. `--judges` is written into run-settings.json, keeping its other settings. `--stage-ids`
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


def load(reg):
    """The scope recorded at the go, or None when there is none."""
    p = pathlib.Path(reg) / layout.SCOPE
    if not p.is_file():
        return None
    got = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(got, dict):
        raise ValueError(f"{p}: not a JSON object")
    return got


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


DEFAULT_JUDGES = 3  # the kit's default


def default_services(reg, surveyed):
    """(in, out): the kit's own choice of which services to read, from the first look's recommendation for each
    (orientation.json), else every surveyed service. The person is shown it, never asked it."""
    o = reg / layout.ORIENTATION
    rec = {s.get("name"): s.get("recommend") for s in
           (json.loads(o.read_text(encoding="utf-8-sig")).get("services") or [] if o.is_file() else [])}
    return [n for n in surveyed if rec.get(n, "in") != "out"], [n for n in surveyed if rec.get(n) == "out"]


def record_go(reg, a):
    """The go after the first look: which flow comes first, and the person's words. Which services are read and how many
    checks each finding gets are the kit's to decide: the first look's recommendation and the kit's default number, shown to
    the person and overridden only when the person says so (`--in`/`--out`, `--judges`)."""
    if a.stages is not None:
        return ("the stages are no longer picked at the go: once the flow is mapped, the person picks how far each "
                "stage goes (go.py --depth)")
    surveyed = [r["service"].strip() for r in rows(reg / "survey.csv")
                if (r.get("kind") or "").strip() == "service" and (r.get("service") or "").strip()]
    if not surveyed:
        return "survey.csv has no service: run survey.py first"
    problems = []
    if a.inn is None and a.out is None:
        inn, out = default_services(reg, surveyed)
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
        problems.append("--judges must be 1 or more")
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
    s = {"flow": a.flow.strip(), "services_in": inn, "services_out": out,
         "stage_ids": [], "words": a.words.strip(),
         "given": a.given or datetime.datetime.now().astimezone().isoformat(timespec="minutes"), "test": a.test,
         "remains": remains or {"services_left_out": out}}
    p = reg / layout.SETTINGS
    settings = json.loads(p.read_text(encoding="utf-8-sig")) if p.is_file() else {}
    settings["judges"] = judges
    a.judges = judges
    write(reg, layout.SETTINGS, json.dumps(settings) + "\n")
    write(reg, layout.SCOPE, json.dumps(s, indent=1) + "\n")
    record_in_run_md(reg, s)
    return s


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
    text = re.sub(r"^(\| 1 The case and its lifecycle \| )to do \|", r"\1doing |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


ALERT_COLS = ("handle", "alert", "expectation", "counted_moves")


def alert_fingerprint(reg):
    """A short hash of the alert choices in measures.csv: each proposed alert's handle, basis, the expectation it
    guards and the moves it counts. A measure's other columns do not change it."""
    import hashlib
    chosen = sorted("\t".join((r.get(c) or "").strip() for c in ALERT_COLS) for r in rows(pathlib.Path(reg) / "measures.csv")
                    if (r.get("alert") or "").strip().lower().startswith("yes"))
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
        write(pathlib.Path(reg), layout.SCOPE, json.dumps(s, indent=1) + "\n")
    if review_state(reg)[0]:
        review_line(reg, "- **Alerts reviewed:** _blank until the person answers on the alerts as now proposed._",
                    "doing")


def record_alerts_shown(reg):
    """The fingerprint of the alerts as the review message showed them, kept until the person's answer on them."""
    s = load(reg)
    if s is None:  # no go recorded (an earlier run): there is no scope to keep it in
        return
    s["alerts_shown"] = alert_fingerprint(reg)
    write(pathlib.Path(reg), layout.SCOPE, json.dumps(s, indent=1) + "\n")


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
        write(reg, layout.SCOPE, json.dumps(s, indent=1) + "\n")
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
    write(reg, layout.SCOPE, json.dumps(s, indent=1) + "\n")
    review_line(reg, f"- **Alerts reviewed:** {a.words.strip()} ({who}, {given})", "done")
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
    write(reg, layout.SCOPE, json.dumps(s, indent=1) + "\n")
    return s


def record_flow_id(reg, flow_id):
    """The id of the flow the pick is for, as the session names it at the pick (brief.py depth), so the run finds its
    flow by id once the walk has named it afresh. Nothing is written for an id not in flows.csv, or before the
    go has made scope.json."""
    s = load(reg)
    known = {(r.get("flow_id") or "").strip() for r in rows(pathlib.Path(reg) / "flows.csv")}
    if s is None or flow_id not in known:
        return
    s["flow_id"] = flow_id
    write(pathlib.Path(reg), layout.SCOPE, json.dumps(s, indent=1) + "\n")


DEPTHS = ("none", "measure", "alerting", "runbooks")  # each needs the one before it; none is mapped only


def pick_state(reg):
    """(the run record has the pick row, it is done). A register whose run record has no such row is from before
    mapping and measuring were picked apart, and is not held to it."""
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    m = re.search(r"^\| Pick of how far each stage goes \| ([^|]*)\|", text, re.M)
    return bool(m), bool(m) and m.group(1).strip().lower() == "done"


def mark_the_pick(reg, depth, line, before=None, picked=None):
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
    text = row("4 ", "doing" if measured else "not picked")
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
    known = [(r.get("stage") or "").strip() for r in rows(reg / "stages.csv") if (r.get("stage") or "").strip()]
    if not known:
        return "stages.csv has no stage: the stages are cut in mapping, before this choice"
    depth = {s: "none" for s in known}
    for pair in names(text):
        sid, _, value = pair.partition("=")
        sid, value = sid.strip(), value.strip().lower()
        if sid not in known:
            return f"not a stage in stages.csv: {sid} (its stages: {', '.join(known)})"
        if value not in DEPTHS:
            return f"{sid}: {value or 'nothing'} is not one of {', '.join(DEPTHS)}"
        depth[sid] = value
    s = load(reg) or {}
    before = s.get("depth") or {}
    lowered = [f"{sid} from {before[sid]} to {d}" for sid, d in depth.items()
               if before.get(sid) in DEPTHS and DEPTHS.index(d) < DEPTHS.index(before[sid])]
    if lowered:
        return ("taking a stage less far than already picked is not supported yet (" + "; ".join(lowered) +
                "): the pages already written for it would stay. Name each stage at least as far as before; taking "
                "a stage further is allowed")
    s["depth"] = depth
    if a is not None:
        given = a.given or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
        s["depth_picked"] = {"words": a.words.strip(), "given": given, "test": a.test}
        who = "a test pick, given by a test standing in for the person" if a.test else "the person"
        mark_the_pick(reg, depth, f"- **Depth picked:** {a.words.strip()} ({who}, {given})", before, s["depth_picked"])
    write(reg, layout.SCOPE, json.dumps(s, indent=1) + "\n")
    return s


def ticked(value):
    """The ticks a page sent for one item: a checkbox group's list, or one value (a radio, a select), as a list."""
    if value is None or value == "":
        return []
    return [str(v) for v in value if str(v)] if isinstance(value, list) else [str(value)]


PICK_MILESTONES = ("Mapped", "Measures defined", "Alerts defined")  # the milestones whose choice the kit records
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
        write(reg, layout.SCOPE, json.dumps(s, indent=1) + "\n")
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
    unknown = [k for k in got if k not in ("choice_id", "words", "milestone") and k not in offered]
    if c["milestone"] == "Mapped":
        if unknown:
            return f"not a flow on the page: {', '.join(unknown)}"
        bad = [f"{k}: {v}" for k in offered for v in ticked(got.get(k)) if v != depth.FLOW_OPT]
        if bad:
            return f"not a tick the page offers: {'; '.join(bad)}"
        picked = [k for k in offered if ticked(got.get(k))]
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
    return ("the review of the alerts is not taken from a page: record their answer with go.py --alerts-reviewed "
            "--decision go|changes --words")


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
    if "--answers" in argv:  # the person's picks from the page, recorded as --flow or --depth records them
        i = argv.index("--answers")
        rest = argv[:i] + argv[i + 2:]
        test = "--test" in rest
        rest = [x for x in rest if x != "--test"]
        if len(rest) != 1 or i + 1 >= len(argv) or not pathlib.Path(rest[0]).is_dir():
            print("Usage: python go.py <register folder> --answers <answers file> [--test]", file=sys.stderr)
            return 2
        reg = pathlib.Path(rest[0])
        key = answers_key(argv[i + 1])
        if key and taken_before(reg, key):
            print("REFUSED: these answers were recorded already, so they are not the person's latest. If nothing "
                  "newer has arrived, ask the question in the chat. Nothing written.", file=sys.stderr)
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
    ap.add_argument("--decision")
    ap.add_argument("--depth")
    ap.add_argument("--page", action="store_true", help=argparse.SUPPRESS)  # from the page: ticks alone answer
    a = ap.parse_args(argv)
    reg = pathlib.Path(a.reg)
    if not reg.is_dir():
        print(f"not a folder: {reg}", file=sys.stderr)
        return 2
    got = (record_review(reg, a) if a.alerts_reviewed else
           record_depth(reg, a.depth, a) if a.depth is not None else
           record_stage_ids(reg, names(a.stage_ids)) if a.stage_ids is not None else record_go(reg, a))
    if isinstance(got, str):
        print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
        return 2
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
    if a.alerts_reviewed:
        import brief
        print(f"Written: the review of the alerts, in {layout.SCOPE} and RUN.md")
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
