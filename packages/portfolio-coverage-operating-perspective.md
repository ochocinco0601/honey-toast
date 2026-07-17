# Portfolio Coverage — an operating perspective

A tool-agnostic operating perspective for running a portfolio-wide observability coverage
program: the aim, the standard to hold, the failure modes to watch, and the practices that
make coverage trustworthy. Written with generic terms — "the portfolio coverage view," "the
required standard," "a critical flow" — so it maps onto whatever tools an environment already
uses.

---

## The aim

One question drives the whole program: **at any moment, where is the problem?** A portfolio
coverage program exists to keep that answered across every application, all the time. Coverage
checks are the lever for that answer — never the goal in themselves. Everything below serves
this single aim.

## 1. Coverage is a means, not an end

A single roll-up view across every application — is each one covered by a working health
check, and is it green or not — so operations can start the day with "where's the problem"
already answered. The view adds no new tool; it is a front end over the checks teams already
run. Value comes from what the checks *confirm*, not from their presence.

## 2. The unit of work is a plan to get to green

For any set of failing checks, the operating request to each domain is a **plan to get them
to green** — owned by that domain, not a one-off central cleanup. Per failing check: if it is
misconfigured, fix it; if it never worked and adds no value, retire it. A red check that means
nothing is worse than no check — it teaches everyone that red is noise.

## 3. The bar is *confirmed* consistency, not mere coverage

"A check exists" is not the bar. The bar has three parts:
1. there is a **standard** for what "healthy" means for a given component,
2. builders are **building to that standard**, and
3. **someone confirms they built it** — rather than each team adding its own ad-hoc signal.

Hold the work to concrete specificity: *the exact query or signal that proves this component
is healthy*, not a description of one. And keep asking the harder question underneath it —
**how does a signal map to the business function it speaks for?** ("This signal degraded"
must be translatable to "this business capability is struggling.") That signal-to-function
registration is usually the missing mechanism.

## 4. A coverage signal can lie — green as well as red

Two failure modes, both of which destroy trust in the view:
- **False-red** — a broken or misconfigured check shows red and means nothing.
- **False-green** — a *missing* check shows healthy while the system is actually down. The
  view looks bright and green during a real outage because the health check was never
  configured.

False-green is the sharper danger: it hides outages behind a clean board. Both are why
coverage must be enforced *and* confirmed, not merely counted.

## 5. Climb the tiers of the signal

Three levels of coverage, worth climbing deliberately:
1. **Basic reachability** — scripted ping/port checks. Necessary but shallow.
2. **Metric-derived availability** — auto-populated from infrastructure exporters (messaging,
   databases, hosts). Stronger than ping-and-port, and it closes "dark" coverage
   *automatically* as it rolls out, without per-application effort.
3. **True end-to-end functional checks** — scripted checks that exercise a real business flow,
   including reusing pre-production test scripts in production.

"A flow, not just a ping" is the distinction that matters.

## 6. Enforcement is a maturity ramp, not a one-time decree

Enforce by tightening the standard progressively: start with the basics as required; promote a
capability from best-practice (beta) to required as it matures; then fold it into the required
standard. The common real problem is not the absence of a requirement but **evasion** of one
with loopholes — so the work is to update the standard *and* actually enforce it.

## 7. Toward business-derived coverage

The direction the program grows toward: **identify the business functions an application
supports, derive what to monitor from stakeholder expectations, and feed that into how
coverage is scored** — so the question becomes "do we have the *right* coverage," not just
"any coverage." Treat this as an emerging practice to prove out and grow into, not yet a hard
requirement to enforce on day one.

## 8. How to run the program

- **Convene by agreement.** Frame the forum as shared, and let each domain own its plan.
- **Organize around problem statements**, not tool demos — one problem theme at a time, each
  domain explains how it solves it, the group decides federated vs. central vs. hybrid.
- **Think in service-provider vs. consumer accountability**, not org-chart lines: who provides
  a capability is accountable for its coverage; who consumes it has a different obligation.
- **Don't over-commit the shape before it's settled** — name a direction without freezing a
  timeline the work can't yet support.

---

## Using this

Map the generic terms to your environment's real tools and views, then use this to anticipate
what a coverage program will demand: a *plan to green* per domain, a *confirmed standard* (not
just an existing check), a *signal-to-function map*, and a deliberate climb up the coverage
tiers. Pitch at the specificity the bar requires — the exact healthy-signal, not a concept —
and treat business-derived coverage as the direction to grow toward rather than a switch to
flip.
