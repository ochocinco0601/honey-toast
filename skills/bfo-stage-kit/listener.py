"""The run's page, brought up by script: one listener for the workspace's work folder, started detached so it outlives
the call that starts it, and the person's browser opened on it.

Usage: python listener.py up <work folder> [<page under it>]   reuse the listener serving the folder, or start one;
                                                                 open the page in the browser; say whether it opened
       python listener.py stop <work folder>                    stop the listener serving the folder

The listener (page_ask.py serve) draws the work page on each request from the folder's files, serves each run's home
screen from its own folder, and records when each page was last asked for (seen.json), so what the person sees moves
on with no model step and an open is judged by the browser's own request. When no request follows, the session is
told to open the address itself. Python standard library only."""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request
import webbrowser

HERE = pathlib.Path(__file__).resolve().parent
WORK = "bfo-work"
URL_FILE, PID_FILE, LOG_FILE, SEEN_FILE = "url.txt", "listener.pid", "listener.log", "seen.json"
# the listener is on this machine: a proxy set for command-line tools never applies to it, as it never does in a browser
LOCAL = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def page_ask():
    """The listener script: in page/ beside this file, or beside it."""
    kit = HERE / "page" / "page_ask.py"
    return kit if kit.is_file() else HERE / "page_ask.py"


def site_of(reg):
    """The folder a register's listener serves: the work folder holding it, or the register itself elsewhere."""
    reg = pathlib.Path(reg).resolve()
    return reg.parent if reg.parent.name == WORK else reg


def alive(site):
    """(address, process id) of the listener serving `site` now, else None: it answers /.alive with the folder it
    serves and its own process id, so a stale url.txt or listener.pid never stands for it."""
    site = pathlib.Path(site).resolve()
    try:
        url = (site / URL_FILE).read_text(encoding="utf-8").strip()
        if not url.startswith("http://127.0.0.1:"):
            return None
        with LOCAL.open(url + ".alive", timeout=3) as r:
            folder, _, pid = r.read().decode("utf-8").partition("\n")
            return (url, int(pid)) if r.status == 200 and folder == str(site) else None
    except (OSError, ValueError):
        return None


def serving(site):
    """The address of the listener serving `site` now, else None."""
    found = alive(site)
    return found[0] if found else None


def start(site, wait=10.0):
    """(address, started): the listener serving `site`, started detached when none is."""
    site = pathlib.Path(site).resolve()
    site.mkdir(parents=True, exist_ok=True)
    url = serving(site)
    if url:
        return url, False
    (site / URL_FILE).unlink(missing_ok=True)  # an old one names a port nobody serves
    kw = {"stdin": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        # no window, ever: a detached process has no console, so a python.exe launcher under it opens a new, visible
        # one for the interpreter it starts; a hidden console is inherited instead, and the listener still outlives us
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    try:
        with open(site / LOG_FILE, "ab") as log:
            subprocess.Popen([sys.executable, "-u", str(page_ask()), "serve", str(site)], stdout=log, stderr=log, **kw)
    except OSError as e:
        raise OSError(f"this machine did not let the page's listener start ({e.strerror or e})") from e
    end = time.time() + wait
    while time.time() < end:
        url = serving(site)
        if url:
            return url, True
        time.sleep(0.1)
    raise OSError(f"the page's listener did not answer within {wait:.0f} seconds (what it said is in "
                  f"{site / LOG_FILE})")


def open_in_browser(url):
    """True when a browser was asked to open the address, which does not prove the person sees it. None is tried
    with BFO_NO_BROWSER set, or on a machine with no display, where the only browser would be one in the terminal that
    holds the call until it is closed."""
    if os.environ.get("BFO_NO_BROWSER"):
        return False
    if os.name != "nt" and sys.platform != "darwin" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    try:
        return bool(webbrowser.open_new_tab(url))
    except webbrowser.Error:
        return False


def seen_at(site, page):
    """When the browser last asked for the page (the listener records every page asked for), else None."""
    try:
        return json.loads((pathlib.Path(site).resolve() / SEEN_FILE).read_text(encoding="utf-8")).get(
            "/" + page.lstrip("/"))
    except (OSError, ValueError, AttributeError):
        return None


def asked_since(site, page, since, wait=0.0):
    """True when the browser asks for the page at or after `since`, waiting up to `wait` seconds."""
    end = time.time() + wait
    while True:
        at = seen_at(site, page)
        if at is not None and at >= since:
            return True
        if time.time() >= end:
            return False
        time.sleep(0.2)


def up(site, page="", opener=None, wait=10.0):
    """(address, started, opened): the browser opened on the page, judged by its own request. A page the browser has
    already asked this listener for is left as it is, so no second tab opens; otherwise the browser is opened, and
    `opened` is True only when it asks for the page within `wait` seconds."""
    site = pathlib.Path(site).resolve()
    url, started = start(site)
    page = page.lstrip("/")
    address = url + page
    if not started and seen_at(site, page) is not None:
        # the browser has had this page from this listener: it is never opened again, as a tab left in the
        # background checks itself too seldom to tell from a closed one, and the address is given every time anyway
        return address, started, True
    t0 = time.time()
    launched = (opener or open_in_browser)(address)
    return address, started, bool(launched) and asked_since(site, page, t0, wait)


def stop(site):
    """True when a listener for `site` was running and is stopped. Only the process the listener itself names is
    ended: a pid left in listener.pid by one that crashed may now be another program's, and is never touched."""
    site = pathlib.Path(site).resolve()
    found = alive(site)
    ended = False
    if found:
        try:
            if os.name == "nt":
                ended = subprocess.run(["taskkill", "/PID", str(found[1]), "/F"], capture_output=True, check=False,
                                       creationflags=subprocess.CREATE_NO_WINDOW).returncode == 0
            else:
                os.kill(found[1], 15)
                ended = True
        except OSError:
            ended = False
    if ended or not found:
        for f in (PID_FILE, URL_FILE, SEEN_FILE):
            (site / f).unlink(missing_ok=True)
    return ended


def say(address, started, opened):
    """What the session is told: the page is open, or the session opens it itself; and in either case the address
    goes to the person in the message."""
    give = f"Give the person the address in your message: {address}"
    if opened:
        return f"PAGE: {address} (open in the person's browser). {give}"
    return (f"OPEN FAILED: open {address} in the person's browser yourself now: in a shell, start \"\" \"{address}\"; "
            f"in PowerShell, Start-Process \"{address}\". {give}")


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) in (2, 3) and argv[0] == "up":
        try:
            print(say(*up(argv[1], argv[2] if len(argv) == 3 else "")))
        except OSError as e:
            print(f"PAGE: none. The page could not be started: {e}. Tell the person so in one plain sentence; the "
                  "run carries on in the chat.")
            return 2
        return 0
    if len(argv) == 2 and argv[0] == "stop":
        print("STOPPED" if stop(argv[1]) else "NOT RUNNING")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
