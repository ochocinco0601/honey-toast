---
name: phrases
description: >
  The person's phrases for asking the team of AI sessions for a view of the work: commander's
  intent, back brief, pre-mortem, sitrep, design walkthrough ("walk me through it"),
  decision brief, demo, debrief, after-action review (AAR). Use when the person types
  "/phrases", or "phrases" on its own (show the table and let them choose); asks "what are
  my phrases"; uses one of the phrases to ask for a view of the work in front of them
  ("sitrep", "back brief on this", "walk me through what you built"); or says they don't
  know what to ask the team or that the work feels like a black box. Here "sitrep" and
  "decision brief" mean a chat message to the person about this work. A briefing document
  for someone else (leadership, a status report), or a portfolio-wide "orient me" or "brief
  me" with no phrase, belongs to a skill for that if one is installed. Do NOT use when a
  phrase's word just comes up in ordinary talk ("the demo on Friday", "walk me through how
  rebase works", "I can't see what's wrong in this stack trace"), and never send a view
  unasked: a reply to a question is a reply, an update is an update.
---

# Phrases: views of the work, on request

## The job this serves

The person directs a team of AI sessions and holds many threads at once. One level up, the job is that they can see, shape and judge the work while it runs, so it never becomes a black box. Two levels up, they can direct the team as a commander directs a staff: a short request, and a view comes back in a known form, without having to invent the question each time.

This skill is the step where the person asks for a view and a session answers. It receives one of three things: the bare word `/phrases`, a phrase, or the person saying they don't know what to ask. It hands back one of two things:
- **the table:** all the phrases, all columns, and a question about which view they want, for a bare `/phrases` or "I don't know what to ask";
- **a view:** at the phrase's rung and in its form, built from the real state of the work (the files, the issues, the version history, the work's own record), never from memory of the chat.

Done means the person can act on what they saw: pick a view, choose, redirect, approve or ask for the next one. A well-formatted answer that still leaves them unable to see the work is not done.

Three design choices hold it together. The person may not remember the phrases, but will remember there is a skill called "phrases", so the bare call shows the table and lets them recognise what they need. Views come only when asked. Most replies are not views.

## When it fires, and when it doesn't

| The person... | Do this |
|---|---|
| types `/phrases`, or "phrases" on its own | Show the whole table below, all columns, exactly as written: no cell shortened, reworded or dropped. Under the table, show this line as written: **Add "one level up" or "two levels up" to any phrase to aim it at the bigger piece of work this is part of.** Then ask which view they want. Don't pick one for them. |
| asks "what are my phrases" | Same: the whole table, all columns, never a bare list. The person orients by when in the work a phrase is used and how far down it goes, so the columns are the point. |
| uses a phrase to ask for a view ("sitrep", "back brief on this", "commander's intent for this stretch", "debrief, one level up") | Give that view, at its rung and in its form. |
| says "walk me through it", where "it" is what is being built in this conversation | A design walkthrough. If "it" could be more than one thing, ask which. |
| says they don't know what to ask the team, or that the work feels like a black box | Show the table and ask which view would help. |
| uses a phrase's word in passing ("the demo on Friday", "I debriefed my manager") | Not a request. Answer normally. |
| asks for an explanation of something general ("walk me through how rebase works"), or is debugging ("I can't see what's wrong here") | Not a request. Answer normally. |
| asks an ordinary question, gives direction, or says "ok" / "push it" | Not a request. Answer normally. A reply is never dressed up as a view. |

Never send a view unasked. Views are not pushed at set moments: it is hard to tell when one is due without dressing ordinary replies up as views. The "When in the work" column says when a phrase fits if they ask for it. It is not a moment to send one.

## The phrases

The phrase comes first because it is what the person picks by; the other columns tell them which one fits.

"Rung" is how far down the ladder of abstraction the answer goes: **top** is purpose and end state; **high** is every thread at a glance; **middle** is one task or decision; **low** is the built parts and the files; **ground** is the thing itself, working on their screen.

| Phrase | When in the work | Rung | What they get | The form of the answer |
|---|---|---|---|---|
| **commander's intent** | Before | top | why this work, its end state and boundaries, and where it stands | purpose; end state; phases, with where we are; boundaries |
| **back brief** | Before | middle | how a task will be done, before it starts | the outcome; who does what; the steps, each with its check; where you come in |
| **pre-mortem** | Before | middle | "imagine this failed: why?", the risks named before building | each likely failure, its early sign, and what is done about it |
| **sitrep** | During | high | where every thread stands now | one row per thread: state, next, waiting on you?; then what waits on you |
| **design walkthrough** | During | low | what is being built, shown on a real example | what it works from; each part with your case's data; where it is thinnest |
| **decision brief** | At a choice | middle | one decision, on its own | the options and what each leaves; what stays the same; the recommendation; what agreeing commits you to |
| **demo** | After a piece | ground | the built thing working on your screen, as its user meets it | open on your screen; before and after side by side |
| **debrief** | After, nothing to demo | middle | what was asked, done and changed, and where it lives | what I understood; what I did, by meaning; what changed for you; the key files; what is open |
| **after-action review (AAR)** | After a piece, to learn from it | middle | what was meant to happen, what did, why, and what changes | those four, about the piece |

Sources, for the session only and not shown with the table: US Army (commander's intent, back brief, sitrep, decision brief, after-action review); Klein (pre-mortem); Yourdon (design walkthrough); Disciplined Agile (demo); the mission debrief (debrief).

## Giving a view

- Answer at the phrase's rung and in its form, and no other. A sitrep is not a debrief with extra rows.
- Build it from the real state: read the work's record, the version history and the open issues first. A view written from memory of the conversation is the black box with a format on it.
- A view covers the work the person names or points at, by default the work this session is on. "One level up" or "two levels up" aims it at what that work is part of, or what it serves, as the work's record states it. When the record does not say what sits above the work, stop there: say in one line that nothing above this work is recorded, and offer the same view at this level. Do not give the current-level view in its place, and do not invent what sits above.
- A phrase is a request for a view, never a decision or a go. A back brief does not start the work; a decision brief waits for their answer.
- Inside a view, never name the frameworks. The sources are for the session; the table is shown without them.
- Rules the table is too short to carry, followed in every view: a demo is never a description, mock-up or test result; a debrief is grouped by meaning, never a file dump, with a count for the files not linked; an after-action review never narrates the session's process; a decision brief ends with how to answer; a back brief says what the person will see at each step.
- End the view with what waits on them, if anything. If nothing does, say so in one line.
- A decision brief here is a chat message, not a document: the bottom line first, the options in their terms, assumptions and risks stated, and a clear ask.

## Changing the phrases

The table ships as a starting set. Add a phrase as a new row only when the person adopts one.
