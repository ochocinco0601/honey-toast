# Platform Capability Assessment — an operating perspective

A tool-agnostic frame for the situation where a consuming team needs a capability, the
platform team reports that the capability exists, and the consuming team's need is still
not met. Written in generic terms — "the platform," "the offering," "a consuming team" —
so it maps onto whatever platform, tooling, and org shape an environment already has.

**How to use this.** It is a frame, not a tutorial. It names the distinctions that make the
situation tractable and the established practices they come from. Apply it to the
conversation at hand; do not restate it back.

---

## The situation

A consuming team asks whether the platform supports something. The answer is yes. The answer
is true. The need remains unmet.

This is almost never a disagreement about facts. It is a collision between two unstated
scopes: the provider answers about the offering in principle, the consumer hears an answer
about what they can obtain. Both are speaking honestly.

The failure is that the question "do we have X?" has no single true answer, and nothing in
the exchange forces it to be decomposed.

## Decomposing the claim

Three levels, asked in order. Each presupposes the one beneath, and a claim cannot skip a level.

- **Presence** — does the capability exist in the offering at all? Answerable yes/no, and
  truthfully "yes" far more often than the consumer's experience suggests.
- **Coverage** — for which workload classes, which signal types, which consumers? This is
  where a narrowly scoped capability becomes visible. A capability scoped to one workload
  class is invisible at the presence level.
- **Depth** — how completely is it delivered inside that coverage? Only meaningful once
  coverage is established.

A capability can be genuinely present and have zero coverage for the workload class in front
of you. That is the common case, and it is what a presence-level answer conceals.

## The second axis: scope state

Status alone is not an answer. A capability's status has to name the state it holds, because
the same capability is honestly "yes" at one state and "no" at another.

- **Product capability** — the underlying technology can do this. "The tool supports it."
- **Available with engagement** — the platform team can stand it up for you, with effort.
  Off the paved road: possible, but bespoke and manual.
- **Self-service** — a consumer can obtain it without an engagement. Documented, supported,
  reachable.

Cutting across all three: **within limits.** A capability available in principle but capped
by ingest volume, cost ceiling, or entitlement is not available at the consumer's scale.
Record the limit, not just the capability.

Most disputes about whether a platform "has" a capability are this collision. The provider
answers at product-capability state; the consumer asked at self-service state.

## What gets recorded

A coverage matrix — the requirements-traceability instrument applied to platform capability.
One row per capability claim, with fixed columns: what the capability is, what workload and
signal class the claim is scoped to, what source data it requires, which level was asked,
status (`covered` · `partial` · `absent` · `unknown`), scope state, limits, the evidence
behind the status, the operational consequence if absent, and the date assessed.

Two disciplines make it worth anything:

- **`unknown` is a first-class value.** It converts a blank into an agenda item rather than a
  hole. A status held on the basis of experience rather than evidence is `unknown`.
- **Answers are recorded separately from the matrix**, as dated decision records the matrix
  points at. The matrix is a reading; positions belong to the team that owns the offering.

Present the matrix as a draft to be corrected, not a finding to be answered. The correction is
the point — it moves the yardstick from the assessor's to the group's.

## The shape of a well-formed request

The weak form asks for a gap to be closed. It invites a yes/no about one team's need and
produces a bespoke answer that helps nobody else.

The durable form asks the provider to **publish the offering's scope** — the coverage
statement itself. It is cheaper for the provider than repeated bespoke engagements, and it
means the next consumer finds the answer instead of booking a meeting.

A request carries more when it names:

- the **workload or signal class** the need sits in, not the capability in general
- the **operational consequence** of absence, stated as what cannot be done — not as complaint
- the **constraint the requester believes is blocking**, so it can be confirmed or corrected
- a distinction between **won't** (a scoping decision, legitimate and answerable) and
  **can't — supplier-gated** (the platform is itself constrained upstream). These have
  different escalation routes and conflating them wastes the exchange.
- an **escalation route** for questions the assessing team does not have standing to answer

## Failure modes to watch

- **Presence-level truth used as a full answer.** The most common one, and it is not dishonest.
- **Status without scope state.** "Supported" that means three different things.
- **The consumer maintaining a model of someone else's platform.** Legitimate as a bridge — it
  supplies an artifact that should exist so the conversation can happen — but it goes stale the
  moment the platform changes. The end state is a provider-published scope, not a better
  consumer-side map.
- **Answers that live only in a meeting.** Without a published position, the same question is
  re-asked by the next team, and the assessment accumulates nothing.

## Established practice this rests on

Named so the relevant knowledge can be loaded directly rather than reconstructed:

- **ISO/IEC 33004** — process assessment architecture. An assessment model is a reference model
  plus a measurement framework; the standard requires the reference model be *external* to the
  assessment. Separation here is architectural, not stylistic.
- **Google SRE Workbook, "Implementing SLOs"** — the SLI specification/implementation
  distinction, and the workload types (request-driven, pipeline, storage) with their SLI types.
  Scheduled and batch work is pipeline, not a fourth class.
- **ITIL** — service portfolio versus service catalogue. The portfolio is what exists; the
  catalogue is what a consumer can order. The distinction this whole frame turns on.
- **CNCF Platform Engineering Maturity Model** — the interfaces dimension, and the
  self-service / request-based / bespoke progression.
- **Platform engineering** — "paved road" and "golden path" as the name for the self-service
  state.
- **Requirements traceability matrix** — the record form.
- **Architecture Decision Record** — the form a recorded position takes.

---

*A capability assessment is a dated snapshot. It goes stale when the platform changes and
carries no claim of currency beyond its date.*
