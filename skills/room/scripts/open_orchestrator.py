"""Open a new Claude Code tab in VS Code, pre-filled to run the room's orchestrator.

The working session must not convene its own room, so the orchestrator runs in
a session of its own. The VS Code extension registers a URI handler,
vscode://anthropic.claude-code/open, that opens a new Claude Code tab and
pre-fills its prompt box. The prompt is pre-filled, NOT submitted: the user
presses Enter once in the new tab. Nothing documented submits it for them.

  python open_orchestrator.py                 orchestrator for the calling session
  python open_orchestrator.py --session <id>  orchestrator for another session
  python open_orchestrator.py --repeat        a standing room (/room repeat) instead
  python open_orchestrator.py --print         print the URI only; open nothing

The calling session's id comes from CLAUDE_CODE_SESSION_ID, which the harness
sets. The tab opens in whichever VS Code window has focus, so the orchestrator
checks its own folder against the working session's before doing anything.

Keep the prompt short: the session id and nothing else. The pre-answer never
travels in this URI -- the orchestrator asks for it by message once it is up.
"""
import os
import subprocess
import sys
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

HANDLER = "vscode://anthropic.claude-code/open"


def uri(session_id, repeat=False):
    verb = "repeat" if repeat else "orchestrate"
    prompt = "/room %s %s" % (verb, session_id)
    return "%s?prompt=%s" % (HANDLER, urllib.parse.quote(prompt, safe=""))


def open_uri(u):
    if sys.platform.startswith("win"):
        os.startfile(u)  # the same handler PowerShell's Start-Process uses
    elif sys.platform == "darwin":
        subprocess.run(["open", u], check=True)
    else:
        subprocess.run(["xdg-open", u], check=True)


def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return 0
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if "--session" in argv:
        i = argv.index("--session")
        sid = argv[i + 1] if len(argv) > i + 1 else None
    if not sid:
        print("No session id: CLAUDE_CODE_SESSION_ID is not set here. Pass --session <id>.")
        return 1
    u = uri(sid, repeat="--repeat" in argv)
    if "--print" in argv:
        print(u)
        return 0
    try:
        open_uri(u)
    except Exception as e:
        print("Could not open the URI (%s). Open a new Claude Code tab yourself and "
              "type:  /room %s %s" % (e, "repeat" if "--repeat" in argv else "orchestrate", sid))
        return 1
    print("Opened a new Claude Code tab with the prompt pre-filled:\n  %s\n"
          "It is NOT submitted. Tell the user: press Enter in the new tab." % u)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
