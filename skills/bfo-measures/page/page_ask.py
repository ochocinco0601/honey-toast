"""Serve a run's pages to the person, read-only: every question is asked and answered in the chat, never here.

  python -u page_ask.py serve DIR   serve DIR on 127.0.0.1

The stage kit's own copy of the page step's listener. Changes from the page step it comes from:
it serves the folder's own pages read-only (any .html, .css, .js or .svg file under the served folder,
never outside it and never under answers/), so the home screen's links to the run's other pages work; it draws the
work page at the folder's root on each request, from the folder's files (work_page.py); it answers /.alive with the
folder it serves and its process id (also written to listener.pid), so it can be found and stopped; and while a flow
is mapped it draws each run's home screen again as each part of the map is written (progress.py), so the open page
shows the latest line. It takes no answers: nothing is posted to it but the tabs' own open and close notes.
"""
import json, os, pathlib, sys, threading, time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [KIT, os.path.dirname(KIT)]  # the kit's own scripts: beside this one, or one folder up in the kit
PAGES = (".html", ".css", ".js", ".svg")
# Every page served says when its tab is left (pagehide: closed, reloaded or followed a link) and when it is shown
# (pageshow: a fresh load, or the back cache with no request), each with the page's own id, so the old page's close
# and the new page's shown can arrive in either order. A page restored from the back cache keeps its id.
BEACON = (b'<script>(function(){if(!navigator.sendBeacon)return;var id=Math.random().toString(36).slice(2,12);'
          b'addEventListener("pagehide",function(){navigator.sendBeacon("/.closed?id="+id)});'
          b'addEventListener("pageshow",function(){navigator.sendBeacon("/.shown?id="+id)});})();</script>')
# The run status page says the same under its own names, kept apart (listener.status_open), so an open status tab
# makes no second one when the start step runs again, and still never counts as a tab the run leads.
STATUS_BEACON = BEACON.replace(b'"/.closed?id="', b'"/.status-closed?id="').replace(b'"/.shown?id="',
                                                                                     b'"/.status-shown?id="')
STATUS_EVENTS = ("/.status-closed", "/.status-shown")
TAB_EVENTS = ("/.closed", "/.shown") + STATUS_EVENTS
# A run's status page (operator.html) reloads only itself and never moves to the run's home screen, so it is not a
# tab the run can lead: it sends only its own beacons (STATUS_BEACON), and its requests, recorded so an open on it is
# judged by the browser's own request, never count as an open tab (listener.tab_open), so an open status tab never
# stops the kit opening the home screen.
UNLED = ("operator.html",)


def led(bare):
    """Whether a page served at this address is one an open tab follows to the page that asks."""
    return bare.rsplit("/", 1)[-1] not in UNLED
SEEN_LOCK = threading.Lock()


def own_page(site, path):
    """The file one of the folder's pages names, or None. `path` is the raw URL path: decoded here, refused if it
    holds a backslash, an empty, "." or ".." segment, or a drive; then resolved, and served only if the real file is
    inside the folder, outside answers/, and a page by its resolved name."""
    root = pathlib.Path(site).resolve()
    rel = unquote(path.split("?")[0].split("#")[0])
    if not rel.startswith("/") or "\\" in rel or "\x00" in rel:
        return None
    segs = rel[1:].split("/")
    if not segs or any(s in ("", ".", "..") for s in segs) or pathlib.PureWindowsPath(segs[0]).drive or ":" in rel:
        return None
    target = root.joinpath(*segs).resolve()
    try:
        parts = target.relative_to(root).parts
    except ValueError:
        return None  # resolves outside the folder, a link included
    if not parts or parts[0].lower() == "answers" or target.suffix.lower() not in PAGES or not target.is_file():
        return None
    return target


def note_seen(site, path):
    """When each page was last asked for, by address: how the run tells that a browser really has the page open."""
    seen = os.path.join(site, "seen.json")
    with SEEN_LOCK:
        _note(seen, path)


def note_tab(site, event, page):
    """A page shown or left, by the page's own id: the pages shown and not yet left are the tabs open on the
    listener, whatever order their beacons arrive in."""
    seen = os.path.join(site, "seen.json")
    with SEEN_LOCK:
        _note(seen, event, page)


