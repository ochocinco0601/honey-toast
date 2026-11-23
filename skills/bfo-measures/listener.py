"""The run's page, brought up by script: one listener for the workspace's work folder, started detached so it outlives
the call that starts it, and the person's browser opened on it.

Usage: python listener.py up <work folder> [<page under it>]   reuse the listener serving the folder, or start one;
                                                                 open the page in the browser; say whether it opened
       python listener.py stop <work folder>                    stop the listener serving the folder
       python listener.py check <work folder> [<page>]          whether the page answers and what it shows now,
                                                                 never counted as the person's browser

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
# pages no open tab follows (page_ask.UNLED): the run status view reloads only itself, so a request for it is never
# an open tab the run can lead
UNLED = ("operator.html",)
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


def tab_open(site):
    """True when a tab is open on this listener: a page has said it is shown and has not said it was left, each page
    by its own id, so a reload or a link to another kit page stays open whatever order the two pages' words arrive
    in; a tab left in the background never says it was left. A browser that sends no such word is judged by its
    requests: open when it has asked for a page."""
    try:
        seen = json.loads((pathlib.Path(site).resolve() / SEEN_FILE).read_text(encoding="utf-8"))
        if isinstance(seen.get("/.tabs"), dict):
            return bool(seen["/.tabs"])
        closed = seen.pop("/.closed", None)
        last = max((t for k, t in seen.items() if not k.startswith("/.") and k.rsplit("/", 1)[-1] not in UNLED),
                   default=None)
    except (OSError, ValueError, AttributeError, TypeError):
        return False
    return last is not None and (closed is None or last > closed)


def status_open(site):
    """True when a run status tab is open on this listener: one has said it is shown and not that it was left (its
    own beacons, kept apart from the led tabs')."""
    try:
        tabs = json.loads((pathlib.Path(site).resolve() / SEEN_FILE).read_text(encoding="utf-8")).get("/.statustabs")
    except (OSError, ValueError, AttributeError):
        return False
    return isinstance(tabs, dict) and bool(tabs)


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


def follows(site, page):
    """True when an open tab can reach `page` by itself: it has been on the page (a page reloads itself). The work
    folder's root lists the runs and leads to none, so a tab there never follows to a run's page."""
    return seen_at(site, page) is not None


def up(site, page="", opener=None, wait=10.0):
    """(address, started, opened): the browser opened on the page, judged by its own request. While a tab open on
    this listener follows to the page by itself (follows), nothing is opened; a tab closed since is opened again.
    A run status page is not opened again while a run status tab is open and has been on it, which never stops
    another run's page opening.
    Otherwise the browser is opened, and `opened` is True only when it asks for the page within `wait` seconds."""
    site = pathlib.Path(site).resolve()
    url, started = start(site)
    page = page.lstrip("/")
    address = url + page
    # another run's tab in the same window never follows to this run's page: only a tab that has been on this page,
    # or on the work page's address while it leads here, does
    if not started and (page.rsplit("/", 1)[-1] in UNLED and status_open(site) and seen_at(site, page) is not None
                        or page.rsplit("/", 1)[-1] not in UNLED and tab_open(site) and follows(site, page)):
        return address, started, True
    t0 = time.time()
    launched = (opener or open_in_browser)(address)
    return address, started, bool(launched) and asked_since(site, page, t0, wait)


def running(pid):
    """True while process `pid` runs."""
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return k.GetLastError() == 5  # access denied: it runs, as another user's
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        if os.waitpid(int(pid), os.WNOHANG)[0]:  # one this process started, now ended: reaped
            return False
    except ChildProcessError:
        pass
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def command_line(pid):
    """The command line of process `pid`, "" when none runs, None when it cannot be read."""
    if os.name == "nt":
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
               f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"]
        kw = {"creationflags": subprocess.CREATE_NO_WINDOW}
    else:
        cmd, kw = ["ps", "-o", "args=", "-p", str(int(pid))], {}
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60, **kw)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout.strip() if p.returncode == 0 or not p.stderr.strip() else None


