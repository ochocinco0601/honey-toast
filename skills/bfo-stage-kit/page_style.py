"""The one style every page this kit writes wears: the map screen's, lifted out of one_canvas.py so the map, a stage's
runbook and alert page, how the map was made and inside each part read as one product.

It holds the map screen's colour tokens, in light and dark, its sans type, and the base rules a page needs (body,
headings, links, tables, code). A page's own components keep their rules in their own module and draw on these
tokens. Nothing here sets a word under 13 px.

It also holds the one way card and form prose is rendered (`prose`, `prose_rows`): a run-on value broken up so it can
be scanned, and any code term mixed into the words set in a code face on a tint (`code_terms`). Cards run the full
width of their page; nothing caps a line's length.

Every page sits in one frame (`main.frame`): a centred column 1240 px wide at most, the widest drawing's room,
with cards at 15 px.

Import it and put `CSS` first in a page's <style>; capability_views.CSS already starts with it, so a page that
includes that needs nothing more."""
import html as _html
import re as _re

TOKENS = """
:root{--m-page:#eef0f3;--m-col:#ffffff;--m-ink:#15171a;--m-ink2:#464b53;--m-ink3:#6b717a;--m-line:#c9ced6;--m-link:#9aa1ab;
--m-acc:#1f5fd0;--m-acc-ink:#ffffff;--m-bus:#fff3c4;--m-bus-s:#a07c0b;
--m-app:#dcebff;--m-app-s:#2f6fbf;--m-agt:#ece2ff;--m-agt-s:#6c46bd;--m-tec:#dcf1d4;--m-tec-s:#3c7f2e;--m-per:#f3e5d2;--m-per-s:#a8672a;
--m-ok:#2f7d4f;--m-bad:#b4561f;--m-code:#e8ecf2;--m-code-ink:#24344f;
--m-sans:"Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
--m-mono:ui-monospace,"SF Mono","Cascadia Mono",Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--m-page:#111316;--m-col:#1b1e22;--m-ink:#f1f2f4;--m-ink2:#c3c8cf;
--m-ink3:#8f96a0;--m-line:#343941;--m-link:#5c636d;--m-acc:#6ea1ff;--m-acc-ink:#0b1526;
--m-bus:#37301a;--m-bus-s:#e6c350;--m-app:#172b45;--m-app-s:#6eaaf0;--m-agt:#2a2145;--m-agt-s:#ae90f0;--m-tec:#1a3117;--m-tec-s:#7dc468;
--m-per:#3a2c1c;--m-per-s:#e0a363;--m-ok:#6fc28f;--m-bad:#e08a52;--m-code:#272d37;--m-code-ink:#cddaf2;color-scheme:dark}}
:root[data-theme="dark"]{--m-page:#111316;--m-col:#1b1e22;--m-ink:#f1f2f4;--m-ink2:#c3c8cf;--m-ink3:#8f96a0;--m-line:#343941;
--m-link:#5c636d;--m-acc:#6ea1ff;--m-acc-ink:#0b1526;--m-bus:#37301a;--m-bus-s:#e6c350;
--m-app:#172b45;--m-app-s:#6eaaf0;--m-agt:#2a2145;--m-agt-s:#ae90f0;--m-tec:#1a3117;--m-tec-s:#7dc468;--m-per:#3a2c1c;--m-per-s:#e0a363;
--m-ok:#6fc28f;--m-bad:#e08a52;--m-code:#272d37;--m-code-ink:#cddaf2;color-scheme:dark}
"""

