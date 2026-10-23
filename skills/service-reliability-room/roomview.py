"""A visual of one service-reliability-room engagement, generated from its state store.

Usage:
  python -I roomview.py STATE_DIR

Writes STATE_DIR/view.html (one self-contained page: inline CSS and SVG, a few lines of inline script, no network
requests) and prints its path. It reads the store through roomstate.py, beside this file, and writes nothing else:
not engagement.json, not log.jsonl, not Beads.

Four panels:
  1. Structure: the capability, its journeys, their components and the components' depends_on, as nodes and lines.
  2. Readiness: journeys x rungs, each cell coloured by its standing. Standing is free text in the store, so the
     colour is the view's reading of its wording (the full text is in the cell's tooltip). A cell whose evidence
     is stale against the source as it is now, or cannot be told, is marked, with the reason in the tooltip.
  3. Board: open work items and asks as cards, in columns by what each waits on. Each card goes to the first column
     that matches: an ask -> a person; in progress; waits on another open item; blocked; ready.
  4. Burn-up: work items and asks closed over time against all of them created, from Beads' dates and the log.
     A forecast line appears only once closures fall on at least 3 distinct days.
"""
import datetime
import html
import importlib.util
import json
import math
import os
import re
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("roomstate", Path(__file__).resolve().parent / "roomstate.py")
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)

RUNG_LABELS = {"understood": "Understood", "health": "Health visible", "alerts": "Alerts reach someone",
               "runbooks": "Runbooks", "learning": "Learning"}
CLASS_LABEL = {"met": "met", "partly": "partly", "notyet": "not yet", "na": "not assessed"}
CLASS_GLYPH = {"met": "✓", "partly": "◐", "notyet": "✕", "na": "?"}
ORDER = {"na": 0, "notyet": 1, "partly": 2, "met": 3}


def e(v):
    return html.escape("" if v is None else str(v), quote=True)


def day(v):
    """The date part of a bd timestamp or a log date, or None."""
    if isinstance(v, str) and len(v) >= 10 and rs.is_date(v[:10]):
        return v[:10]
    return None


def short(text, n):
    text = "" if text is None else str(text)
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------- reading the standings ----------

QUALIFIERS = ("not ", "blank", "unrehearsed", "disabled", "partial", "proposed", "draft", "prepared", "pending",
              "only", "missing", "no ", "unconfirmed", "to do", "todo")


def classify_text(text):
    t = (text or "").strip().lower()
    if not t or t.startswith("not assessed"):
        return "na"
    if re.match(r"^(no|none|not|nothing|missing|absent)\b", t):
        return "notyet"
    if re.search(r"\b(met|meets|done|in place|live|deployed|complete|completed)\b", t) and \
            not any(q in t for q in QUALIFIERS):
        return "met"
    return "partly"


def classify(eng, journey, rung, seen=None):
    """The view's reading of a standing's wording; 'as J1' takes J1's cell for the same rung."""
    st = (journey.get("rungs") or {}).get(rung)
    if not isinstance(st, dict):
        return "na", None
    if st.get("level"): return {"not_started": "notyet", "partly": "partly", "met": "met", "not_assessed": "na"}.get(st["level"], "na"), None
    text = st.get("standing") or ""
    ids = {j.get("id"): j for j in eng.get("journeys", []) if isinstance(j, dict)}
    m = re.search(r"\b(?:standing\s+)?as\s+([A-Za-z0-9_.-]+)\b", text)
    if m and m.group(1) in ids and m.group(1) != journey.get("id"):
        seen = (seen or set()) | {journey.get("id")}
        if m.group(1) not in seen:
            cls, _ = classify(eng, ids[m.group(1)], rung, seen)
            return cls, m.group(1)
    return classify_text(text), None


# ---------- gathering ----------

def gather(state_dir):
    eng = rs.load(state_dir)
    for key in ("sources", "components", "journeys", "published"):
        if not isinstance(eng.get(key), list):
            eng[key] = []
    log = [x for _, x in rs.read_log(state_dir) if isinstance(x, dict)]
    try:
        items, bd_error = rs.bd_items(state_dir), None
    except (RuntimeError, json.JSONDecodeError) as ex:
        items, bd_error = [], str(ex)
    items = [i for i in items if "refused" not in rs.labels(i)]
    checker = rs.EvidenceChecker(state_dir, eng)
    return eng, log, items, bd_error, checker


def evidence_marks(checker, evidence):
    """[(state, source, ref, note)] for every piece of evidence; state current|stale|cannot tell|by hand."""
    out = []
    for ev in evidence or []:
        if not isinstance(ev, dict):
            continue
        try:
            state, note = checker.status(ev)
        except Exception as ex:  # a broken source must not stop the view
            state, note = "cannot tell", f"could not be checked ({ex})"
        out.append((state, ev.get("source"), ev.get("ref"), note))
    return out


def worst_mark(marks):
    states = {m[0] for m in marks}
    return "stale" if "stale" in states else "cannot" if "cannot tell" in states else None


