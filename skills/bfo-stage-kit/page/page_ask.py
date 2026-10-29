"""Serve a local question page and hand its answers to a waiting Claude Code session.

  python -u page_ask.py serve DIR   serve DIR on 127.0.0.1; save each POST /answers to DIR/answers/
  python -u page_ask.py watch DIR   print one line per answers file not yet announced (run under Monitor)

The stage kit's own copy of the page step's listener. One change from the page step it comes from: besides
page-kit.js, it serves the folder's own pages read-only (any .html, .css, .js or .svg file under the served folder,
never outside it and never under answers/), so the home screen's links to the run's other pages work.
"""
import json, os, pathlib, sys, time, uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

MAX_BODY = 1_000_000
KIT = os.path.dirname(os.path.abspath(__file__))
PAGES = (".html", ".css", ".js", ".svg")


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


def serve(site):
    answers = os.path.join(site, "answers")
    os.makedirs(answers, exist_ok=True)

    class Handler(SimpleHTTPRequestHandler):
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
            if self.path.split("?")[0].split("#")[0] == "/page-kit.js":
                target, ctype = pathlib.Path(KIT) / "page-kit.js", "text/javascript; charset=utf-8"
            else:
                target = own_page(site, self.path)
                if target is None:
                    self.send_error(404)
                    return
                ctype = self.guess_type(str(target))
                ctype += "; charset=utf-8" if ctype.startswith("text/") and "charset" not in ctype else ""
            body = target.read_bytes()
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
    with open(os.path.join(site, "url.txt"), "w", encoding="utf-8") as f:
        f.write(url)
    print("READY " + url, flush=True)
    httpd.serve_forever()


def watch(site):
    answers = os.path.join(site, "answers")
    seen_path = os.path.join(answers, ".announced")
    os.makedirs(answers, exist_ok=True)
    while True:
        try:
            with open(seen_path, encoding="utf-8") as f:
                seen = set(f.read().split())
        except FileNotFoundError:
            seen = set()
        for name in sorted(os.listdir(answers)):
            if name.endswith(".json") and name not in seen:
                print("ANSWERS " + os.path.join(answers, name), flush=True)
                with open(seen_path, "a", encoding="utf-8") as f:
                    f.write(name + "\n")
        time.sleep(0.5)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("serve", "watch"):
        sys.exit(__doc__)
    site = os.path.abspath(sys.argv[2])
    serve(site) if sys.argv[1] == "serve" else watch(site)
