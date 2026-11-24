"""The checks before the first look's costly work, each built on what the run itself uses: the tools the code reader
needs answer here; every code source the person gave is a folder that is there and readable; the folder the code
reader will scan holds roughly what was named, not a whole workspace beside it; a timed sample of the code reader
says whether the full scan fits its time (a warning when it will not); the register's folders take a write; and the
run status page answers (a warning). `first_look.py prepare` runs them after the survey and before the code reader.
A failure holds the run with the reason and the fix for each: one in the sources, the folders or this computer holds
it here (two choices, `answer`); one in the code reader itself holds it as the code reader's own hold does (fix, go
on without it, or stop). Their result is kept in preflight.json; the run status page lists every warning and failure.

Usage: python preflight.py <register>                print each check, pass, warn or fail, with the fix for each
                                                      failure; exit 1 on a failure
       python preflight.py answer <register> <1|2> --words "<their words>" [--test]
Python standard library only."""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import register_layout as layout  # noqa: E402

FILE = "preflight.json"
PASS, WARN, FAIL = "pass", "warn", "fail"
PYTHON = (3, 9)  # USE.md: Python 3.9 or later
FAR_MORE, MORE_FILES = 5, 1000  # the scan target fails at this many times the named repositories' files, and this many more
SAMPLE_SECONDS = 30  # the timed sample's own limit
ANSWER_SECONDS = 30  # `semgrep --version`
LEAD = "The run is held before the first look"
NEXT = "Answer the run's last message in its chat; it lists your choices: fix it and try again, or stop."
STOP_CODE = "preflight-failed"
ANSWERS = {"1": "retry", "2": "stop", "retry": "retry", "stop": "stop"}


def _check(name, state, said, fix="", reader=False, tool=False):
    """One line of the result. `reader`: only the code reader needs it, so going on without the code reader clears
    it; `tool`: the code reader's own hold says it already, in the same words, before anything runs."""
    return {"check": name, "state": state, "said": said, "fix": fix, "reader": reader, "tool": tool}


def _files(folder, most=None):
    """Files under `folder`, leaving out the folders the first look leaves out; counting stops past `most`."""
    import first_look as fl
    n = 0
    for _, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in fl.SKIP_DIRS]
        n += len(files)
        if most is not None and n > most:
            return n
    return n