def serves(line, site):
    """Whether a command line is a listener (page_ask.py serve) of `site`."""
    line, site = line.rstrip().rstrip('"'), str(site)
    if os.name == "nt":
        line, site = line.lower(), site.lower()
    return "page_ask.py" in line and " serve " in line and line.endswith(site)


def end(pid):
    """Asks the system to end process `pid`."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, check=False,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            os.kill(pid, 15)
    except OSError:
        pass


def stop(site, wait=10.0):
    """True when a listener for `site` was running and is stopped. Only a listener of `site` is ended: the process
    that answers /.alive for the folder or, when that answer is late (as on a busy machine), the process listener.pid
    names while its command line is page_ask.py serve of the folder. A pid left by one that crashed may now be another
    program's, and is never touched. The folder's files are removed only once no listener of it runs: a listener
    still running keeps the pid file that names it."""
    site = pathlib.Path(site).resolve()
    try:  # the pages it drew live are saved first, so each run still opens from disk once it has gone
        import saved_pages
        saved_pages.write_all(site)
    except Exception:  # noqa: BLE001 - a page not saved never keeps the listener running
        pass
    try:
        named = int((site / PID_FILE).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        named = None
    found = alive(site)
    pid = found[1] if found else None
    if pid is None and named is not None and running(named):
        line = command_line(named)
        if line is None:
            return False  # what it is cannot be read: it and its record are left
        if serves(line, site):
            pid = named
    if pid is not None:
        end(pid)
        until = time.time() + wait
        while running(pid):
            if time.time() >= until:
                return False  # still running: its pid file stays
            time.sleep(0.1)
    for f in (PID_FILE, URL_FILE, SEEN_FILE):
        (site / f).unlink(missing_ok=True)
    return pid is not None


def say(address, started, opened):
    """What the session is told: the page is open, or the session opens it itself; and in either case the address
    goes to the person in the message."""
    give = f"Give the person the address in your message: {address}"
    if opened:
        return f"PAGE: {address} (open in the person's browser). {give}"
    return (f"OPEN FAILED: open {address} in the person's browser yourself now: in a shell, start \"\" \"{address}\"; "
            f"in PowerShell, Start-Process \"{address}\". {give}")


def ask_check(url, page):
    """The listener's own answer about `page` (/.check), or None when it does not answer. The check is never counted
    as the person's browser."""
    from urllib.parse import quote
    try:
        with LOCAL.open(url + ".check?page=" + quote(page), timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def check(site, page="/operator.html"):
    """(what to say, exit code): whether the listener serving `site` answers, and what `page` gives through it. For the
    session asked why the page is not updating: the run status page is drawn on each request and is never a file."""
    site = pathlib.Path(site).resolve()
    url = serving(site)
    if not url:
        return (f"NOT ANSWERING: no listener serves {site}. Restart it (listener.py up, as at every stop) and say so "
                "in one line."), 1
    got = ask_check(url, page)
    if got is None:
        return f"NOT ANSWERING: the listener at {url} did not answer the check.", 1
    said = f"ANSWERS {got.get('status')}: {url.rstrip('/')}{got.get('page')}"
    if got.get("badge"):
        said += f" · the page's badge now: {got['badge']}"
    return said, 0 if got.get("status") == 200 else 1


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
    if len(argv) in (2, 3) and argv[0] == "check":
        said, code = check(argv[1], argv[2] if len(argv) == 3 else "/operator.html")
        print(said)
        return code
    if len(argv) == 2 and argv[0] == "stop":
        if stop(argv[1]):
            print("STOPPED")
        elif (pathlib.Path(argv[1]).resolve() / PID_FILE).is_file():
            print("NOT STOPPED: the listener did not end; listener.pid still names it")
        else:
            print("NOT RUNNING")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