BASE = """
html,body{background:var(--m-col)}
body{margin:0;color:var(--m-ink);font:15px/1.5 var(--m-sans)}
main{margin:0 auto;padding:24px 16px 64px}
h1{font:700 30px/1.15 var(--m-sans);margin:8px 0 4px}
h2{font:600 22px/1.3 var(--m-sans);margin:0}
h3{font:600 16px/1.35 var(--m-sans);margin:0}
a{color:var(--m-acc)}
code,pre{font-family:var(--m-mono)}
code{font-size:max(13px,.92em)}
code.ct{background:var(--m-code);color:var(--m-code-ink);border-radius:3px;padding:0 .3em;overflow-wrap:anywhere}
main.frame{max-width:1240px;margin:0 auto;padding:8px 20px 48px;box-sizing:border-box}
main.frame .trail{font-size:13px;margin:0 0 2px;color:var(--m-ink2)}main.frame .trail .sep{color:var(--m-ink3)}
main.frame h1{font-size:22px;line-height:1.25;margin:0 0 4px}
h2.sec{display:flex;align-items:baseline;gap:16px;font:600 18px/1.3 var(--m-sans);color:var(--m-ink);margin:14px 0 6px;padding:0 0 4px;border-top:none;border-bottom:2px solid rgba(127,127,127,.35)}
details.fold>summary{list-style:none;cursor:pointer}details.fold>summary::-webkit-details-marker{display:none}
details.fold>summary h2.sec::before{content:"\\25B8\\00a0"}details.fold[open]>summary h2.sec::before{content:"\\25BE\\00a0"}
main.frame .card,main.frame dl.card{font-size:15px}main.frame .card dl{font-size:15px}
.prose p{margin:0 0 4px}.prose p:last-child{margin-bottom:0}
.prose ul{margin:2px 0 6px;padding-left:20px}.prose li{margin:0 0 3px}
"""

CSS = "\n/* page style: begin */" + TOKENS + BASE + "/* page style: end */\n"


# ---------------------------------------------------------------- the frame every flow, stage and step page wears
# A compact head: a trail of links (system, flow, stage), then the title, which names the kind ("Flow: ...",
# "Stage 2: ...", "Process step 2.2: ..."); then three sections in the same order on every page, each named by what it
# holds: the drawing, with the square key at the end of its heading; the card (folding, open); the measures.
SECTIONS = {
    "flow": ("Stages, and where each is measured", "The case, whom it serves, what it delivers", "Measures"),
    "stage": ("The process of the stage, and where each process step is measured", "Expectations, entry, outcomes and alerts",
              "Measures"),
    "step": ("The calls that carry it, and where each is measured", "Trigger, what happens, outcomes and timeouts",
             "Measures"),
    "part": ("The process steps that rely on it, and where it is measured", "What it is, what it depends on, where it sits",
             "Measures"),
}


MAP = "Map"  # the trail's first crumb, which opens the map


def frame_head(trail, title, here=None):
    """The trail and the page's title, which names its kind, as HTML. The trail is where the page sits: `trail`
    [(words, href)] is the map (MAP), then each level above the page, each named by its own page's title and opening
    that page; the page itself ends it as plain text, named `here`, else by its title."""
    E = _html.escape
    links = [f'<a href="{E(h)}">{E(w)}</a>' for w, h in trail]
    links.append(f'<span aria-current="page">{E(title if here is None else here)}</span>')
    return f'<p class="trail">{TRAIL_SEP.join(links)}</p><h1>{E(title)}</h1>'


TRAIL_SEP = ' <span class="sep">\u203a</span> '


def frame_sections(kind, drawing, card, measures=None, key="", card_open=True):
    """The page's three sections, named for `kind` (SECTIONS): the drawing, with `key` at the end of its heading; the
    card folding, open unless `card_open` is False; the measures."""
    a, b, c = (_html.escape(x) for x in SECTIONS[kind])
    return (f'<h2 class="sec">{a}{key}</h2>{drawing}'
            f'<details class="fold"{" open" if card_open else ""}><summary><h2 class="sec">{b}</h2></summary>{card}</details>'
            + (f'<h2 class="sec">{c}</h2>{measures}' if measures is not None else ""))


# ---------------------------------------------------------------- prose on a card or a form

