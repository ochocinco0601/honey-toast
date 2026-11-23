"""The fast map of one flow: chosen at the go (go.py --fast), run by run control after the lead's steps, Business
Impact and the pick, in place of many readers, re-reads and judges.

One mapping agent per service (agents/bfo-flow-mapper.md: Read, Grep, Glob and Write, no shell), all launched at once,
each reads its own service's units and writes each unit's rows in the unit formats as soon as it has read that unit,
so a stop or a lost agent leaves every unit already written. Each agent's reading budget is its context window less
what its prompt, tools and writing take (OVERHEAD); a service too big for one agent is split across several, and a
file too big for one agent is listed as not read with that reason. Then, by script: every citation's range exists
(refused when not); the name a row gives is found in its cited lines (reported, never refused: spellings differ); the
code scanner's facts in those services that no row covers are listed as gaps, never added silently; every row is
labelled; and the map is drawn. No second agent checks a row in this build; the page says so.

Usage:
  python fast_map.py plan    <register> <flow> [--ws DIR]   the reading plan and the mapping agent's prompt
  python fast_map.py check   <register> <flow> [--ws DIR]   the rule checks; exit 1 with what must be put right
  python fast_map.py draw    <register> <flow> [--ws DIR]   refuses while the check fails; writes fast-map.html
  python fast_map.py summary <register> <flow>              counts, one line
Python standard library only."""
import csv
import html
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FOLDER = "fast"
PAGE = "fast-map.html"
PROMPT = "mapper-prompt.md"
PLAN = "reading-plan.csv"
AGENT = "bfo-flow-mapper"
TOKENS_PER_LINE = 19  # Read loads about 17 to 20 tokens per line of code
DEFAULT_CONTEXT = 200000  # run-settings.json `fast_context_tokens` (go.py --context-tokens): the mapping agent's
# context window, in tokens. A subagent launched with `model: inherit` runs on the session's model; whether it gets
# that model's largest window is not stated in the Claude Code documentation this kit could reach, so the default is
# the standard 200,000 and a larger window is set at the go, never assumed.
OVERHEAD = 120000  # of the window, what the code may not take: the agent's system prompt, tools and prompt take about
# 62,000 tokens and its writing 40,000-50,000
STATUS = "mapper-status.csv"  # each mapping agent's: unit,status,note, written as it finishes each unit
MAPPERS = "mappers"  # fast/mappers/<group>/: one mapping agent's prompt and status file
GROUPS = "mappers.csv"  # fast/: group,service,units,tokens: which mapping agent reads which units
TABLES = ("subjects", "operations", "calls", "participation")
PLACEABLE = {"inbound_route", "grpc_method", "outbound_http", "durable_read", "durable_write"}
LABEL_READ = "read in one pass"
LABEL_UNREAD = "not read"
LABEL_GAP = "gap"
LABEL_UNPICKED = "not checked in this run"  # a step of a stage left mapped only: mapped at the service level
LABEL_NOT_CHECKED = "reading not checked"
NOT_DONE = ("Every row on this map was written in one pass by a mapping agent that first read the code of its service; no "
            "second agent has checked any row. The lines each row cites exist (checked by script). A file listed as not read "
            "carries its reason: left out to stay within the reading budget of a mapping agent, read in part, never opened, "
            "read blocked (every Read of it failed, with what the tool said), or in a part of the code the agent did "
            "not finish; a gap is something the code scanner found that no row covers, a call whose two "
            "sides do not meet, or a process step no part takes part in.")
SPAN = re.compile(r"([\w./-]+\.\w+):(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)")
IDENT = re.compile(r"`@?([A-Za-z_][\w.]*)(?:\(\))?`|@([A-Z]\w+)")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def rows(p):
    p = pathlib.Path(p)
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if p.is_file() else []


def write(path, data, keys):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)


def spans(text):
    out = []
    for m in SPAN.finditer(text or ""):
        for part in m.group(2).split(","):
            lo, _, hi = part.strip().partition("-")
            out.append((m.group(1), int(lo), int(hi or lo)))
    return out


def workspace(reg, ws=None):
    """The folder citations are relative to, as for readers and judges (judges.workspace): `ws`, else where the
    register records the code (layout.code_root), else the register's grandparent."""
    if ws:
        return pathlib.Path(ws).resolve()
    import register_layout as layout
    return layout.code_root(reg) or pathlib.Path(reg).resolve().parent.parent


def budget(reg):
    """The tokens of code ONE mapping agent may read: its context window (`fast_context_tokens`, DEFAULT_CONTEXT when
    unset) less OVERHEAD, so its prompt, tools and writing still fit; a `fast_budget_tokens` set by hand is used,
    never above that."""
    import settings
    s = settings.load(reg)
    try:
        window = int(s.get("fast_context_tokens") or DEFAULT_CONTEXT)
    except (ValueError, TypeError):
        window = DEFAULT_CONTEXT
    cap = window - OVERHEAD if window > OVERHEAD else window // 4
    try:
        asked = int(s.get("fast_budget_tokens") or 0)
    except (ValueError, TypeError):
        asked = 0
    return min(asked, cap) if asked else cap


def flow_steps(reg, flow):
    stages = {r["stage"] for r in rows(pathlib.Path(reg) / "stages.csv") if (r.get("flow") or "").strip() == flow}
    return [r for r in rows(pathlib.Path(reg) / "steps.csv") if (r.get("stage") or "").strip() in stages]


def picked_steps(reg, flow):
    """The process steps of the stages the person took past mapped only (go.picked_stages); every step of the flow
    when no pick is recorded (a register made before the pick was asked)."""
    steps = flow_steps(reg, flow)
    try:
        import go
        s = go.load(reg)
    except Exception:  # noqa: BLE001  (no record of the go: no pick to narrow by)
        return steps
    if not s or "depth" not in s:
        return steps
    picked = set(go.picked_stages(s))
    return [r for r in steps if (r.get("stage") or "").strip() in picked]


def flow_moves(reg, flow):
    return {(r.get("move_id") or "").strip(): r for r in rows(pathlib.Path(reg) / "lifecycle.csv")
            if (r.get("flow") or flow).strip() == flow}


