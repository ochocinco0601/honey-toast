# Observability Discipline — Start Here

This is the observability discipline: a body of knowledge, an interview instrument, and a comprehension check. Nothing here is specific to one organization — it is the reference pattern, meant to be made real in your environment.

**What's in here**
- **`observability-bok/`** — the body of knowledge: knowledge areas, instruments (including the standard, IN-23), and platform perspectives. Begin at `observability-bok/start-here.md`. To grow or maintain it, see `observability-bok/contribute.md` and `observability-bok/maintaining-the-bok.md` — the latter includes a test suite an AI agent can run to keep the body of knowledge healthy.
- **`the-practice-system.md`** — the delivery model: who consumes observability work at which altitude, and how to slot an ask to the fitted form. Read before producing. The BOK is the depth behind it; this document is how you choose what to hand a given consumer.
- **`observability-bok.yaml`** — the machine-readable registry of the body of knowledge (its knowledge areas, instruments, perspectives, and relationships). An AI copilot consumes it to read the fabric structurally, and the maintainer-guide's mechanical checks validate against it.
- **`the-instrument-sud-v2.yaml`** — the interview that walks a team through defining what "working" means for one of their services.
- **`acceptance-test.md`** — a comprehension check: does a reader hold the whole of the discipline?

**How to use it**
Read the body of knowledge to learn what good observability looks like; run the interview to define it for a real service; use the acceptance test to confirm the understanding landed.
