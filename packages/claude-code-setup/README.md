# Claude Code setup

Two optional changes to a person's own Claude Code configuration. Each is independent; apply only the ones the person asks for. Written so an assistant can apply them: read the whole section first, merge into existing files rather than replacing them, and show the person each change before saving it.

Both go in the person's **user** configuration (their home folder), so they apply in every project. Nothing here goes in a shared repository.

Managed settings set by an organisation override user settings. If a change has no effect, check whether a managed setting overrides it, and leave it there.

---

## 1. Chrome DevTools MCP server

**What it does.** Gives the assistant tools to open a page in Chrome, take screenshots at chosen sizes, read console errors and run Lighthouse. Skills that judge a rendered page need it; without it they can only read the source.

**Before adding it.** It is installed through npm on first use. Run `npx --version` in a terminal. If that fails, or the network blocks the npm registry, stop: get Node.js and registry access through the organisation's approved route first. Chrome must be installed.

**Change.** Add a user-scoped server named `chrome-devtools` with this configuration (Windows):

```json
{
  "type": "stdio",
  "command": "cmd",
  "args": ["/c", "npx", "-y", "chrome-devtools-mcp@latest", "--isolated", "--no-usage-statistics", "--no-performance-crux"]
}
```

- Where the `claude` command is available in a terminal, add it with `claude mcp add-json chrome-devtools '<the JSON above>' --scope user`, the supported route (https://code.claude.com/docs/en/mcp). Run that from Git Bash: cmd does not accept single quotes, and Windows PowerShell strips the inner double quotes, so the JSON arrives broken.
- Otherwise it goes in `~/.claude.json`, under its top-level `mcpServers` key, as `"chrome-devtools": { … }`. That file also holds Claude Code's own state: copy it to a backup first, add only this entry, change nothing else, and restart Claude Code.

On macOS or Linux, use `"command": "npx"` and drop `"/c"` from the arguments.

- **`--isolated`.** Runs Chrome with a fresh temporary profile, so the assistant never sees the person's logins, cookies or history. The browser can still reach any site this machine can, internal ones included, run scripts in pages and upload local files to them.
- **`--no-usage-statistics`.** Turns off the usage statistics the server sends to Google by default.
- **`--no-performance-crux`.** Stops the performance tools sending page URLs to Google's Chrome UX Report service. Both flags are described in the server's README: https://github.com/ChromeDevTools/chrome-devtools-mcp
- If Chrome is not in its default location, add `"--executablePath=<path to chrome>"` to the arguments.

**Check.** Start a new session and ask it to open `https://example.com` and take a screenshot.

---

## 2. Turn off the option picker (optional)

**What it does.** Stops the assistant from opening the multiple-choice question dialog, so it asks in plain text in its reply instead.

**Where your own permission rules apply** (no organisation setting overrides them), add a deny rule in `~/.claude/settings.json` and stop there:

```json
"permissions": { "deny": ["AskUserQuestion"] }
```

Keep any `deny` entries already present.

**Where they are ignored.** When an organisation's managed settings make managed rules the only permission rules (`allowManagedPermissionRulesOnly`), a user's own `deny` rule has no effect, but user hooks still run unless managed settings disable them. Use a hook instead. It only removes a tool from the person's own assistant; it grants nothing a managed setting withholds.

**Change.** In `~/.claude/settings.json`, add a `PreToolUse` hook. If the file already has a `"hooks"` key, add the `"PreToolUse"` entry inside it; if it already has `"PreToolUse"`, add this object to that list.

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "AskUserQuestion",
      "hooks": [
        {
          "type": "command",
          "command": "python -c \"import sys; print('Do not use the option picker. Ask the question in plain text in your reply.', file=sys.stderr); sys.exit(2)\""
        }
      ]
    }
  ]
}
```

Exit code 2 from a `PreToolUse` hook cancels the tool call and passes the message back to the assistant. Source: https://code.claude.com/docs/en/hooks. It needs Python 3 on `PATH` as `python`: check that `python --version` prints a Python 3 version first. On Windows, `python` can resolve to the Microsoft Store alias, which exits with an error instead of running, so the hook would block nothing and say nothing; use `py` if only the launcher is installed.

**Check.** Start a new session and ask something open-ended, such as "help me choose between two approaches". The reply should ask in text, with no dialog.
