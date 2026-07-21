# Questions the BOK Answers

This page states the BOK's usefulness claim at full scope. Assuming all Seeded and Missing topics became Current, this is what the BOK should answer well — organized by what kind of answer it should produce. (Knowledge Area codes like [KA02.5](ka02-signal-design.md#semantic-conventions), instrument codes like [IN-16](instruments/in-16-onboarding-simulation.md), and the Current/Seeded/Missing content states are defined in [How the BOK is Organized](how-the-bok-is-organized.md).)

Each question in sections I–IV should reach a substantive answer through the BOK's structure. Each question in section V should be explicitly scoped out. A BOK that claims to answer everything claims to answer nothing; scope discipline is part of usefulness.

---

## I. Direct domain questions (definitional, methodological)

These are the "what is X?" class. The BOK should answer these from the content itself.

**Methodology questions**

- What is business observability? How does it differ from monitoring?
- What's the Four-Layer Model and why is it organized that way?
- When a workflow step is software that can be *confidently wrong* — up, fast, error-free, and mistaken — what does observability owe it? When does the Agent Workflow stratum *(conditional; provisional vocabulary)* activate?
- What's the semantic chain? Why does it start with stakeholders?
- Where do SLOs fit? How do they relate to error budgets?
- What's the difference between a signal and a metric?

**Role and accountability questions**

- Who owns defining stakeholder expectations? Who validates them?
- What's the Developer's role in signal design vs. the Product Owner's?
- Who owns alert configuration? Who owns escalation policy?
- What's the three-actor ownership model and where does it apply?

**Process / workflow questions**

- How do I construct a service profile?
- How do I write a stakeholder expectation that's measurable?
- What makes a signal production-ready?
- What's the incident response sequence when a business health signal fires?

**Taxonomy / location questions**

- Where does "quality gates in CI/CD" belong?
- Is capacity planning observability or platform engineering?
- Is this a signal problem ([KA02](ka02-signal-design.md)) or a monitoring problem ([KA04](ka04-monitoring-visualization.md))?
- Where does compliance integration live?

---

## II. Role / workflow-moment questions

Organized by who's asking and when. Each entry points to the KA/instrument that should be reached.

**Product Owner onboarding a new service**

