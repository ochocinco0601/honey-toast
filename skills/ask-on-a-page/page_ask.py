"""Serve a local question page and hand its answers to a waiting Claude Code session.

  python -u page_ask.py serve DIR   serve DIR on 127.0.0.1; save each POST /answers to DIR/answers/
  python -u page_ask.py watch DIR   print one line per answers file not yet announced (run under Monitor)
  python -u page_ask.py poll DIR SECONDS
                                    the same, but exit after the first pass that announces anything,
                                    or print TIMEOUT and exit after SECONDS (run as a background task)
"""
import json, os, sys, time, uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1_000_000
KIT = os.path.dirname(os.path.abspath(__file__))


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

        def do_GET(self):
            if not self.own_host():
                self.send_error(403)
                return
            path = self.path.split("?")[0]
            # Only the page and its script are served: nothing else in the folder is reachable.
            if path not in ("/index.html", "/page-kit.js"):
                self.send_error(404)
                return
            if path == "/page-kit.js":
                with open(os.path.join(KIT, "page-kit.js"), "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

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
