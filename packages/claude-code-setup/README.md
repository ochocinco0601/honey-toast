# Claude Code setup

Four optional changes to a person's own Claude Code configuration. Each is independent; apply only the ones the person asks for. Written so an assistant can apply them: read the whole section first, merge into existing files rather than replacing them, and show the person each change before saving it.

All of them go in the person's **user** configuration (their home folder), so they apply in every project. Nothing here goes in a shared repository.

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

---

Sections 3 and 4 are practices, not settings. For each one, decide how to put it in place in this environment: a block in the person's user instructions file (`~/.claude/CLAUDE.md`, loaded in every project: https://code.claude.com/docs/en/memory), a skill, or an addition to something already set up. Read what is already configured first, including any instructions the organisation manages. Show the person what you propose and where, and save it only when they agree.

## 3. Say back what the person's words mean (optional)

**What it does.** When the person's own words are written into a record, the assistant does not stop at copying them. It also writes, beneath them, what they mean in the field's terms, plays that back to the person, and records the answer in the same place.

**What must hold.** Everything in the block below. It is a reference, not text to paste: write it in the setup's own words, and keep every point.

```markdown
## When my words go into a record

When you write my words into anything kept that someone will read later (for example a work item, a note, a decision log or a handoff; these are examples, not the whole list), do steps 1 to 3, and the first half of step 4, in the same turn:

1. **Capture.** Keep my words verbatim. Do not condense or paraphrase them.
2. **Interpret.** Beneath them, write what they mean in the field's established terms, not in my working vocabulary or in a term you coined. Keep my hedges as hedges: "maybe" and "plausibly" stay a candidate, never a decision. Something I reported second-hand stays attributed to whoever said it. Anything you add that I did not say, such as an option I did not name, is labelled as your suggestion.
3. **Play back.** Show me every reading as a short list: my words, then what they mean. Ask whether they fit, and name the ones you are least sure of.
4. **Write back.** Put the reading in the record under my words, marked "unconfirmed" until I answer, then record my answer there too, with my words if I gave any.

A reading that exists only in the conversation is not done. This is elicitation validation: confirming with the stakeholder what was heard, before anything is built on it.
```

**Check.** Start a new session, say something hedged about a piece of work, and ask for it to be recorded. The record should hold your words, a reading in the field's terms marked unconfirmed, and the reply should ask you whether that reading fits.

## 4. Write work items to a standard (optional)

**What it does.** Applies one standard to every work item the assistant writes, whatever the person tracks work in: a tracker tool, or a folder per item.

**Before adding it.** Ask the person where their work items live and replace `<where my work items live>` in the block with their answer, for example "the issue tracker" or "one folder per item under C:\work\items".

**What must hold.** Everything in the block below. It is a reference, not text to paste: write it in the setup's own words, and keep every point.

```markdown
## Writing a work item

My work items live in: <where my work items live>. Whenever you create or change one, follow this:

- **The summary line says what is wrong, and for whom,** in plain words a stranger could picture. Not the task, not the topic, not the fix. A missing capability is stated flat as a lack ("A failed run cannot be resumed"). Name a party only if the description names one. Put no number, date, cause or consequence in the summary line that the description does not contain.
- **The description is for a later reader arriving cold** (another session, or me months from now). It carries the problem, how it was found, and enough context that the reader needs nobody for the backstory.
- **My words are kept verbatim**, with your reading beneath them, as in "When my words go into a record".
- **Your analysis goes under a heading that states its status and date**, such as "Proposed by the assistant (input, not decisions)". "Endorsed" means I said so; record what I said, nothing wider.
- **Open questions are listed**, including ones that would overturn your own reading. Write it so the next reader feels free to push back, not directed to comply.
- **It says what "done" means**: what will be true when this item can be closed.
```

**Check.** Ask a new session to record a problem you describe in a sentence or two. The item should have a summary line saying what is wrong, your words verbatim with a reading beneath, its open questions, and a done statement.
