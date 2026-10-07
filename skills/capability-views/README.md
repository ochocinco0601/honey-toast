# capability-views — early release 0.1

Draws the design-for-operations map and views of one business capability, from its code, documents and
people, as one self-contained HTML page. The views are the map (capability, flows, stages, steps, the parts
carrying each step, what they depend on), what each layer could report, each AI agent as its own system,
and where a failure reaches. They describe design, not a running system.

**This is an early release.** It does the whole path, from naming a capability to a drawn page, but every
part is a draft: the procedure, the register's columns and the drawing. Expect to correct what it
produces. A later release will fold it into the design-for-operations skill.

## How to start

1. Put this folder where your assistant finds skills: `.github/skills/capability-views/` in a workspace,
   or your personal skills folder.
2. Open the workspace that holds (or can reach) the capability's repositories, and ask:
   *"Draw the map and views for the [capability name] capability"*, naming the repositories, documents and
   people you have.
3. The assistant asks for anything missing, fills a register in `capability-views/<capability>/`, and
   draws `views.html` there. It then lists what is not assessed, where sources disagree, and what needs
   a person's yes.
4. When a new source turns up (a missing repository, a document, a person's answers), ask it to update
   that capability's map with the new source. It adds a pass to the same map rather than starting again.

**Needs:** Python 3 (standard library only). A code reader is optional. If the design-for-operations skill
is installed, its fact extractor is used; otherwise the assistant reads the code itself and marks what it
found as proposed.

**Check the install:** in this folder, `python -m unittest` runs 48 tests: 47 pass and 1 is skipped by
design (contracts at handoffs, which are not built).

## What is in the folder

| | |
|---|---|
| `SKILL.md` | The procedure the assistant follows: frame, read sources, fill the register, draw, present |
| `FILL-STEPS.md` | The detailed steps for filling a register, and for updating one when a new source arrives |
| `register-template/` | The blank register; `REGISTER.md` defines every table and column |
| `method/` | The method's closed lists |
| `capability_views.py` | Checks a register and draws the page |
| `click_check.py`, `test_capability_views.py`, `fixtures/` | The program's tests |
| `registers/eshop/` | A filled register for a public sample shop, as a worked example |

## Not done yet

- **Contracts at handoffs** between teams are not built.
- **Drafts within the drafts:** the order of calls within a step, the parts of an outside service, and
  links to another owner's map are built and tested but not yet reviewed as method.
- **The order of calls within a step shows only a strict sequence.** It is the form of a C4 dynamic
  diagram, a UML sequence diagram and arc42's runtime view, but with one position number per call. It
  cannot show branches, parallel or asynchronous calls, loops or returns, so calls that branch are left
  unnumbered.
- **Two gaps in `FILL-STEPS.md` / `REGISTER.md`:**
  - "When something new arrives" says to put a disagreeing source's account "in `note`". But
    `subjects.csv` and `measures.csv` have no `note` column. For now, add a second row instead.
  - The update steps say to add the parts a new source shows. Step 5 leaves out monitoring and platform
    tooling. And nothing says what to do with a part a document names but the code lacks. For now, apply
    Step 5's exclusion. Add a part the code lacks as `proposed:`, cite the document, and give it no
    participation rows.
- **Not yet tested cold** on an application nobody has mapped before, and not yet tested by stopping a run
  part way and resuming in a new session.
- **No run status file:** a run's state is its register, `sources.csv` and `how-made.csv`.