# ---------- panel 1: structure ----------

def structure_svg(eng, cells):
    journeys = [j for j in eng["journeys"] if isinstance(j, dict)]
    comps = [c for c in eng["components"] if isinstance(c, dict)]
    if not journeys and not comps:
        return '<p class="empty">No journeys or components recorded yet.</p>'
    cid = {c.get("id"): c for c in comps}
    depended = {d for c in comps for d in (c.get("depends_on") or []) if d in cid}
    level = {}

    def lvl(c_id, stack=()):
        if c_id in level:
            return level[c_id]
        if c_id in stack:
            return 0
        parents = [c.get("id") for c in comps if c_id in (c.get("depends_on") or [])]
        level[c_id] = 0 if not parents else 1 + max(lvl(p, stack + (c_id,)) for p in parents)
        return level[c_id]

    for c in comps:
        lvl(c.get("id"))
    rows = [[{"kind": "cap", "id": "__cap", "label": eng.get("capability") or "(capability not named yet)"}]]
    if journeys:
        rows.append([{"kind": "journey", "id": j.get("id"), "label": f"{j.get('id')} {j.get('name') or ''}", "j": j}
                     for j in journeys])
    for n in range(max(level.values(), default=-1) + 1):
        rows.append([{"kind": "comp", "id": c.get("id"), "label": c.get("id"), "c": c}
                     for c in comps if level.get(c.get("id")) == n])
    W, H, GX, GY, PAD = 150, 54, 18, 56, 12
    width = max(len(r) for r in rows) * (W + GX) - GX + 2 * PAD
    width = max(width, 320)
    height = len(rows) * (H + GY) - GY + 2 * PAD + 22
    pos = {}
    for ri, row in enumerate(rows):
        rw = len(row) * (W + GX) - GX
        x0 = (width - rw) / 2
        for ni, node in enumerate(row):
            pos[node["id"]] = (x0 + ni * (W + GX), PAD + ri * (H + GY))
    out = [f'<svg class="struct" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" '
           f'role="img" aria-label="Structure of {e(eng.get("capability"))}">',
           '<defs><marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" '
           'orient="auto"><path d="M0,0L8,4L0,8z" class="arrowhead"/></marker></defs>']

    def bottom(i):
        x, y = pos[i]
        return x + W / 2, y + H

    def top(i):
        x, y = pos[i]
        return x + W / 2, y

    for j in journeys:
        if "__cap" in pos and j.get("id") in pos:
            (x1, y1), (x2, y2) = bottom("__cap"), top(j.get("id"))
            out.append(f'<line class="tie" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>')
    if not journeys:
        for c in comps:
            if level.get(c.get("id")) == 0:
                (x1, y1), (x2, y2) = bottom("__cap"), top(c.get("id"))
                out.append(f'<line class="tie" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>')
    for c in comps:
        for d in c.get("depends_on") or []:
            if d in pos and c.get("id") in pos:
                (x1, y1), (x2, y2) = bottom(c.get("id")), top(d)
                if y2 <= y1:  # a cycle or same level: curve round the side
                    x1, y1 = pos[c.get("id")][0] + W, pos[c.get("id")][1] + H / 2
                    x2, y2 = pos[d][0] + W, pos[d][1] + H / 2
                    out.append(f'<path class="dep" d="M{x1:.0f},{y1:.0f} C{x1 + 40:.0f},{y1:.0f} {x2 + 40:.0f},'
                               f'{y2:.0f} {x2 + 4:.0f},{y2:.0f}" marker-end="url(#ar)"><title>{e(c.get("id"))} '
                               f'depends on {e(d)}</title></path>')
                else:
                    out.append(f'<line class="dep" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2 - 2:.0f}" '
                               f'marker-end="url(#ar)"><title>{e(c.get("id"))} depends on {e(d)}</title></line>')
    for row in rows:
        for node in row:
            x, y = pos[node["id"]]
            if node["kind"] == "cap":
                tip = eng.get("intent") or ""
                out.append(f'<g><title>{e(node["label"])}\n{e(tip)}</title>'
                           f'<rect class="n-cap" x="{x:.0f}" y="{y:.0f}" width="{W}" height="{H}" rx="6"/>'
                           f'<text class="t-cap" x="{x + W / 2:.0f}" y="{y + 32:.0f}">{e(short(node["label"], 22))}'
                           f'</text></g>')
            elif node["kind"] == "journey":
                j = node["j"]
                classes = [cells[(j.get("id"), r)]["cls"] for r in rs.RUNGS if (j.get("id"), r) in cells]
                assessed = [c for c in classes if c != "na"]
                worst = min(assessed, key=lambda c: ORDER[c]) if assessed else "na"
                tip = f"{j.get('id')} {j.get('name') or ''}\nworst assessed rung: {CLASS_LABEL[worst]}" + \
                      f"\nnot assessed: {classes.count('na')} of {len(classes)} rungs" + \
                      ("\nincludes a judgment step" if j.get("judgment_step") else "")
                out.append(f'<g><title>{e(tip)}</title><rect class="n-j s-{worst}" x="{x:.0f}" y="{y:.0f}" '
                           f'width="{W}" height="{H}" rx="6"/><text class="t-j" x="{x + W / 2:.0f}" '
                           f'y="{y + 32:.0f}">{e(short(node["label"], 21))}</text></g>')
            else:
                c = node["c"]
                tip = f"{c.get('id')}: {c.get('name') or ''}\nowner: {c.get('owner') or 'not recorded'}" + \
                      (f"\ndepends on: {', '.join(c.get('depends_on'))}" if c.get("depends_on") else "")
                out.append(f'<g><title>{e(tip)}</title><rect class="n-c" x="{x:.0f}" y="{y:.0f}" width="{W}" '
                           f'height="{H}" rx="6"/><text class="t-c" x="{x + W / 2:.0f}" y="{y + 16:.0f}">'
                           f'{e(short(c.get("id"), 20))}</text><text class="t-c2" x="{x + W / 2:.0f}" '
                           f'y="{y + 31:.0f}">{e(short(c.get("name"), 24))}</text><text class="t-c3" '
                           f'x="{x + W / 2:.0f}" y="{y + 45:.0f}">owner: {e(short(c.get("owner") or "not recorded", 18))}'
                           f'</text></g>')
    out.append("</svg>")
    return "".join(out)