def _note(seen, path, page=None):
    try:
        with open(seen, encoding="utf-8") as f:
            got = json.load(f)
    except (OSError, ValueError):
        got = {}
    got[path] = time.time()
    if page is not None:
        key = "/.statustabs" if path in STATUS_EVENTS else "/.tabs"
        tabs = got.get(key) if isinstance(got.get(key), dict) else {}
        if path in ("/.shown", "/.status-shown"):
            tabs[page] = time.time()
        else:
            tabs.pop(page, None)
        got[key] = tabs
    try:
        tmp = "%s.%d.tmp" % (seen, os.getpid())
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(got, f)
        os.replace(tmp, seen)
    except OSError:
        pass


def _waits(folder):
    """The mtime of the say-back waiting on the person in this folder (operator_page.said_back's test), or None."""
    p = folder / "say-back.json"
    try:
        sb = json.loads(p.read_text(encoding="utf-8"))
        return p.stat().st_mtime if isinstance(sb, dict) and sb.get("state") == "waiting" and sb.get("lines") else None
    except (OSError, ValueError):
        return None


def status_of(site):
    """Where the work folder's own run status address (/operator.html) leads: nowhere while the folder is itself a
    register, whose view the address draws; else the list of runs at the root. It never picks one of several runs: a
    guess by time or by a say-back leads a new run's clicks to an earlier run's pages. A say-back an earlier release left
    at the root (before each run had its start folder) belongs to no run now, and is not drawn."""
    site = pathlib.Path(site).resolve()
    return None if (site / "RUN.md").is_file() else "/"


RUN_DIR = "_start-"  # start.RUN_DIR: one run's own folder before its register exists


