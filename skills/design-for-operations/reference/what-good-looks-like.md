# What good looks like — level one

*A specification of the target, not an instance of it. This says what must exist, what it is made of, and how you would know it is wrong. It deliberately stops short of content.*

---

## The shape

Three stacked views over one capability. Each answers a different person's question, is built from different material, and is measured in a different idiom. You drill from the top down; you never read one layer's claim as another layer's.

---

## Business process view

**Made of:** stages a business person would name unprompted, in the order work moves through them. Nothing that exists only because a system exists.

**Shows:** whether work is moving, at what volume, and where it stopped.

**Measured in:** business KPIs and lagging indicators — applications in flight, completion rate, aging work at a stage, drop-off between stages.

**Must not claim:** cause, or severity. A red stage says work is not progressing here; it does not say why, and it does not say how badly. Reading it as a diagnosis is the most common misuse of this view.

**Test:** hand it to someone who has never seen the systems. They can say what is wrong for customers without asking a follow-up question.

---

## Application process view

**Made of:** two kinds of thing, deliberately drawn apart.

- **Components** — the deployable units that realise one stage above. Carved by what can be separately deployed and separately failed, not by team or repository. A component is what you restart, scale or roll back.
- **Services** — the promises those components expose upward. A service has a name, a consumer and an SLI. It is the unit the layer above actually depends on.

Scoped by the stage, not by the org chart. Several components may realise one service.

**Shows:** which component in that stage is failing, and separately, whether the promise it participates in is still being kept. Location, not diagnosis.

**Measured in:** golden signals and SLIs — placed on the service, not inside the component. Latency, errors, traffic, saturation, measured where a promise is made and consumed.

**Must not claim:** cause. This view answers *where*; why runs one layer further down. It also must not claim business impact upward — a failing call is not automatically a stopped stage, and the mapping is asserted deliberately, not assumed. And a degraded component is not a breached service: if a second instance or a retry is carrying the load, the promise holds and the view must be able to say so.

**Test:** a responder can name the component to act on without opening a codebase — and can tell, without inference, whether anything upstream is yet entitled to care.

---

## Technology view

**Made of:** the hosts, queues, connection pools, third parties and platform dependencies the components sit on.

**Shows:** what is degrading underneath, ideally before anything above has noticed.

**Measured in:** resource and dependency health — this is where leading indicators live, because causes precede symptoms and causes are dependencies.

**Must not claim:** that its own health is anyone else's health. Green here is not green above; the layer is necessary, not sufficient.

**Test:** at least one signal here fires ahead of a business-stage symptom, and the path from it upward is walkable.

---

## How the layers hold together

Health composes upward and only upward: signals compose into service health, service health composes into stage health, stage health composes into the capability. Component health does not compose directly — it composes through the service, which is what makes a degraded-but-covered component visible without being alarming. Every element on a view traces back down to a code location, and the chain is walkable in both directions.

Each layer is carved by a different tradition, and they are not interchangeable. The business process view is carved by **bounded context** — coherent business meaning, its own vocabulary, its own owner. The application process view is carved by the **deployable unit**, C4's container, because *where* has to resolve to something a responder can act on. The technology view is carved by what a thing runs on. Borrowing one layer's carving for another produces views that are internally sensible and operationally useless.

The four concerns distribute across the stack rather than sitting on one view: **impact** and **throughput** are asked of the business process view, **where** of the application process view, **cause** of the technology view, **trend** of all three.

Escalation follows from the split: a red component is a ticket, a breached service is a candidate for a page, and the page itself fires on the business stage above it — the symptom, not the location.

---

## Completion criteria for the set

- Each view states its question on its face.
- Every claim on every view traces to something in code or runtime.
- Every boundary is either owned or visibly named as unowned.
- Every service names its consumer, or it is not a service.
- The drill-down works: any red stage leads to a service leads to a component leads to a dependency, without a leap of inference.

---

*Level two would take one view and specify its elements. Not yet.*
