"""Ready the home screen to take the person's pick and topics, and print what the session runs to wait on it.

Usage: python wait_on_page.py <register folder>

Writes depth.json again and draws the home screen (index.html) from it, so the page carries the choice open now;
writes resume.md (which stop, which register, and the go.py --answers command that records what the page sends);
One listener serves the run from its first stop to its end, and the page open in the person's browser checks its own
address by itself, so it shows each new choice in the same tab within about 15 seconds (it holds while ticks or
words on it are not yet sent, and says so at its top). When the listener named in
url.txt still serves this folder, it says so and prints nothing to start or open; otherwise it removes the stale
url.txt and prints the two commands the session runs (the listener in the background, and the watch under the Monitor
tool with timeout_ms 1800000) and how to open the page, which at a later stop means a new tab: the earlier one has
stopped updating.
At the go and at the pick the page takes the person's pick; at any other stop it takes only topics to talk about.
Exit 0 ready, 2 refused. Python standard library only."""
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import depth  # noqa: E402
import home  # noqa: E402

RESUME = "resume.md"
PAGE_ASK = HERE / "page" / "page_ask.py"
WATCH_MS = 1800000
ON_PAGE = ("Choose the flow to map first", "Pick how far each stage goes")


def commands(reg):
    reg, kit = pathlib.Path(reg).resolve(), PAGE_ASK
    return {"serve": f'python -u "{kit}" serve "{reg}"',
            "watch": f'python -u "{kit}" watch "{reg}" 2>&1',
            "record": f'python "{HERE / "go.py"}" "{reg}" --answers "<the answers file>"',
            "url": reg / "url.txt"}


def live_listener(reg, url_file):
    """The URL in url.txt when the listener there serves this folder's home screen as it is on disk now, else None."""
    try:
        url = url_file.read_text(encoding="utf-8").strip()
        if not url.startswith("http://127.0.0.1:"):
            return None
        with urllib.request.urlopen(url + home.FILE, timeout=3) as r:
            return url if r.status == 200 and r.read() == (reg / home.FILE).read_bytes() else None
    except (OSError, ValueError):
        return None


def resume_text(reg, c, cmd):
    asked = (f"{c['task']} (milestone: {c['milestone']}), choice id `{c['choice_id']}`" if c and c["task"] in ON_PAGE
             else "no pick is taken on the page now; it takes topics to talk about")
    return "\n".join([
        "# Waiting on the person, on the home screen",
        "",
        f"- **Register:** `{pathlib.Path(reg).resolve()}`",
        f"- **Stop:** {asked}",
        "",
        "## When an answers file arrives (`ANSWERS <path>` from the watch)",
        "",
        f"Read the file, then record it: `{cmd['record']}`, with the path the watch printed.",
        "On exit 0, say back to the person in one or two lines what was recorded, and the line go.py printed after",
        "\"You asked to talk about:\" if there is one; then talk about those topics with them, and carry on with the run.",
        "On a refusal (exit 2), tell the person why, in plain words from what go.py printed, and how to answer",
        "again: on the page, which has been drawn again, or in the chat. Talk about any topics the file holds.",
        "",
        "## If the watch has ended, or the session was restarted",
        "",
        f"Start the watch again under the Monitor tool, timeout_ms {WATCH_MS}: `{cmd['watch']}`.",
        "It announces any answers sent while it was down.",
        "",
        "## If the person says \"read it\"",
        "",
        "Read the newest file in `answers/` in the register folder that go.py has not recorded already, and record",
        "it as above. If there is none, ask the question in the chat, and record their typed answer as the run's",
        "text for this stop says.",
        ""])


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 1 or not pathlib.Path(argv[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    reg = pathlib.Path(argv[0])
    c = depth.write(reg)["open_choice"]
    home.write(reg)  # drawn now from the depth.json just written: its choice id is the open choice's
    cmd = commands(reg)
    (reg / RESUME).write_text(resume_text(reg, c, cmd), encoding="utf-8", newline="\n")
    takes = f"{c['task']}, {c['choice_id']}" if c and c["task"] in ON_PAGE else "topics only"
    print(f"Written: {depth.FILE}, {home.FILE} and {RESUME} (the page takes: {takes})")
    live = live_listener(reg, cmd["url"])
    if live:
        print(f"The listener is already serving this run at {live}: the page open on it checks for changes by itself "
              "and shows this choice in its own tab within about 15 seconds, unless ticks or words on it are not yet "
              "sent: then it says so at its top and updates once they are sent or cleared. Start no listener and open "
              "no page. "
              f"If the watch has ended, start it again with the Monitor tool, timeout_ms {WATCH_MS}: {cmd['watch']}")
        return 0
    cmd["url"].unlink(missing_ok=True)  # the listener writes a fresh one; an old one names a port nobody serves
    print(f"1. Start the listener in the background: {cmd['serve']}")
    print(f"2. Start the watch with the Monitor tool, timeout_ms {WATCH_MS}: {cmd['watch']}")
    print(f"3. Open the page: read the URL in {cmd['url']} once the listener has written it, then "
          f'python -m webbrowser -t "<that URL>{home.FILE}". If a page from an earlier stop is still open, it has '
          "stopped updating: tell the person to use the new tab and close the old one.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