def run_leads(site, bare):
    """Where one run's own status address leads once that run has a register: the register's own status page."""
    segs = bare[1:].split("/")
    if len(segs) != 2 or segs[1] != "operator.html" or not segs[0].startswith(RUN_DIR):
        return None
    root = pathlib.Path(site).resolve()
    try:
        reg = pathlib.Path(json.loads((root / segs[0] / "run-started.json").read_text(encoding="utf-8"))["register"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if reg.parent.resolve() != root or not (reg / "RUN.md").is_file():
        return None
    if (root / segs[0] / "say-back.json").is_file() and _waits(root / segs[0]):
        return None  # its say-back still waits on the person: that is where they are needed
    return "/" + reg.name + "/operator.html"


def check_page(site, path):
    """/.check?page=<address>: whether the address answers, following the same redirects the page itself would, as
    JSON {"page", "status", "badge"}. Never counted as the person's tab (no note_seen, no /.tabs)."""
    from urllib.parse import parse_qs, urlsplit
    page = (parse_qs(urlsplit(path).query).get("page") or ["/"])[0]
    page = "/" + page.lstrip("/")
    bare = page.split("?")[0].split("#")[0]
    for _ in range(3):
        to = status_of(site) if bare == "/operator.html" else run_leads(site, unquote(bare))
        if not to:
            break
        bare = to.split("?")[0]
    badge = ""
    if bare == "/.alive":
        status = 200
    else:
        try:
            body = live(site, bare)
        except Exception as e:  # noqa: BLE001
            return json.dumps({"page": bare, "status": 500, "badge": "", "error": str(e)[:200]})
        status = 200 if body is not None or own_page(site, bare) is not None else 404
        if body is not None:
            import re
            m = re.search(rb'<span class="badge [^"]*">.*?</svg>([^<]*)</span>', body)
            badge = m.group(1).decode("utf-8", "replace") if m else ""
    return json.dumps({"page": bare, "status": status, "badge": badge})


def live(site, path):
    """The work page, drawn now from the folder's files, for the folder's root; a run's sources page, drawn now from
    its sources.csv and RUN.md, for <run>/sources.html; a run's operator view, drawn now from its record, for
    <run>/operator.html; else None."""
    bare = unquote(path.split("?")[0].split("#")[0])
    segs = bare[1:].split("/")
    if segs[-1] == "map-so-far.html" and len(segs) == 2 and "\\" not in bare and ":" not in bare and \
            segs[0] not in (".", "..", "answers"):
        run = pathlib.Path(site).resolve() / segs[0]
        if run.is_dir() and (run / "RUN.md").is_file():
            try:
                import partial_map
            except ImportError:
                return None
            return partial_map.render(run).encode("utf-8")  # drawn now, never a file: never the checked map
    if segs[-1] in ("sources.html", "operator.html") and len(segs) <= 2 and "\\" not in bare and ":" not in bare:
        root = pathlib.Path(site).resolve()
        name = segs[0] if len(segs) == 2 else ""
        if name not in (".", "..", "answers"):
            run = root / name if name else root
            if segs[-1] == "operator.html" and run.is_dir() and ((run / "RUN.md").is_file() or not name
                                                                  or name.startswith(RUN_DIR)):
                try:
                    import operator_page
                except ImportError:
                    return None
                # the work folder's own address before a run folder is in it: the first look under way
                return operator_page.render(run, starting=not (run / "RUN.md").is_file()).encode("utf-8")
            if segs[-1] == "sources.html" and run.is_dir() and (run / "sources.csv").is_file():
                try:
                    import sources_page
                except ImportError:
                    return None
                return sources_page.render(run).encode("utf-8")
    if bare not in ("/", "/run.html"):
        return None
    try:
        import work_page
    except ImportError:
        return None
    return work_page.render(site).encode("utf-8")


def not_found(site):
    """The page for an address that does not exist: links to the list of runs and to the home screen of each
    register under the folder (the folder's own, when it is one), so the person is never left on a bare error."""
    from html import escape
    root = pathlib.Path(site).resolve()
    try:
        regs = [root] * (root / "RUN.md").is_file() + sorted(
            d for d in root.iterdir() if d.is_dir() and d.name.lower() != "answers" and (d / "RUN.md").is_file())
    except OSError:
        regs = []
    rows = []
    for reg in regs:
        name = escape(reg.name)
        at = "" if reg == root else reg.name + "/"
        rows.append('<li><a href="/%sindex.html">%s: home screen</a></li>' % (escape(at), name)
                    if (reg / "index.html").is_file() else "<li>%s: home screen not drawn yet</li>" % name)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Page not found</title>'
            '<meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font:16px/1.5 system-ui,'
            'sans-serif;max-width:40rem;margin:2rem auto;padding:0 16px;color:#1d1d1f;background:#fff}'
            '@media (prefers-color-scheme: dark){body{color:#eee;background:#1b1b1d}a{color:#8ab4f8}}</style></head>'
            "<body><h1>This page does not exist</h1><p>The address is not one of the run's pages. Go to:</p><ul>"
            '<li><a href="/">Every run in this work folder</a></li>%s</ul></body></html>' % "".join(rows)).encode("utf-8")


def serve(site):
    # a listener left behind ends after a spell with no request; the next stop starts a fresh one
    idle = float(os.environ.get("BFO_LISTENER_IDLE_SECONDS") or 8 * 3600)
    last = [time.time()]

    class Handler(SimpleHTTPRequestHandler):
        def setup(self):
            last[0] = time.time()
            super().setup()

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def own_host(self):
            # Refuses DNS-rebinding: a foreign site resolved to 127.0.0.1 still sends its own Host.
            return self.headers.get("Host") == "127.0.0.1:%d" % self.server.server_address[1]

        def respond(self, body_too):
            if not self.own_host():
                self.send_error(403)
                return
            # Only the page step's script and the folder's own pages are served: nothing outside the folder,
            # nothing under answers/, and nothing but pages. The file checked is the file served.
            body, bare = None, self.path.split("?")[0].split("#")[0]
            if bare == "/.check":  # a script asking whether a page answers: never counted as the person's tab
                said = check_page(site, self.path).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(said)))
                self.end_headers()
                if body_too:
                    self.wfile.write(said)
                return
            if bare == "/" or bare.endswith(".html"):
                note_seen(site, bare)
            to = status_of(site) if bare == "/operator.html" else run_leads(site, unquote(bare))
            if to:  # a run's start folder's status address leads to its own register's; the work folder's to the list
                self.send_response(302)
                self.send_header("Location", to)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if bare == "/.alive":
                body = ("%s\n%d" % (pathlib.Path(site).resolve(), os.getpid())).encode("utf-8")
                ctype = "text/plain; charset=utf-8"
            elif live(site, self.path) is not None:
                body, ctype = live(site, self.path), "text/html; charset=utf-8"
            else:
                target = own_page(site, self.path)
                if target is None:  # never a bare error: a page that leads to the run status and each home screen
                    page = not_found(site)
                    self.send_response(404)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(page)))
                    self.end_headers()
                    if body_too:
                        self.wfile.write(page)
                    return
                ctype = self.guess_type(str(target))
                ctype += "; charset=utf-8" if ctype.startswith("text/") and "charset" not in ctype else ""
            if body is None:
                body = target.read_bytes()
            if ctype.startswith("text/html"):
                said = BEACON if led(bare) else STATUS_BEACON
                at = body.rfind(b"</body>")
                body = body[:at] + said + body[at:] if at >= 0 else body + said
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body_too:
                self.wfile.write(body)

        def do_GET(self):
            self.respond(True)

        def do_HEAD(self):
            self.respond(False)

        def do_POST(self):
            # Only the page this server served may post; stops other sites posting to localhost.
            own = "http://127.0.0.1:%d" % self.server.server_address[1]
            event, _, query = self.path.partition("?")
            page = query[3:] if query.startswith("id=") else ""
            if (event in TAB_EVENTS and self.own_host() and self.headers.get("Origin") in (own, None)
                    and page.isascii() and page.isalnum() and len(page) <= 32):
                note_tab(site, event, page)
                self.send_response(204)
                self.end_headers()
                return
            self.send_error(403)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=site))
    url = "http://127.0.0.1:%d/" % httpd.server_address[1]
    with open(os.path.join(site, "listener.pid"), "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    with open(os.path.join(site, "url.txt"), "w", encoding="utf-8") as f:
        f.write(url)
    print("READY " + url, flush=True)
    httpd.timeout = min(5.0, idle)
    grace = float(os.environ.get("BFO_LISTENER_END_GRACE_SECONDS") or 120)
    watch, ended_at = RunEnd(site), None
    try:  # the run's watchdog: reads each run's state and tells the person when it stops or finishes
        import watchdog
        dog = watchdog.Watchdog(site)
    except Exception:  # noqa: BLE001 - a kit without it serves its pages all the same
        dog = None
    while time.time() - last[0] < idle:
        httpd.handle_request()
        if dog:
            dog.tick()
        refresh_progress(site)
        if watch.ended():
            ended_at = ended_at or time.time()
            if time.time() - ended_at >= grace:  # an open tab keeps asking, so the idle clock never runs out
                break
        else:
            ended_at = None
    try:  # the run has ended or gone idle: its live pages are saved, so they still open from disk
        import saved_pages
        saved_pages.write_all(site)
    except Exception:  # noqa: BLE001 - a page not saved never keeps the listener up
        pass
    httpd.server_close()


class RunEnd:
    """Whether the run this listener serves has ended: a run under the folder was seen under way, and now none is.
    Read from the run record, so it never waits on the session remembering the stop command."""

    def __init__(self, site):
        self.site, self.seen_running, self.checked, self.answer = site, False, 0.0, False

    def ended(self):
        if time.time() - self.checked < 5:
            return self.answer
        self.checked = time.time()
        try:
            import start
            import work_page
            running = any(start.resumable(r) for r in work_page.runs(self.site))
        except Exception:  # noqa: BLE001 - a record mid-write, or a kit without them: never stop on a guess
            return False
        self.seen_running = self.seen_running or running
        self.answer = self.seen_running and not running
        return self.answer


_PROGRESS_AT = [0.0]


def refresh_progress(site):
    """While a flow is mapped, each run's home screen drawn again once a part of the map is written since the last
    look (progress.py), at most every two seconds, so the open page shows the latest line; never stops the listener."""
    if time.time() - _PROGRESS_AT[0] < 2:
        return
    _PROGRESS_AT[0] = time.time()
    try:
        import home
        import progress
        root = pathlib.Path(site)
        runs = [root] if (root / "RUN.md").is_file() else [d for d in root.iterdir() if (d / "RUN.md").is_file()]
        for reg in runs:
            if progress.new_lines(reg):
                home.write(reg)
    except Exception:  # noqa: BLE001 - a record mid-write, or a kit without them: the pages are served all the same
        pass


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "serve":
        serve(os.path.abspath(args[1]))
    else:
        sys.exit(__doc__)
