"""Every question the kit puts to the person, in one fixed form, asked in the chat: a Markdown blockquote card.

    > **❓ 1 of 3 · Which flow should I map first?**
    >
    > **Terms:** flow: one piece of work the system does from start to end, such as placing an order
    >
    > | # | Flow | What happens |
    > |---|---|---|
    > | 1 | Placing an order | the shopper pays and the order ships |
    >
    > **Why:** I map one flow at a time, starting where a failure costs most
    >
    > 1. **Map it**: I map Placing an order first
    > 2. **Pick another**: you name the flow; I map that one first
    >
    > **Recommended: 1** · it is where the shop takes the money
    >
    > **To answer:** reply with the number, or say it in your own words

`card(...)` renders one from its parts; `cards([...])` numbers several in one message ("1 of N") and says once, after
the last, how to answer them all. `faults(text)` is the
check `brief.py say` runs on every message, over the cards' structure only: a card missing its title, its Why, its
numbered choices or its recommendation, recommending a choice while its table's Recommended column is empty, or
holding a line that is no field, table row or choice, is refused, and so is a message still asking in the old
numbered "What I need from you" block. `form_advice(text)` and `loose_questions(text)` judge the words inside the form
(a long field, cell, choice or Terms line; a question mark outside a card): advice for the writer, never a refusal,
since they read the business's own words. card() builds the structure faults() checks (each value one line,
"|" escaped in cells), so a card the kit builds with a Why, two choices and a recommendation is never refused; it
cuts no length, since a cut would drop the fact a cell or a choice carries. `terms(reg, words)` is the Terms field: the kit's own words defined the first time a run
uses them, and remembered in the register so a later card does not define them again.

Python standard library only."""
import json
import pathlib
import re

MARK = "❓"  # the question mark the title opens with
TITLE = re.compile(r"^\*\*" + MARK + r" (?:(\d+) of (\d+) · )?(.+)\*\*$")
FIELD = re.compile(r"^\*\*([A-Z][A-Za-z]*(?: [a-z]+){0,3}):\*\* (\S.*)$")
CHOICE = re.compile(r"^(\d+)\. \*\*([^*]+)\*\*: (\S.*)$")
RECOMMENDED = re.compile(r"^\*\*Recommended: (\d+|none)\*\* · (\S.*)$")
ROW = re.compile(r"^\|.*\|$")
# a field holds one line: a fragment or one short sentence, never a paragraph
FIELD_WORDS = 40
CHOICE_WORDS = 30
CELL_WORDS = 20  # a table cell is a fragment: one fact, never a sentence
FRAGMENT_WORDS = 12  # a record's sentence shown in a cell or a one-line field is cut to a fragment this long
OLD_ASK = "**What I need from you.**"
TERMS_TOLD = "terms-told.json"

# The kit's own words, each a fragment for someone who has never seen the kit, the first time a run uses it.
TERMS = {
    "flow": "work done start to end, like placing an order",
    "stage": "a part of a flow a business person would name",
    "map": "a flow's stages, its steps and the parts carrying each",
    "measure": "a number showing whether a stage works, like orders failed",
    "alert": "a measure that wakes someone when it goes wrong",
    "runbook": "the steps to check and fix what an alert reports",
    "first look": "my first quick read, to find the flows",
    "service": "one program of the system with one job, like payments",
    "finding": "one recorded fact about the system, citing its code",
    "checked finding": "a finding a second reader confirmed against its code",
}
# one definition in a Terms value, "*word*: meaning", the next starting after "; "
TERM = re.compile(r"\*([^*]+)\*: (.*?)(?=; \*[^*]+\*: |$)")
TERMS_INLINE = 2  # at most this many definitions on one Terms line; more are a Term | Meaning table
CLAUSE = re.compile(r", |; |: | — ")


