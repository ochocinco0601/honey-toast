"""Ready the home screen to take the person's pick and topics, and print what the session runs to wait on it.

Usage: python wait_on_page.py <register folder>

Writes depth.json again and draws the home screen (index.html) from it, so the page carries the choice open now;
writes resume.md (which stop, which register, and the go.py --answers command that records what the page sends);
then brings up the page by script (listener.py): it reuses the listener serving the work folder, or starts one
detached and opens the person's browser on the home screen unless it is open there already. One listener
serves the run from its first stop to its end, and the page open in the person's browser checks its own address by
itself, so it shows each new choice in the same tab within about 15 seconds (it holds while ticks or words on it are
not yet sent, and says so at its top). Then it prints the wait the session starts (the watch under the Monitor tool
with timeout_ms 1800000, or, where the session has no Monitor tool, a poll run as a background task and run again
each time it exits), what answers a stop, and how the wait and the listener are stopped at the run's end.
At the go and at the pick the page takes the person's pick; at any other stop it takes only topics to talk about.
Exit 0 ready, 2 refused. Python standard library only."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import depth  # noqa: E402
import home  # noqa: E402
import listener  # noqa: E402
import run_lock  # noqa: E402

RESUME = "resume.md"
PAGE_ASK = HERE / "page" / "page_ask.py"
WATCH_MS = 1800000
ON_PAGE = ("Choose the flow to map first", "Pick how far each stage goes")


def how_to_wait(cmd):
    return (f"If the Monitor tool is in your tool list, or ToolSearch finds it (select:Monitor), start the watch with it, "
            f"timeout_ms {WATCH_MS}: {cmd['watch']} . Without it, run this as a background task instead, and run it "
            f"again each time it exits (with answers, or with TIMEOUT after 30 minutes): {cmd['poll']} . When a poll "
            "exits, handle every ANSWERS line in its output before running it again: a file announced once is never "
            "announced again. Each run of the poll is a new task, so the task id to keep is the poll running now's. "
            "Check for Monitor every time you start a wait; never run two waits at once.")


def commands(reg):
    reg, kit = pathlib.Path(reg).resolve(), PAGE_ASK
    return {"stop": f'python "{HERE / "listener.py"}" stop "{listener.site_of(reg)}"',
            "watch": f'python -u "{kit}" watch "{reg}" 2>&1',
            "poll": f'python -u "{kit}" poll "{reg}" {WATCH_MS // 1000}',
            "record": f'python "{HERE / "go.py"}" "{reg}" --answers "<the answers file>"',
            "ready": f'python "{HERE / "wait_on_page.py"}" "{reg}"'}


def resume_text(reg, c, cmd, address):
    asked = (f"{c['task']} (milestone: {c['milestone']}), choice id `{c['choice_id']}`" if c and c["task"] in ON_PAGE
             else "no pick is taken on the page now; it takes topics to talk about")
    return "\n".join([
        "# Waiting on the person, on the home screen",
        "",
        f"- **Register:** `{pathlib.Path(reg).resolve()}`",
        f"- **Stop:** {asked}",
        f"- **The page:** {address or 'could not be started: take the answer in the chat'} (it may have changed after "
        "a restart, so run the command below first, which opens it again)",
        f"- **At the run's end:** stop the listener with `{cmd['stop']}`",
        "",
        "## When an answers file arrives (`ANSWERS <path>` from the watch or a finished poll)",
        "",
        f"Read the file, then record it: `{cmd['record']}`, with the path the watch or poll printed.",
        "On exit 0, say back to the person in one or two lines what was recorded, and the line go.py printed after",
        "\"You asked to talk about:\" if there is one; then talk about those topics with them, and carry on with the run.",
        "On a refusal (exit 2), tell the person why, in plain words from what go.py printed, and how to answer",
        "again: on the page or in the chat. If go.py says to draw the page again, first run",
        f"`{cmd['ready']}`; otherwise the page already shows the choice open now. Talk about any topics the file holds.",
        "",
        "## If the watch has ended, or the session was restarted",
        "",
        f"First run `{cmd['ready']}`: it brings the page back if its listener has gone, and opens it.",
        f"Then start the wait again. {how_to_wait(cmd)}",
        "It announces any answers sent while no wait was running.",
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
    run_lock.guard(reg)
    c = depth.write(reg)["open_choice"]
    home.write(reg)  # drawn now from the depth.json just written: its choice id is the open choice's
    cmd = commands(reg)
    site = listener.site_of(reg)
    page = ("" if site == reg.resolve() else reg.resolve().name + "/") + home.FILE
    try:
        brought = listener.up(site, page)
        address, started = brought[0], brought[1]
    except OSError as e:
        (reg / RESUME).write_text(resume_text(reg, c, cmd, None), encoding="utf-8", newline="\n")
        print(f"REFUSED: the page could not be started ({e}). Send the stop's message, say in one "
              "plain sentence that the page could not be opened, and take the person's answer in the chat.",
              file=sys.stderr)
        return 2
    (reg / RESUME).write_text(resume_text(reg, c, cmd, address), encoding="utf-8", newline="\n")
    takes = f"{c['task']}, {c['choice_id']}" if c and c["task"] in ON_PAGE else "topics only"
    print(f"Written: {depth.FILE}, {home.FILE} and {RESUME} (the page takes: {takes})")
    print(listener.say(*brought))
    if not started:
        print("The listener was already serving: the page open on it checks for changes by itself and shows this "
              "choice in its own tab within about 15 seconds, unless ticks or words on it are not yet sent: then it "
              "says so at its top and updates once they are sent or cleared.")
    print(f"If no wait is running (a poll exits once it has announced answers, and a watch expires), start one. "
          f"{how_to_wait(cmd)}")
    print("Keep the wait's task id (the watch, or the poll running now). A stop is answered only when go.py records a "
          "pick; a post of topics alone, words with no tick at the pick, and a refusal leave it waiting. Stop the "
          f"wait by its task id, and the listener with {cmd['stop']}, once the run's report is sent at its end.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
