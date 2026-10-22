"""Link check over a capability's home, in Markdown or HTML.

Usage: python -I linkcheck.py HOME_DIR [--baseline DIR ...]

Fails, listing every breach, when:
- a link points at a file or anchor that does not exist
- a link leaves HOME_DIR, unless it lands under a declared --baseline folder (the shared baseline area); such links
  are listed in their own section, so a home that cannot stand on its own fails
- there is no alert index on the home or a page it links, or the index lists a name twice, or a row links no page
  (each row's first link is its runbook; later links, such as the component page, are allowed; an index with no rows yet passes)
- an alert name from the index is linked anywhere else to a different target than its runbook
- a page under HOME_DIR cannot be reached from the home by following links

The home is index.md, index.html or README.md at the top of HOME_DIR. The alert index is any table in the home whose
first column header starts with "Alert": each row's first cell is an alert name, and the row links one page.
Links must be relative; absolute URLs are not followed.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

MD_LINK = re.compile(r'\[[^\]]*\]\(<?([^)\s>]+)>?(?:\s+"[^"]*")?\)')
HTML_LINK = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
MD_NAMED = re.compile(r'\[([^\]]*)\]\(<?([^)\s>]+)>?(?:\s+"[^"]*")?\)')
HTML_NAMED = re.compile(r"""<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""", re.S)
PAGE = (".md", ".html")


def named_links(text):
    """(link text, target) pairs, with markup stripped from the text."""
    text = strip_code(text)
    pairs = MD_NAMED.findall(text) + [(t, h) for h, t in HTML_NAMED.findall(text)]
    return [(re.sub(r"<[^>]+>", "", t).strip(" *`"), h) for t, h in pairs]


def slug(heading):
    s = re.sub(r"<[^>]+>|[`*]", "", heading).strip().lower()
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", s))


def strip_code(text):
    text = re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.S)
    return re.sub(r"^```.*?^```|`[^`\n]*`", "", text, flags=re.S | re.M)


def anchors(path, text):
    ids = set(re.findall(r'\b(?:id|name)="([^"]+)"', text))
    if path.suffix == ".md":
        ids |= {slug(h) for h in re.findall(r"^#+\s+(.+)$", strip_code(text), re.M)}
    return ids


def links(text):
    text = strip_code(text)
    return MD_LINK.findall(text) + HTML_LINK.findall(text)


def resolve(page, target):
    if re.match(r"[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("/"):
        return None, None
    path, _, anchor = target.partition("#")
    path = unquote(path.split("?")[0])
    dest = (page.parent / path).resolve() if path else page
    if dest.is_dir():
        dest = next((dest / n for n in ("index.md", "index.html", "README.md") if (dest / n).exists()), dest)
    return dest, anchor


def alert_tables(text):
    """Rows of every table whose first column header starts with 'Alert', and whether any such table exists."""
    rows, found = [], False
    for table in re.findall(r"(?:^\|.*\|\s*$\n?)+", text, re.M):
        lines = table.strip().splitlines()
        if lines and lines[0].strip("| ").lower().startswith("alert"):
            found = True
            rows += [l.strip().strip("|").split("|") for l in lines[2:]]
    for table in re.findall(r"<table.*?</table>", text, re.S):
        head = re.search(r"<th[^>]*>(.*?)</th>", table, re.S)
        if head and re.sub(r"<[^>]+>", "", head.group(1)).strip().lower().startswith("alert"):
            found = True
            rows += [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", table, re.S)]
    return [r for r in rows if r], found


def check(root, baselines=()):
    root = root.resolve()
    baselines = [b.resolve() for b in baselines]
    inside = lambda d: d == root or root in d.parents
    in_baseline = lambda d: any(d == b or b in d.parents for b in baselines)
    pages = sorted(p.resolve() for p in root.rglob("*") if p.suffix in PAGE)
    home = next((root / n for n in ("index.md", "index.html", "README.md") if (root / n).exists()), None)
    if not home:
        return ["no home page (index.md, index.html or README.md) at the top of the folder"]
    home = home.resolve()
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in pages}
    errors, leaving, graph = [], [], {}
    for page in list(texts):
        graph[page] = set()
        for target in links(texts[page]):
            dest, anchor = resolve(page, target)
            if dest is None:
                continue
            if not inside(dest) and not in_baseline(dest):
                leaving.append(f"{page.relative_to(root)}: {target}")
                continue
            if not dest.is_file():
                errors.append(f"{page.relative_to(root)}: link to a file that does not exist: {target}")
                continue
            if dest.suffix not in PAGE:
                continue
            if dest not in texts:
                texts[dest] = dest.read_text(encoding="utf-8", errors="replace")
            graph[page].add(dest)
            if anchor and anchor not in anchors(dest, texts[dest]):
                errors.append(f"{page.relative_to(root)}: link to an anchor that does not exist: {target}")
    index = next((p for p in [home, *sorted(graph[home])] if alert_tables(texts[p])[1]), None)
    if not index:
        errors.append(f"{home.name}: no alert index (a table whose first column header starts with 'Alert'), "
                      "on the home or a page it links")
    runbooks = {}
    for row in alert_tables(texts[index])[0] if index else []:
        name = re.sub(r"<[^>]+>|\[([^\]]*)\]\([^)]*\)", r"\1", row[0]).strip(" *`")
        runbook = next((t for t in links("|".join(row)) if resolve(index, t)[0]), None)
        if name in runbooks:
            errors.append(f"alert index: '{name}' is listed twice")
        if not runbook:
            errors.append(f"alert index: '{name}' leads to no page; its first link is its runbook")
        runbooks[name] = resolve(index, runbook) if runbook else None
    for page in pages:
        for text, target in named_links(texts[page]):
            want = runbooks.get(text)
            got = resolve(page, target)
            if want and got[0] and (got[0], got[1] or "") != (want[0], want[1] or ""):
                errors.append(f"{page.relative_to(root)}: alert '{text}' links {target}, not its runbook")
    reached, todo = {home}, [home]
    while todo:
        for nxt in graph.get(todo.pop(), ()):
            if nxt not in reached:
                reached.add(nxt)
                todo.append(nxt)
    errors += [f"{p.relative_to(root)}: not reachable from {home.name}" for p in pages if p not in reached]
    if leaving:
        errors += [f"links that leave the home ({len(leaving)}); declare a --baseline folder or bring them inside:"]
        errors += [f"  {l}" for l in leaving]
    return errors


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    base = [Path(a) for i, a in enumerate(args) if i and args[i - 1] == "--baseline"]
    if len(args) != 1 + 2 * len(base):
        sys.exit(__doc__)
    problems = check(Path(args[0]), base)
    if problems:
        sys.exit("\n".join(problems))
    print("link check passed")
