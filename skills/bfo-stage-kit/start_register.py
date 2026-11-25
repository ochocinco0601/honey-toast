"""Start a new register: copy register-template/ into a new, empty register folder, and never over earlier work.

Usage: python start_register.py <register folder> [--workspace <root>] [--new --words "<the person's words>"]

Copies every CSV file in register-template/, and RUN.md unless the folder already has one. REGISTER.md is not
copied. If the folder already holds any CSV file, it is a register from an earlier run: nothing is copied, and the
script exits non-zero with a message saying so.

A new register is not started while the workspace holds a run of this kit that is not finished (start.py finds them):
that run is picked up with start.py instead. Only the person's say-so starts new work beside it: `--new --words`
with their words, word for word, which are recorded in the new RUN.md. The workspace is the folder holding
`bfo-work/` when the register is inside it; otherwise name it with `--workspace`."""
import datetime
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "register-template"
sys.path.insert(0, str(HERE))
import run_lock  # noqa: E402
import start  # noqa: E402

STARTED_NEW = "- **Started new beside unfinished work:**"


def option(args, name):
    """The value after `name` in `args`, and `args` without both; (None, args) when absent; ('', ...) with no value."""
    if name not in args:
        return None, args
    i = args.index(name)
    return (args[i + 1] if i + 1 < len(args) else ""), args[:i] + args[i + 2:]


def record_new(run_md, words, beside):
    """The person's words for starting new beside unfinished work, in the new RUN.md's Earlier registers section."""
    when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = (f'{STARTED_NEW} the person said, on {when}, "{words}". Not finished, and left as it is: '
            + "; ".join(str(b) for b in beside) + ".")
    text = run_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    at = next((i for i, x in enumerate(lines) if x.startswith(STARTED_NEW)), None)
    if at is not None:
        lines[at] = line
    else:
        head = next((i for i, x in enumerate(lines) if x.strip() == start.KIT_SECTION), None)
        if head is None:
            lines += ["", start.KIT_SECTION, "", line]
        else:
            at = head + 1
            while at < len(lines) and not lines[at].startswith("- **Found:**"):
                at += 1
            lines.insert(min(at, len(lines)), line)
    run_md.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def start_step_ran(root):
    """True when start.py recorded this run's start in the workspace's work folder: the page first, then the search."""
    try:
        d = json.loads(start.start_file(pathlib.Path(root) / "bfo-work", start.STARTED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if run_lock.identity() is None:  # nothing names the run: the start step's record is enough
        return bool(d.get("started"))
    return bool(d.get("run")) and d.get("run") == run_lock.identity()


def main(argv):
    args = list(argv)
    new = "--new" in args
    args = [a for a in args if a != "--new"]
    words, args = option(args, "--words")
    root, args = option(args, "--workspace")
    if len(args) != 1 or words == "" or root == "":
        sys.exit(__doc__)
    reg = pathlib.Path(args[0])
    if reg.name.lower() == run_lock.ANSWERS:  # the page saves what the person sends into a folder by this name
        print(f"refused: {reg} is named {run_lock.ANSWERS}, the name of the folder the page saves the person's answers "
              "in. Start the register in a folder named for the system. Nothing was copied.", file=sys.stderr)
        return 2
    inside = next((d for d in [reg.resolve(), *reg.resolve().parents] if (d / "SKILL.md").is_file()), None)
    if inside is not None:  # a relative path given from the kit's own folder lands in the kit
        print(f"refused: {reg.resolve()} is inside the skill folder {inside}: a register is never written into a "
              "skill. Give the register's full path, under the workspace's bfo-work/ folder. Nothing was copied.",
              file=sys.stderr)
        return 2
    held = sorted(p.name for p in reg.glob("*.csv")) if reg.is_dir() else []
    if held:
        print(f"refused: {reg} already holds a register ({', '.join(held)}). Nothing was copied, so the earlier "
              "work is untouched. Start the new register in a new, empty folder.", file=sys.stderr)
        return 2
    if root is None:
        if reg.resolve().parent.name != "bfo-work":
            print(f"refused: {reg} is not in a bfo-work folder, so the workspace to search for unfinished work is not "
                  "known. Name it with --workspace <root>. Nothing was copied.", file=sys.stderr)
            return 2
        root = reg.resolve().parent.parent
    if not pathlib.Path(root).is_dir():
        print(f"refused: the workspace {root} is not a folder. Nothing was copied.", file=sys.stderr)
        return 2
    # another chat's work under way (its lock fresh) is not unfinished work to decide about: it is being worked on
    beside = [r for r in start.to_pick_up(root)[0] if r != reg.resolve() and not start.held_by_another(r)]
    if beside and not new:
        print("refused: the workspace holds work this kit started that is not finished: "
              + "; ".join(str(b) for b in beside) + ". Pick it up with start.py, which gives the person the re-entry "
              "brief. Only when the person says to start new work beside it, run this again with --new --words "
              "\"<their words, word for word>\". Nothing was copied.", file=sys.stderr)
        return 2
    if new and words is None:
        print("refused: --new needs the person's words, word for word: --words \"<their words>\". Nothing was copied.",
              file=sys.stderr)
        return 2
    if not start_step_ran(root):
        print("refused: the start step has not run for this run, so the page is not up and earlier work was not "
              f'looked for. Run python start.py "{root}" first, and follow its decision. Nothing was copied.',
              file=sys.stderr)
        return 2
    if reg.is_dir():
        run_lock.guard(reg, take_missing=True)
    reg.mkdir(parents=True, exist_ok=True)
    run_lock.guard(reg, take_missing=True)
    for f in sorted(TEMPLATE.glob("*.csv")):
        shutil.copy2(f, reg / f.name)
    if not (reg / "RUN.md").exists():
        shutil.copy2(TEMPLATE / "RUN.md", reg / "RUN.md")
    if new and beside:
        record_new(reg / "RUN.md", words, beside)
    try:  # the person's request, as the start step kept it, recorded as data in the new run record
        d = json.loads(start.start_file(pathlib.Path(root) / "bfo-work", start.STARTED).read_text(encoding="utf-8"))
        start.record_request(reg, d.get("request") or "", (d.get("started") or "")[:16] or None)
        state = reg / "_run-state"
        state.mkdir(exist_ok=True)
        (state / start.STARTED).write_text(json.dumps(d), encoding="utf-8")
        start.record_start(pathlib.Path(root) / "bfo-work", reg=reg)  # this run's page now leads to its register
    except (OSError, ValueError):
        pass
    said_back = start.start_file(pathlib.Path(root) / "bfo-work", "say-back-decisions.jsonl")
    if said_back.is_file():  # the person's answers to the say-back, given before this register existed
        import case
        case.import_decisions(reg, [e for e in case.decisions_in(said_back) if e.get("session") == case.session()])
    run_lock.guard(reg, take_missing=True)  # again, now RUN.md is here to record a lock not taken
    print(f"register started: {reg}")
    print(f"FOLDER: {reg.resolve()}")  # the register folder: the <your-folder> of every later command
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