- Who cares about this service? ([KA01.1](ka01-business-context.md#stakeholder-identification-expectations) + [IN-06](instruments/in-06-stakeholder-expectation-template.md))
- What happens to the business if it fails? ([KA01.4](ka01-business-context.md#impact-category-classification))
- What should I set as an SLO? ([KA01.6](ka01-business-context.md#slo-definition-error-budget-allocation))
- Where do I start? ([IN-16](instruments/in-16-onboarding-simulation.md) Onboarding Simulation)

**Developer implementing instrumentation**

- What signals should I instrument for this expectation? ([KA02.1](ka02-signal-design.md#signal-type-taxonomy) + [KA02.2](ka02-signal-design.md#signal-to-function-mapping))
- My service contains an agentic step — what additional signals does it need, and graded against what reference? ([Agentic perspective](perspectives/agentic.md) + [KA02.1](ka02-signal-design.md#signal-type-taxonomy) + [IN-23](instruments/in-23-observability-standard.md))
- Where should the signal be emitted? ([KA02.3](ka02-signal-design.md#instrumentation-strategy))
- What metadata needs to carry with every signal? ([KA02.5](ka02-signal-design.md#semantic-conventions))
- How do I avoid high cardinality costs? ([KA02.7](ka02-signal-design.md#data-cardinality-dimensionality) + [KA06.6](ka06-platform-tooling.md#observability-economics-cost-optimization))

**Platform Engineer / SRE responding to an incident**

- What does this alert mean in business terms? ([KA05.1](ka05-incident-response.md#triage-severity-determination) + [KA01.4](ka01-business-context.md#impact-category-classification))
- Who do I escalate to? ([KA05.2](ka05-incident-response.md#escalation-team-composition) + [KA08.5](ka08-data-governance.md#ownership-accountability))
- What playbook applies? ([KA05.3](ka05-incident-response.md#playbook-design-execution) + [IN-13](instruments/in-13-playbook-factory.md))
- What do we learn from this? ([KA05.4](ka05-incident-response.md#postmortem-learning))

**Platform Lead evaluating tools**

- Which tool is right for this signal type? ([KA06.1](ka06-platform-tooling.md#tool-landscape-selection))
- Should we consolidate or specialize? ([KA06.3](ka06-platform-tooling.md#consolidation-vs-best-of-breed))
- How do we control observability cost? ([KA06.6](ka06-platform-tooling.md#observability-economics-cost-optimization))
- How does this fit into our enterprise architecture? ([KA07.5](ka07-integration-architecture.md#enterprise-architecture-positioning))

**Practice lead planning adoption**

- How do we onboard the next team? ([KA12.1](ka12-adoption-enablement.md#onboarding-first-experience) + [IN-16](instruments/in-16-onboarding-simulation.md))
- What's in a transfer package? ([KA12.2](ka12-adoption-enablement.md#transfer-packages-enablement-kits) + [IN-17](instruments/in-17-transfer-packages.md))
- How do we scale from 5 teams to 50? ([KA12.4](ka12-adoption-enablement.md#scaling-patterns))
- Where's the friction? ([KA12.3](ka12-adoption-enablement.md#pilot-design-execution) + [IN-18](instruments/in-18-friction-logging-protocol.md))

**Architect integrating with the enterprise**

- How does observability connect to CMDB? ([KA07.1](ka07-integration-architecture.md#cmdb-service-registry-integration))
- Where does this fit in BIAN/ITIL/TOGAF? ([KA07.5](ka07-integration-architecture.md#enterprise-architecture-positioning))
- How does it integrate with CI/CD? ([KA07.2](ka07-integration-architecture.md#cicd-pipeline-integration))
- What about regulatory and compliance alignment? ([KA07.3](ka07-integration-architecture.md#regulatory-compliance-frameworks))

**Executive / Leadership reviewing portfolio**

- What's our observability maturity? ([IN-01](instruments/in-01-service-maturity-model.md) + [IN-02](instruments/in-02-industry-maturity-arc.md) + [IN-03](instruments/in-03-division-maturity-assessment.md))
- What's the state of the portfolio? ([IN-20](instruments/in-20-portfolio-maturity-view.md))
- Where should we invest? ([KA09.3](ka09-strategy-program.md#theme-prioritization) + [KA09.7](ka09-strategy-program.md#investment-justification-value-demonstration))
- How does this map to strategic priorities? ([KA09.1](ka09-strategy-program.md#enterprise-alignment) + [KA09.5](ka09-strategy-program.md#roadmap-altitude-cascade))

**Stakeholder / Communicator landing the message**

- How do I frame observability for this audience? ([KA10.2](ka10-stakeholder-engagement.md#cross-altitude-communication))
- What do executives need to see? ([KA04.5](ka04-monitoring-visualization.md#business-health-views) + [IN-22](instruments/in-22-executive-dashboard-patterns.md))
- Who are our champions? ([KA10.1](ka10-stakeholder-engagement.md#champion-networks))
- How do we position this to a new LOB? ([KA10.4](ka10-stakeholder-engagement.md#advocacy-positioning) + [IN-21](instruments/in-21-terrain-presentation.md))

**New practitioner learning the practice**

- Where do I start? (the hub README → The Methodology)
- What should I read first? ([the-methodology](the-methodology.md) → [KA01](ka01-business-context.md) → [KA02](ka02-signal-design.md))
- What does good look like? ([IN-04](instruments/in-04-service-profile-template.md) with worked example)

**Practitioner facing platform-specific variation**

- How does this apply to mainframe? (Mainframe perspective → variations)
- How does this apply to cloud-native? (Cloud-Native perspective)
- How do I handle cross-platform correlation? (Hybrid perspective)
- How do I observe a SaaS integration? (SaaS perspective)

---

## III. Traversal / investigative questions (the BOK's distinctive value)

These are the "walk through dependencies with state-awareness" questions. The BOK should do what classification alone cannot.

- **"We need better correlation capabilities."** Walk: [KA04.3](ka04-monitoring-visualization.md#cross-signal-correlation) depends on [KA02](ka02-signal-design.md) depends on [KA01](ka01-business-context.md). Content state at each stop reveals where the chain breaks. Investment conclusion: addressing [KA04.3](ka04-monitoring-visualization.md#cross-signal-correlation) without fixing [KA02](ka02-signal-design.md) is wasted.

- **"Our signals are noisy and alerts are unreliable."** Walk: [KA04.2](ka04-monitoring-visualization.md#real-time-monitoring) (monitoring) → [KA02](ka02-signal-design.md) (signal design — are signals well-designed?) → [KA03](ka03-standards-quality.md) (standards — are standards enforced?) → [KA08.5](ka08-data-governance.md#ownership-accountability) (ownership — is someone accountable for signal quality?). The noise is a symptom; the cause is usually upstream.

- **"Leadership can't see business impact."** Walk: [KA04.5](ka04-monitoring-visualization.md#business-health-views) (business health views) → [KA01.4](ka01-business-context.md#impact-category-classification) (impact categories) → [KA01.1](ka01-business-context.md#stakeholder-identification-expectations) (stakeholder expectations). If Business Health/Business Impact signals aren't defined, no dashboard can surface business impact. The problem is usually [KA01](ka01-business-context.md), not [KA04](ka04-monitoring-visualization.md).

- **"Our dashboards don't drive decisions."** Walk: [KA04.1](ka04-monitoring-visualization.md#dashboard-design-standards) (dashboard design) → [KA10.2](ka10-stakeholder-engagement.md#cross-altitude-communication) (cross-altitude communication) → [KA09.1](ka09-strategy-program.md#enterprise-alignment) (strategic alignment). Dashboard failure is often misaligned altitude or missing business-context context, not rendering choices.

- **"We can't get teams to adopt this."** Walk: [KA12.1](ka12-adoption-enablement.md#onboarding-first-experience) (onboarding) → [KA12.5](ka12-adoption-enablement.md#ai-mediated-practice-distribution) (AI-mediated distribution) → [KA10.1](ka10-stakeholder-engagement.md#champion-networks) (champion networks) → [KA11.5](ka11-organizational-capability.md#culture-mindset) (culture). Adoption stalls at specific points; the walk reveals which.

- **"This LOB's observability feels behind."** Walk: [IN-03](instruments/in-03-division-maturity-assessment.md) (maturity assessment) → [IN-01](instruments/in-01-service-maturity-model.md) (service maturity across portfolio) → [KA09](ka09-strategy-program.md) (strategic gaps) → [KA12.4](ka12-adoption-enablement.md#scaling-patterns) (scaling methodology).

- **"Incidents keep revealing context we didn't capture."** Walk: [KA05.5](ka05-incident-response.md#feedback-to-definition) (feedback to definition) → [KA01.1](ka01-business-context.md#stakeholder-identification-expectations) (stakeholder identification) → [KA08.3](ka08-data-governance.md#data-quality-currency) (currency). The lifecycle feedback loop is the mechanism; the gap is typically at [KA01](ka01-business-context.md) currency discipline, not [KA05](ka05-incident-response.md).

---

## IV. Meta / coverage questions

These ask the BOK about itself — what does it cover, where are the gaps, what's the state.

- **Do we cover topic X?** (Yes, Seeded, or Missing — honestly answered via content state discipline)
- **What state is KA X.Y in?** (KA Section 7 audit)
- **Where does this new concern fit?** (disambiguation tests from maintaining-the-bok Part I)
- **What's the dependency chain from X?** (KA cross-references)
- **Which KAs does instrument Y draw from?** (instrument page + KA Section 5)
- **What's the maturity across our portfolio?** ([IN-01](instruments/in-01-service-maturity-model.md) + [IN-20](instruments/in-20-portfolio-maturity-view.md) + [IN-03](instruments/in-03-division-maturity-assessment.md))
- **What platform types do we have perspectives for?** (Perspectives catalog)
- **What's missing from our practice?** (aggregate Section 7 Missing topics + Perspectives not yet authored)
- **How is this BOK structured?** ([how-the-bok-is-organized.md](how-the-bok-is-organized.md))
- **How does the BOK itself evolve?** ([contribute.md](contribute.md) + maintaining-the-bok.md)

---

## V. What the BOK is NOT for

Scope clarity matters. The BOK should explicitly not try to answer:

**Tactical vendor-specific implementation**

- What's the Splunk SPL query for a ratio signal? (Vendor documentation, not BOK)
- How do I configure a Prometheus exporter for mainframe telemetry? (Product docs)
- What's the Grafana panel JSON for the product and product-line rollup views? (Dashboard implementation notes)

**Real-time operational data**

- Is service X healthy right now? (Monitoring platform, not BOK)
- What's the SLO burn rate this week? (Observability platform)
- Which services are alerting? (Alert management)

**Incident-specific investigation**

- Why is service X slow? (Investigation using the BOK's methods, but the answer is in the data, not the BOK)
- What caused the outage at 3 AM? (Postmortem artifact, informed by [KA05.4](ka05-incident-response.md#postmortem-learning))

**Organizational specifics**

- Who's on the on-call rotation? (Team roster, not BOK)
- What's our OKR target this quarter? (OKR system)
- Which team owns this service? (Service catalog, referenced from BOK but not owned by it)

**Policy decisions**

- Should we buy tool X? (Decision made by an architecture team using BOK frameworks, not decided by the BOK)
- What's our cost target for observability? (Finance + FinOps decision, BOK frames the tradeoff)

The BOK is a methodological and structural resource. It defines how to think about observability, where concepts fit, who owns what, how dependencies connect, and what variations matter. It does not replace vendor documentation, live monitoring platforms, incident tooling, or organizational artifacts.

---

## The usefulness test

For the BOK to pass the usefulness test at full scope, every question in sections I-IV should reach a substantive answer through the BOK's structure. Every question in section V should be explicitly scoped out. The BOK's honesty is in both — not claiming to answer questions it can't, but claiming firmly the questions it does.

Currently, the BOK passes this test *structurally* (every question in I-IV has a home) but not *substantively* at every node. Some topics are Seeded; some perspective variations are queued. The frame is in place and declares itself, even where the content isn't complete yet.

If the test fails at a specific question — the BOK doesn't have a home for it — that's a structural signal per [Maintaining the BOK](maintaining-the-bok.md) Part VIII. The question tells you either a topic is missing, a perspective is needed, or a structural element needs revision.
