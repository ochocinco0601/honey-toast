"""Ready the run's pages while the run waits on the person at a stop, and bring the page up.

Usage: python wait_on_page.py <register folder>

Every question is asked and answered in the chat, as a question card; the pages only show. This writes depth.json
again and draws the home screen (index.html) from it, so the page says what the run waits on ("Waiting on you: answer
in the chat"), saves the run's pages to disk, then brings up the page by script (listener.py): it reuses the
listener serving the work folder, or starts one detached and opens the person's browser on the home screen unless it
is open there already. One listener serves the run from its first stop to its end; the page open in the person's
browser checks its own address by itself and shows each redraw in the same tab within about 15 seconds. Stop the
listener once no flow is left to offer after the run's end, or the person says stop at the offer of the next flow.
Exit 0 ready, 2 refused. Python standard library only."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import depth  # noqa: E402
import home  # noqa: E402
import listener  # noqa: E402
import run_lock  # noqa: E402

STOP_WHEN = ("once no flow is left to offer after the run's end, or the person says stop at the offer of the next "
             "flow")


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    run_lock.refuse_unless_register(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) != 1 or not pathlib.Path(argv[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    reg = pathlib.Path(argv[0])
    run_lock.guard(reg)
    depth.write(reg)
    home.write(reg)  # drawn now from the depth.json just written: it says what the run waits on
    import saved_pages  # every stop leaves the run's pages on disk, for when its listener has gone
    saved_pages.write(reg)
    site = listener.site_of(reg)
    page = ("" if site == reg.resolve() else reg.resolve().name + "/") + home.FILE
    try:
        brought = listener.up(site, page)
    except OSError as e:
        print(f"REFUSED: the page could not be started ({e}). Send the stop's message all the same: the question is "
              "in the chat, and the page is only a display.", file=sys.stderr)
        return 2
    print(f"Written: {depth.FILE} and {home.FILE}")
    print(listener.say(*brought))
    print(f"The question is asked and answered in the chat; the page only shows. Stop the listener with "
          f'python "{HERE / "listener.py"}" stop "{site}", {STOP_WHEN}.')
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
