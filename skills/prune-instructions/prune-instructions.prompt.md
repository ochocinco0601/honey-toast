---
description: Prune and restructure an overgrown copilot-instructions.md into the right Copilot layers, with checkpointed multi-session reliability
model: 'Claude Opus 4.6'
tools:
  - read
  - edit
  - execute
  - search
---

# Prune the Copilot Instructions

You are restructuring this repo's `.github/copilot-instructions.md` — an always-loaded file that has
grown too large. The goal is **not** to shorten it. The goal is that every line lives in the layer
where it earns its place. Length falls out of that.

This is a **large, multi-session job.** A big instructions file will not fit one Copilot context — the
session will summarize and continue, and anything held only in chat (the classification, the plan) will
degrade or vanish. So **all durable state lives in a progress ledger file on disk, never only in chat.**
Chat is disposable; the ledger is the source of truth.

---

## Reliability model — read first

- **Ledger file:** `.github/prune-instructions-progress.md`. It holds everything needed to resume:
  the classification table, the routing plan, and the apply-checklist (done vs pending).
- **Resume-first:** a session always begins by looking for the ledger and continuing from the first
  unfinished item. Never restart from scratch.
- **Checkpoint often:** after every expensive step and every applied edit, update the ledger and
  **commit it via the terminal** (`copilot-instructions.md` + the ledger together). A crash or summarize
  then loses nothing — and the commit history is a second resume trail alongside the ledger.
- **Batch the work:** classify and apply in small batches; persist each batch to the ledger before
  moving on. If it's not in the ledger, a summarize will lose it.
- **Hand off cleanly:** when context runs low, make sure the ledger is current, then tell the user
  exactly where things stand and that re-running `/prune-instructions` will resume from the ledger.

---

## The method

### The file is sediment
An always-loaded file accretes in layers, each rational when written, because the system has an
**addition trigger** (every failure spawns a line) and **no deletion trigger**. Two harms follow:
the reader changes with every model release (a line written for a *weak* model becomes a paralysis
*amplifier* under a strong one), and always-loaded text taxes every request, including the many that
don't need it. Misplaced residency is the problem, not length.

### The residency test — per line, mechanically
| Class | Definition | Verdict |
|---|---|---|
| **GATE** | Compliance checkable *outside the chat* — a file exists, a label is set, a commit has a shape, a test passes. | **Keep** in the always-loaded file. The only class with a record of changing behavior. |
| **FACT / POINTER** | Not an instruction — a statement or path ("X lives at Y"). | Keep **only as a hub** (one pointer per area). Detail moves out. |
| **CONDUCT** | Visible *only* in how the model writes/behaves — "be concise," "use a professional tone." | **Remove from the always-loaded file** (inert, or belongs in a scoped file). |

**Container rule:** "remove conduct" applies **only to the always-loaded file.** Conduct is legitimate
inside scoped `.instructions.md` and `.prompt.md` files — relocating it there is the point, not deleting
it. For surviving FACTs: **era-stamp** (written for a model/tool now gone? cut it) and **dormancy**
(would you just ask the model to look it up? cut the always-loaded line, keep the doc).

### The three Copilot layers — routing is the whole method
| Layer | File | Loads when | Holds |
|---|---|---|---|
| **Always-loaded** | `.github/copilot-instructions.md` | Every request | Always-true GATEs; FACT/POINTER hubs; invariants. |
| **Path-scoped** | `.github/instructions/<name>.instructions.md` (`applyTo:` glob) | When working on matching files | Conduct/rules specific to an area. |
| **On-demand** | `.github/prompts/<name>.prompt.md` (`/<name>`) | When invoked | Multi-step workflows. |

**Two-tier fallback:** if little is genuinely path-specific, or the middle tier won't be maintained,
collapse to two layers (always-loaded + prompts). An unmaintained `.instructions.md` is new sediment.