def units(reg):
    """The reading units of the services the flow reads (readers.in_scope: owed and read), in units.csv order."""
    import readers
    owed, done = readers.in_scope(reg)
    keep = set(owed) | set(done)
    return [r for r in rows(pathlib.Path(reg) / "units" / "units.csv")
            if r.get("unit") in keep and r.get("unit") != "flow"]


GENERATED_NAME = re.compile(r"(\.pb\.go|_grpc\.pb\.go|_pb2(_grpc)?\.py|\.pb\.(cc|h)|\.g\.cs|\.designer\.cs|"
                            r"_generated\.\w+)$|(^|/)(genproto|generated|gen-src)/", re.I)
GENERATED_MARK = re.compile(r"Code generated .*DO NOT EDIT|@generated|<auto-generated|Generated by the protocol buffer",
                            re.I)


def generated(rel, path):
    """True for code a tool wrote: by its name or folder, or by the mark such tools put in a file's first lines."""
    if GENERATED_NAME.search(rel.replace("\\", "/")):
        return True
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = "".join(fh.readline() for _ in range(5))
    except OSError:
        return False
    return bool(GENERATED_MARK.search(head))


def _lines(path):
    data = pathlib.Path(path).read_bytes()
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def path_files(reg, ws):
    """The files the picked stages' path starts in (path_reading.starting_points), for reading first."""
    try:
        import path_reading
        entries = path_reading.starting_points(reg, ws)
    except Exception:  # noqa: BLE001  (no pick or no path: every file counts the same)
        return set()
    out = set()
    for e in entries.values():
        for x in e.get("lines") or []:
            out.add(x.rsplit(":", 1)[0])
        for o in e.get("operations") or []:
            out.add((o.get("at") or "").rsplit(":", 1)[0])
    return out


NAMED = "a picked stage's move names it"
REACHED = "called by a service on the picked stages' path"


def plan(reg, flow, ws=None):
    """Write fast/reading-plan.csv (unit, path, lines, tokens, status, reason, why), fast/mappers.csv and one prompt
    per mapping agent. The units are the closure of the picked stages (readers.in_scope, go.services_read); `why` says
    whether a picked stage's move names the unit's service or it is only reached by following calls. Each mapping
    agent reads one service, or a share of one: a service's units are packed into agents each within the budget (one
    agent's context window less OVERHEAD), so a service too big for one agent is split, never read in part. Inside a
    unit larger than the budget, the files on the picked stages' path come first, and a file that does not fit is
    listed as not read with the reason, never read in part silently."""
    import go
    import reading_check
    reg, ws = pathlib.Path(reg), workspace(reg, ws)
    seeds = go.stage_seeds(reg, go.load(reg))
    cap = budget(reg)
    first = path_files(reg, ws)
    owed, by_unit = [], {}
    for u in units(reg):
        paths = [p for p in (u.get("paths") or "").split(";") if p.strip()]
        got, _ = reading_check.owed_files(ws, paths)
        service = (u.get("deployable") or u["unit"]).strip().lower()
        why = "" if seeds is None else (NAMED if service in seeds else REACHED)
        mine = []
        for rel, absolute in sorted(got.items()):
            n = _lines(absolute)
            gen = generated(rel, absolute)
            mine.append({"unit": u["unit"], "path": rel, "lines": n, "tokens": 0 if gen else n * TOKENS_PER_LINE,
                         "status": "not read" if gen else "", "reason": "generated code" if gen else "", "why": why})
        mine.sort(key=lambda r: not any(r["path"].endswith(f) or f.endswith(r["path"]) for f in first))
        used = 0
        for r in mine:
            if r["status"]:
                continue
            if r["tokens"] > cap:
                r["status"], r["reason"] = "not read", (f"larger than one mapping agent's reading budget "
                                                        f"({r['tokens']:,} of {cap:,} tokens)")
            elif used + r["tokens"] <= cap:
                used += r["tokens"]
                r["status"], r["reason"] = "read", ""
            else:
                r["status"], r["reason"] = "not read", "over the reading budget of the unit's mapping agent"
        by_unit[u["unit"]] = (service, used)
        owed += mine
    write(reg / FOLDER / PLAN, owed, ["unit", "path", "lines", "tokens", "status", "reason", "why"])
    made = []
    for service in dict.fromkeys(s for s, _ in by_unit.values()):
        current = None
        for u, (s, used) in by_unit.items():
            if s != service:
                continue
            if current is None or current["tokens"] + used > cap:
                n = sum(1 for g in made if g["service"] == service)
                current = {"group": service if n == 0 else f"{service}-{n + 1}", "service": service, "units": [],
                           "tokens": 0}
                made.append(current)
            current["units"].append(u)
            current["tokens"] += used
    write(reg / FOLDER / GROUPS, [dict(g, units=";".join(g["units"])) for g in made],
          ["group", "service", "units", "tokens"])
    write_prompt(reg, flow, ws)
    total = sum(r["tokens"] for r in owed)
    return {"units": len(by_unit), "files": len(owed), "read": sum(r["status"] == "read" for r in owed),
            "lines": sum(r["lines"] for r in owed), "tokens_estimated": total, "budget": cap,
            "tokens_planned": sum(r["tokens"] for r in owed if r["status"] == "read"), "mappers": len(made)}


def groups(reg):
    """[{"group", "service", "units": [unit], "tokens"}]: the mapping agents of the plan (fast/mappers.csv)."""
    return [dict(r, units=[x for x in (r.get("units") or "").split(";") if x])
            for r in rows(pathlib.Path(reg) / FOLDER / GROUPS)]


def group_prompt(reg, group):
    return pathlib.Path(reg) / FOLDER / MAPPERS / group / PROMPT


def group_status(reg, group):
    return pathlib.Path(reg) / FOLDER / MAPPERS / group / STATUS


