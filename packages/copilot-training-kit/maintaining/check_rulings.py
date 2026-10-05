"""Fail the build on faults that are easy to miss when pages are reviewed by hand.

Run by build_pages.py as `check_rulings.py KIT OUT`, or alone with the kit folder to see every hit.
Each rule names the fault and what to write instead. An empty RULED checks every learner page
(markdown outside maintaining/, facilitator/, read-in-browser/ and sample-files/); a non-empty one
checks only the pages it lists. EXEMPT lists pages not yet rebuilt to the page standard, so they
don't fail the build; take each out when it is rebuilt.
"""
import io, os, re, sys

RULED = []   # empty: every learner page
# Pages not yet rebuilt to the page standard; take each out when it is rebuilt.
EXEMPT = []
# The tool the kit teaches. Rules listed in TOOL_RULES run only when TOOL matches; every other rule
# runs always.
TOOL = "Copilot"
TOOL_RULES = {"NAME": "copilot", "EXTENSION": "copilot", "KEEPUNDO": "copilot", "ADDTOCHAT": "copilot",
              "YOURPLAN": "copilot"}
NOT_LEARNER = ("maintaining", "facilitator", "read-in-browser", "sample-files")


def ruled_pages(kit):
    """The learner pages these rules check, relative to the kit, with forward slashes."""
    if RULED:
        pages = list(RULED)
    else:
        pages = []
        for root, dirs, files in os.walk(kit):
            rel = os.path.relpath(root, kit).replace(os.sep, "/")
            if rel == ".":
                dirs[:] = [d for d in dirs if d not in NOT_LEARNER and not d.startswith(".")]
            pages += [(f if rel == "." else rel + "/" + f) for f in files if f.endswith(".md")]
    return sorted(p for p in pages if p not in EXEMPT)

WRITE = re.compile(r"\b(create|write|delete|remove|rename|move|save|add|replace|change)\b", re.I)
KEEP_SCOPE = re.compile(r"no other file|nothing else|change nothing|don't change|do not change", re.I)

# (code, pattern, where, fix). where: "any" line, "prompt" (a "> " line), "check" (a "Check:" line),
# "text" (not a prompt).
# NAME, EXTENSION, KEEPUNDO, ADDTOCHAT and YOURPLAN hold for Copilot only (see TOOL_RULES); for another tool,
# add its own rules to RULES and TOOL_RULES.
RULES = [
    ("NAME", r"\bthe assistant\b", "text", 'call it "Copilot"'),
    ("EXTENSION", r"\binstall\w* (the )?(GitHub )?Copilot\b|\bCopilot (Chat )?extension\b|\bextension\b.{0,20}\bCopilot\b", "text",
     "Copilot is built into VS Code; it is set up by signing in"),
    ("KEEPUNDO", r"\*\*Keep\*\*", "text",
     "current VS Code saves edits directly; take a change back with Restore Checkpoint "
     "(Keep and Undo only as 'on some versions')"),
    ("ADDTOCHAT", r"added to the chat|add (a|the|your) folder to the chat|drag .{0,40} into the chat", "any",
     "the agent searches the open folder; name the folder in the request instead"),
    ("OPENFOLDER", r"\bfolder I have open\b", "prompt",
     "a request that writes names its target folder (for example, copilot-practice), never 'the folder I have open'"),
    ("REPLYCHECK", r"\breply (arrives|appears)|appears in the chat\b|a summary .{0,30} appears", "check",
     "a Check names something the learner can see in the files or the answer, not that a reply came"),
    ("AIWARNING", r"\b(can|could|may|might) (be wrong|make mistakes|get .{0,10} wrong)\b", "text",
     "no blanket warnings that AI makes mistakes; teach the checking technique once, with its purpose"),
    ("DOWNLOADS", r"\bDownloads folder\b|\bmy Downloads\b", "prompt",
     "no step depends on content the learner may not have; use practice files Copilot creates"),
    ("WHOTOASK", r"\bwhoever (gave|sent)\b|\byour manager\b|\bask (someone in )?your organization\b|"
                 r"\byour organization (decides|allows|tells)\b|\bYour organization\]\(", "text",
     "no 'ask whoever gave you the training', no organization page"),
    ("THISWEEK", r"\bthis week\b", "text", "no 'this week, on your own work' units"),
    ("CAUTION", r"\bnever choose\b|\bdo not choose\b|\bif in doubt, decline\b", "text",
     "a permission request: if it matches what you asked, Allow; if not, Skip"),
    ("ORDINALREF", r"\b(first|second|third|fourth|fifth|next|previous|last|earlier|later) (unit|lesson|step|training)\b", "text",
     "name the unit or step by its title, or link it; an ordinal goes stale when the order changes"),
    ("TIMEINTEXT", r"\babout (five|ten|fifteen|twenty|twenty-five|thirty|\d+) minutes\b", "text",
     "the time is shown in the unit header and menu; don't repeat it in the page text"),
]

# Judged a sentence at a time after wrapped lines are joined, because a sentence wraps across
# lines. Reported at the first line of its paragraph or list item. They catch the common wordings,
# not every one: the review still reads setup steps against the guide's "Setup is the workplace's
# way". YOURPLAN holds for Copilot only (see TOOL_RULES).
SITE = (r"(?:\[[^\]]*\]\()?(?:https?://)?(?:[\w-]+\.)+"
        r"(?!(?:md|txt|json|csv|zip|py|html|pdf|docx|xlsx|png)\b)[a-z]{2,}\b[^\s)]*")