def fragment(s, cap=FRAGMENT_WORDS):
    """A record's sentence as a fragment of at most `cap` words, never with a word added: as it is when within `cap`,
    else up to its first clause boundary (a comma, semicolon, colon or dash), else its first `cap` words and "…"."""
    s = (s or "").strip()
    if len(s.split()) <= cap:
        return s
    m = CLAUSE.search(s)
    if m and 2 <= len(s[:m.start()].split()) <= cap:
        return s[:m.start()].rstrip()
    return " ".join(s.split()[:cap]).rstrip(",;:") + "…"


def used_terms(texts):
    """The kit words (keys of TERMS) that `texts` use, singular or plural, in TERMS order."""
    said = " ".join(texts).lower()
    return [w for w in TERMS if re.search(rf"\b{w}s?\b", said)]


def one_line(x):
    """A value as one line: every run of white space, newlines too, made one space."""
    return " ".join(str(x if x is not None else "").split())


def _fmt_field(label, value):
    return f"**{label}:** {one_line(value)}".rstrip()


def table_lines(header, rows):
    """A Markdown table: the header, its rule, then one line per row. Cells are made one line, with `|` escaped."""
    def cell(x):
        return one_line(x).replace("|", "/") or "-"
    out = ["| " + " | ".join(cell(h) for h in header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return out


def card(title, why, choices, recommended=None, fields=(), table=None, answer=None, of=None, after=()):
    """One question card, as the lines of a blockquote.

    title        the question, one line
    why          why it is asked, one line (required: the check refuses a card without it)
    choices      [(verb, what happens, naming who acts)], numbered 1, 2, ... in order
    recommended  (number, short reason), or (None, reason) when nothing can be recommended
    fields       [(label, value)] before the table: Terms, What, Look where, Affects, Cost, Who can fix, ...
    table        (header, rows), a list of like things
    answer       how to answer, when it is not "reply with the number"
    of           (i, n) when the message holds n questions
    after        [(label, value)] after the table, before Why
    """
    # Built to the form's structure, so faults() never refuses a card built here: every value one line (a newline
    # would end the blockquote), "|" escaped in cells, no "*" in a verb (it would break its bold).
    # Lengths are not cut: a cut drops the fact a cell or a choice carries (a setup problem's reason, a choice's
    # consequence), and form_advice only advises on them.
    head = f"{of[0]} of {of[1]} · " if of else ""
    body = [f"**{MARK} {head}{one_line(title).rstrip('.')}**"]
    for label, value in fields:
        if value and label == "Terms" and len(TERM.findall(value)) > TERMS_INLINE:
            body += [""] + table_lines(("Term", "Meaning"), TERM.findall(value))
        elif value:
            body += ["", _fmt_field(label, value)]
    if table and table[1]:
        body += [""] + table_lines(*table)
    for label, value in after:
        if value:
            body += ["", _fmt_field(label, value)]
    body += ["", _fmt_field("Why", why), ""]
    body += [f"{i}. **{one_line(verb).replace('*', '')}**: {one_line(what)}" for i, (verb, what) in enumerate(choices, 1)]
    if recommended is not None:
        n, reason = recommended
        body += ["", f"**Recommended: {n if n else 'none'}** · {one_line(reason)}"]
    if answer is not False:  # False: one line under the message's last card says how to answer them all
        body += ["", _fmt_field("To answer", answer or "reply with the number, or say it in your own words")]
    return "\n".join(("> " + x) if x else ">" for x in body)


def cards(parts):
    """Several cards in one message, each numbered "i of n", a blank line between them, and one line after the last
    saying how to answer them all; one card alone carries its own How to answer. `parts` are card() kwargs."""
    n = len(parts)
    if n <= 1:
        return "\n\n".join(card(**p) for p in parts)
    return "\n\n".join([card(**dict(p, of=(i, n), answer=False)) for i, p in enumerate(parts, 1)]
                       + [answer_all(parts)])


def answer_all(parts):
    """How to answer every card of a message, once, after the last: the example is each card's recommended choice,
    or 1 where a card recommends none."""
    picks = [str((p.get("recommended") or (None,))[0] or 1) for p in parts]
    return f'**To answer all {len(parts)}:** one choice per card, e.g. "{", ".join(picks)}"'


def blocks(text):
    """Each card in `text` as (its first line's number, [its lines without the quote mark]); a card is a run of quoted
    lines whose first line with words is a question title."""
    return [(s, b) for s, b in quotes(text) if next((x for x in b if x.strip()), "").startswith("**" + MARK)]


STATUS_LABEL = "**Where things stand:**"


def misplaced(text):
    """A card that does not open with its title, or the status line inside a quote, each said with where: the status
    line sits above the card, outside the quote, and a card's first line is its title (a status line quoted on top of
    a card hides the card from every check)."""
    out = []
    for start, lines in quotes(text):
        at = next((i for i, x in enumerate(lines) if STATUS_LABEL in x), None)
        if at is not None:
            out.append(f"line {start + at} puts the status line inside a quote: it sits above the card, outside the "
                       "quote, as the script printed it")
        first = next((x for x in lines if x.strip()), "")
        if not first.startswith("**" + MARK) and any(x.strip().startswith("**" + MARK) for x in lines):
            out.append(f"the quote at line {start} holds a question whose title is not its first line: a card opens "
                       f"with its title (**{MARK} ...**); send the text as the script printed it")
    return out


def quotes(text):
    """Each run of quoted lines in `text` as (its first line's number, [its lines without the quote mark])."""
    out, cur, start = [], None, 0
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith(">"):
            inner = line[1:].lstrip(" ") if line[1:2] in (" ", "") else line[1:]
            if cur is None:
                cur, start = [], n
            cur.append(inner.rstrip())
        else:
            if cur is not None:
                out.append((start, cur))
            cur = None
    if cur is not None:
        out.append((start, cur))
    return out


def faults(text):
    """What breaks the question form's structure in a message, each said with where; [] when every card holds. Only
    structure a parser decides: a title, a Why, numbered choices, a recommendation naming one, the numbering of the
    cards, no stray prose line. The words inside are form_advice's."""
    return _form(text)[0]


def form_advice(text):
    """What in a message's cards is longer than the form wants (a field, a table cell, a choice, a Terms line), each
    said with where: advice for the writer, never a refusal, since it reads the business's own words."""
    return _form(text)[1]


def _form(text):
    """(structure faults, advice) of the question form in a message."""
    out, advice = misplaced(text), []
    if OLD_ASK in text:
        out.append('the message asks in the old "What I need from you" list: put each question in its own card '
                   f"(> **{MARK} ...**), as question_card.py renders it")
    found = blocks(text)
    numbered = []
    for start, lines in found:
        where = f"the card at line {start}"
        title = TITLE.match(lines[0].strip()) if lines else None
        if not title:
            out.append(f"{where}: its first line is not a one-line title (**{MARK} the question**)")
            continue
        if title.group(1):
            numbered.append((int(title.group(1)), int(title.group(2))))
        labels, choices, rec, tables, rows = [], [], None, [], None
        for x in lines[1:]:
            x = x.strip()
            if ROW.match(x):
                if rows is None:
                    rows = []
                    tables.append(rows)
                rows.append([c.strip() for c in x.strip("|").split("|")])
                long = [(n, c) for c in rows[-1] for n in [len(c.replace("·", " ").split())]
                        if n > CELL_WORDS and not is_list(c)]
                if long:
                    advice.append(f"{where}: a table cell is {long[0][0]} words ({long[0][1][:50]}...): a fragment of "
                               "a few words, one fact per cell")
                continue
            rows = None
            if not x:
                continue
            m = CHOICE.match(x)
            if m:
                choices.append(int(m.group(1)))
                if len(x.split()) > CHOICE_WORDS:
                    advice.append(f"{where}: choice {m.group(1)} is {len(x.split())} words: say what happens in a few")
                continue
            m = RECOMMENDED.match(x)
            if m:
                rec = m.group(1)
                continue
            m = FIELD.match(x)
            if m:
                labels.append(m.group(1))
                value = m.group(2)
                if m.group(1) == "Terms" and len(TERM.findall(value)) > TERMS_INLINE:
                    advice.append(f"{where}: the Terms line defines {len(TERM.findall(value))} words: more than "
                                  f"{TERMS_INLINE} go in a | Term | Meaning | table, each meaning a fragment")
                elif len(value.split()) > FIELD_WORDS or re.search(r"[.!?] +[A-Z]", value):
                    advice.append(f"{where}: the {m.group(1)} field is a paragraph: one line, a fragment or one short "
                               "sentence")
                continue
            if x.startswith("**" + MARK):
                out.append(f"{where}: a second title inside it: one question per card, a blank line between cards")
                continue
            out.append(f"{where}: a line of prose inside the card ({x[:60]}...): put it in a field (**Label:** "
                       "value), a table, or a numbered choice")
        if "Why" not in labels:
            out.append(f"{where}: no Why field: say in one line why it is asked")
        if len(choices) < 2:
            out.append(f"{where}: fewer than two numbered choices (1. **Verb**: what happens)")
        elif choices != list(range(1, len(choices) + 1)):
            out.append(f"{where}: its choices are not numbered 1, 2, 3 ... in order")
        if rec is None:
            out.append(f"{where}: no recommendation (**Recommended: N** · reason, or **Recommended: none** · why not)")
        elif rec != "none" and int(rec) not in choices:
            out.append(f"{where}: it recommends {rec}, which is not one of its choices")
        elif rec != "none" and any(empty_recommendation(t) for t in tables):
            out.append(f"{where}: it recommends {rec}, but its table's Recommended column is empty for some rows: "
                       "drop that column and recommend none, or fill each row from the record")
    if numbered:
        n = numbered[0][1]
        if numbered != [(i, n) for i in range(1, n + 1)] or len(numbered) != len(found):
            out.append(f"the cards are numbered {', '.join(f'{a} of {b}' for a, b in numbered)}: number every card in "
                       f"the message 1 of {len(found)} to {len(found)} of {len(found)}, or none when there is one")
    return out, advice


def is_list(cell):
    """Whether a table cell is a list of names (items split by ", ", "; " or " · ", each of four words at most),
    such as the values a column takes: one fact per item, so not held to the cell's word count."""
    items = [x for x in re.split(r", |; | · ", cell) if x.strip()]
    return len(items) > 1 and all(len(x.split()) <= 4 for x in items)


def empty_recommendation(rows):
    """Whether a card's table (its rows as cells, the header first, then the rule) has a Recommended column with an
    empty or "-" cell: a recommendation resting on it points at nothing."""
    if len(rows) < 3 or "Recommended" not in rows[0]:
        return False
    at = rows[0].index("Recommended")
    return any(at >= len(r) or r[at] in ("", "-") for r in rows[2:])


QUOTED = re.compile(r"“[^”]*”|\"[^\"]*\"|`[^`]*`|‘[^’]*’")


def loose_questions(text):
    """Questions put to the person outside a card, each said with where: a line outside every card, table and code
    block whose own words (quoted words, code and table cells set aside) hold a question mark. A question the run
    quotes, such as a measure's "how many orders failed?", is not one it asks. Advice only, never a refusal: a step's
    own name ("Is the payee on the sanctions list?") and a web address hold question marks too."""
    out, fenced = [], False
    for n, line in enumerate(text.splitlines(), 1):
        x = line.strip()
        if x.startswith("```"):
            fenced = not fenced
            continue
        if fenced or not x or x.startswith(">") or x.startswith("|"):
            continue
        if "?" in QUOTED.sub("", x):
            out.append(f"line {n} asks a question outside a card ({x[:60]}): put it in a card (> **{MARK} ...**), "
                       "as question_card.py renders it, or say it as a statement; a name or an address that holds the "
                       "mark is fine as it is")
    return out


PARAGRAPH_WORDS = 40  # a message's text outside its cards: a line or two, never a paragraph
PARAGRAPH_SENTENCES = 2
LABELLED = re.compile(r"^(?:[-*] +)?\*\*[^*]+:\*\*")  # a field, alone or as a list item: **Label:** value
SENTENCE_END = re.compile(r"[.!?](?:[\"”’)]*)(?:\s+|$)")


def _sentences(text):
    return len([x for x in SENTENCE_END.split(text) if re.search(r"[A-Za-z]", x)])


def paragraphs(text):
    """Prose outside the cards that is a paragraph, each said with where: a run of lines outside every card, table,
    list and code block over PARAGRAPH_WORDS words or PARAGRAPH_SENTENCES sentences, or a field (**Label:** value)
    over PARAGRAPH_SENTENCES sentences. The status line and web addresses are not counted. A report that opens
    "Three things to know. ..." or "What would make this map fuller: ..." as prose is the paragraph this catches."""
    out, fenced, run, start = [], False, [], 0

    def close():
        if run:
            said = re.sub(r"https?://\S+", " ", " ".join(run))
            n, k = len(said.split()), _sentences(said)
            if n > PARAGRAPH_WORDS or k > PARAGRAPH_SENTENCES:
                out.append(f"line {start} is a paragraph ({n} words, {k} sentences: {run[0][:50]}...): say it as "
                           "labelled one-line fields (**Label:** value) or a table, one fact a line")
    for n, line in enumerate(text.splitlines(), 1):
        x = line.strip()
        if x.startswith("```"):
            fenced = not fenced
        skip = (fenced or x.startswith("```") or not x or x.startswith(">") or x.startswith("|")
                or STATUS_LABEL in x)
        prose = False
        if skip:
            pass
        elif LABELLED.match(x):
            value = re.sub(r"https?://\S+", " ", LABELLED.sub("", x, count=1))
            if _sentences(value) > PARAGRAPH_SENTENCES:
                out.append(f"line {n} is a field holding a paragraph ({x[:50]}...): one line, a fragment or one or "
                           "two short sentences")
        elif re.match(r"^(?:[-*]|\d+\.) ", x):
            said = re.sub(r"https?://\S+", " ", x)
            if len(said.split()) > PARAGRAPH_WORDS or _sentences(said) > PARAGRAPH_SENTENCES:
                out.append(f"line {n} is a list item holding a paragraph ({x[:50]}...): one fact a line")
        else:
            prose = True
        if prose:
            if not run:
                start = n
            run.append(x)
        else:
            close()
            run = []
    close()
    return out


def terms(reg, words):
    """The Terms field's value for those of `words` (keys of TERMS) the run has not defined to the person yet, and
    remembers them as told; "" when all were told. With no register (`reg` None), every word is defined. card() shows
    more than TERMS_INLINE of them as a Term | Meaning table."""
    told_file = pathlib.Path(reg) / TERMS_TOLD if reg else None
    told = []
    if told_file and told_file.is_file():
        try:
            told = json.loads(told_file.read_text(encoding="utf-8")) or []
        except (OSError, ValueError):
            told = []
    new = [w for w in words if w in TERMS and w not in told]
    if not new:
        return ""
    if told_file and told_file.parent.is_dir():
        told_file.write_text(json.dumps(told + new), encoding="utf-8", newline="\n")
    return "; ".join(f"*{w}*: {TERMS[w]}" for w in new)


def told_terms(reg):
    """The kit words the run has defined to the person already."""
    f = pathlib.Path(reg) / TERMS_TOLD
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else []
    except (OSError, ValueError):
        return []


def snapshot(reg):
    """The terms told so far, as bytes (None when none), kept before a render that may be refused."""
    f = pathlib.Path(reg) / TERMS_TOLD
    return f.read_bytes() if f.is_file() else None


def restore(reg, kept):
    """The terms told put back as they were before a refused render, so the next render defines them again."""
    f = pathlib.Path(reg) / TERMS_TOLD
    if kept is None:
        f.unlink(missing_ok=True)
    else:
        f.write_bytes(kept)
