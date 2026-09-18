# Assessing whether a business capability is observable

*What the work is, in the field's own terms, with the practice each claim descends from.*

Nothing here is novel. Each claim below is a statement the field already makes, and where one
rests on a particular body of work, the citation under it says which. The purpose of setting
them out together is that the combination is what the work rests on, and a combination is easy
to drift out of without noticing which part was abandoned.

---

## What is being assessed

**Whether a business capability's behaviour can be determined from what its systems emit.**

Observability is the property that a system's internal state is determinable from its outputs.
A business capability is delivered by a flow of activity crossing several systems and several
owners, so its observability is the observability of the parts *and of the transitions between
them* — which no single part holds.

**The unit of assessment is one flow, because observability is a property of a traversal
rather than of an inventory.**

The same component can be adequately instrumented for one flow and blind for another. What
decides it is whether the particular transition through that component is visible. Assessing
an estate yields per-system coverage, which is what platform monitoring already produces, and
is exactly what cannot answer whether a payment that fails halfway through can be seen. The
gaps being sought are at the seams, and a seam exists only relative to a path crossing it.

**The flow's boundary is the expectation's boundary.**

It begins where the stakeholder's expectation begins and ends where that expectation is
satisfied or not. This is why a flow's stages are named as states reached rather than as
activities performed.

**The capability is the anchor, because an expectation must outlive the implementation.**

A stakeholder does not expect a particular flow to execute; they expect that the business can
do a thing. The flow is the means, and means change — a new path, a new service, a re-platform.
An expectation tied to the flow is orphaned by every re-implementation, and the observability
record has to be rebuilt each time. Tied to the capability it survives, which is what capability
modelling holds capability for: defined independently of people, process and technology, and
stable when any of those change underneath.

*BIZBOK; TOGAF Business Architecture.*

---

## The method, in four established steps

**1. Recover the structure from the system that exists.** The capability, the flow delivering
it, its ordered stages and steps, the components performing them, and the dependencies they
require.

*Architecture reconstruction and software archaeology; business capability modelling;
ArchiMate's business / application / technology layering.*

**2. State what would evidence health.** Whose expectation each element serves, the condition
that satisfies it, the indicator that would evidence the condition, and an objective where one
can be set. Stated before any measurement is chosen.

*Goal-Question-Metric (Basili); service level indicator and objective (Google SRE);
objective-as-code (OpenSLO, Sloth).*

**3. Compare that against what the estate emits.** The model on one side, the instrumentation
actually present on the other.

*Coverage analysis; conformance checking, de jure against de facto (van der Aalst); the
software reflexion model (Murphy, Notkin, Sullivan).*

**4. Render the comparison in standard views.** Swimlane, sequence, dependency matrix, register
— each declaring what it shows and what it cannot.

*BPMN swimlanes; UML sequence diagrams; the dependency structure matrix; the catalog. One model
through several views: ISO/IEC/IEEE 42010, C4.*

---

## The output is a measurement, and a measurement can come back complete

The result is the relation between what the capability requires in order to be observable and
what is observed. **Fully covered is a valid outcome**, and it has to be distinguishable on its
face from *not assessed*. An instrument that cannot report the negative case cannot be trusted
when it reports the positive one.

This is worth stating because the opposite framing is common and quietly corrosive: a method
whose stated purpose is *finding where nothing is watching* presupposes its own finding, and
cannot return a clean result without appearing to have failed.

---

## The six levels, and what each can report

Six kinds of thing. They differ in what observing them can tell you, and collapsing any two
destroys a distinction somebody downstream needs.

- **Capability** — reports coverage, and reports it derived rather than emitted: it has no
  executions of its own.
- **Intended flow** — reports completion. It finished or it did not.
- **Stage** — reports duration: how far one case got — one loan application, one payment, one
  order — and how long that stage took.
- **Process step** — reports health. It happened or it did not, and produced something or did not.
- **Component** — reports a diagnostic.
- **External dependency** — reports a diagnostic.

**They are not one ladder, and the relations between them are four different things.** A capability
and an intended flow are cross-mapped, many to many, and neither contains the other — one path
serves several capabilities, and one capability is served by several paths. A flow contains its
stages and its steps. A component realises a step. An external dependency is required by a
component.

**What that forbids is rolling anything up past the flow.** Summing across a many-to-many
cross-map double counts, and a realisation does not sum into the thing it realises. Measures
compose from step to stage to flow and stop there; above that they are derived or asserted, and
have to say which.

Three of the distinctions above carry more weight than the rest, and they are not all the same
kind of distinction.

**A capability does not run — a real distinction.** Nothing at that level executes, so any
statement about how a capability is doing was derived or asserted, never measured, and has to
carry which. Capability heat maps, maturity ratings and readiness figures are all real and all
made this way; forbidding the number does not prevent it, it only strips the provenance.

**Stage against process step — real, but not a limit on what can be known.** Unlike the other
two, this line marks no change in what is knowable. It is simply where measuring conventionally
begins — a habit of measurement rather than a property of the work — and it is the reason
duration data is so often missing: in most business processes the waiting term dominates the
working term by an order of magnitude, and a model that starts at the step cannot see it at all.

*Queueing theory (Kendall); value-stream mapping on value-added time against lead time.*

**Process step against component — the distinction that carries the most.** Above the line a
measure answers *did the business get what it expected*; below it, *how did the mechanism
behave* — a number that explains rather than answers. A component's error rate is not a fraction
of a capability, and summing one into the other is a category error. A draft that collapses
those two levels can no longer tell a stakeholder anything.

---

## Why capability nesting carries no level numbers

A capability contains capabilities, to any depth. Numbered tiers invite an argument about
whether something is a level-two or a level-three capability, which is an argument about the
numbering rather than about the business. Containment to arbitrary depth carries the same
information and has no such argument in it. This is capability inside capability, and it is not
what orders the six: the levels are an ordering by what each answers, not a hierarchy of one
inside the next.

---

## What is recent here is the mechanization, not the practice

A language model performs inference steps a person would otherwise perform — reading the source,
proposing the capability, drafting the expectation and its condition — and labels each output
with how it was obtained. The levels, the relations between them, the layering, the evidence
relation, the views and the artifacts are all pre-existing. Nothing in the list of citations
above was invented for this.

---

## Related

- **`assigning-business-work-to-levels.md`** — the procedure for deciding which of the six levels
  a given piece of business work belongs to, with the tests that justify each cut.
- **`design-for-operations.md`** — the method run as a sequence of passes, with the four views it
  gathers for.
- **`observability-practice/`** — the Body of Knowledge these rest on, including the Four-Layer
  Model that stratifies a service's signals into Business Health, Business Impact, Application
  and System.