SENTENCE_RULES = [
    ("PUBLICINSTALL", r"(?i)\b(?:install|reinstall|download|upgrade)\w*\b[^.:;,]{0,40}?\b(?:from|at)\s+" + SITE
                      + r"|\bgo to\s+" + SITE + r"[^.]*?\b(?:download|install)",
     "learners get software from their company's software portal, not a vendor's site"),
    ("SELFUPDATE", r"\bCheck for Updates\b|\bRestart to Update\b",
     "updates come from the company's software portal, not the tool's own update command"),
    ("YOURPLAN", r"(?i)\byour (Copilot )?plan\b|\baccount that has your\b|\byour personal (GitHub )?account\b",
     "learners sign in with their work account; the kit says nothing about plans or personal accounts"),
]


def where(line):
    s = line.strip()
    if s.startswith(">"):
        return "prompt"
    if s.startswith("Check:"):
        return "check"
    return "text"


def check_answers(rel, lines):
    """ANSWERBLOB: an answer paragraph that runs several cases together."""
    hits = 0
    for n, line in enumerate(lines, 1):
        if not re.match(r"(Check your answer|Answers):", line.strip()):
            continue
        para = []
        for later in lines[n - 1:]:
            if not later.strip() or later.lstrip().startswith(("- ", "#")) or re.match(r"\s*\d+\.\s", later):
                break
            para.append(later.strip())
        if len(" ".join(para).split()) > 40:
            hits += 1
            print("ANSWERBLOB %s:%d -> an answer to several cases is a list after the 'Check your answer:' line, "
                  "one case to an item" % (rel, n))
    return hits


def check_sentences(rel, lines):
    """SENTENCE_RULES over each paragraph or list item of ordinary text, joined and split into sentences."""
    rules = [r for r in SENTENCE_RULES if TOOL_RULES.get(r[0], TOOL.lower()) == TOOL.lower()]
    hits = 0
    start, block = 0, []
    for n, line in enumerate(lines + [""], 1):
        s = line.strip()
        text = bool(s) and where(line) != "prompt" and not s.startswith("#")
        if block and (not text or re.match(r"(\d+\.|[-*])\s", s)):
            for sentence in re.split(r"(?<=[.!?])\s+", " ".join(block)):
                if re.match(r"Sources?:", sentence):
                    continue
                for code, pat, fix in rules:
                    m = re.search(pat, sentence.replace("*", ""))
                    if m:
                        hits += 1
                        print("%s %s:%d %r -> %s" % (code, rel, start, m.group(0), fix))
            block = []
        if text:
            if not block:
                start = n
            block.append(s)
    return hits


def check(kit):
    hits = 0
    rules = [r for r in RULES if TOOL_RULES.get(r[0], TOOL.lower()) == TOOL.lower()]
    for rel in ruled_pages(kit):
        path = os.path.join(kit, rel)
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding="utf-8").read().splitlines()
        for n, line in enumerate(lines, 1):
            kind = where(line)
            window = " ".join(lines[max(0, n - 2):n + 1])
            for code, pat, scope, fix in rules:
                if scope != "any" and scope != kind and not (scope == "text" and kind == "check"):
                    continue
                if code == "ORDINALREF" and ("TO BE WRITTEN" in line or line.lstrip().startswith("#")):
                    continue
                if code == "KEEPUNDO" and re.search(r"instead of \*\*Restore Checkpoint\*\*|some versions", window):
                    continue
                m = re.search(pat, line, re.I)
                if m:
                    hits += 1
                    print("%s %s:%d %r -> %s" % (code, rel, n, m.group(0), fix))
            if kind != "prompt" or (n > 1 and where(lines[n - 2]) == "prompt"):
                continue
            # A request can run over several "> " lines; it is judged as a whole, at its first line.
            block = []
            for later in lines[n - 1:]:
                if where(later) != "prompt":
                    break
                block.append(later)
            whole = " ".join(block)
            touches_files = re.search(r"\b(file|files|folder|folders)\b|\.\w{2,4}\b", whole, re.I)
            if touches_files and WRITE.search(whole) and not KEEP_SCOPE.search(whole):
                if not re.search(r"\b(summarize|explain|tell me|which|where|what)\b", whole, re.I) or \
                        re.search(r"\bcreate\b", whole, re.I):
                    hits += 1
                    print("SCOPE %s:%d -> a request that writes files says 'Add or change no other file.'"
                          % (rel, n))
        hits += check_sentences(rel, lines)
        hits += check_answers(rel, lines)
    return hits


def open_corrections(kit):
    """Rows of the guide's Corrections table not yet applied; nothing goes to the requester while any is open."""
    guide = os.path.join(kit, "maintaining", "README.md")
    if not os.path.exists(guide):
        return 0
    text = io.open(guide, encoding="utf-8").read()
    m = re.search(r"\n## Corrections\n(.*?)(?=\n## |\Z)", text, re.S)
    if not m:
        return 0
    rows = [l for l in m.group(1).splitlines() if l.startswith("|") and not re.match(r"\|\s*-", l)][1:]
    return sum(1 for r in rows if r.rstrip(" |").split("|")[-1].strip().lower().startswith("open"))


if __name__ == "__main__":
    kit = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("NOTE: open corrections in maintaining/README.md: %d (no 'Ready to read' while any is open)" % open_corrections(kit))
    print("ruling faults on learner pages: %d" % check(kit))
    sys.exit(0)