# The shapes of a code term, each one a reader would not take for an English word. Kebab-case, words joined by one
# slash ("and/or"), abbreviations ("e.g."), decimals, curly quotes, quoted sentences and a quoted word in lower case
# ("none") are never marked; nor is a product's own name (PRODUCTS) or a name the register gives (`exempt`).
_EXT = r"(?:py|cs|cshtml|razor|ts|tsx|js|jsx|java|kt|go|rb|php|html|yaml|yml|json|md|sql|xml|toml|ini|cfg|proto|sh)"
CODE_TERM = _re.compile("|".join([
    r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD)\s+/(?:[\w{}*:./-]*[\w}])?",            # a route: POST /api/orders
    r"(?<![\w/.])/[A-Za-z_{][\w{}*:.-]*(?:/[\w{}*:.-]*[\w}])+",                   # a path from the root: /api/orders
    r"\b[\w.-]+(?:/[\w.-]+)+\." + _EXT + r"\b(?::\d+(?:-\d+)?)?",                  # a file path: src/a/b.py
    r"\b[\w-]+\." + _EXT + r"\b(?::\d+(?:-\d+)?)?",                                # a file, a file:line
    r'\b[A-Za-z_]\w*\."[A-Za-z_]\w*"',                                            # schema."Table"
    r"\b[A-Za-z_]\w+(?:\.[A-Za-z_]\w+)+\b(?!\.?\w)",                              # dotted: ordering.orders
    r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*[A-Za-z0-9]\b",                         # snake_case, SCREAMING_SNAKE
    r"\b[a-z]+[A-Z][a-z]\w*\b",                                                   # lowerCamel: orderItems
    r"\b[A-Z][a-z0-9]+(?:[A-Z]+[a-z0-9]*)*[A-Z][a-z]\w*\b",                       # UpperCamel: BuyerId
    r'(?<![\w"])"(?=[a-z]*[A-Z_.0-9])[A-Za-z_][\w.]*"(?![\w"])',                  # a quoted name: "OrderDate"
    r"(?<![\w'])'(?=[a-z]*[A-Z_.0-9])[A-Za-z_][\w.]*'(?!\w)",                     # a quoted name: 'Paid'
]))
PRODUCTS = {"GitHub", "GitLab", "OpenTelemetry", "ASP.NET", "JavaScript", "TypeScript", "PostgreSQL", "MySQL",
            "MongoDB", "DynamoDB", "CosmosDB", "BigQuery", "PagerDuty", "ServiceNow", "YouTube", "LinkedIn", "PayPal",
            "RabbitMQ", "AlloyDB", "OpenAI", "DevOps", "SignalR", "iPhone", "macOS"}
_ABBREV = _re.compile(r"(?:\b(?:e\.g|i\.e|etc|vs|approx|cf|incl|no|Mr|Ms|Dr|St)|\b[A-Za-z])$", _re.I)


def _named(term, exempt):
    """Whether a term is a name the register gives (a part, a step, the system), so a name, never code."""
    return term in PRODUCTS or term in exempt or any(term in e.split() for e in exempt)


def code_terms(text, exempt=()):
    """The code terms in plain text, in order, each as written: what `prose` sets in the code face. A word in
    `exempt` (a part's, a step's, the system's own name, as the register writes it) is a name, never code."""
    ex = set(exempt or ())
    return [m.group(0) for m in CODE_TERM.finditer(text or "") if not _named(m.group(0), ex)]


def marked(text, exempt=()):
    """Plain text as escaped HTML, each code term in the code face."""
    text, out, at, ex = text or "", [], 0, set(exempt or ())
    for m in CODE_TERM.finditer(text):
        if _named(m.group(0), ex):
            continue
        out += [_html.escape(text[at:m.start()]),
                f'<code class="ct">{_html.escape(m.group(0))}</code>']
        at = m.end()
    return "".join(out) + _html.escape(text[at:])


