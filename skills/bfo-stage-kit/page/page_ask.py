"""Serve a local question page and hand its answers to a waiting Claude Code session.

  python -u page_ask.py serve DIR   serve DIR on 127.0.0.1; save each POST /answers to DIR/answers/
  python -u page_ask.py watch DIR   print one line per answers file not yet announced (run under Monitor)
  python -u page_ask.py poll DIR SECONDS
                                    the same, but exit after the first pass that announces anything,
                                    or print TIMEOUT and exit after SECONDS (run as a background task)

The stage kit's own copy of the page step's listener. Changes from the page step it comes from: besides
page-kit.js, it serves the folder's own pages read-only (any .html, .css, .js or .svg file under the served folder,
never outside it and never under answers/), so the home screen's links to the run's other pages work; it draws the
work page at the folder's root on each request, from the folder's files (work_page.py); it answers /.alive with the
folder it serves and its process id (also written to listener.pid), so it can be found and stopped; and it saves an answer
into the answers/ of the run folder whose page sent it (by the page's address), or the served folder's own.
"""
import json, os, pathlib, sys, threading, time, uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

MAX_BODY = 1_000_000
KIT = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [KIT, os.path.dirname(KIT)]  # the kit's own scripts: beside this one, or one folder up in the kit
PAGES = (".html", ".css", ".js", ".svg")
# Every page served says when its tab is left (pagehide: closed, reloaded or followed a link) and when it is shown
# (pageshow: a fresh load, or the back cache with no request), each with the page's own id, so the old page's close
# and the new page's shown can arrive in either order. A page restored from the back cache keeps its id.
BEACON = (b'<script>(function(){if(!navigator.sendBeacon)return;var id=Math.random().toString(36).slice(2,12);'
          b'addEventListener("pagehide",function(){navigator.sendBeacon("/.closed?id="+id)});'
          b'addEventListener("pageshow",function(){navigator.sendBeacon("/.shown?id="+id)});})();</script>')
TAB_EVENTS = ("/.closed", "/.shown")
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


def answers_for(site, referer):
    """The answers/ folder of the run folder whose page posted: the first folder of the page's address under the
    served folder when it is a folder there, else the served folder's own."""
    path = unquote((referer or "").split("://", 1)[-1].partition("/")[2].split("?")[0].split("#")[0])
    first = path.split("/")[0] if "/" in path else ""
    root = pathlib.Path(site).resolve()
    if first and first not in (".", "..") and "\\" not in first and ":" not in first and first.lower() != "answers":
        run = (root / first).resolve()
        if run.parent == root and run.is_dir():
            return str(run / "answers")
    return str(root / "answers")


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
        tabs = got.get("/.tabs") if isinstance(got.get("/.tabs"), dict) else {}
        if path == "/.shown":
            tabs[page] = time.time()
        else:
            tabs.pop(page, None)
        got["/.tabs"] = tabs
    try:
        tmp = "%s.%d.tmp" % (seen, os.getpid())
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(got, f)
        os.replace(tmp, seen)
    except OSError:
        pass


def home_of(site):
    """The newest run's home screen under the folder, once drawn, else None."""
    try:
        import work_page
    except ImportError:
        return None
    return work_page.home(site)


def live(site, path):
    """The work page, drawn now from the folder's files, for the folder's root; a run's sources page, drawn now from
    its sources.csv and RUN.md, for <run>/sources.html; else None."""
    bare = unquote(path.split("?")[0].split("#")[0])
    segs = bare[1:].split("/")
    if segs[-1] == "sources.html" and len(segs) <= 2 and "\\" not in bare and ":" not in bare:
        root = pathlib.Path(site).resolve()
        name = segs[0] if len(segs) == 2 else ""
        if name not in (".", "..", "answers"):
            run = root / name if name else root
            if run.is_dir() and (run / "sources.csv").is_file():
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


def serve(site):
    os.makedirs(os.path.join(site, "answers"), exist_ok=True)
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
            if bare == "/" or bare.endswith(".html"):
                note_seen(site, bare)
            to = home_of(site) if bare == "/" else None
            if to:  # a run's home screen is drawn: the work page's address leads there, and its open tab follows
                self.send_response(302)
                self.send_header("Location", to)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if bare == "/.alive":
                body = ("%s\n%d" % (pathlib.Path(site).resolve(), os.getpid())).encode("utf-8")
                ctype = "text/plain; charset=utf-8"
            elif bare == "/page-kit.js":
                target, ctype = pathlib.Path(KIT) / "page-kit.js", "text/javascript; charset=utf-8"
            elif live(site, self.path) is not None:
                body, ctype = live(site, self.path), "text/html; charset=utf-8"
            else:
                target = own_page(site, self.path)
                if target is None:
                    self.send_error(404)
                    return
                ctype = self.guess_type(str(target))
                ctype += "; charset=utf-8" if ctype.startswith("text/") and "charset" not in ctype else ""
            if body is None:
                body = target.read_bytes()
            if ctype.startswith("text/html"):
                at = body.rfind(b"</body>")
                body = body[:at] + BEACON + body[at:] if at >= 0 else body + BEACON
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
            if self.path != "/answers" or self.headers.get("Origin") != own:
                self.send_error(403)
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY:
                self.send_error(413)
                return
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("not an object")
            except ValueError:
                self.send_error(400)
                return
            name = "answers-%s-%s.json" % (time.strftime("%Y%m%d-%H%M%S"), uuid.uuid4().hex[:8])
            answers = answers_for(site, self.headers.get("Referer"))
            os.makedirs(answers, exist_ok=True)
            path = os.path.join(answers, name)
            with open(path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(path + ".tmp", path)
            print("SAVED " + path, flush=True)
            self.send_response(204)
            self.end_headers()

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
    while time.time() - last[0] < idle:
        httpd.handle_request()
        if watch.ended():
            ended_at = ended_at or time.time()
            if time.time() - ended_at >= grace:  # an open tab keeps asking, so the idle clock never runs out
                break
        else:
            ended_at = None
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


def announce_new(site):
    answers = os.path.join(site, "answers")
    seen_path = os.path.join(answers, ".announced")
    os.makedirs(answers, exist_ok=True)
    try:
        with open(seen_path, encoding="utf-8") as f:
            seen = set(f.read().split())
    except FileNotFoundError:
        seen = set()
    found = 0
    for name in sorted(os.listdir(answers)):
        if name.endswith(".json") and name not in seen:
            # Ledger first: a caller that stops the process on reading the line cannot cause a repeat.
            with open(seen_path, "a", encoding="utf-8") as f:
                f.write(name + "\n")
            print("ANSWERS " + os.path.join(answers, name), flush=True)
            found += 1
    return found


def watch(site):
    while True:
        announce_new(site)
        time.sleep(0.5)


def poll(site, timeout):
    end = time.time() + timeout
    while not announce_new(site):
        if time.time() >= end:
            print("TIMEOUT no answers yet", flush=True)
            return
        time.sleep(0.5)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] in ("serve", "watch"):
        site = os.path.abspath(args[1])
        serve(site) if args[0] == "serve" else watch(site)
    elif len(args) == 3 and args[0] == "poll":
        try:
            timeout = float(args[2])
        except ValueError:
            timeout = 0
        if timeout <= 0:
            sys.exit(__doc__)
        poll(os.path.abspath(args[1]), timeout)
    else:
        sys.exit(__doc__)
