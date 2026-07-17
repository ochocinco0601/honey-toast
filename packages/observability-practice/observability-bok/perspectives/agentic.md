# Perspective — Agentic

**State:** Current — the stratum vocabulary is provisional (industry converging, not converged).

The context where a workflow step is **software that makes a judgment call** — review this document package, decide whether the case proceeds — and can therefore be **confidently wrong**: up, fast, error-free, and mistaken. This perspective describes how observability bends when a service contains such a step.

**Scope.** "Agent" carries three meanings in observability practice, and this perspective covers exactly one: the agentic step as an *observed subject*. It does not cover AI assistants that help run the observability practice itself ([KA12](../ka12-adoption-enablement.md) — practice distribution), and it does not cover agent-based instrumentation — telemetry collectors ([KA02.3](../ka02-signal-design.md#instrumentation-strategy)). A reader — or an AI assistant answering on a reader's behalf — asking *"how do we know an AI agent is actually working?"* is asking this perspective's question.

## What distinguishes this perspective

**The assumption that breaks.** Traditional observability rests on an assumption so old it is invisible: software is deterministic, so the specification is the answer key. "Wrong" shows up as errors, latency, or saturation — and the classic signal sets feel complete rather than arbitrary because they enumerate the failure modes of that contract: it did the thing too slowly, it visibly failed, demand moved, headroom ran out. An agentic step keeps the machinery contract and breaks the specification contract. Its spec is "exercise discretion well," and it can satisfy every mechanism expectation — successful responses, within latency budget, saturation nominal — and still have decided wrongly. That is a failure surface no classic signal watches: the judgment itself.

**One conditional stratum, not a new practice.** The Four-Layer Model stays intact. For qualifying services, one additional mechanism stratum activates — **Agent Workflow** *(conditional; provisional name — see the status note in [KA02](../ka02-signal-design.md#signal-type-taxonomy))* — answering the question none of the four layers asks: *are the discretionary steps deciding well?* Its signals are ordinary SLIs ("agreement ≥ 98% on the labelled set") that sit as diagnostic descent — the investigation path from a breached business signal down through the mechanism signals that explain it — under the Business Health signal, beside Application signals. Decision quality keeps a business-owned top: the correctness expectation itself is an ordinary Business Health effectiveness signal. Most services never activate the stratum.

**The design frame: a new hire with discretion.** Don't reason about the step as software; reason about it as a new hire whose job is judgment. What would an accountable owner insist on knowing about a person doing that job?

| The worry about the hire | Dimension *(provisional set)* | What measuring it takes |
|---|---|---|
| Are their calls right? | **Correctness** | An answer key — a **golden set** (cases with known answers, re-run per release) or a **judge** (a second opinion sampling live decisions) |
| Did they decide from the actual case file, or from what they imagined? | **Grounding** | Checking outputs against the inputs they claim to rest on — the fabrication check |
| Can they show their work? | **Traceability** | Reconstructing the decision: which decider (model + prompt + ruleset version), what inputs, what steps |
| Are they still the person you vetted? | **Drift** | Comparing today's input mix and decision distribution against the validated baseline |
| Do they know when *not* to decide? | **Escalation/Autonomy** *(candidate — not yet in the set)* | Abstention and deferral rate when uncertain or out of policy |

*The set is this body of knowledge's provisional synthesis, not an industry canon — the ingredients are named public sources (the NIST AI Risk Management Framework's trustworthiness characteristics, OpenTelemetry's GenAI conventions, the evaluation-taxonomy literature); the composition is this BOK's own, held open to refutation by real use: an accountable owner's worry that fits no dimension, or a production decision failure none would have caught, amends the set; industry convergence, as it lands, is reconciled into it.*

**Mostly familiar machinery — plus one genuinely new obligation.** Offline versus online evals are synthetics versus real-user monitoring. Decision provenance is deploy versioning applied to the decider — a wrong decision is attributed to a specific decider identity, and a silent model fallback *changes the decider*. Drift is baseline monitoring where the watched quantity is a decision distribution instead of CPU. The one slot with no traditional analogue is the answer key: determinism used to supply the reference for free, and for a judgment step the practice must now supply it — build and maintain the golden set or the judge that defines "right." Everything unfamiliar about agent observability radiates from that one obligation.

## KA Variations under this perspective

| KA | Variation |
|----|-----------|
| [KA01 Business Context](../ka01-business-context.md) | No new positions in the stakeholder → expectation → signal chain. The decision-quality expectation is elicited as an ordinary stakeholder expectation with a Business Health effectiveness signal — the stratum's descent hangs beneath it. |
| [KA02 Signal Design](../ka02-signal-design.md) | The taxonomy's conditional stratum is defined here — the provisional Agent Decision dimensions above, plus the machinery classic signals never needed: the answer key (a golden set or judge), decision provenance (which decider — model + prompt + ruleset version — made the call), and the offline/online eval split. |
| [KA05 Incident Response](../ka05-incident-response.md) | Silent Business Failure gains a second investigation branch: mechanism green, business failing, *and the failing function contains a judgment step*. The descent continues into the stratum — check correctness against the eval reference, grounding, a changed decider, distribution drift. |

The written standard ([IN-23](../instruments/in-23-observability-standard.md)) carries the stratum as one conditional row in its per-layer bar: *is the decision right, and how would we know?*

## Known gaps in this perspective

Held open deliberately, ruled only as real evidence accrues. Real use can refute or extend the dimension set — it cannot prove it: an onboarding where an accountable owner's worry fits no dimension amends it; a production decision failure no dimension would have caught amends it (the incident feedback loop); clean runs, in any number, accumulate survived challenges rather than proof. Worked examples render from real onboarded records, never constructed; when the first exists, it lands as the agent-conditional slice of the written standard's worked model ([IN-23](../instruments/in-23-observability-standard.md), Form A — the BOK's designed teach-by-example slot), and this page cites it rather than duplicating it:

- **Completeness of the dimension set.** Escalation/Autonomy is the named candidate; policy and authorization scope ("did it stay inside its authority?") is a known edge that fits none of the four cleanly.
- **An operational vocabulary beside the decision-quality one.** Per-decision cost, content refusals (a refusal is a decision, not a machinery error), model fallbacks (a fallback changes the decider), and memory-state evolution have no slot in classic operational sets.
- **Maturity varies across the machinery — by design, not oversight.** The onboarding interview that captures a service's record ([IN-19](../instruments/in-19-discovery-dialogue-protocol.md) is its facilitated form) elicits the stratum today, and the interview record serializes it; monitoring surfaces and production data models do not yet accept the layer. Simultaneous change across every artifact is not how practice matures; each piece advances when its own evidence arrives.
- **Industry state.** Converging, not converged — as of mid-2026: OpenTelemetry's model-call (client) GenAI conventions stabilized in early 2026 while its agent-level conventions remain in Development, and standards bodies have opened dedicated AI-agent standards work (NIST's AI Agent Standards Initiative, CAISI, February 2026). Expect this perspective to iterate more than its peers.

## Why this perspective matters

Ignore it and a service with a judgment step ships observable as a *service* but invisible as a *decider* — every dashboard green while the judgment quietly fails, until a business outcome exposes what no signal was watching. The stratum exists so that failure mode is watched the way every other failure mode already is: by a signal, at the layer where the failure lives.

## External references

- OpenTelemetry GenAI semantic conventions (`gen_ai.*`) — model-call (client) spans stabilized early 2026; agent-level spans still in Development. Decision provenance and trace attributes.
- NIST — the AI Risk Management Framework (dimension grounding: Valid & Reliable → Correctness; Accountable & Transparent → Traceability), and the AI Agent Standards Initiative (CAISI, announced February 2026)
- Evaluation taxonomies (LLM-as-judge, faithfulness/groundedness evaluators — the Arize/OpenInference and Traceloop/OpenLLMetry lineages) — the eval-reference machinery
- Osmani, Saboo & Kartakis, *The New SDLC With Vibe Coding* (Google, May 2026) — from the software-building side, independently states this perspective's core failure mode: *"a fluent output that skipped its verification steps is a more dangerous failure than one with a visible error"* (p22). Corroborates the answer-key obligation (*"set the bar at the eval, not the demo"*) and the output-vs-trajectory eval split. Boundary: it observes the agent as an *execution artifact* (traces, evals of the agent itself), **not** the business outcome the agent serves — the layer this perspective supplies.
- This BOK's read of the vendor landscape: fleet-governance platforms (agent inventory, policy, kill-switch) and execution-quality platforms (traces, evals) both observe the agent itself; the business-outcome layer — *is the business process the agent serves actually working?* — is the layer this methodology supplies
