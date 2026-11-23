"""The run's pages saved into its register, so a run whose page listener has stopped still opens from disk.

The run status page, the sources page and the map so far are drawn by the listener on each request and are never
files while it runs; once it stops (the run's end, Claude Code closed) the person would lose them. At every stop and
at the end, each is drawn once more and written into the register beside the home screen (index.html), with its
links relative to the register, and marked as a saved copy that does not update. The listener still draws the live
page at the same address while it runs.

Usage: python saved_pages.py <register folder>   writes them and prints the file to open. Python standard library only."""
import datetime as dt
import html
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

STATUS = "operator.html"
NOTE = ('<p class="saved" style="margin:12px auto 0;max-width:1400px;padding:8px 14px;border:1px solid #DAD7CD;'
        'border-radius:6px;background:#FFFDF5;font:13px system-ui,sans-serif;color:#3D3B35">Saved copy, written {at}: '
        'it does not update. While the run is under way, its live page is at the address the chat gave.</p>')


def _pages(reg):
    """[(file name, the page as the listener draws it now)] for each live page this register has."""
    out = []
    if (reg / "RUN.md").is_file():
        import operator_page
        out.append((STATUS, operator_page.render(reg)))
    if (reg / "sources.csv").is_file():
        import sources_page
        out.append(("sources.html", sources_page.render(reg)))
    if (reg / "RUN.md").is_file():
        import partial_map
        out.append(("map-so-far.html", partial_map.render(reg).replace(
            "drawn live by the listener, never written", "a saved copy of the map so far, never the checked map")))
    return out


def _relative(page, reg):
    """The work folder's own addresses ("/" and "/<this register>/...") as links inside the register: from disk "/"
    is the drive's root. The list of runs is not in the register, so a link to it goes to Home, or is dropped."""
    home = "index.html" if (reg / "index.html").is_file() else None
    page = re.sub(r'href="/' + re.escape(reg.name) + r'/', 'href="', page)
    if home:
        return page.replace('href="/"', f'href="{home}"')
    return re.sub(r'<a class="go" href="/">[^<]*</a>|<a href="/">[^<]*</a>', "", page)


def write(reg, now=None):
    """Each live page, drawn now and written into the register as a saved copy; the paths written. Never raises: a
    page that cannot be drawn is left as it was."""
    reg = pathlib.Path(reg)
    at = (now or dt.datetime.now().astimezone()).strftime("%a %d %b, %H:%M")
    written = []
    try:
        pages = _pages(reg)
    except Exception:  # noqa: BLE001 - saving is a courtesy to the person: it never stops a stop
        return written
    for name, page in pages:
        try:
            page = _relative(page, reg).replace("This page reloads itself every 15 seconds.", "")
            note = NOTE.format(at=html.escape(at))
            page = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + note, page, count=1)
            target = reg / name
            part = target.with_name(f"{name}.{os.getpid()}.part")
            part.write_text(page, encoding="utf-8", newline="\n")
            os.replace(part, target)
            written.append(target)
        except Exception:  # noqa: BLE001
            continue
    return written


def line(reg):
    """The line naming the file that opens the finished run from disk, for the done check and the report."""
    return (f"PAGES SAVED: the run's pages open from disk with no listener: open {(pathlib.Path(reg) / STATUS).resolve()}"
            " in a browser. Name this file in the report.")


def write_all(site):
    """Saved pages for every register under the work folder (and the folder itself, when it is one)."""
    site = pathlib.Path(site)
    try:
        regs = [d for d in [site] + [p for p in site.iterdir() if p.is_dir()] if (d / "RUN.md").is_file()]
    except OSError:
        return []
    out = []
    for reg in regs:
        out += write(reg)
    return out


def main(argv):
    if len(argv) != 1 or not pathlib.Path(argv[0]).is_dir():
        sys.exit(__doc__)
    import run_lock  # run by hand, it writes into the register: only the run that holds it, or none
    run_lock.guard(pathlib.Path(argv[0]), touch=False)
    write(argv[0])
    print(line(argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