def write_prompt(reg, flow, ws=None, only=None):
    """Each mapping agent's prompt, from the reading plan: for every unit, or, on a relaunch, only for the agents with
    a unit `only` names (not yet written or marked unfinished), each prompt naming only those of its units. The
    prompts together are also written to fast/mapper-prompt.md, for the person to read (never given to an agent).
    Returns [(group, prompt path, units)] of the agents to launch."""
    reg, ws = pathlib.Path(reg), workspace(reg, ws)
    owed = rows(reg / FOLDER / PLAN)
    for r in owed:
        r["lines"], r["tokens"] = int(r.get("lines") or 0), int(r.get("tokens") or 0)
    cap = budget(reg)
    written = [] if only is None else sorted({r["unit"] for r in owed} - set(only))
    out, texts = [], []
    for g in groups(reg):
        mine = [u for u in g["units"] if only is None or u in only]
        if not mine:
            continue
        marked = statuses(reg)
        rs = []
        for u in mine:
            mine_rows = [r for r in owed if r["unit"] == u]
            if only is not None and RAN_OUT.search(marked.get(u, ("", ""))[1]):
                mine_rows = _split(reg, u, mine_rows)
            rs += mine_rows
        text = prompt(reg, flow, ws, rs, sum(r["tokens"] for r in rs if r["status"] == "read"), cap, g["group"],
                      written)
        p = group_prompt(reg, g["group"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        out.append((g["group"], p, mine))
        texts.append(text)
    (reg / FOLDER).mkdir(parents=True, exist_ok=True)
    (reg / FOLDER / PROMPT).write_text("\n\n---\n\n".join(texts), encoding="utf-8")
    return out


def statuses(reg):
    """{unit: (status, note)} from every mapping agent's status file, and the single one an earlier build wrote."""
    reg = pathlib.Path(reg)
    files = sorted((reg / FOLDER / MAPPERS).glob(f"*/{STATUS}")) + [reg / FOLDER / STATUS]
    got = {}
    for f in files:
        for r in rows(f):
            got[(r.get("unit") or "").strip()] = ((r.get("status") or "").strip().lower(), r.get("note") or "")
    return got


def unfinished(reg):
    """The units of the plan still owed: no `files.csv` yet, or marked `unfinished` in a mapping agent's status file."""
    reg = pathlib.Path(reg)
    marked = statuses(reg)
    owed = sorted({r["unit"] for r in rows(reg / FOLDER / PLAN)})
    return [u for u in owed if not (reg / "units" / u / "files.csv").is_file()
            or (marked.get(u, ("", ""))[0] == "unfinished" and not only_blocked(marked[u][1]))]


BLOCKED = re.compile(r"\bblocked\b", re.I)  # a status note naming a file a hook or the tool refused to read
RAN_OUT = re.compile(r"\bran out\b|\bsplit\b", re.I)  # a status note: the agent ran out of room, or a split share


def only_blocked(note):
    """True when an unfinished unit's note names only files that cannot be read: a relaunch would hit the same block,
    so the unit is done with those files listed as not read (gaps shows each)."""
    return bool(BLOCKED.search(note or "")) and not RAN_OUT.search(note or "")


def listed(reg, unit, read_only=False):
    """The files a unit's files.csv already lists (cited, not relevant or not read); with `read_only`, only those it
    read (cited or not relevant)."""
    return {(r.get("path") or "").strip() for r in rows(pathlib.Path(reg) / "units" / unit / "files.csv")
            if not read_only or (r.get("status") or "").strip().lower() != "not read"}


def _split(reg, unit, rs):
    """For a unit whose agent ran out of room: its planned rows with every file it already listed left out, and only
    the first half of the rest to read now, the other half named as left for the next launch, so a relaunch never
    repeats the same overrun."""
    done = listed(reg, unit, read_only=True)
    left = [dict(r) for r in rs if r["path"] not in done]
    to_read = [r for r in left if r["status"] == "read"]
    if not to_read:  # every file read already: the unit is finished from its tables, as any relaunch
        return rs
    keep = max(1, -(-len(to_read) // 2))
    for r in to_read[keep:]:
        r["status"], r["reason"] = "later", ("left for the next launch of this unit: it ran out of room, so its files "
                                             "are read in shares")
    return left


def prompt(reg, flow, ws, owed, used, cap, group, written=()):
    steps = "\n".join(f"- step {s['step']} ({s['stage']}): {s['name']}. Cites: {s.get('source') or '-'}"
                      for s in picked_steps(reg, flow))
    by_unit = {}
    for r in owed:
        by_unit.setdefault(r["unit"], []).append(r)
    blocks = []
    redo = row_id_reasons(reg)
    for u, rs in by_unit.items():
        if u in redo:
            blocks.append(f"### Unit `{u}` was written before and set aside\n\nIts rows broke the unit rules: "
                          f"{redo[u]}. Write it again from the start, by the rules for rows and parts below.")
        read = "\n".join(f"  - {r['path']} ({r['lines']} lines)" for r in rs if r["status"] == "read")
        left = "\n".join(f"  - {r['path']}: {r['reason']}" for r in rs if r["status"] not in ("read", "later"))
        later = [r for r in rs if r["status"] == "later"]
        blocks.append(f"### Unit `{u}` (write `{reg.as_posix()}/units/{u}/`)\n\nRead:\n{read or '  - (none)'}"
                      + (f"\n\nNot read (list each in files.csv as `not read`, with the reason given):\n{left}"
                         if left else "")
                      + (f"\n\nLeft for the next launch of this unit (do not read them now; mark the unit `unfinished` "
                         f"with the note `split: {len(later)} file(s) left`):\n"
                         + "\n".join(f"  - {r['path']}" for r in later) if later else ""))
    over = any(r["status"] != "read" and "budget" in (r.get("reason") or "") for r in owed)
    size = (f"Your code is about {used:,} tokens, within your reading budget of {cap:,}: read all of it."
            + (" Files that would not fit are listed under each unit as not read, over the reading budget."
               if over else ""))
    again = ("" if not written else
             "\n\nThis is a relaunch. These units are written already; leave them as they are and do not read their "
             "files: " + ", ".join(f"`{u}`" for u in written) + ". A unit below whose folder already has tables: read "
             "the tables first, keep every right row and its `row_id`, number new rows above the highest, and finish "
             "it.")
    status = group_status(reg, group).as_posix()
    return f"""# Map flow {flow}: the units of mapping agent `{group}`

Workspace: {ws.as_posix()} (citations are paths relative to it). Register: {reg.as_posix()}.

You are one of the mapping agents of this flow's fast map (agent `{AGENT}`; its definition holds your rules). Other
mapping agents read the other services at the same time; you read only your units below. Read nothing else: only the
files listed below, and no file they import; when a call's target cannot be told from what you read, record the call
as the caller writes it and say so in its `source`.{again}

1. **One unit at a time: First read every file listed for the unit,** with the Read tool, many at a time in
   parallel. {size} The Read tool returns at most 2,000 lines when given no limit: for a longer file, read on with
   `offset` and `limit` until its last line. A Read that fails (the file is too large for one Read, or a hook blocked
   it) is no read: read a too-large file in parts with `offset` and `limit`; list a blocked file in `files.csv` as
   `not read` with the reason the tool gave. A file you could not read to its end is listed as `not read` with the
   reason `read in part: lines <first>-<last> read`, never as `cited` or `not relevant`.
2. **Then write that unit's tables as soon as its files are read, in one pass,** before you read the next unit: its
   `subjects.csv`, `operations.csv`, `calls.csv`, `participation.csv` and `files.csv` in `units/<unit>/`, in the unit
   formats (`split-run-formats.md` beside this kit, section "units/<unit>/ (a reader's output)"). Row ids:
   {ROW_ID_RULE}. Parts: {PART_RULES.format(kinds=_kinds_said())} A unit that breaks these rules is set aside as you return and written again.
   A unit written is kept even if you are stopped later. Write rows only
   for the process steps below: they are the steps of the stages the person picked. Every row cites `path:line` or
   `path:first-last` from what you read. You read the code once: never re-read a file to check a row.
3. **Calls to another unit:** give `to_unit` and the `operation` spelled exactly as the called side serves it, as
   the code you read shows it (the route, the client method, the message name). Another agent may write that unit's
   `operations.csv`; a call whose two sides do not meet is shown as a gap.
4. **After each unit, add its row to `{status}`** with the columns `unit,status,note`: `status` `done` when every
   listed file is cited, not relevant, or not read with a reason no relaunch can cure (blocked, generated, over the
   budget); `unfinished` only for what a relaunch can finish, with the note `ran out: <n> file(s) left` when you ran
   out of room (write the unit from what you read first, the rest `not read: ran out of room`) or the `split:` note
   this prompt gives. A call into a service that is not one of this run's units keeps its `to_unit` as the caller
   names it, with "outside this run" in its `source`.

Your final reply is one line: `MAPPED units=<n> files_read=<n> lines_read=<n> rows=<n>`, then, when you fell short,
`; READ IN PART: <file> lines <a>-<b>, ...` and `; UNFINISHED: <unit>, ...`.

## The flow's process steps (the picked stages)

{steps or '(no stage is taken past mapped only: write nothing and say so)'}

## What to read ({used:,} tokens planned)

{chr(10).join(blocks) or '(no unit is owed: write nothing and say so)'}
"""


def unit_rows(reg):
    """[(unit, table, row)] of every row the mapping agent wrote, for the units of the plan."""
    reg = pathlib.Path(reg)
    out = []
    for u in sorted({r["unit"] for r in rows(reg / FOLDER / PLAN)}):
        for t in TABLES:
            out += [(u, t, r) for r in rows(reg / "units" / u / f"{t}.csv")]
    return out


BAND_OF_FAMILY = {"service": "application", "pipeline": "application", "agent": "application",
                  "store": "technology", "platform": "technology"}  # REGISTER.md, subjects.csv `band`
NO_LEVEL = ("person", "case", "interaction")  # REGISTER.md, subjects.csv `level`: blank for these


def part_problems(unit, row, families=None):
    """What a mapped part row (subjects.csv) lacks by the register's rules for band and level: every element has a
    band; every deployable has a level; a service, worker or agent is `application`, a store or platform
    `technology`. A part kind not in method/part-kinds.csv is held to the first two only."""
    if (row.get("kind") or "").strip() != "element":
        return []
    if families is None:
        import go
        families = go.part_families()
    where = f"{unit}/subjects.csv {row.get('row_id') or ''}".strip()
    family = families.get((row.get("part_kind") or "").strip().lower(), "")
    band, level = (row.get("band") or "").strip(), (row.get("level") or "").strip()
    out = []
    if not band:
        out.append(f"{where}: no band (business, application or technology)")
    elif BAND_OF_FAMILY.get(family) and band != BAND_OF_FAMILY[family]:
        out.append(f"{where}: band {band}, but a {row.get('part_kind')} is {BAND_OF_FAMILY[family]}")
    if not level and family not in NO_LEVEL:
        out.append(f"{where}: no level (component, or external dependency when its code cannot be had)")
    kind = (row.get("part_kind") or "").strip()
    if kind and kind.lower() not in families:
        out.append(f"{where}: part_kind {kind!r} is not one of the kit's part kinds (method/part-kinds.csv): use one "
                   f"of {', '.join(sorted(families))}")
    if level == "component" and not (row.get("repository") or "").strip():
        if not (band == "technology" and re.search(r"\bno repository\b", row.get("source") or "", re.I)):
            out.append(f"{where}: a component with no repository: write the repository folder its code or its "
                       "definition sits in (`repo` or `repo: path`), or, for a store or platform no repository "
                       "defines, leave it blank and say `no repository defines it` in source")
    return out


def unit_problems(reg, unit, families=None):
    """[what is wrong with a unit the mapping agent wrote, by the register's rules]: its row ids, each part's kind,
    band, level and repository, and any numbered call sequence (a fast map leaves `sequence` blank: one agent per
    service cannot know the order of calls made from another). Found as the agent returns, never at the drawing."""
    folder = pathlib.Path(reg) / "units" / unit
    out = row_id_problems(reg, unit)
    for r in rows(folder / "subjects.csv"):
        out += part_problems(unit, r, families)
    for t in ("subjects", "calls"):
        for r in rows(folder / f"{t}.csv"):
            if (r.get("sequence") or "").strip():
                out.append(f"units/{unit}/{t}.csv {r.get('row_id') or ''}: sequence "
                           f"{r.get('sequence')!r}: leave sequence blank on a fast map")
    return out


def _resolve(ws, f):
    p = ws / f
    if p.is_file():
        return p
    hits = [q for q in ws.rglob(pathlib.Path(f).name) if q.as_posix().endswith(f.replace("\\", "/"))]
    return hits[0] if len(hits) == 1 else None


def _text(p):
    return p.read_text(encoding="utf-8", errors="replace").splitlines()


def lead_problems(reg, flow, ws):
    """Every span the lead's own stages, steps and moves cite resolves to one file with its lines in range, and a
    name the same field gives in backticks or as an annotation is in the span when it is in that file at all."""
    fields = [(f"stage {r['stage']}", r.get("source")) for r in rows(reg / "stages.csv")
              if (r.get("flow") or "").strip() == flow]
    fields += [(f"step {r['step']}", r.get("source")) for r in flow_steps(reg, flow)]
    for mid, m in flow_moves(reg, flow).items():
        fields += [(f"move {mid}", m.get(k)) for k in ("source", "travels_by")]
    out = []
    for where, text in fields:
        names = {a or b for a, b in IDENT.findall(text or "")}
        for f, lo, hi in spans(text):
            p = _resolve(ws, f)
            if p is None:
                out.append(f"{where} cites {f}:{lo}-{hi}: no single file of that name in the workspace")
                continue
            lines = _text(p)
            if not 1 <= lo <= hi <= len(lines):
                out.append(f"{where} cites {f}:{lo}-{hi}: the file has {len(lines)} lines")
                continue
            near, whole = "\n".join(lines[max(0, lo - 3):hi + 2]), "\n".join(lines)
            for name in names:
                last = name.split(".")[-1]
                if last in whole and last not in near:
                    out.append(f"{where} cites {f}:{lo}-{hi} for {name}, which is elsewhere in the file")
    return out


ANY_TYPE = "fast_mapper_any_type"  # run-settings.json, a trial run only: a mapper launched as another type is accepted
INSTALL = ("copy the kit's agents/bfo-flow-mapper.md into the project's .claude/agents/, start a new session so the "
           "type loads, and launch the mapping agent again (fast read)")


REFUSED = "refused"  # fast/refused/<session>/<unit>/: a refused writer's tables, set aside by run control
SET_ASIDE = "set-aside.json"  # fast/: [{"session", "units", "at"}], the writers set aside and their units
MAX_SET_ASIDE = 1  # refused writers set aside for one unit (each followed by one relaunch) before run control stops
# for the person instead: a second refusal of the same unit is not something a further launch will cure


def refused_writers(reg, transcripts=None):
    """[{"session", "units", "why"}]: every subagent that wrote the map's unit rows and is refused, read from the
    transcripts as for unit readers (provenance.py): it ran a shell, or it is not the kit's mapping agent. The lead's
    own session may correct a row (the fast check asks it to). For a trial run only, run-settings.json
    `fast_mapper_any_type: true` accepts a mapper launched as another type (the type was not installed); a shell is
    never accepted. A writer run control has already set aside (SET_ASIDE) is not refused again: its tables are gone
    from units/. No transcript found adds nothing here: the map then says its reading was not checked."""
    import paths
    import provenance
    import settings
    reg = pathlib.Path(reg).resolve()
    sessions, _ = provenance.flow_sessions(reg, transcripts)
    units = paths.norm(reg / "units") + "/"
    any_type = bool(settings.load(reg).get(ANY_TYPE))
    gone = {r["session"] for r in set_aside(reg)}
    out = []
    for s in sessions:
        wrote = sorted({p[len(units):].split("/", 1)[0] for _, p in s.writes if p.startswith(units)})
        if not wrote or pathlib.Path(s.path).parent.name != "subagents":
            continue  # wrote no unit rows, or the lead's own corrections
        name = pathlib.Path(s.path).stem
        if name in gone:
            continue
        if s.shell:
            out.append({"session": name, "units": wrote,
                        "why": f"{name} ran a shell while writing the map's rows: its rows are not counted. Launch the "
                               f"mapping agent again (fast read), as {AGENT}, which has no shell"})
            continue
        _, why = provenance.agent_type(s.path, AGENT)
        if why and not any_type:
            out.append({"session": name, "units": wrote,
                        "why": f"{name} wrote the map's rows and is {why}: {INSTALL}"})
    return out


def provenance_problems(reg, transcripts=None):
    """[what must be put right] about who wrote the map's unit rows (refused_writers)."""
    return [w["why"] for w in refused_writers(reg, transcripts)]


def set_aside(reg):
    p = pathlib.Path(reg) / FOLDER / SET_ASIDE
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else []
    except ValueError:
        return []


def set_aside_refused(reg, transcripts=None):
    """(units owed again, units stuck, why): each refused writer's unit tables moved to fast/refused/<session>/<unit>/
    and recorded in SET_ASIDE, so the mapping agent is launched again for those units only. A unit whose writers have
    been set aside MAX_SET_ASIDE times is not set aside again: it is stuck, and the person is told why."""
    import datetime
    import shutil
    reg = pathlib.Path(reg).resolve()
    record = set_aside(reg)
    times = {}
    for r in record:
        for u in r.get("units") or []:
            times[u] = times.get(u, 0) + 1
    owed, stuck, why = [], [], []
    for w in refused_writers(reg, transcripts):
        if any(times.get(u, 0) >= MAX_SET_ASIDE for u in w["units"]):
            stuck += [u for u in w["units"] if u not in stuck]
            why.append(w["why"])
            continue
        for u in w["units"]:
            src = reg / "units" / u
            if src.is_dir():
                dest = reg / FOLDER / REFUSED / w["session"] / u
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(src), str(dest))
            times[u] = times.get(u, 0) + 1
            if u not in owed:
                owed.append(u)
        record.append({"session": w["session"], "units": w["units"],
                       "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")})
    if owed:
        (reg / FOLDER / SET_ASIDE).write_text(json.dumps(record, indent=1), encoding="utf-8")
    return sorted(owed), sorted(stuck), why


ROW_ID_REASONS = "row-id-reasons.json"  # fast/: {unit: why}, the reason a unit was set aside for its row ids
ROW_ID_RULE = ("one `row_id` numbering across all of the unit's tables: `<unit>-1`, `<unit>-2`, ... counting on from "
               "one table to the next (subjects, then operations, calls, participation), never starting again at 1 in "
               "a table and never a second number inside the id; a row is addressed as `<unit>/<row_id>` whatever "
               "its table")


def _kinds_said():
    import go
    return ", ".join(f"`{k}`" for k in sorted(go.part_families()))


PART_RULES = ("each deployable you read is one `subjects.csv` row of kind `element`, level `component`, its "
              "`repository` the repository folder its code sits in; a store or platform its deployment provisions "
              "(a database, a cache, a broker) is a component too, band `technology`, its `repository` the one that "
              "defines it (`repo: path`), or blank with `no repository defines it` in its source; a part whose code "
              "cannot be had is level `external dependency`, repository blank. `part_kind` is exactly one of the "
              "kit's part kinds (method/part-kinds.csv): {kinds}; a service such as an HTTP or gRPC server is "
              "`API service`, a browser-facing one `web front end`. `band` is `application` for a service, worker or "
              "agent and `technology` for a store or platform. Leave `sequence` blank: the order of calls across "
              "services is not known from one service's code. `carries_case_id` is `yes` where this part's own code "
              "handles the case's id (logs it, stores it, passes it on), cited, else `no`.")


def row_id_problems(reg, unit):
    """[what is wrong with a unit's row ids]: a row with none, or an id used in more than one row of the unit's tables
    (split-run-formats.md: unique in the unit). The merge refuses both; this finds them as soon as the agent returns."""
    import register_layout as layout
    folder = pathlib.Path(reg) / "units" / unit
    seen, out = {}, []
    for t in layout.UNIT_TABLES:
        for i, r in enumerate(rows(folder / f"{t}.csv"), 2):
            rid = (r.get("row_id") or "").strip()
            if not rid:
                out.append(f"units/{unit}/{t}.csv line {i}: no row_id")
            else:
                seen.setdefault(rid, []).append(t)
    out += [f"units/{unit}: row_id {rid} used {len(ts)} times ({', '.join(ts)})"
            for rid, ts in seen.items() if len(ts) > 1]
    return out


def row_id_reasons(reg):
    p = pathlib.Path(reg) / FOLDER / ROW_ID_REASONS
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except ValueError:
        return {}


def register_refusals(reg):
    """{unit: [error]}: the register check's errors (capability_views.check) on rows of the merged map that a mapping
    agent wrote, by the unit that wrote each (the merge's own resolution). The lead may not edit a unit's rows, so
    these go back to that unit's mapping agent; errors on the lead's own rows are not here."""
    import capability_views as cv
    import merge
    reg = pathlib.Path(reg)
    errors = cv.check(cv.load(reg))[0]
    if not errors:
        return {}
    got = {}
    merge.build(reg, out=got)
    unit_of = {r.get("subject_id"): r.get("unit") for r in got.get("resolution") or [] if r.get("unit")}
    out = {}
    for e in errors:
        m = re.match(r"subjects\.csv (\S+?):", e)
        u = unit_of.get(m.group(1)) if m else None
        if u:
            out.setdefault(u, []).append(e)
    return out


def set_aside_bad_ids(reg, extra=None):
    """(units owed again, units stuck, why): each written unit that breaks the unit rules (unit_problems), or that
    `extra` ({unit: [problem]}, the register check's refusals of its rows) names, is moved to
    fast/refused/row-ids-<unit>-<n>/<unit>/ and recorded in SET_ASIDE, with the reason kept for its relaunch prompt, so
    the mapping agent writes it again before the merge. A unit set aside MAX_SET_ASIDE times already is stuck."""
    extra = extra or {}
    import datetime
    import shutil
    reg = pathlib.Path(reg).resolve()
    record = set_aside(reg)
    times = {}
    for r in record:
        for u in r.get("units") or []:
            times[u] = times.get(u, 0) + 1
    reasons = row_id_reasons(reg)
    owed, stuck, why = [], [], []
    units = reg / "units"
    for d in sorted(p for p in units.iterdir() if p.is_dir()) if units.is_dir() else []:
        u = d.name
        if not (d / "files.csv").is_file():
            continue
        found = unit_problems(reg, u) + list(extra.get(u) or [])
        if not found:
            continue
        said = "; ".join(found[:5]) + (f"; and {len(found) - 5} more" if len(found) > 5 else "")
        if times.get(u, 0) >= MAX_SET_ASIDE:
            stuck.append(u)
            why.append(f"{u}'s rows broke the unit rules again after it was written once more: {said}")
            continue
        n = times.get(u, 0) + 1
        dest = reg / FOLDER / REFUSED / f"row-ids-{u}-{n}" / u
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(d), str(dest))
        times[u] = n
        owed.append(u)
        reasons[u] = said
        record.append({"session": f"row-ids-{u}-{n}", "units": [u],
                       "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")})
    if owed:
        (reg / FOLDER).mkdir(parents=True, exist_ok=True)
        (reg / FOLDER / SET_ASIDE).write_text(json.dumps(record, indent=1), encoding="utf-8")
        (reg / FOLDER / ROW_ID_REASONS).write_text(json.dumps(reasons, indent=1), encoding="utf-8")
    return sorted(owed), sorted(stuck), why


