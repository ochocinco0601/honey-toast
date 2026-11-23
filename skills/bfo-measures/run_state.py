"""The run's one state, for everything that tells the person about it: working, quiet, waiting (on the person),
stopped or finished. The run status page's badge, its step parts, its title, banner and browser notice, and the
listener's watchdog all read of() (state() reads the page's own model first), so none of them can say something the
others do not.

Stopped needs positive evidence, never a clock alone: the kit's stop record for the flow worked now (stop.json,
written by every kit step that ends a phase without a way on); a step the record says is blocked; the lead's turn
ended (its transcript's last reply called no tool) while no agent works and the step is not done; or no sign of any
agent past agents_now's own red limit. A lead quiet in the middle of its turn (a run of retries on the model, a
long command) is quiet, never stopped. Python standard library only."""
import json
import pathlib

STOP = "stop.json"  # in the register: {"code", "reason", "next", "flow"}, the kit's own record of a stop
WORKING, QUIET, WAITING, STOPPED, FINISHED = "working", "quiet", "waiting", "stopped", "finished"
IN_MOTION = (WORKING, QUIET)  # a run with work under way: its parts may say they are being read
# A lead's turn has ended only once its last reply (no tool call, end_turn) has had nothing after it for this long.
# The lines of one reply (thinking, text, tool call) can be written minutes apart, and a line partway through a
# reply can carry end_turn, so the limit sits well above any gap within one reply.
TURN_ENDED_SECONDS = 240
TOLD_RESET_SECONDS = 120  # a stop is told again only after the run has worked this long without a break
RESUME = "Ask the run's session to carry on (for example \"continue the run\"); it picks up where the run stopped."
TURN_ENDED = ("lead-turn-ended", "the session that runs it has ended its turn and no agent is working")
NO_SIGN = ("no-sign", "No sign of work for 40 minutes: check the run's Claude Code tab.")


def _flow(reg):
    import run_md
    return run_md.current_flow(reg)


def record_stop(reg, reason, next_step=RESUME, code="kit-stop"):
    """Write the kit's stop record for the flow worked now: a code that names the stop, why it stopped in one plain
    sentence of the kit's own, and what the person does next."""
    p = pathlib.Path(reg) / STOP
    p.write_text(json.dumps({"code": code, "reason": reason, "next": next_step, "flow": _flow(reg)},
                            ensure_ascii=False) + "\n", encoding="utf-8")


def clear_stop(reg):
    (pathlib.Path(reg) / STOP).unlink(missing_ok=True)


def read_stop(reg):
    """The stop record, when it is the flow worked now's; a record another flow left is no stop of this one."""
    try:
        got = json.loads((pathlib.Path(reg) / STOP).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not (isinstance(got, dict) and got.get("reason")):
        return None
    return got if (got.get("flow") or "") == _flow(reg) else None


def resumed(reg):
    """The run picked up again: its stop is over, and a first look the person stopped is asked afresh, never with the
    old question (first_look.READER_STOP once its answer was stop)."""
    reg = pathlib.Path(reg)
    clear_stop(reg)
    held = reg / "code-reader-held.json"
    try:
        if json.loads(held.read_text(encoding="utf-8")).get("stopped"):
            held.unlink()
    except (OSError, ValueError, AttributeError):
        pass


def _step(m):
    cur = m.get("current")
    steps = m.get("steps") or []
    return steps[cur]["title"] if cur is not None and 0 <= cur < len(steps) else "the current step"


def _one(state, code="", reason="", next_step=""):
    return {"state": state, "code": code, "reason": reason, "next": next_step}


def of(m, reg):
    """{"state", "code", "reason", "next", "key"} from the run status page's model `m` (its status, the agents'
    account and the current step) and the register's stop record. Only this function decides the run's state.
    `key` names a stop by its code, its step and its flow, never by words that change while it lasts."""
    got = _of(m, reg)
    got["key"] = f"{got['state']}|{got['code']}|{_step(m)}|{_flow(reg)}"
    return got


def _of(m, reg):
    status = m.get("status")
    if status == "finished":
        return _one(FINISHED, "finished")
    stop = read_stop(reg)
    if stop:
        return _one(STOPPED, stop.get("code") or "kit-stop", stop["reason"], stop.get("next") or RESUME)
    ag = m.get("agents") or {}
    if ag.get("at_work") or m.get("at_work"):  # an agent working, by its transcript or the case record
        return _one(WORKING)
    if status in ("waiting", "idle"):
        return _one(WAITING)
    if status == "blocked":
        return _one(STOPPED, "step-blocked", f"The run stopped at {_step(m)}: the step is blocked.", RESUME)
    if not ag.get("readable"):  # the agents' account cannot be read: no stop is said on the page's clock alone. A
        # run long silent waits on the person to resume it (the page's resume card); never a stop, never a notice
        return _one(WORKING if status in ("running", "starting") else WAITING if status == "paused" else QUIET)
    lead = ag.get("lead") or {}
    if lead.get("idle_turn") and m.get("current") is not None:
        return _one(STOPPED, TURN_ENDED[0], f"The run stopped at {_step(m)}: {TURN_ENDED[1]}.", RESUME)
    rows = ([lead] if lead else []) + list(ag.get("agents") or [])
    open_ = [r for r in rows if r.get("state") != "finished"]
    if open_ and all(r.get("state") == "red" for r in open_):
        return _one(STOPPED, NO_SIGN[0], NO_SIGN[1], RESUME)
    return _one(QUIET)


def state(reg, now=None):
    """The run's state now: the page's own model, which carries it (operator_page.read)."""
    import operator_page
    return operator_page.read(pathlib.Path(reg), now)["run"]


def title(st, name):
    """The page's tab title, from the state."""
    if st.get("state") == STOPPED:
        return f"STOPPED · needs you · {name}"
    if st.get("state") == FINISHED:
        return f"Finished · {name}"
    return f"Run status · {name}"