### Consumer check (skip if Copilot runs Claude)
The "conduct is inert" finding was measured on Claude reading its own instructions. On Claude/Opus the
method applies as-is. On a markedly weaker model, sanity-check once that it doesn't visibly degrade
without conduct scaffolding before deleting in bulk. Either way the net is **recurrence, not hoarding**:
delete inert conduct, work normally, re-add only what visibly breaks (one edit). Don't carry conduct
"just in case" — that's the no-deletion bias the method exists to break.

---

## The ledger format

Create `.github/prune-instructions-progress.md` with these sections, and keep them current:

```markdown
# Prune Progress — copilot-instructions.md

## Status
Phase: [inventory | classifying | planned | applying | verifying | done]
Source line count: NNN     Last checkpoint: [what was last persisted]

## Classification   (built in batches; this is the expensive artifact — persist it)
| # | line (abbrev) | class | era/dormancy | destination |
|---|---|---|---|---|
| 12 | "always be thorough" | CONDUCT | inert | DELETE |
| 13 | "tests live in /spec" | FACT | live | always-loaded (hub) |
...

## Routing plan   (filled at Plan step; approved by user before any edit)
- copilot-instructions.md (slimmed): keep #…, hubs #…
- .github/instructions/<name>.instructions.md (applyTo: …): move #…
- .github/prompts/<name>.prompt.md: move #…
- DELETE (proven-dead): #…

## Apply checklist   (one row per edit; mark as you go)
- [ ] remove lines #12, #27 (conduct)  — pending
- [x] move #40-46 → tests.instructions.md — done, committed
```

---

## Run protocol

0. **Resume check.** Search for `.github/prune-instructions-progress.md`. If it exists, read it and
   continue from the first unfinished item below. If not, create it from the format above.
1. **Inventory.** Read `.github/copilot-instructions.md`. Record the total line count and a numbered
   view in the ledger. *No edits.*
2. **Classify in batches — do not edit.** Take a manageable run of lines at a time. For each: GATE /
   FACT / CONDUCT, then era-stamp + dormancy on FACTs. **Write each batch's verdicts to the ledger
   before starting the next batch.** Note whether conduct clusters by path (decides two- vs three-tier).
   When the whole file is classified, present the table and **commit the ledger.** **Checkpoint.**
3. **Blind-check (optional, for a first large split).** True independence needs a context that hasn't
   seen your reasoning — Copilot has no subagent, so ask the user to open a **fresh Copilot chat**, paste
   the raw lines with the same classification task, and diff against the ledger. Divergences are where
   conduct got rationalized back in. Skip for small touch-ups.
4. **Plan — and stop for approval.** Fill the routing plan in the ledger (what stays, what moves where,
   what's cut). **Present the full plan to the user and get explicit approval before any edit.** Do not
   start editing until approved. **Commit the ledger. Checkpoint.**
5. **Apply piecemeal.** Edit the always-loaded file as **exact before → after, one change at a time,
   user confirms each.** After each applied change, mark it done in the ledger's apply-checklist and
   **commit** (the always-loaded file + ledger together). The always-loaded file is read by every
   request — surgery, not a sweep. If context runs low, the latest commit + ledger already hold the
   state; hand off and re-running resumes from there.
6. **Verify.** Open a file matching an `applyTo` glob and confirm scoped instructions engage; invoke a
   new `/prompt` and confirm it runs. Then watch real work — if a removed line's failure recurs, re-add
   it (to a scoped file, not the always-loaded one). When done and verified, delete the ledger and
   commit. Push when it suits your branch workflow.

---

## Hard rules

- **State lives in the ledger, not chat.** If it isn't written down, a summarize loses it. Persist
  after every batch and every edit.
- **Never restart from scratch.** Resume from the ledger.
- **Never bulk-rewrite the always-loaded file.** One confirmed change at a time.
- **Never delete knowledge — only change where it loads.** Cut a line only when proven-dead or
  proven-dormant; when unsure, relocate or keep.
- **"Remove conduct" applies only to the always-loaded file.** Conduct is legitimate in scoped files.
- **Route by class, not by line count.** Do not optimize for shortness.
