---
name: model-lookup
description: Surface the conceptual models already built for a practice — the typed-slot structures (a business semantic chain, the four-layer signal model, a task-decomposition schema, the four model shapes, and ~20 more) catalogued in the model compendium — that are relevant to the work in front of the session, so it reaches for what already exists instead of groping or reinventing it. This is the human-invoked "turn the catalogue on" move: the user carries ONE cue, not the whole catalogue. Use this skill WHENEVER the user asks "what are the models for this?", "what models apply here", "which models fit this", "what models do we have for [X]", "model this", "is there a model for this", "have we modeled this before", "do we already have a structure/schema/typology for this", or otherwise asks whether there is already a model for the domain or problem in front of them — even when they don't name the compendium and even when the ask is casual. On trigger, load the compendium, judge which entries fit the current work, surface them by name with what-each-is-for and its shape, then name what fits — often one model, frequently a combination and how they compose (the seam), sometimes none. The session makes the fit call, including whether it is one or several; it does not hand the user a menu to pick from. Do NOT trigger for building or choosing a machine-learning, statistical, financial, or simulation model ("model the load if we 10x"), for a database/data schema for code, or for choosing which model to run a session on — those are a different sense of "model" and should fall through to normal work. A named external discipline (a security/threat model, STRIDE, etc.) is established prior art, not one of these originated models. This skill is about a practice's own conceptual models only.
---

# Model Lookup — turn the catalogue on

## Why this skill exists

A practice builds conceptual models — small fixed sets of typed slots with defined
relations that give messy reality a place to go — repeatedly, across a body of
work. Then they get lost track of: at the top of a session you don't remember *which*
models exist, so you never reach for one, so sessions grope and rebuild what is already
built.

You can't carry twenty models in your head. You *can* carry one cue — **"what are the
models for this?"** This skill is what that cue turns on. The compendium is the store;
this skill is the switch.

The deficit it repairs is **specific recall, not judgment.** You know what you're working
on; you just can't recall what's already been built for it. So this skill does the recall
for you — it does not decide your work, it hands you the models you'd have reached for if
you'd remembered them.

## What to do when this fires

### 1. Load the compendium
Read the model compendium (`model-compendium.md`) in full. It is self-contained — each
model's slots and relation are inlined, indexed by the model **shapes** (sequence / stack
/ set / trajectory, plus the candidate web/graph shape and a composite bucket). The shapes
are the index; the model entries are the contents.

### 2. Judge which models fit the work in front of you
Look at what the session is actually doing — the domain, the problem, the kind of
structure being reached for — and match it against the compendium. Matching is a judgment,
not a keyword scan:

- **By subject** — is the work in a domain a model already covers? (observability signals →
  the four-layer signal model; consumer/audience stratification → the consumer layers;
  decomposing an action → the task-decomposition schema.)
- **By shape** — is the session groping to *arrange* something? Name the shape it's reaching
  for (a sequence? a stratification? a typed set? a grid?) and surface the models of that
  shape as precedent, even from other domains — the shape transfers.
- **By the seam** — if the work has both structure and behavior-over-time, say so and point
  at both the structural model and the (thin) behavioral family.

### 3. Surface them — named, with what they're for
Lead with the fit — one model, or the *combination* that composes (name the seam that
joins them); include near-fits worth knowing about. For each: the model, what it is / its
slots, its shape, and one line on why it fits. Say plainly when nothing in the compendium
fits an aspect — that is a valid, useful answer.

### 4. Make the fit call — one, several, or none
You made the fit call in step 3 — act on it. **The fit is frequently a *combination*, not
one model** — a structural model + a behavioral one; a stack for "where it fits" + a graph
for "how it connects." Naming the composition — which models, and *how they join at the
seam* — IS the craft call. Do not collapse a real combination to a single "best" one for
tidiness; do not manufacture a combination when one model genuinely suffices. Because the
compendium inlines each model's detail, the model is *right there* once you name it — read
its entry and use it. Defer a choice to the user *only* when it truly turns on their intent
— and then frame it intent-keyed ("if you're doing X → this"), never as an open menu.

## Honesty rules — hold these, they are the whole value

- **"No model fits" is a valid, useful answer.** Like an established-prior-art "no match,"
  it tells the session the ground is open — build fresh (and the new model should later land
  in the compendium). Never force-fit a model that doesn't belong just to have something to say.
- **Respect the "under review" flag.** The business semantic chain is marked under review —
  its shape is settled, its exact slots are provisional. Surface it, but never present its
  slot list as settled, and don't have downstream work build on those exact slots.
- **Respect "superseded."** A superseded model (e.g. the Three-Signal model → the Four-Layer
  model) is surfaced only to point at its successor, never as the live answer.
- **Make the craft call — don't offload it.** Which conceptual model best fits a structural
  problem is *craft*, the session's job. Offloading it ("here are six, which do you want?")
  reintroduces the exact burden this skill exists to remove — the user can't be asked to pick
  among models they couldn't recall. So **name what fits — one model, or a composition and how
  the pieces join at the seam — with your reasoning.** The user rules only on *fit-to-intent*:
  if your call serves the wrong real-world goal, they redirect. Decide the model(s); let them
  decide the work.

## The boundary — what this is NOT

- Not for machine-learning / statistical / financial / simulation models, database schemas
  for code, or picking which model to run a session on. Those are a different sense of
  "model" and should fall through to normal work. A named external discipline (threat model,
  STRIDE) is established prior art, not one of these originated models.
- Not an environmental auto-fire — this is human-invoked, by design. The user supplies the cue.
- Not the place that *edits* the compendium. When a new model is born, that's the
  compendium's own upkeep, a separate concern from this lookup.
