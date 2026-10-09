# The observability layers

Each measure belongs to one layer, by the question it asks. The first two ask about the business outcome; the next
two about the mechanism; the fifth applies only where a step makes a judgment call. They are read outside-in: when
a business measure moves, the application and system layers explain why.

| Layer | The question | What it counts | Examples |
|---|---|---|---|
| **Business health** | Is the expectation being met? | Cases: how many reached the right outcome, within the promise | Orders accepted within the promise; applications decided right |
| **Business impact** | For how many cases is it not, and what does that cost? | Cases, in the unit the affected party feels: customers affected, money at risk, compliance cases, operational effort | Orders stranded with payment taken; order totals not collected |
| **Application** | Is the software executing the workflow correctly? | Requests, events and runs: errors, validation failures, step completions, duration | Failed message handling; outbox publish failures; request errors |
| **System** (technology) | Is the platform the software runs on operational? | Resources: availability, latency, saturation, utilization | Database accepting connections; queue depth; broker reachable |
| **Agentic** (conditional) | Is a step that makes a judgment call deciding well? | Decisions: correct against a reference, grounded in its inputs, traceable | Share of decisions agreeing with a labelled set |

**Why all of them.** The application and system layers can be green while cases are failing, and the business
layers can show failure without saying where. A stage's alert pages on the business layer, counted on cases. The
runbook's tests read the application and system layers to find the cause.

**Where each sits in the register.** `measures.csv` → `layer`. A system component (a database, a broker) is measured
at the system layer, never as an application. An external dependency is measured from the calling side.

**What a measure is about.** A business measure counts cases, never requests. A stage measure is counted from the
case's state changes: at the park where cases wait, or, for a stage that never parks, at its exits. A part's
measure is that part's own (`method/part-kinds.csv` gives the set for each kind of part).
