# The observability layers

Each measure belongs to one layer, by the question it asks. The first two ask about the business outcome; the next
two about the mechanism; the fifth applies only where a step makes a judgment call. They are read outside-in: when
a business measure moves, the application and system layers explain why.

| Layer | The question | What it counts | Examples |
|---|---|---|---|
| **Business health** | Is the expectation being met? | Cases: how many reached the right outcome, within the time limit | Orders accepted within the time limit; applications decided right |
| **Business impact** | For how many cases is it not, and what does that cost? | Cases, in the unit the affected party feels: customers affected, money at risk, compliance cases, operational effort | Orders stranded with payment taken; order totals not collected |
| **Application** | Is the software executing the workflow correctly? | Requests, events and runs: errors, validation failures, operation completions, duration | Failed message handling; outbox publish failures; request errors |
| **System** (technology) | Is the platform the software runs on operational? | Resources: availability, latency, saturation, utilization | Database accepting connections; queue depth; broker reachable |
| **Agentic** (conditional) | Is a step that makes a judgment call deciding well? | Decisions: correct against a reference, grounded in its inputs, traceable | Share of decisions agreeing with a labelled set |

**Why all of them.** The application and system layers can be green while cases are failing, and the business
layers can show failure without saying where. A stage's proposed alerts are on the business layer, counted on cases. The
runbook's tests read the application and system layers to find the cause.

**Where each sits in the register.** `measures.csv` → `layer`. A system component (a database, a broker) is measured
at the system layer, never as an application. An external dependency is measured from the calling side.

**What a measure is about.** A business measure counts cases, never requests. A stage measure is counted from the
case's state changes at the stage's entry and exit: where cases wait inside it, and where they leave it. A part's
measure is that part's own (`method/part-kinds.csv` gives the set for each kind of part).

**The agentic layer is read at two grains.** At the **decision point**, a step the agent serves where it makes a
judgment (its participation row and the tool it calls there), the questions are whether the decision was right,
grounded, traceable and still the one vetted: correctness from the person's agreement or override on that decision,
grounding from checking the decision against the inputs it claims, traceability from a run and tool-call record that
carries the case, drift from that decision point's inputs and outputs against a baseline and the agent's
configuration. At the **run**, one invocation of the agent, the question is whether it operated: run duration, failed
tool calls and tokens (the OpenTelemetry GenAI conventions' operation and token metrics), refusals and fallbacks to
a person *[This practice]*. Run
measures are evidence about the agent's operation, never a judgment of whether it decided well.