# ---------- panel 2: readiness grid ----------

def build_cells(eng, items, checker):
    cells = {}
    open_work = [i for i in items if not rs.is_ask(i) and i.get("status") != "closed"]
    for j in eng["journeys"]:
        if not isinstance(j, dict):
            continue
        for r in rs.RUNGS:
            st = (j.get("rungs") or {}).get(r)
            cls, via = classify(eng, j, r)
            marks = evidence_marks(checker, st.get("evidence")) if isinstance(st, dict) else []
            work = [i for i in open_work if rs.label_value(i, "journey") == j.get("id")
                    and rs.label_value(i, "rung") == r]
            cells[(j.get("id"), r)] = {"cls": cls, "via": via, "st": st if isinstance(st, dict) else None,
                                      "marks": marks, "mark": worst_mark(marks), "work": work}
    return cells


def cell_tip(j, r, cell):
    st = cell["st"]
    lines = [f"{j.get('id')} · {RUNG_LABELS[r]} · {CLASS_LABEL[cell['cls']]}"
             + (f" (as {cell['via']})" if cell["via"] else "")]
    if not st:
        lines.append("No standing recorded: not assessed.")
    else:
        lines.append(f"Standing: {st.get('standing')}")
        lines.append(f"Bar: {st.get('bar')}")
        lines.append(f"As of: {st.get('as_of')}")
        for state, src, ref, note in cell["marks"]:
            lines.append(f"Evidence {src} ({ref}): {state.upper() if state in ('stale', 'cannot tell') else state}"
                         + (f": {note}" if note else ""))
    if cell["work"]:
        lines.append(f"Open work ({len(cell['work'])}): " + "; ".join(f"{i['id']} {i.get('title')}" for i in cell["work"]))
    return "\n".join(lines)


def grid_html(eng, cells):
    journeys = [j for j in eng["journeys"] if isinstance(j, dict)]
    if not journeys:
        return '<p class="empty">No journeys recorded yet, so there is nothing to place on the rungs.</p>'
    out = ['<div class="mxwrap"><div class="mx" role="grid"><span></span>']
    for r in rs.RUNGS:
        out.append(f'<span class="h">{e(RUNG_LABELS[r])}</span>')
    for j in journeys:
        chips = "".join(f'<i class="cchip">{e(c)}</i>' for c in j.get("components") or [])
        out.append(f'<span class="rowh"><b title="{e(j.get("name"))}">{e(j.get("id"))} {e(short(j.get("name"), 28))}'
                   f'</b><span class="chips">{chips}</span></span>')
        for r in rs.RUNGS:
            cell = cells[(j.get("id"), r)]
            mark = cell["mark"]
            badge = f'<em class="wk" aria-label="open work items">{len(cell["work"])}</em>' if cell["work"] else ""
            flag = '<em class="flag f-stale">!</em>' if mark == "stale" else \
                '<em class="flag f-cannot">?</em>' if mark == "cannot" else ""
            tip = cell_tip(j, r, cell)
            out.append(f'<button type="button" class="cell s-{cell["cls"]}{" m-" + mark if mark else ""}" '
                       f'title="{e(tip)}" data-tip="{e(tip)}">{CLASS_GLYPH[cell["cls"]]}{flag}{badge}</button>')
    out.append("</div></div>")
    out.append('<div class="detail" id="detail" aria-live="polite">Hover or tap a cell for its standing, bar and '
               'evidence.</div>')
    return "".join(out)


# ---------- panel 3: board ----------