def _split(text, sep):
    """`text` cut at each `sep` that sits outside brackets and quotes."""
    out, depth, quote, at, i = [], 0, "", 0, 0
    while i < len(text):
        c = text[i]
        if quote:
            quote = "" if c == quote else quote
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif c == '"' or (c == "'" and (i == 0 or not text[i - 1].isalnum())):
            quote = c
        elif depth == 0 and text.startswith(sep, i):
            out.append(text[at:i])
            i = at = i + len(sep)
            continue
        i += 1
    return out + [text[at:]]


def sentences(text):
    """A value's sentences: cut at ". " before a capital, outside brackets and quotes, never after an abbreviation."""
    parts = []
    for piece in _split(text or "", ". "):
        if parts and (_ABBREV.search(parts[-1]) or not piece[:1].isupper()):
            parts[-1] += ". " + piece
        else:
            parts.append(piece)
    return [p.strip() for p in parts if p.strip()]


def recovery(text):
    """(the value, its trailing "Recovery: ..." or "")."""
    text = text or ""
    m = _re.search(r"(?:^|(?<=[.;])\s*|\s)Recovery:\s*([^.]+?)\.?\s*$", text)
    if not m:
        return text.strip(), ""
    return text[:m.start()].strip().rstrip(".;").strip(), m.group(1).strip()


def _identifier(text, exempt=()):
    """Whether an item starts with an identifier, which is never re-cased: a code term; a first word holding a hyphen,
    an underscore, a dot, a slash, a colon or a digit (a service's or a host's name); or a first word followed straight
    by a code term (a command and its argument)."""
    first, _, rest = text.partition(" ")
    if any(text.startswith(t) for t in code_terms(text, exempt)) or _re.search(r"[-_./:0-9]", first):
        return True
    return bool(rest) and any(rest.startswith(t) for t in code_terms(rest, exempt))


def _cap(text, exempt=()):
    """An item's first letter as a capital, unless the item starts with an identifier."""
    if not text[:1].islower() or _identifier(text, exempt):
        return text
    return text[:1].upper() + text[1:]


def _end(text):
    return text if text.endswith((".", "?", "!")) else text + "."


def prose(text, exempt=(), inline=None):
    """One card or form value as a reader scans it, as HTML. A value of one sentence with no ';' list stays inline,
    as written. Otherwise each sentence is its own line; a sentence whose lead clause ends in ':' before a ';' list is
    the lead, then each item its own bullet; a ';' list with no lead is bullets alone. A trailing "Recovery: ..." is
    left for its own row (`prose_rows`). Code terms wear the code face everywhere. The words are never changed, only
    laid out. `inline` renders each piece in place of `marked`, for a page with its own reading of register text."""
    mk = inline or (lambda t: marked(t, exempt))
    body, _ = recovery(text)
    sents = sentences(body)
    if len(sents) <= 1 and len(_split(body, "; ")) == 1:
        return mk(body)
    out = []
    for snt in sents:
        snt = snt.rstrip(".")
        head = _split(snt, ": ")
        lead, tail = (head[0], ": ".join(head[1:])) if len(head) > 1 else ("", snt)
        items = [i.strip().rstrip(".") for i in _split(tail, "; ") if i.strip()]
        if len(items) > 1:
            out.append((f"<p>{mk(lead)}:</p>" if lead else "")
                       + "<ul>" + "".join(f"<li>{mk(_end(_cap(i, exempt)))}</li>" for i in items) + "</ul>")
        else:
            out.append(f"<p>{mk(_end(snt))}</p>")
    return '<div class="prose">' + "".join(out) + "</div>"


def prose_rows(label, text, exempt=()):
    """[(label, html)] for a card's field: the value by `prose`, then its "Recovery: ..." as a row of its own."""
    body, rec = recovery(text)
    rows = [(label, prose(body, exempt))]
    if rec:
        rows.append(("Recovery", marked(_cap(rec, exempt), exempt)))
    return rows