def check(reg, flow, ws=None, transcripts=None):
    """(problems, notes): what must be put right before the map is drawn, and what is reported only."""
    reg, ws = pathlib.Path(reg), workspace(reg, ws)
    plan_rows = rows(reg / FOLDER / PLAN)
    if not plan_rows:
        return ["the reading plan has not been made (fast_map.py plan)"], []
    problems, notes = [], []
    for u in sorted({r["unit"] for r in plan_rows}):
        if not (reg / "units" / u / "files.csv").is_file():
            problems.append(f"unit {u}: the mapping agent has not written its tables")
    families = None
    for u, t, r in unit_rows(reg):
        if t == "subjects":
            if families is None:
                import go
                families = go.part_families()
            problems += part_problems(u, r, families)
        where = f"{u}/{t}.csv {r.get('row_id') or ''}".strip()
        cells = " ".join(v or "" for k, v in r.items() if k in ("source", "activity"))
        for f, lo, hi in spans(cells):
            p = _resolve(ws, f)
            if p is None:
                problems.append(f"{where} cites {f}:{lo}-{hi}: no single file of that name in the workspace")
                continue
            if not (ws / f).is_file():  # found by its name elsewhere: the checkers open the path as written
                full = p.relative_to(ws).as_posix() if p.is_relative_to(ws) else p.as_posix()
                problems.append(f"{where} cites {f}:{lo}-{hi} without its repository folder: write {full}:{lo}-{hi}")
                continue
            lines = _text(p)
            if not 1 <= lo <= hi <= len(lines):
                problems.append(f"{where} cites {f}:{lo}-{hi}: the file has {len(lines)} lines")
                continue
            if t in ("operations", "calls"):
                said = r.get("operation") or ""
                words = [w for w in WORD.findall(said) if w.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH")]
                near = "\n".join(lines[max(0, lo - 3):hi + 2]).lower()
                if words and not any(w.lower() in near for w in words):
                    notes.append(f"{where}: '{said}' is not spelled so in {f}:{lo}-{hi}")
    problems += lead_problems(reg, flow, ws)
    problems += provenance_problems(reg, transcripts)
    return problems, notes


def facts(reg):
    p = pathlib.Path(reg) / "fact-base.json"
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8-sig")).get("facts") or []


def _mapper_transcripts(folders):
    """The mapping agent's transcripts under the project folders: a subagent whose meta file names AGENT, or whose
    first message points at the mapping prompt."""
    out = []
    for folder in folders:
        for t in pathlib.Path(folder).glob("*/subagents/*.jsonl"):
            meta = t.with_name(t.stem + ".meta.json")
            try:
                kind = json.loads(meta.read_text(encoding="utf-8")).get("agentType") if meta.is_file() else None
            except (OSError, ValueError):
                kind = None
            if kind == AGENT:
                out.append(t)
                continue
            try:
                with open(t, encoding="utf-8", errors="replace") as fh:
                    first = fh.readline()
            except OSError:
                continue
            if PROMPT in first:
                out.append(t)
    return out


def read_coverage(reg, ws=None, transcripts=None):
    """{"found", "partly": {path: "a-b, ..." not read}, "unopened": [path]} for the planned files the mapping agent
    was to read, from the Read calls in its transcripts: a file the Read tool cut at its 2,000-line default and the
    agent did not read on is read in part."""
    import reading_check
    reg, ws = pathlib.Path(reg), workspace(reg, ws)
    folders = [pathlib.Path(transcripts)] if transcripts else reading_check.project_folders(reg)
    sessions = _mapper_transcripts(folders)
    got = {"found": bool(sessions), "partly": {}, "unopened": [], "blocked": {}}
    if not sessions:
        return got
    opened = reading_check.reads(sessions)
    failed = reading_check.blocked(sessions)
    for r in rows(reg / FOLDER / PLAN):
        if r.get("status") != "read":
            continue
        p = ws / r["path"]
        key = reading_check.path_rule.norm(p)
        spans = [s for k, ss in opened.items() if k == key or k.endswith("/" + r["path"].lower()) for s in ss]
        why = next((m for k, m in failed.items() if k == key or k.endswith("/" + r["path"].lower())), None)
        if not spans and why is not None:
            got["blocked"][r["path"]] = why
        elif not spans:
            got["unopened"].append(r["path"])
            continue
        n = _lines(p) if p.is_file() else 0
        left = reading_check._gaps(1, n, spans) if n else []
        if left:
            got["partly"][r["path"]] = ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in left)
    return got


