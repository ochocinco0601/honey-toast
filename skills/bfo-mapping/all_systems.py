"""All systems: index.html at the root of the workspace's work folder, one row per register in it (a folder holding
depth.json), newest first, each linking its home screen. A file, so it opens with no run going and keeps one address.
Redrawn by home.py each time a home screen in the folder is drawn.

Usage: python all_systems.py <work folder>"""
import datetime
import html
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import depth  # noqa: E402
import page_style as ps  # noqa: E402

E = html.escape
CSS = """body{margin:0;background:#F6F5F1;font-family:'Segoe UI',system-ui,sans-serif;color:#1D1D1B}
.nav{display:flex;flex-wrap:wrap;align-items:center;gap:6px 18px;background:#FFFFFF;border-bottom:1px solid #DAD7CD;padding:10px 24px;font-size:14px}
.nav .sys{font-weight:600}
main{box-sizing:border-box;max-width:1280px;margin:0 auto;padding:18px 24px 48px;display:flex;flex-direction:column;gap:14px}
.card{background:#FFFFFF;border:1px solid #DAD7CD;border-radius:8px;padding:16px 20px;overflow-x:auto}
.mute{color:#5A5850;font-size:14px;margin:0}
table{border-collapse:collapse;width:100%;font-size:15px}
th{text-align:left;font-size:13px;color:#5A5850;font-weight:600;padding:6px 16px 8px 0;border-bottom:1px solid #DAD7CD}
td{padding:9px 16px 9px 0;border-bottom:1px solid #EEECE6;vertical-align:top}
td.n{font-variant-numeric:tabular-nums}
a{color:#1F4E8C;font-weight:600;text-decoration:none}
a:hover{text-decoration:underline}"""


def registers(work):
    """Every register folder in the work folder, newest depth.json first."""
    try:
        found = [d for d in pathlib.Path(work).iterdir() if d.is_dir() and (d / depth.FILE).is_file()]
    except OSError:
        return []
    return sorted(found, key=lambda d: (d / depth.FILE).stat().st_mtime, reverse=True)


def row(reg):
    import home
    try:
        d = json.loads((reg / depth.FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    name = home.title(reg, d)
    link = (f'<a href="{E(reg.name)}/{ps.HOME_FILE}">{E(name)}</a>' if (reg / ps.HOME_FILE).is_file() else E(name))
    stands = home.where_it_stands(d) or ""
    when = datetime.datetime.fromtimestamp((reg / depth.FILE).stat().st_mtime)
    return (f"<tr><td>{link}</td><td>{E(reg.name)}</td><td class=\"n\">{len(d.get('flows') or [])}</td>"
            f"<td>{E(stands[:1].upper() + stands[1:])}</td>"
            f"<td class=\"n\">{when.day} {when.strftime('%b %Y, %H:%M')}</td></tr>")


def render(work):
    body = "".join(row(r) for r in registers(work))
    return ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n     Source: depth.json in each register folder here\n"
            "     Builder: all_systems.py\n     Build: python all_systems.py <this folder>\n-->\n"
            "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{ps.ALL_SYSTEMS}</title><style>{CSS}</style></head><body>"
            f'<div class="nav"><span class="sys">{ps.ALL_SYSTEMS}</span></div><main>'
            '<p class="mute">Every system the kit has been run on in this folder, newest first. '
            "Click a name to open its Home page.</p>"
            '<div class="card"><table><thead><tr><th>System</th><th>Folder</th><th>Flows</th>'
            f"<th>Where it stands</th><th>Last changed</th></tr></thead><tbody>{body}</tbody></table></div>"
            "</main></body></html>\n")


def write(work):
    """Written beside it and moved into place in one step, as two runs in the folder may redraw it at once."""
    work = pathlib.Path(work)
    part = work / f"{ps.HOME_FILE}.{os.getpid()}.part"
    part.write_text(render(work), encoding="utf-8", newline="\n")
    try:
        os.replace(part, work / ps.HOME_FILE)
    except OSError:
        part.unlink(missing_ok=True)
        raise
    return work / ps.HOME_FILE


def update(reg):
    """Redraw the list for the work folder holding the register `reg`; nothing when it sits anywhere else."""
    work = pathlib.Path(reg).resolve().parent
    return write(work) if work.name == ps.WORK else None


def main(argv):
    if len(argv) != 1 or pathlib.Path(argv[0]).name != ps.WORK or not pathlib.Path(argv[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    print(f"Written: {write(argv[0])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
