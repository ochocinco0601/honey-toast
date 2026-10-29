"""The run at work: the page at the root of the workspace's work folder, drawn by the listener on each request from
the folder's files, so what the person sees moves on with no model step.

A minimal page for now: per run folder under the work folder (newest first), the run's status line and a link to its
home screen once one is drawn; before any run folder exists, that the run is starting. It carries a stamp of what it
shows and checks its own address, reloading when the stamp changes. Python standard library only."""
import hashlib
import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import brief  # noqa: E402
import sources_page  # noqa: E402

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


def runs(site):
    """The run folders under the work folder, the work folder itself included when it is one, newest first."""
    site = pathlib.Path(site)
    found = [d for d in [site] + [p for p in site.iterdir() if p.is_dir()] if (d / "RUN.md").is_file()]
    return sorted(found, key=lambda d: (d / "RUN.md").stat().st_mtime, reverse=True)


def home(site):
    """The address of the newest run's home screen once one is drawn, else None: the listener sends the work page's
    address there, so the open page reaches the home by itself."""
    site = pathlib.Path(site).resolve()
    for reg in runs(site):
        if (reg / "index.html").is_file():
            return "/" + ("" if reg == site else reg.name + "/") + "index.html"
    return None


def render(site):
    site = pathlib.Path(site).resolve()
    rows = []
    for reg in runs(site):
        try:
            line = brief.status(reg)
        except Exception:  # noqa: BLE001 - a record mid-write: show the folder, the next request draws it whole
            line = "Updating"
        rel = "" if reg == site else reg.name + "/"
        link = (f' <a href="/{html.escape(rel)}index.html">Home</a>' if (reg / "index.html").is_file() else "")
        try:
            listed = sources_page.has_any(reg)
        except Exception:  # noqa: BLE001 - a list that cannot be read never takes the page down; the link is drawn
            listed = True
        if listed:
            link += f' <a href="/{html.escape(rel)}sources.html">Sources</a>'
        rows.append(f'<li><span class="st">{html.escape(line)}</span>{link}</li>')
    body = f'<ul>{"".join(rows)}</ul>' if rows else f'<p class="st">{html.escape(STARTING)}</p>'
    page = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>The run at work</title>"
            "<style>body{font:15px/1.5 system-ui,sans-serif;margin:24px;background:#FBFAF7;color:#1D1D1B}"
            "ul{padding-left:18px}.st{font-weight:600}a{margin-left:8px}</style></head>"
            f"<body><h1>The run at work</h1>{body}{WATCH}</body></html>")
    stamp = hashlib.sha256(page.encode("utf-8")).hexdigest()[:16]
    return page.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><meta name="drawn" content="{stamp}">', 1)
