# The Methodology — Business Observability

This page explains what business observability *is* as a methodology. The rest of this body of knowledge (BOK) organizes the knowledge; this page names the thing being organized.

## The core claim

**Observability begins with defining success in business health terms — not with telemetry.** Traditional monitoring starts with the data you can collect (metrics, logs, traces) and layers business meaning on top when time permits. Business observability reverses that order. Business context is defined first. Signals are designed to measure that context. Everything downstream — dashboards, alerts, playbooks — derives from the business definition, not from whatever the platform happened to collect.

This ordering is a deliberate departure from the industry's common default, chosen for a testable reason: a telemetry-first practice produces comprehensive dashboards that an executive cannot use to answer *"is the business healthy right now?"* A business-context-first practice can.

## The Four-Layer Model

| Layer | Question it answers | Primary owner |
|-------|---------------------|---------------|
| Business Health | Is the stakeholder expectation being met? | Product Owner |
| Business Impact | How bad is it when we fail? | PO + Ops / Compliance |
| Application | Is the workflow executing correctly? | Developer / QA |
| System | Is the platform operational? | SRE / Platform |

Application and System validate the mechanism (up, fast, correct). Business Health validates the intended outcome. Business Impact quantifies the consequence when outcomes miss. A service can be green on Application and System (workflows running, infrastructure healthy) while failing on Business Health (business outcomes not met). That gap is why the business layers exist.

**The conditional stratum — Agent Workflow (provisional name).** When a workflow step is software that makes a judgment call — software that can be *confidently wrong*: up, fast, error-free, and mistaken — the model activates one additional mechanism stratum for that service. It answers the question none of the four layers asks: *are the discretionary steps deciding well?* Its signals are ordinary SLIs that sit alongside Application signals as diagnostic support for Business Health. The stratum is conditional (most services never activate it) and its vocabulary is explicitly provisional — the industry is converging, not converged. Taxonomy and dimensions: [KA02](ka02-signal-design.md#signal-type-taxonomy); the per-layer signal sets: [IN-23](instruments/in-23-observability-standard.md); the composed account: [the Agentic perspective](perspectives/agentic.md).

## The Semantic Chain

Every signal traces back to a business reason through an explicit chain:

```
[Stakeholder] has an [Expectation]
  which is measured by a [Business Health Signal]
    supported by [Application Signals] and [System Signals]
      if the expectation is breached → [Business Impact Signal]
        → [Alert] → [Owner + Next Action]
```

No signal exists without a stakeholder expectation it serves. No stakeholder expectation exists without a signal measuring it. The methodology requires the chain to be enforced structurally — in a conforming implementation, traceability is a data-model relationship, not a documentation convention.

## How this relates to SRE / SLO practice

SLO/SLI practice (Google SRE, Hidalgo) is compatible and upstream-consumed: an SLO is a quantified stakeholder expectation (Business Health). Error budgets are the reliability-velocity tradeoff made explicit within a business context. Business observability does not replace SRE — it extends it with the business-context layer that SLOs alone don't require. Teams with mature SLO practice have most of Business Health — and System/Application telemetry in abundance. What's typically missing is the structure around the SLOs: named stakeholder expectations each SLO serves, Business Impact quantification when one breaches, and the explicit linkage that ties existing telemetry into the chain.

## How this relates to telemetry pillars

The industry-standard pillars (metrics, logs, traces, profiles) are a classification by data shape. The Four-Layer Model is a classification by business meaning. Both are valid; they answer different questions. A well-instrumented service has signals across all pillars — this methodology organizes them by layer first, pillar second.

## What this BOK organizes

The rest of the BOK is the practitioner knowledge that makes this methodology operational — across the observability lifecycle (Define, Implement, Enforce, Observe, Respond), across the enabling capabilities (platform, integration, governance), and across the management practices (strategy, stakeholders, capability, adoption, improvement). 13 Knowledge Areas, 23 Practice Instruments. See [How the BOK is Organized](how-the-bok-is-organized.md).