def tools(reg):
    """The checks of this computer: (lines, the code reader's environment or None)."""
    import first_look as fl
    v = sys.version_info
    out = [_check("python", PASS if v[:2] >= PYTHON else FAIL, f"Python {v[0]}.{v[1]}.{v[2]} at {sys.executable}",
                  "" if v[:2] >= PYTHON else f"install Python {PYTHON[0]}.{PYTHON[1]} or later and start the run "
                  "with it")]
    if fl.reader_skipped(reg) is not None:
        return out + [_check("semgrep", PASS, "the code reader is not used, as you chose", reader=True)], None
    override = os.environ.get("DFO_SEMGREP")
    if override and not fl._usable(override):
        return out + [_check("semgrep", FAIL, f"the setting DFO_SEMGREP names {override}, which is not there",
                             "correct DFO_SEMGREP to the full path of the semgrep program, or remove it",
                             reader=True, tool=True)], None
    exe = fl._semgrep()
    if exe is None:
        return out + [_check("semgrep", FAIL, f"semgrep is not installed for {sys.executable}",
                             f'run "{sys.executable}" -m pip install semgrep', reader=True, tool=True)], None
    folder = os.path.dirname(os.path.abspath(exe)) if os.path.isfile(exe) else ""
    path = os.pathsep.join(x for x in (folder, os.environ.get("PATH", "")) if x)
    env = dict(os.environ, DFO_SEMGREP=exe, PATH=path)
    if folder and not shutil.which("pysemgrep", path=path):
        return out + [_check("pysemgrep", FAIL, f"semgrep is installed in {folder} but its companion program "
                             "pysemgrep is not", f'run "{sys.executable}" -m pip install --force-reinstall semgrep',
                             reader=True, tool=True)], None
    try:
        p = subprocess.run([exe, "--version", "--disable-version-check"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, timeout=ANSWER_SECONDS)
        said = (p.stdout or "").strip().splitlines()[-1:] if p.returncode == 0 else []
    except (OSError, subprocess.TimeoutExpired):
        said = []
    if not said:
        return out + [_check("semgrep", FAIL, f"{exe} did not answer when asked its version",
                             f'run "{sys.executable}" -m pip install --force-reinstall semgrep', reader=True)], None
    return out + [_check("semgrep", PASS, f"semgrep {said[0]} answers, at {exe}", reader=True)], env


def sources(reg):
    """The checks of the code sources: (lines, {repository: (folder, files)}, scan target, its files)."""
    import first_look as fl
    rows = fl._code_rows(reg)
    if not rows:
        return [_check("code sources", PASS, "no code source listed")], {}, None, 0
    found = layout.code_folders(reg)
    out, named = [], {}
    for r in rows:
        name = pathlib.PurePath((r.get("repository") or "").strip().replace("\\", "/")).name
        where = (r.get("location") or "").strip() or name
        p = found.get(name)
        if p is None:
            out.append(_check("code source", FAIL, f"the folder of the repository {name or '(no name)'} ({where}) is "
                              "not there", f"add the repository {name} to this workspace, or say where its folder is"))
        elif not os.access(p, os.R_OK | os.X_OK):
            out.append(_check("code source", FAIL, f"the folder of the repository {name} ({p}) cannot be read",
                              f"let this account read {p}"))
        else:
            named[name] = (p, _files(p))
    if not named or fl.reader_skipped(reg) is not None:
        return out, named, None, 0
    target = layout.code_root(reg)
    if target is None:
        return out + [_check("scan target", FAIL, "the repositories named sit in different folders, so the code "
                             "reader has no one folder to read", "put the repositories named in one folder",
                             reader=True)], named, None, 0
    want = sum(n for _, n in named.values())
    most = max(FAR_MORE * want, want + MORE_FILES)
    scanned = list(found.values()) or [target]  # what first_look._facts hands the code reader as --targets
    have = sum(_files(p, most) for p in scanned)
    if scanned != [target]:
        target = "; ".join(str(p) for p in scanned)
    names = ", ".join(sorted(named))
    if have > most:
        out.append(_check("scan target", FAIL, f"the code reader would scan {target}, which holds more than {most} "
                          f"files, far more than the {want} files of the repositories named ({names})",
                          f"open only the repositories named in this workspace, or move the other folders out of "
                          f"{target}", reader=True))
    else:
        out.append(_check("scan target", PASS, f"the code reader scans {target}: {have} files, for the {want} files "
                          f"of the repositories named ({names})", reader=True))
    return out, named, target, have


def _timed(fl, run, folder, env, limit):
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "out.json"), "w", encoding="utf-8") as o, \
                open(os.path.join(tmp, "err.txt"), "w", encoding="utf-8") as e:
            t0 = time.monotonic()
            code = fl._run_bounded([sys.executable, str(run), str(folder)], o, e, str(folder), env, limit)
            took = time.monotonic() - t0
        last = pathlib.Path(tmp, "err.txt").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1:]
    return code, took, (last[0] if last else "no message")[:200]


