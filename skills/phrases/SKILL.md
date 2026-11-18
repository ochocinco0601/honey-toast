---
name: phrases
description: >
  The person's phrases for asking the team of AI sessions for a view of the work: commander's
  intent, essential statement ("boil it down"), back brief, pre-mortem, playback, concept of
  operations (CONOPS), sitrep, update brief, design walkthrough ("walk me through it"),
  decision brief, whose call is this, demo, debrief, after-action review (AAR). Use when the person types
  "/phrases", or "phrases" on its own (show the table and let them choose); asks "what are my
  phrases"; uses one of the phrases to ask for a view of the work in front of them ("sitrep",
  "back brief on this", "play that back to me", "CONOPS for this", "update brief", "walk me
  through what you built", "boil this down to the essential statement", "whose call is this?",
  "is this mine or yours?"); or says they don't
  know what to ask the team or that the work feels like a black box. Here "sitrep", "update
  brief" and "decision brief" mean a chat message to the person about the work in front of
  them (for an update brief, all of it). A briefing
  document for someone else (leadership, a status report), or a portfolio-wide "orient me" or
  "brief me" with no phrase, belongs to a skill for that if one is installed. Do NOT use when a
  phrase's word just comes up in ordinary talk ("the demo on Friday", "the video playback", "walk me through how
  rebase works", "I can't see what's wrong in this stack trace", "update the CONOPS"
  or "update the brief" meaning a document, "who decides the budget at work?"), and never send a view unasked: a reply to a question is a
  reply, an update is an update.
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
| asks to boil this work down, or for its essential statement | An essential statement of the work in front of them. "Boil it down" said about something else (an article, a log) is not a request. |
| asks whose call the matter in front of them is, in any words ("whose call is this?", "is this mine or yours?", "is this my call?", "who decides this?") | Give the whose-call view. If it is unclear which matter they mean, ask which. |
| asks who decides something outside this work ("who decides the budget at work?", "is the release date the manager's call?") | Not a request. Answer normally. |
| says they don't know what to ask the team, or that the work feels like a black box | Show the table and ask which view would help. |
| uses a phrase's word in passing ("the demo on Friday", "I debriefed my manager") | Not a request. Answer normally. |
| asks to write, update or read a document ("update the CONOPS", "edit the CONOPS for design-for-operations", "update the brief") | Not a request for a view. It is work on that document. |
| asks "any updates?" or "give me an update" | Not an update brief unless they name it. Answer normally. |
| asks for an explanation of something general ("walk me through how rebase works"), or is debugging ("I can't see what's wrong here") | Not a request. Answer normally. |
| asks an ordinary question, gives direction, or says "ok" / "push it" | Not a request. Answer normally. A reply is never dressed up as a view. |

Never send a view unasked. Views are not pushed at set moments: it is hard to tell when one is due without dressing ordinary replies up as views. The "When in the work" column says when a phrase fits if they ask for it. It is not a moment to send one.

## The phrases

The phrase comes first because it is what the person picks by; the other columns tell them which one fits.

"Rung" is how far down the ladder of abstraction the answer goes: **top** is purpose and end state; **high** is every thread at a glance; **middle** is one task or decision; **low** is the built parts and the files; **ground** is the thing itself, working on their screen.

| Phrase | When in the work | Rung | What they get | The form of the answer |
|---|---|---|---|---|
| **commander's intent** | Before | top | why this work, its end state and boundaries, and where it stands | purpose; end state; phases, with where we are; boundaries |
| **essential statement** | Whenever your inputs have tangled | top | what everything else rests on, in a few lines | the need; the problem underneath it; what good enough is; a line or two each |
| **back brief** | Before | middle | how a task will be done, before it starts | the outcome; who does what; the steps, each with its check; where you come in |
| **pre-mortem** | Before | middle | "imagine this failed: why?", the risks named before building | each likely failure, its early sign, and what is done about it |
| **playback** | Before building on what was heard | top | the team's understanding of what you want and why, the whole of it, for you to correct | each concern on its own, in your terms; what came from you and what the team inferred; what the team would build on that understanding |
| **concept of operations** | Before building, once the intent is set | top | how the thing will be used once it exists: by whom, when, and what happens, seen from its users' side | who uses it and in what situation; what it has to do for them; one real scenario walked start to finish; what is outside it |
| **sitrep** | During | high | where every thread stands now | one row per thread: state, next, waiting on you?; then what waits on you |
| **update brief** | Start of a day, or coming back after time away | high | what moved since you last looked, across every part of the work | the point it counts from; one section per part (team or workstream): what changed since then, where it stands against the plan, what it needs from you today; then the decisions waiting on you, in one list |
| **design walkthrough** | During | low | what is being built, shown on a real example | what it works from; each part with your case's data; where it is thinnest |
| **decision brief** | At a choice | middle | one decision, on its own | the options and what each leaves; what stays the same; the recommendation; what agreeing commits you to |
| **whose call is this?** | Whenever something is in front of you and you want to know who decides it | middle | the session's reading of who does what on it and what it recommends, before anything is done on it | who produces it, and what is yours to judge, each with its kind in plain words; why, in a line; the recommendation and its grounds, in a line; how to answer; then it stops |
| **demo** | After a piece | ground | the built thing working on your screen, as its user meets it | open on your screen; before and after side by side |
| **debrief** | After, nothing to demo | middle | what was asked, done and changed, and where it lives | what I understood; what I did, by meaning; what changed for you; the key files; what is open |
| **after-action review (AAR)** | After a piece, to learn from it | middle | what was meant to happen, what did, why, and what changes | those four, about the piece |