def call_mismatches(reg):
    """[(unit, row, to_unit, operation)]: a call to another unit of the plan whose operation that unit's
    operations.csv does not serve, spelled so."""
    reg = pathlib.Path(reg)
    planned = {r["unit"] for r in rows(reg / FOLDER / PLAN)}
    served = {u: {(r.get("operation") or "").strip() for r in rows(reg / "units" / u / "operations.csv")}
              for u in planned}
    out = []
    for u, t, r in unit_rows(reg):
        to = (r.get("to_unit") or "").strip()
        if t != "calls" or to not in planned or to == u:
            continue
        op = (r.get("operation") or "").strip()
        if op not in served.get(to, set()):
            out.append((u, r.get("row_id") or "", to, op))
    return out


def gaps(reg, flow, ws, transcripts=None):
    """[(step, what, why)]: a picked step no part takes part in; a scanner fact in a read unit's files that no row's
    citation covers; a planned file not read, read in part or never opened; a unit the agent left unfinished; a call
    whose operation the called unit does not serve as spelled; and, when no transcript of the agent is found, that
    its reading was not checked."""
    reg = pathlib.Path(reg)
    out = []
    taking = {(r.get("step") or "").strip() for u, t, r in unit_rows(reg) if t == "participation"}
    taking |= {(r.get("step") or "").strip() for r in rows(reg / "participation.csv")}
    for u, rid, to, op in call_mismatches(reg):
        out.append(("", f"{u}: call {rid} to {to}: {op}",
                    f"the call's operation is not served by {to} as spelled: the two sides do not meet"))
    planned_units = {r["unit"] for r in rows(reg / FOLDER / PLAN)}
    for u, t, r in unit_rows(reg):
        to = (r.get("to_unit") or "").strip()
        if t == "calls" and to and to not in planned_units and not to.lower().startswith("external"):
            out.append(("", f"{u}: call {r.get('row_id') or ''} to {to}: {(r.get('operation') or '').strip()}",
                        "calls a service outside this run: its side is not read, so whether it serves the call is "
                        "not known"))
    for u, (st, note) in sorted(statuses(reg).items()):
        if st == "unfinished":
            out.append(("", f"{u}: unit not finished", f"{LABEL_UNREAD}: {note or 'unfinished'}"))
    cover = read_coverage(reg, ws, transcripts)
    if not cover["found"]:
        out.append(("", "the mapping agents' reading", LABEL_NOT_CHECKED + ": no transcript of a mapping agent was "
                    "found, so which files were read in full is not known"))
    for path, msg in cover.get("blocked", {}).items():
        out.append(("", path, f"{LABEL_UNREAD}: read blocked, every Read of it failed; the tool said: {msg[:200]}"))
    for path, left in cover["partly"].items():
        out.append(("", path, f"{LABEL_UNREAD}: read in part, lines {left} not read"))
    for path in cover["unopened"]:
        out.append(("", path, f"{LABEL_UNREAD}: planned, never opened"))
    for s in picked_steps(reg, flow):
        if s["step"] not in taking:
            out.append((s["step"], s["name"], "no part takes part in this step on the map"))
    planned = {r["path"]: r for r in rows(reg / FOLDER / PLAN)}
    covered = [sp for u, t, r in unit_rows(reg)
               for sp in spans(" ".join(v for v in r.values() if isinstance(v, str)))]
    for f in facts(reg):
        if f.get("kind") not in PLACEABLE or f.get("in_test"):
            continue
        p = planned.get(f["file"])
        if p is None or p["status"] != "read":
            continue
        if not any((f["file"].endswith(c) or c.endswith(f["file"])) and lo <= f["line"] <= hi
                   for c, lo, hi in covered):
            out.append(("", f"{f['service']}: {f['kind'].replace('_', ' ')} at {f['file']}:{f['line']}",
                        "the code scanner found this and no row on the map covers it"))
    for r in planned.values():
        if r["status"] != "read":
            out.append(("", f"{r['unit']}: {r['path']}", f"{LABEL_UNREAD}: {r['reason']}"))
    return out