def sample(reg, env, named, have):
    """The timed sample: the code reader over an empty folder (its start-up) and over the smallest repository named,
    and the full scan projected from them as start-up plus the sample's own rate over the scan target's files."""
    import first_look as fl
    import settings
    run = fl._tool("fact-extractor/run.py")
    if env is None or run is None or not named or not have:
        return []
    limit = int(settings.load(reg).get("code_reader_seconds") or fl.CODE_READER_SECONDS)
    name, (folder, files) = min(named.items(), key=lambda x: x[1][1])
    with tempfile.TemporaryDirectory() as empty:
        code, start, last = _timed(fl, run, empty, env, SAMPLE_SECONDS)
    if code == 0:
        code, took, last = _timed(fl, run, folder, env, SAMPLE_SECONDS)
    if code is None:
        return [_check("timed sample", WARN, f"the code reader did not finish a sample of {files} files "
                       f"({name}) in {SAMPLE_SECONDS} seconds, so the scan of {have} files will not fit its "
                       f"{limit} seconds", reader=True)]
    if code != 0:
        return [_check("timed sample", FAIL, f"the code reader stopped with an error on a sample ({name}): {last}",
                       f'run "{sys.executable}" -m pip install --force-reinstall semgrep', reader=True)]
    projected = start + max(took - start, 0.0) * have / max(files, 1)
    said = (f"a sample of {files} files ({name}) took {took:.1f} seconds, {start:.1f} of them starting up; the scan "
            f"of {have} files would take about {projected:.0f} seconds, against the code reader's {limit}")
    return [_check("timed sample", WARN if projected > limit else PASS, said, reader=True)]


def writable(reg):
    out = []
    for d in (reg, reg.parent):
        try:
            with tempfile.NamedTemporaryFile(dir=d, prefix=".preflight-"):
                pass
        except OSError as e:
            out.append(_check("writable", FAIL, f"{d} does not take a write ({e.strerror or e})",
                              f"let this account write to {d}"))
            continue
        out.append(_check("writable", PASS, f"{d} takes a write"))
    return out


def page(reg):
    import listener
    site = listener.site_of(reg)
    said, code = listener.check(site, f"/{reg.name}/operator.html" if site != reg else "/operator.html")
    return [_check("run status page", PASS if code == 0 else WARN, said)]