def board_columns(items):
    by_id = {i["id"]: i for i in items}
    open_items = [i for i in items if i.get("status") != "closed"]
    cols = {"person": [], "in_progress": [], "item": [], "blocked": [], "ready": []}
    for it in sorted(open_items, key=lambda i: (i.get("priority", 9), i["id"])):
        waits = [d.get("depends_on_id") for d in it.get("dependencies") or []
                 if by_id.get(d.get("depends_on_id"), {}).get("status") != "closed"]
        if rs.is_ask(it):
            cols["person"].append((it, waits))
        elif it.get("status") == "in_progress":
            cols["in_progress"].append((it, waits))
        elif waits:
            cols["item"].append((it, waits))
        elif it.get("status") == "blocked":
            cols["blocked"].append((it, waits))
        else:
            cols["ready"].append((it, waits))
    return cols, by_id


def card(it, waits, by_id, checker, ask=False, blocks=0, main=False):
    m = rs.meta(it)
    place = "/".join(x for x in (rs.label_value(it, "journey"), rs.label_value(it, "rung")) if x)
    tags = sorted(rs.labels(it) & {"in-review", "walked", "triage"})
    marks = evidence_marks(checker, m.get("evidence")) if not ask else []
    mark = worst_mark(marks)
    tip = [f"{it['id']} ({it.get('status')})", it.get("title") or ""]
    for state, src, ref, note in marks:
        if state in ("stale", "cannot tell"):
            tip.append(f"Evidence {src} ({ref}): {state}: {note}")
    parts = [f'<div class="card{" m-" + mark if mark else ""}{" main" if main else ""}" title="{e(chr(10).join(tip))}">',
             f'<div class="ct">{e(it.get("title"))}</div><div class="cm"><code>{e(it["id"])}</code>']
    if place:
        parts.append(f' <span class="pl">{e(place)}</span>')
    for t in tags:
        parts.append(f' <span class="tg">{e(t)}</span>')
    if mark:
        label = {"stale": "stale evidence", "cannot": "evidence: cannot tell"}[mark]
        parts.append(f' <span class="tg t-{mark}">{label}</span>')
    parts.append("</div>")
    if ask:
        asked = m.get("asked") or day(it.get("created_at")) or ""
        if main:
            parts.append('<div class="mb">main blocker</div>')
        parts.append(f'<div class="cs">asked of <b>{e(it.get("assignee") or "not recorded")}</b>, {e(asked)}</div>')
        parts.append(f'<div class="cw">blocks {blocks} item{"" if blocks == 1 else "s"}</div>')
    else:
        parts.append(f'<div class="cs">seat: <b>{e(it.get("assignee") or "unassigned")}</b></div>')
        parts.append(f'<div class="co">output: {e(m.get("output") or "none recorded")}</div>')
    for w in waits:
        dep = by_id.get(w)
        if dep is None:
            parts.append(f'<div class="cw">waits on {e(w)}</div>')
        else:
            who = f" (an ask, with {dep.get('assignee') or '?'})" if rs.is_ask(dep) else f" ({dep.get('status')})"
            parts.append(f'<div class="cw">waits on <code>{e(w)}</code> {e(short(dep.get("title"), 70))}{e(who)}</div>')
    parts.append("</div>")
    return "".join(parts)


def board_html(items, bd_error, checker):
    if bd_error:
        return f'<p class="empty">Beads could not be read, so no work items are shown: {e(bd_error)}</p>'
    cols, by_id = board_columns(items)
    heads = [("person", "Waits on a person", "open asks, by who was asked"),
             ("item", "Waits on another item", "an open dependency"),
             ("blocked", "Blocked", "no open dependency recorded"),
             ("in_progress", "In progress", "with its seat"),
             ("ready", "Ready", "open, nothing to wait on")]
    out = ['<div class="board">']
    for key, title, sub in heads:
        group = cols[key]
        out.append(f'<div class="col c-{key}"><h3>{e(title)} <span>{len(group)}</span></h3><p class="csub">{e(sub)}</p>')
        if not group:
            out.append('<p class="none">none</p>')
        if key == "person":
            people = {}
            for it, waits in group:
                people.setdefault(it.get("assignee") or "?", []).append((it, waits))
            blocks = {it["id"]: sum(1 for o in items if o.get("status") != "closed" and it["id"] in
                                   {d.get("depends_on_id") for d in o.get("dependencies") or []}) for it, _ in group}
            top = max(blocks.values(), default=0)
            main_id = next((i for i, n in blocks.items() if n == top), None) if top else None
            for who in sorted(people):
                out.append(f'<div class="who">{e(who)} <span>{len(people[who])}</span></div>')
                out += [card(it, waits, by_id, checker, ask=True, blocks=blocks[it["id"]], main=it["id"] == main_id)
                        for it, waits in sorted(people[who], key=lambda x: -blocks[x[0]["id"]])]
        else:
            out += [card(it, waits, by_id, checker) for it, waits in group]
        out.append("</div>")
    out.append("</div>")
    return "".join(out)


