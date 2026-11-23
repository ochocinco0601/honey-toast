"""The runs in the work folder: the page at the root of the workspace's work folder, drawn by the listener on each
request from the folder's files, so what the person sees moves on with no model step.

One row per run, newest start first: each register, and each run's start folder that has not led to a register yet,
named by its application and its start time, with the links to that run's own pages. It never picks a run: two runs
in one work folder are two rows, and every link on a run's row carries that run's folder. Before any run exists, that
the run is starting. It carries a stamp of what it shows and checks its own address, reloading when the stamp changes.
Python standard library only."""
import datetime
import hashlib
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import brief  # noqa: E402
import sources_page  # noqa: E402

TITLE = "Runs in this work folder"
FOR = ("Every run in this work folder, newest first, each with its own pages. Open a run's Run status to see where it "
       "stands; when it waits on you, open its Home, where you answer what it asks.")
STARTING = f"{brief.STATUS_LEAD} Starting · Nothing read yet · Next: a first look over the system · Waiting on you: nothing"
WATCH = """<script>
(function () {
  if (!window.fetch) return;
  var own = document.querySelector('meta[name="drawn"]').content;
  function check() {
    fetch(location.pathname, { cache: 'no-store' }).then(function (r) { return r.text(); }).then(function (t) {
      var m = /<meta name="drawn" content="([0-9a-f]+)">/.exec(t);
      if (m && m[1] !== own) location.reload(); else setTimeout(check, 3000);
    }, function () { setTimeout(check, 15000); });
  }
  setTimeout(check, 3000);
})();
</script>"""
LOCAL_TIME = ("<script>document.querySelectorAll('time[datetime]').forEach(function(el){var d=new Date("
              "el.getAttribute('datetime'));if(!isNaN(d))el.textContent=d.toLocaleString([],{weekday:'short',"
              "day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',timeZoneName:'short'})});</script>")

LABEL = brief.STATUS_LEAD.strip("*")
RUN_DIR = "_start-"  # start.RUN_DIR: one run's own folder before its register exists


def shown(line):
    """The status line as HTML: its leading label, written in the chat's bold markup, drawn bold; the rest escaped as
    written, so a `**` in a flow or stage name stays as it is."""
    if line.startswith(brief.STATUS_LEAD):
        return f"<strong>{html.escape(LABEL)}</strong>{html.escape(line[len(brief.STATUS_LEAD):])}"
    return html.escape(line)


def runs(site):
    """The run folders under the work folder, the work folder itself included when it is one, newest first."""
    site = pathlib.Path(site)
    found = [d for d in [site] + [p for p in site.iterdir() if p.is_dir()] if (d / "RUN.md").is_file()]
    return sorted(found, key=lambda d: (d / "RUN.md").stat().st_mtime, reverse=True)


def _json(p):
    try:
        d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _started(text):
    try:
        t = datetime.datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else None


def _led_to(start_dir):
    """The register a run's start folder led to, or None while it has none."""
    r = _json(pathlib.Path(start_dir) / "run-started.json").get("register")
    return pathlib.Path(r).resolve() if r and (pathlib.Path(r) / "RUN.md").is_file() else None


def listed(site):
    """[(folder, kind, name, started)] for every run in the work folder, newest start first: each register ("register"),
    and each run's start folder that has not led to a register yet ("start"). Never a pick between them."""
    import operator_page as op
    site = pathlib.Path(site).resolve()
    starts = [d for d in site.iterdir() if d.is_dir() and d.name.startswith(RUN_DIR)]
    out = []
    for reg in runs(site):
        began = op.started_at(reg)
        out.append((reg, "register", op.capability(reg, _json(reg / "depth.json")),
                    began if began is not None and began.tzinfo else None))
    for d in starts:
        rec = _json(d / "run-started.json")
        sb = op.said_back(d)
        if _led_to(d) is not None or not (rec or sb):
            continue
        named = next((x.get("value") for x in (sb or {}).get("lines") or []
                      if isinstance(x, dict) and x.get("label") == "Application" and x.get("value")), None)
        out.append((d, "start", named or "Not named yet", _started(rec.get("started"))))

    def key(r):
        if r[3] is not None:
            return r[3].timestamp()
        p = r[0] / ("RUN.md" if r[1] == "register" else "run-started.json")
        return p.stat().st_mtime if p.is_file() else 0.0
    return sorted(out, key=key, reverse=True)


def render(site):
    import operator_page as op
    site = pathlib.Path(site).resolve()
    rows = []
    for folder, kind, name, began in listed(site):
        rel = html.escape("" if folder == site else folder.name + "/")
        if kind == "register":
            try:
                line = brief.status(folder)
            except Exception:  # noqa: BLE001 - a record mid-write: show the folder, the next request draws it whole
                line = "Updating"
        else:
            line = (f"{brief.STATUS_LEAD} Starting · Waiting on you: say back what to map" if op.said_back(folder)
                    else f"{brief.STATUS_LEAD} Starting")
        links = [f'<a href="{rel}operator.html">Run status</a>']
        if (folder / "index.html").is_file():
            links.insert(0, f'<a href="{rel}index.html">Home</a>')
        try:
            has_sources = kind == "register" and sources_page.has_any(folder)
        except Exception:  # noqa: BLE001 - a list that cannot be read never takes the page down; the link is drawn
            has_sources = True
        if has_sources:
            links.append(f'<a href="{rel}sources.html">Sources</a>')
        try:
            import progress  # while a flow is mapped, the last part of the map written, as the chat said it
            moving = progress.latest(folder) if kind == "register" else ""
        except Exception:  # noqa: BLE001
            moving = ""
        moving = f'<br><span class="mv">{html.escape(moving)}</span>' if moving else ""
        when = f" · started {op.stamp(began)}" if began else ""
        rows.append(f'<li><span class="nm">{html.escape(name)}</span> <span class="fd">{html.escape(folder.name)}'
                    f'{when}</span><br><span class="st">{shown(line)}</span>{"".join(links)}{moving}</li>')
    body = f'<ul>{"".join(rows)}</ul>' if rows else f'<p class="st">{shown(STARTING)}</p>'
    page = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{TITLE}</title>"
            "<style>body{font:15px/1.5 system-ui,sans-serif;margin:24px;background:#FBFAF7;color:#1D1D1B}"
            "ul{padding-left:18px}li{margin:0 0 12px}.nm{font-weight:700;font-size:17px}.fd{color:#5A5850}"
            ".st{font-weight:600}a{margin-left:8px}</style></head>"
            f'<body><h1>{TITLE}</h1><p class="for">{html.escape(FOR)}</p>{body}{LOCAL_TIME}{WATCH}</body></html>')
    stamp = hashlib.sha256(page.encode("utf-8")).hexdigest()[:16]
    return page.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><meta name="drawn" content="{stamp}">', 1)