Sources, for the session only and not shown with the table: US Army (commander's intent, back brief, sitrep, decision brief, after-action review, and the update brief: the commander's or battle update brief, a daily battle-rhythm event, FM 6-0); IEEE 1362, superseded by ISO/IEC/IEEE 29148, which splits it into an organisation-level ConOps and a system-level operational concept (OpsCon); the users'-view form used here is the OpsCon (concept of operations); McMenamin and Palmer, Essential Systems Analysis (1984), whose essential model is the problem stated free of any implementation (essential statement); Klein (pre-mortem); playback: the word from IBM Enterprise Design Thinking's Playbacks, the meaning from requirements practice (BABOK v3 §4.3, Confirm Elicitation Results); Yourdon (design walkthrough); Disciplined Agile (demo); the mission debrief (debrief); whose call is this?: who holds which decision, Rogers and Blenko, "Who Has the D?", Harvard Business Review (2006), and suggest and wait for approval rather than act and inform, Sheridan and Verplank (1978), levels of automation, level 5.

## Giving a view

- Answer at the phrase's rung and in its form, and no other. A sitrep is not a debrief with extra rows.
- Build it from the real state: read the work's record, the version history and the open issues first. A view written from memory of the conversation is the black box with a format on it.
- A view covers the work the person names or points at, by default the work this session is on. "One level up" or "two levels up" aims it at what that work is part of, or what it serves, as the work's record states it. When the record does not say what sits above the work, stop there: say in one line that nothing above this work is recorded, and offer the same view at this level. Do not give the current-level view in its place, and do not invent what sits above.
- A phrase is a request for a view, never a decision or a go. A back brief does not start the work; a decision brief waits for their answer.
- Inside a view, never name the frameworks. The sources are for the session; the table is shown without them.
- Rules the table is too short to carry, followed in every view: a demo is never a description, mock-up or test result; a debrief is grouped by meaning, never a file dump, with a count for the files not linked; an after-action review never narrates the session's process; a decision brief ends with how to answer; a back brief says what the person will see at each step; a playback is understanding, not a plan, so it carries no steps, and it marks each point as theirs or inferred; it is built from the person's own words, quoted and cited from the work's record and from this conversation (one of three views that may draw on the chat, with the essential statement and whose call is this?, because the chat is where their words, and the matter in front of them, are); and it is the team's whole understanding on request, not shape-ask's read-back of one imprecise ask.
- An essential statement distils the person's inputs, from the chat and the work's record, into the session's own words in the field's terms, never their words quoted back. It carries no history, mechanism or invented measures, and no phases, status or boundaries (that is commander's intent). It is the whole work reduced, not shape-ask's read-back of one ask, and it does not ask them what is wrong with it in place of doing the distilling.
- A concept of operations describes the thing in use from its users' side, not how the team will build it (back brief) or the parts once built (design walkthrough). When the work already has a concept of operations document, build the view from it and cite it. Its users and its scenario come from the work's record, named as the record names them; never an invented user or a made-up scenario. When the record names no users or holds no scenario, say which is missing, give the rest, and stop there.
- An update brief covers every part of the work, not one thread: by default everything in flight as the record shows it (the open issues and project board, and the version history), unless they name a piece of work. It opens with the point it counts from: the time they named; else the last update brief or sitrep given to them, in this conversation or the record; else the start of the previous working day. It states that point in its first line so they can correct it. It reports only what changed since then; a part with no change says so in one line rather than being left out. A sitrep is any-moment state; an update brief is change since a baseline.
- End the view with what waits on them, if anything. If nothing does, say so in one line.
- A whose-call view splits the matter into who produces the answer and what is the person's to judge, each kind shown with its plain meaning, never the label alone: **fit** (does it serve the need, is it what you meant), **warrant** (is trusting the answer justified), **craft** (form, structure, technique: the session's to produce). A matter the session produces is almost always still the person's to judge for fit or warrant, and the view says so; it never says a matter is not theirs to judge. The recommendation carries its grounds in one line: who checked it, against what, and what they found, or that nobody has yet. It ends with how to answer (agree, change it, or take it yourself), which is what waits on them, and stops: nothing is done on that matter until the person answers about it, even when the session reads the matter as its own; "ok" or "go" on it is an answer, and other work goes on. If something was already done on the matter before they asked, say that first, plainly.
- A decision brief here is a chat message, not a document: the bottom line first, the options in their terms, assumptions and risks stated, and a clear ask.

## Changing the phrases

The table ships as a starting set. Add a phrase as a new row only when the person adopts one.