# ---------- panel 4: burn-up ----------

def burn_series(items, log):
    first_ref, closed_log = {}, {}
    for x in log:
        d = day(x.get("date"))
        if not d:
            continue
        for ref in x.get("refs") or []:
            first_ref.setdefault(ref, d)
        m = re.match(r"bd close (.+?)(?::|$)", x.get("text") or "")
        if m and x.get("by") == "roomstate.py":
            for i in m.group(1).split(","):
                closed_log.setdefault(i.strip(), d)
    starts, ends = {}, {}
    for it in items:
        cands = [d for d in (day(it.get("created_at")), first_ref.get(it["id"])) if d]
        if not cands:
            continue
        starts[it["id"]] = min(cands)
        if it.get("status") == "closed":
            c = closed_log.get(it["id"]) or day(it.get("closed_at")) or day(it.get("updated_at"))
            if c:
                ends[it["id"]] = max(c, starts[it["id"]])
    return starts, ends


def burn_svg(items, log):
    starts, ends = burn_series(items, log)
    if not starts:
        return '<p class="empty">No work items or asks yet, so there is nothing to burn up.</p>', ""
    log_days = [d for d in (day(x.get("date")) for x in log) if d]
    d0 = min(list(starts.values()) + log_days)
    d1 = max(list(starts.values()) + list(ends.values()) + log_days)
    D = lambda s: datetime.date.fromisoformat(s)
    span = (D(d1) - D(d0)).days
    days = [(D(d0) + datetime.timedelta(n)).isoformat() for n in range(span + 1)]
    scope = [sum(1 for s in starts.values() if s <= d) for d in days]
    done = [sum(1 for s in ends.values() if s <= d) for d in days]
    close_days = sorted(set(ends.values()))
    forecast = None
    if len(close_days) >= 3:
        xs = [(D(d) - D(d0)).days for d in close_days]
        ys = [sum(1 for s in ends.values() if s <= d) for d in close_days]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        den = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0
        if slope > 0 and scope[-1] > done[-1]:
            need = (scope[-1] - done[-1]) / slope
            forecast = (span, done[-1], span + need, scope[-1], slope)
    total_x = forecast[2] if forecast else span
    total_x = max(total_x, 1)
    ymax = max(scope + [1])
    L, R, T, B = 40, 530, 34, 210  # room on the right and top for the labels
    W = R - L
    X = lambda v: L + (v / total_x) * W if span or forecast else L + W / 2
    Y = lambda v: B - (B - T) * v / ymax
    out = [f'<svg class="burn" viewBox="0 0 640 250" width="640" height="250" role="img" '
           f'aria-label="Burn-up: {done[-1]} of {scope[-1]} closed">']
    step = max(1, round(ymax / 4))
    for v in list(range(0, ymax + 1, step)) + ([ymax] if ymax % step else []):
        out.append(f'<line class="gl" x1="{L}" x2="{R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text class="ax" x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    out.append(f'<line class="axis" x1="{L}" x2="{R}" y1="{B}" y2="{B}"/>')

    def path(series):
        if not span:
            return None
        pts = []
        for n, v in enumerate(series):
            if n:
                pts.append(f"L{X(n):.1f},{Y(series[n - 1]):.1f}")
            pts.append(f"{'M' if not n else 'L'}{X(n):.1f},{Y(v):.1f}")
        return "".join(pts)

    if span:
        out.append(f'<path class="scope" d="{path(scope)}"/><path class="done" d="{path(done)}"/>')
        every = max(1, math.ceil(48 * total_x / W))  # at least 48px between date labels
        for n in range(0, span + 1, every):
            d = days[n]
            out.append(f'<text class="ax" x="{X(n):.1f}" y="{B + 16}" text-anchor="middle">{e(d[5:])}</text>')
    else:
        bw = 60
        x = X(0) - bw / 2
        out.append(f'<rect class="b-scope" x="{x:.0f}" y="{Y(scope[0]):.1f}" width="{bw}" height="{B - Y(scope[0]):.1f}"/>'
                   f'<rect class="b-done" x="{x:.0f}" y="{Y(done[0]):.1f}" width="{bw}" height="{B - Y(done[0]):.1f}"/>'
                   f'<text class="ax" x="{X(0):.0f}" y="{B + 16}" text-anchor="middle">{e(days[0])}</text>')
    lx = X(span) if span else X(0) + 36
    out.append(f'<text class="lbl" x="{lx + 6:.1f}" y="{Y(scope[-1]) - 4:.1f}">{scope[-1]} in scope</text>'
               f'<text class="lbl ld" x="{lx + 6:.1f}" y="{Y(done[-1]) + 14:.1f}">{done[-1]} closed</text>')
    if forecast:
        x0, y0, x1, y1, slope = forecast
        when = (D(d0) + datetime.timedelta(days=round(x1))).isoformat()
        out.append(f'<line class="fc" x1="{X(x0):.1f}" y1="{Y(y0):.1f}" x2="{X(x1):.1f}" y2="{Y(y1):.1f}"/>'
                   f'<text class="lbl" x="{X(x1):.1f}" y="{Y(y1) - 10:.1f}" text-anchor="end">at {slope:.1f}/day: '
                   f'{e(when)}, if scope holds</text>')
    out.append("</svg>")
    note = (f"Closures fall on {len(close_days)} distinct day{'s' if len(close_days) != 1 else ''}; "
            + ("the forecast is a straight line through them, to today's scope." if forecast else
               "a forecast line appears once there are at least 3." if len(close_days) < 3 else
               "no forecast: the rate is not positive or nothing is left."))
    return "".join(out), note


# ---------- page ----------

CSS = """
:root{--plane:#f4f3ef;--surface:#fcfcfb;--card:#ecebe5;--ink:#0b0b0b;--ink2:#52514e;--muted:#6f6e69;
--grid:#e1e0d9;--axis:#b5b4a9;--ring:rgba(11,11,11,.12);--accent:#2a78d6;--met:#2e9e3e;--partly:#f0b429;
--notyet:#e8775a;--na:#e6e5df;--na-ink:#52514e;--on:#0b0b0b;--hatch:rgba(11,11,11,.16);--stale:#c0187a;
--scope:#6f6e69;--done:#2e9e3e;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--plane:#0d0d0d;--surface:#1a1a19;--card:#262624;
--ink:#f0efec;--ink2:#c3c2b7;--muted:#a3a29a;--grid:#2c2c2a;--axis:#4a4a46;--ring:rgba(255,255,255,.12);
--accent:#3987e5;--na:#2c2c2a;--na-ink:#c3c2b7;--hatch:rgba(255,255,255,.14);--stale:#ff5cb4;--scope:#a3a29a;
--done:#48c35a;color-scheme:dark}}
:root[data-theme="dark"]{--plane:#0d0d0d;--surface:#1a1a19;--card:#262624;--ink:#f0efec;--ink2:#c3c2b7;
--muted:#a3a29a;--grid:#2c2c2a;--axis:#4a4a46;--ring:rgba(255,255,255,.12);--accent:#3987e5;--na:#2c2c2a;
--na-ink:#c3c2b7;--hatch:rgba(255,255,255,.14);--stale:#ff5cb4;--scope:#a3a29a;--done:#48c35a;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--plane);color:var(--ink);font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;
padding:16px 16px 40px}
.wrap{max-width:1280px;margin:0 auto;display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}
header h1{font-size:22px;margin:0 0 4px;text-wrap:balance}
.meta{font-size:12px;color:var(--muted);font-family:ui-monospace,Consolas,monospace;word-break:break-all}
.intent{font-size:13px;color:var(--ink2);margin:6px 0 0;max-width:90ch}
.strip{display:flex;flex-wrap:wrap;gap:10px 24px}
.kpi b{display:block;font:500 20px ui-monospace,Consolas,monospace}.kpi span{font-size:12px;color:var(--ink2)}
.kpi.warn b{color:var(--stale)}
.row{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(min(100%,560px),1fr))}
.panel{background:var(--surface);border:1px solid var(--ring);border-radius:8px;padding:14px 16px;min-width:0}
.panel h2{font-size:15px;margin:0 0 2px}.q{font-size:13px;color:var(--ink2);margin:0 0 10px}
.empty{color:var(--muted);font-style:italic}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12px;color:var(--ink2);margin-top:8px;align-items:center}
.sw{display:inline-flex;align-items:center;gap:6px}
.chip{width:18px;height:18px;border-radius:4px;display:inline-grid;place-items:center;font-size:12px;font-weight:600;
color:var(--on);font-style:normal}
.s-met{background:var(--met)}.s-partly{background:var(--partly)}.s-notyet{background:var(--notyet)}
.s-na{background:var(--na);color:var(--na-ink);background-image:repeating-linear-gradient(45deg,transparent 0 4px,var(--hatch) 4px 5px)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
svg{display:block;max-width:none;height:auto}
svg.burn{width:100%;max-width:760px;min-width:480px}
svg text{fill:var(--ink);font-size:12px}
.n-cap{fill:var(--ink)}.t-cap{fill:var(--surface);font-weight:600;font-size:13px;text-anchor:middle}
.n-j{stroke:var(--surface);stroke-width:2}.n-j.s-met{fill:var(--met)}.n-j.s-partly{fill:var(--partly)}
.n-j.s-notyet{fill:var(--notyet)}.n-j.s-na{fill:var(--na)}
.t-j{text-anchor:middle;font-weight:600;font-size:12px;fill:#0b0b0b}
.n-c{fill:var(--card);stroke:var(--axis)}.t-c{text-anchor:middle;font:600 12px ui-monospace,Consolas,monospace}
.t-c2{text-anchor:middle;font-size:10px;fill:var(--ink2)}.t-c3{text-anchor:middle;font-size:10px;fill:var(--muted)}
.tie{stroke:var(--axis);stroke-width:1.5}.uses{stroke:var(--axis);stroke-width:1.2;stroke-dasharray:2 4}
.dep{stroke:var(--ink2);stroke-width:1.8;fill:none}.arrowhead{fill:var(--ink2)}
.mxwrap{overflow-x:auto;padding:4px}
.mx{display:grid;grid-template-columns:minmax(150px,1.6fr) repeat(5,minmax(58px,1fr));gap:4px;align-items:stretch;min-width:470px}
.mx .h{font-size:12px;color:var(--ink2);text-align:center;line-height:1.15;align-self:end;padding-bottom:4px}
.rowh{font-size:12px;padding-right:6px;display:grid;gap:3px;align-content:center}
.chips{display:flex;flex-wrap:wrap;gap:3px}
.cchip{font:normal 10px ui-monospace,Consolas,monospace;background:var(--card);border-radius:3px;padding:1px 4px;color:var(--ink2)}
.cell{min-height:44px;border-radius:4px;border:0;cursor:pointer;display:grid;place-items:center;font-size:15px;
font-weight:600;color:var(--on);position:relative;font-family:inherit}
.cell.s-na{color:var(--na-ink)}
.cell:focus-visible,.cell.sel{outline:2px solid var(--ink);outline-offset:1px}
.cell.m-stale{box-shadow:inset 0 0 0 3px var(--stale)}
.cell.m-cannot{outline:2px dotted var(--ink2);outline-offset:-4px}
.flag{position:absolute;top:2px;right:4px;font:700 11px ui-monospace,Consolas,monospace;font-style:normal}
.f-stale{color:#fff;background:var(--stale);border-radius:8px;padding:0 5px}
.f-cannot{color:var(--on)}
.wk{position:absolute;bottom:2px;left:4px;font:500 10px ui-monospace,Consolas,monospace;font-style:normal;
background:var(--surface);color:var(--ink);border-radius:6px;padding:0 4px}
.detail{margin-top:10px;font-size:13px;color:var(--ink2);min-height:52px;border-top:1px solid var(--grid);
padding-top:8px;white-space:pre-wrap;overflow-wrap:anywhere}
.board{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
.col{display:grid;gap:6px;align-content:start;padding:8px;border-radius:6px;background:var(--plane)}
.col h3{margin:0;font-size:13px;display:flex;justify-content:space-between}
.col h3 span{font-family:ui-monospace,Consolas,monospace;color:var(--ink2);font-weight:400}
.csub{margin:0;font-size:11px;color:var(--muted)}.none{margin:0;font-size:12px;color:var(--muted)}
.c-person{border-top:3px solid var(--accent)}.c-item{border-top:3px solid var(--axis)}
.c-blocked{border-top:3px solid var(--notyet)}.c-in_progress{border-top:3px solid var(--partly)}
.c-ready{border-top:3px solid var(--met)}
.who{font-size:12px;font-weight:600;margin-top:4px}.who span{color:var(--muted);font-weight:400}
.card{font-size:12px;line-height:1.3;padding:7px 8px;border-radius:5px;background:var(--surface);
border:1px solid var(--ring);display:grid;gap:3px;overflow-wrap:anywhere}
.card.m-stale{border:2px solid var(--stale)}.card.m-cannot{border:1px dotted var(--ink2)}
.card.main{border:2px solid var(--accent)}
.mb{font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--accent)}
.ct{font-weight:600}.cm{color:var(--muted);font-size:11px}
.cm code,.cw code{font-family:ui-monospace,Consolas,monospace}
.pl,.tg{font-size:10px;background:var(--card);border-radius:3px;padding:0 4px;color:var(--ink2)}
.tg.t-stale{background:var(--stale);color:#fff}.cs{color:var(--ink2)}
.co{font:11px ui-monospace,Consolas,monospace;color:var(--muted)}.cw{font-size:11px;color:var(--ink2)}
.gl{stroke:var(--grid)}.axis{stroke:var(--axis)}.ax{fill:var(--muted);font-size:11px}
.scope{stroke:var(--scope);stroke-width:2;fill:none}.done{stroke:var(--done);stroke-width:2.5;fill:none}
.b-scope{fill:var(--card);stroke:var(--axis)}.b-done{fill:var(--done)}
.fc{stroke:var(--done);stroke-width:1.5;stroke-dasharray:5 4}
.lbl{font-size:12px;font-weight:600}.ld{fill:var(--done)}
.ln{display:inline-block;width:18px;height:3px;border-radius:2px}
.foot{font:11px ui-monospace,Consolas,monospace;color:var(--muted);word-break:break-all}
"""

JS = """
(function(){var d=document.getElementById('detail');if(!d)return;var sel=null;
document.querySelectorAll('.cell').forEach(function(b){function show(){d.textContent=b.getAttribute('data-tip')}
b.addEventListener('mouseenter',show);b.addEventListener('focus',show);
b.addEventListener('click',function(){if(sel)sel.classList.remove('sel');sel=b;b.classList.add('sel');show()})})})();
"""


def render(state_dir):
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"  # git status must not rewrite a source repo's index
    eng, log, items, bd_error, checker = gather(state_dir)
    cells = build_cells(eng, items, checker)
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    cap = eng.get("capability") or "(capability not named yet)"
    work = [i for i in items if not rs.is_ask(i)]
    asks = [i for i in items if rs.is_ask(i)]
    open_work = [i for i in work if i.get("status") != "closed"]
    open_asks = [a for a in asks if a.get("status") != "closed"]
    marks = [c["mark"] for c in cells.values()]
    stale, cannot, total = marks.count("stale"), marks.count("cannot"), len(marks)
    burn, burn_note = burn_svg(items, log)
    kpis = [(len(eng["journeys"]), "journeys"), (len(eng["components"]), "components"),
            (len(open_work), "open work items"), (len(open_asks), "open asks"),
            (f"{sum(1 for i in items if i.get('status') == 'closed')}/{len(items)}", "closed of all items")]
    kpi_html = "".join(f'<div class="kpi"><b>{e(v)}</b><span>{e(t)}</span></div>' for v, t in kpis)
    kpi_html += (f'<div class="kpi{" warn" if stale else ""}"><b>{stale} of {total}</b><span>cells stale</span></div>'
                 f'<div class="kpi"><b>{cannot} of {total}</b><span>cells whose evidence cannot be told</span></div>')
    sessions = [x for x in log if x.get("kind") == "session"]
    last = (f'Last session {e(sessions[-1].get("date"))}, {"closed" if sessions[-1].get("closed") else "not closed"}.'
            if sessions else "No session recorded yet.")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(short(cap, 60))}: service reliability room view</title><style>{CSS}</style></head><body><div class="wrap">