def run(reg):
    """Every check, in order, kept in preflight.json; returns its record."""
    reg = pathlib.Path(reg).resolve()
    t0 = time.monotonic()
    out, env = tools(reg)
    lines, named, _, have = sources(reg)
    out += lines
    if not any(c["state"] == FAIL and c["check"] == "scan target" for c in out):
        out += sample(reg, env, named, have)
    out += writable(reg) + page(reg)
    got = {"at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "seconds": round(time.monotonic() - t0, 1), "checks": out}
    try:
        (reg / FILE).write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass
    return got


def lines(got):
    out = [f"{c['state'].upper()} {c['check']}: {c['said']}" + (f". Fix: {c['fix']}" if c["fix"] and
                                                                  c["state"] == FAIL else "") for c in got["checks"]]
    bad = sum(c["state"] == FAIL for c in got["checks"])
    warned = sum(c["state"] == WARN for c in got["checks"])
    out.append(f"PREFLIGHT: {'FAILED' if bad else 'passed'} in {got['seconds']} seconds"
               + (f", {bad} failure(s)" if bad else "") + (f", {warned} warning(s)" if warned else ""))
    return out


def _read(reg):
    try:
        got = json.loads((pathlib.Path(reg) / FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return got if isinstance(got, dict) else None


def held(reg):
    """The run's own hold before the first look ({"message", ...}), or None."""
    got = _read(reg)
    return got if got and got.get("held") else None


def before_code_reader(reg):
    """Run every check and hold on a failure: one the sources or this computer must put right holds it here; one
    only the code reader needs, as the code reader's own hold (a tool the code reader's hold names already is left to
    it). Returns the checks' lines, for prepare to print."""
    import first_look as fl
    import run_state
    reg = pathlib.Path(reg).resolve()
    got = run(reg)
    fails = [c for c in got["checks"] if c["state"] == FAIL]
    own = [c for c in fails if not c["reader"] or c["check"] == "scan target"]  # the folders, not the tool
    reader = [c for c in fails if c not in own and not c["tool"]]
    stop = run_state.read_stop(reg)
    if stop and stop.get("code") == STOP_CODE and not own:
        run_state.clear_stop(reg)
    if own:
        text = "\n".join([f"{LEAD}: {len(own)} check(s) of this computer and the sources you gave failed. What "
                          "would you like to do?", ""] + [f"- {c['said']}. To fix it: {c['fix']}." for c in own] + [
            "", "1. Fix it and try again: put right what each line above says. Then tell me, and I check again.",
            "2. Stop here.", "", "Answer with the number, or in your own words."])
        got.update(held=True, message=text, choices=["retry", "stop"])
        (reg / FILE).write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        run_state.record_stop(reg, f"{LEAD}: " + "; ".join(c["said"] for c in own) + ".", NEXT, code=STOP_CODE)
    elif reader and fl.reader_held(reg) is None:
        fl._hold(reg, "; ".join(c["said"] for c in reader), "; ".join(dict.fromkeys(c["fix"] for c in reader)),
                 "code reader: NOT RUN: " + "; ".join(c["said"] for c in reader) + ".")
    return "\n".join(lines(got))


def answer(reg, choice, words, test=False):
    """Record the person's answer to the run held before the first look and act on it; returns what to do next."""
    import case
    import run_state
    reg = pathlib.Path(reg).resolve()
    got = held(reg)
    if got is None:
        return "REFUSED: the run is not held before the first look. Nothing recorded."
    kind = ANSWERS.get(str(choice).strip().lower())
    if kind is None:
        return "REFUSED: the answer is 1 or 2 (retry, stop). Nothing recorded."
    if not (words or "").strip():
        return "REFUSED: --words is required: the person's answer, word for word. Nothing recorded."
    case.decide(reg, "preflight", got.get("message", ""), words, "the person", test=test, choice=kind)
    got["held"] = False
    (reg / FILE).write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if kind == "stop":
        run_state.record_stop(reg, "The run stopped before the first look, as you chose: a check of this computer or "
                              "the sources you gave failed.", run_state.RESUME, code="preflight-stopped")
        return "STOPPED: the run stops here, as the person chose."
    run_state.clear_stop(reg)
    return f'NEXT: run python "{HERE / "first_look.py"}" prepare "{reg}" again.'


def issues(reg):
    """The run status page's issues from the last checks, until the code reader has run after them: each failure and
    warning, with its fix. The page's own check is left out: the page that shows it answers."""
    reg = pathlib.Path(reg)
    got = _read(reg) or {}
    base = reg / "fact-base.json"
    try:
        if base.is_file() and base.stat().st_mtime > (reg / FILE).stat().st_mtime:
            return []
    except OSError:
        return []
    return [{"what": f"Check before the first look: {c['said']}", "bad": c["state"] == FAIL,
             "clears": c["fix"] or "Nothing before the code reader runs; if it is stopped for time, choose more time"}
            for c in got.get("checks") or [] if c.get("state") in (FAIL, WARN) and c.get("check") != "run status page"]


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(argv)
    if args[:1] == ["answer"]:
        test = "--test" in args
        args = [a for a in args if a != "--test"]
        words = args[args.index("--words") + 1] if "--words" in args and args.index("--words") + 1 < len(args) else ""
        if len(args) < 3:
            print('usage: preflight.py answer <register> <1|2> --words "<their words>"', file=sys.stderr)
            return 2
        import run_lock
        run_lock.guard(pathlib.Path(args[1]).resolve())
        said = answer(args[1], args[2], words, test=test)
        print(said, file=sys.stderr if said.startswith("REFUSED") else sys.stdout)
        return 2 if said.startswith("REFUSED") else 0
    if len(args) != 1 or not (pathlib.Path(args[0]) / "sources.csv").is_file():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    got = run(args[0])
    print("\n".join(lines(got)))
    return 1 if any(c["state"] == FAIL for c in got["checks"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