def draw(reg, flow, ws=None):
    reg, ws = pathlib.Path(reg), workspace(reg, ws)
    problems, notes = check(reg, flow, ws)
    if problems:
        raise ValueError("; ".join(problems))
    table = [{"unit": u, "table": t, "row": r.get("row_id", ""), "step": r.get("step") or r.get("step_hint") or "",
              "what": r.get("operation") or r.get("name") or r.get("activity") or r.get("subject_id") or "",
              "cite": r.get("source") or "", "label": LABEL_READ, "note": ""} for u, t, r in unit_rows(reg)]
    table += [{"unit": "", "table": "", "row": "", "step": st, "what": what, "cite": "",
               "label": (LABEL_UNREAD if why.startswith(LABEL_UNREAD) else
                         LABEL_NOT_CHECKED if why.startswith(LABEL_NOT_CHECKED) else LABEL_GAP), "note": why}
              for st, what, why in gaps(reg, flow, ws)]
    table += [{"unit": "", "table": "", "row": "", "step": "", "what": n, "cite": "", "label": "spelling",
               "note": "reported, not refused"} for n in notes]
    write(reg / FOLDER / "map.csv", table, ["unit", "table", "row", "step", "what", "cite", "label", "note"])
    (reg / PAGE).write_text(page(reg, flow, table), encoding="utf-8")
    return summary(reg, flow, table)