<header><h1>{e(cap)}</h1>
<div class="meta">Generated {e(now)}. {last}</div>
{f'<p class="intent">{e(eng.get("intent"))}</p>' if eng.get("intent") else ''}</header>
<section class="panel" aria-label="Summary"><div class="strip">{kpi_html}</div></section>
<section class="panel"><h2>1 · What is open, and what each waits on</h2>
<p class="q">Open work items and asks from Beads. Each card is in the first column that fits: an ask waits on a person; then in progress; then waits on another open item; then blocked; else ready.</p>
{board_html(items, bd_error, checker)}</section>
<div class="row">
<section class="panel"><h2>2 · What the capability is made of</h2>
<p class="q">Capability → journeys → components. Arrows are a component's depends_on; panel 3 lists the components each journey uses. A journey is coloured by its worst assessed rung.</p>
<div class="scroll">{structure_svg(eng, cells)}</div>
<div class="legend"><span class="sw"><svg width="28" height="10"><line class="dep" x1="0" y1="5" x2="22" y2="5" marker-end="url(#ar)"/></svg>depends on</span>
<span>Hover a box for its full name and what it depends on.</span></div></section>
<section class="panel"><h2>3 · Where each journey stands</h2>
<p class="q">Journeys × rungs, with the components each journey uses. The colour is the standing's level; the cell's tooltip has the standing itself. The number in a cell's corner is its open work items.</p>
{grid_html(eng, cells)}
<div class="legend"><span class="sw"><i class="chip s-met">✓</i>met</span><span class="sw"><i class="chip s-partly">◐</i>partly</span>
<span class="sw"><i class="chip s-notyet">✕</i>not yet</span><span class="sw"><i class="chip s-na">?</i>not assessed</span>
<span class="sw"><i class="chip" style="box-shadow:inset 0 0 0 3px var(--stale)"></i>stale: evidence taken at an older version than the source is now</span>
<span class="sw"><i class="chip" style="outline:2px dotted var(--ink2);outline-offset:-4px"></i>cannot tell (no seen value recorded, or the source cannot be read)</span></div></section>
</div>
<section class="panel"><h2>4 · Work items closed</h2>
<p class="q">Readiness history, how each rung's standing changed over time, isn't shown yet. This panel is work items and asks closed over time, against all of them created. Dates are Beads' created and closed dates, moved earlier where the log records an item sooner.</p>
<div class="scroll">{burn}</div>
<div class="legend"><span class="sw"><i class="ln" style="background:var(--scope)"></i>in scope</span>
<span class="sw"><i class="ln" style="background:var(--done)"></i>closed</span><span>{e(burn_note)}</span></div></section>
<footer class="foot">Store: {e(state_dir)}</footer>
</div><script>{JS}</script></body></html>
"""
    return page


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    state_dir = Path(argv[1]).resolve()
    if not (state_dir / "engagement.json").is_file():
        print(f"no engagement.json in {state_dir}", file=sys.stderr)
        return 2
    page = render(state_dir)
    out = state_dir / "view.html"
    tmp = out.with_name("view.html.tmp")
    tmp.write_text(page, encoding="utf-8", newline="\n")
    os.replace(tmp, out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
