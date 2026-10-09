# Vocabulary

The terms `FILL-STEPS.md`, the register and the generated files use, each defined once. Where a field already has a
term, the field's term is used.

## Levels: how far in a thing sits

| Level | What it is | Example (an online shop) |
|---|---|---|
| **Capability** | What the business is able to do, named apart from how it is built | Taking customers' orders |
| **Intended flow** | One path a single case takes through the business, start to ending, as designed | Placing an order |
| **Stage** | A stretch of the flow between two places where the case waits, or after a step that cannot be undone | Accept the order |
| **Process step** | One outcome inside a stage that the business would recognise, named without its performer | Stock is confirmed for the order |
| **Component** | A part of the application that delivers the capability: a service, a worker, a front end, a database, a broker | The ordering service; the ordering database |
| **External dependency** | Something the application calls, waits on or fails over to, and does not include | A payment provider |

**Relations.** A capability is **delivered by** flows (several, and a flow may deliver several): the two are
**cross-mapped**, and neither contains the other. A flow
**contains** stages; a stage **contains** steps. A component **performs** a step, or **supports** one it does not
perform (the step blocks or goes wrong without it). A component **depends on** an external dependency, which can also
**support** a step, or **perform** one itself where no component mediates it. Measures
never roll up past the flow: a component's error rate is not a fraction of a capability.

## Layers: two things share the word

| Name | What it sorts | Its values |
|---|---|---|
| **Architecture layer** | Parts, by what they are | ArchiMate's layers: business, application, technology. Services, workers, front ends and AI agents are ArchiMate **application components**. Databases, caches, message brokers, search indexes, file stores and hosts sit at ArchiMate's technology layer, even when the application owns them; this kit calls them **system components** (its own term, not ArchiMate's) |
| **Observability layer** | Measures, by the question each asks | business health, business impact, application, system (technology), and agentic where a step makes a judgment call. See `four-layers.md` |

A **level** says how far in a thing sits; a **layer** says what kind of thing or question it is. A component has a
level and an architecture layer; a measure has an observability layer.

## The case and its lifecycle

| Term | Meaning |
|---|---|
| **Observed flow** | The flow as it actually happened for one case, reconstructed from what the running system records: measured, not authored. The runtime counterpart of the intended flow, which is authored, not measured |
| **Case** | One individual business item a flow carries: one order, one application, one claim. Never a system, a batch or a request |
| **State** | Where a case is: as the system records it (a status value, a row), or `implicit:` where it plainly waits and nothing records it |
| **Move** | The act that takes a case from one state to the next. One row of `lifecycle.csv` |
| **Park** | A state where nothing is progressing the case and the next move needs a trigger not already in motion: a timer or schedule, a person, an outside party, the customer |
| **In act** | A state the case passes through while an act is still working (a message on its way to a consumer that will act on it, a call out and back) |
| **Path** | `main`; `alternative` (another ending the design allows: rejected, cancelled); `exception` (a failure the code reports back) |
| **Recovery** | What happens to cases when a move does not happen: `moves on` once the cause is fixed; `stranded` until someone acts; `not created` (the request fails and nothing is kept) |
| **Irreversible** | A move that cannot be undone: money taken, goods shipped, a filing made |
| **Promise** | The time within which a case should leave a stage, stated by a source or `proposed:` from the timing the design assumes |

## Measures

| Term | Meaning |
|---|---|
| **Measurement** | A number that exists about the system. Says nothing about whether anyone watches it |
| **Indicator** | A measurement chosen to show whether an expectation is met (a service level indicator) |
| **Objective** | A number agreed against an indicator over a window, with someone accountable for it (a service level objective). The kit never sets one: thresholds, windows and targets are the operators' values |
| **Impact** | The consequence when an expectation is not met, in the unit the affected party feels it. Category from `method/impact.csv` |
| **Diagnostic measurement** | A measurement about the mechanism, read to explain why an indicator moved |
| **Exists / proposed** | `exists` where the system already emits it (a log line counts, cited to the line); otherwise `proposed` |

## Marks used in the register

| Mark | Meaning |
|---|---|
| `proposed:` | Inferred, not stated by any source; the basis follows. A person confirms or corrects it |
| `partial:` | The step is carried only in part; what is missing follows |
| `stub:` | The step is carried by a stand-in (a hard-coded value, a simulated call) |
| `implicit:` | A state nothing records |
| `file:line` | The citation a claim rests on, in the application's code |