def page(reg, flow, table):
    E = html.escape
    parts = []
    picked = {s["step"] for s in picked_steps(reg, flow)}
    for s in flow_steps(reg, flow):
        if s["step"] not in picked:
            parts.append(f"<section><h3>Step {E(s['step'])} ({E(s['stage'])}): {E(s['name'])}</h3>"
                         f"<p class='why'><b>{E(LABEL_UNPICKED)}</b>: its stage was left mapped only, so it is mapped "
                         f"at the service level and no code was read for it.</p></section>")
            continue
        mine = [r for r in table if s["step"] in [x.strip() for x in re.split(r"[;,]", r["step"] or "")]]
        items = "".join(f"<li class='{'gap' if r['label'] != LABEL_READ else ''}'><b>{E(r['label'])}</b>: "
                        f"{E(r['what'])}" + (f" <code>{E(r['cite'])}</code>" if r["cite"] else "")
                        + (f" <span class='why'>{E(r['note'])}</span>" if r["note"] else "") + "</li>" for r in mine)
        parts.append(f"<section><h3>Step {E(s['step'])} ({E(s['stage'])}): {E(s['name'])}</h3>"
                     f"<ul>{items or '<li>nothing</li>'}</ul></section>")
    other = [r for r in table if r["label"] != LABEL_READ and not r["step"]]
    rest = "".join(f"<li class='gap'><b>{E(r['label'])}</b>: {E(r['what'])} <span class='why'>{E(r['note'])}</span></li>"
                   for r in other)
    views = '<a href="views.html">The map\'s views</a> &middot; ' if (pathlib.Path(reg) / "views.html").is_file() else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Fast map, flow {E(flow)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;line-height:1.45}}
