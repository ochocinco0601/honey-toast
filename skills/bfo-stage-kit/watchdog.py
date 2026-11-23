"""The run's watchdog: not the lead, and no model. The page listener runs it every CHECK_SECONDS for every run it
serves; it reads each run's state (run_state.state, the one the page shows) and keeps which stop was last told, by
the stop's stable identity (its code, step and flow): each stop is told once, and again only after the run worked
since; the first look at a run (a listener started on a run already stopped) tells none. Telling is a notifier the
caller passes; the kit itself passes none yet (no desktop notification: a stopped run shows in the page's tab title
and banner). Python standard library only."""
import json
import pathlib
import time

CHECK_SECONDS = 20
SEEN = "_run-state/watch.json"  # {"state", "key", "told"}: the last state seen and the stop last told


def _load(reg):
    try:
        return json.loads((pathlib.Path(reg) / SEEN).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _save(reg, got):
    p = pathlib.Path(reg) / SEEN
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(got) + "\n", encoding="utf-8")


def check(reg, notify=None, now=None):
    """Read one run's state and record it; on a change to stopped or finished not yet told, call `notify` once (when
    one is given). A stop's told mark clears only after the run has worked run_state.TOLD_RESET_SECONDS without a
    break, never on a flash of work. Returns the state."""
    import run_state
    now = time.time() if now is None else now
    st = run_state.state(reg)
    seen = _load(reg)
    key = st.get("key") or st["state"]  # the stop's code, step and flow: stable while the stop lasts
    told = (seen or {}).get("told")
    since = ((seen or {}).get("working_since") or now) if st["state"] == run_state.WORKING else None
    if since is not None and now - since >= run_state.TOLD_RESET_SECONDS:
        told = None  # worked long enough without a break: a next stop, even the same one, is told
    changed = seen is not None and seen.get("key") != key  # a first look at a run is no change
    if changed and st["state"] in (run_state.STOPPED, run_state.FINISHED) and key != told:
        if notify is not None:
            if st["state"] == run_state.STOPPED:
                notify("Run stopped: it needs you", f"{st['reason']} {st['next']}".strip())
            else:
                notify("Run finished", "The final check passed. Open the run status page for the report.")
        told = key
    _save(reg, {"state": st["state"], "key": key, "told": told, "working_since": since})
    return st


class Watchdog:
    """For the listener's loop: check every run of the site at most once every CHECK_SECONDS. Never raises."""

    def __init__(self, site):
        self.site, self.last = site, 0.0

    def tick(self):
        if time.time() - self.last < CHECK_SECONDS:
            return
        self.last = time.time()
        try:
            import work_page
            regs = list(work_page.runs(self.site))
        except Exception:  # noqa: BLE001 - a kit without it, or a record mid-write: never stop the listener
            return
        for reg in regs:
            try:
                check(reg)
            except Exception:  # noqa: BLE001 - one run's record mid-write never stops the others' watch
                continue