.note{{background:#fff7e0;border:1px solid #e8c66a;padding:10px 14px;border-radius:6px}}
li.gap{{color:#9a4b00}} code{{font-size:12px}} .why{{color:#6b6b6b}}</style></head><body>
<p><a href="index.html">Home</a> &middot; {views}<a href="operator.html">Run status</a></p>
<h1>Fast map of flow {E(flow)}</h1>
<p class="note">{E(NOT_DONE)}</p>
<p>{E(summary(reg, flow, table))}</p>
{''.join(parts)}
<section><h3>Not on this map, or not read</h3><ul>{rest or '<li>nothing listed</li>'}</ul></section>
</body></html>
"""


def summary(reg, flow, table=None):
    if table is None:
        table = rows(pathlib.Path(reg) / FOLDER / "map.csv")
    n = lambda lab: sum(r["label"] == lab for r in table)  # noqa: E731
    return (f"{n(LABEL_READ)} rows read in one pass, {n(LABEL_UNREAD)} files not read, {n(LABEL_GAP)} gaps, "
            f"{n('spelling')} names spelled differently in their code")


def main(argv):
    ws = None
    if "--ws" in argv:
        i = argv.index("--ws")
        ws = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 3 or argv[0] not in ("plan", "check", "draw", "summary"):
        print(__doc__)
        return 2
    cmd, reg, flow = argv[0], pathlib.Path(argv[1]), argv[2]
    if cmd in ("plan", "draw"):
        import run_lock  # the register is written by one run at a time
        run_lock.guard(reg)
    if cmd == "plan":
        print(json.dumps(plan(reg, flow, ws)))
        return 0
    if cmd == "check":
        problems, notes = check(reg, flow, ws)
        print("\n".join(problems + [f"note: {n}" for n in notes]) or "PASSED: every citation resolves")
        return 1 if problems else 0
    if cmd == "draw":
        try:
            print(draw(reg, flow, ws))
        except ValueError as e:
            print(f"REFUSED: the fast map's check fails: {e}", file=sys.stderr)
            return 1
        if (reg / "subjects.csv").is_file():  # the kit's own views, where the merged map allows them
            subprocess.run([sys.executable, str(HERE / "one_canvas.py"), str(reg), str(reg / "views.html")],
                           capture_output=True)
        return 0
    print(summary(reg, flow))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
