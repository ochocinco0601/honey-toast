---
name: bfo-stage-kit
description: Describe one business flow of an application from its code, and for one stage of it propose what to measure, what to alert on, and a runbook per alert, then draw the whole flow as one map. Use when asked to map a business flow or business capability for operations, to work out what to monitor or alert on for a flow, or to write runbooks for a flow's alerts, for an application whose code is in the workspace. Design time only - it reads code, documents and recorded answers, never a running system. Use this rather than the older capability-views skill, which draws an earlier form of the same map and writes no alerts or runbooks.
---

# Business flow observability: one flow, one stage

This folder is the kit. Everything below calls it **the skill folder**. Wherever `FILL-STEPS.md` writes
`<skill>`, it means this folder, and the folders it names (`register-template/`, `reference/`, `method/`) are
inside this folder too.

## What to do

1. Read `FILL-STEPS.md` in the skill folder, then `register-template/REGISTER.md` and the reference files
   `FILL-STEPS.md` cites in `reference/`. Look at `example-eshop/` only to see what a finished register and its
   outputs look like. It is a different application and never a source of facts.
2. Follow `FILL-STEPS.md` from start to finish for the application whose code is in this workspace.
3. Write the register **in the workspace, not in the skill folder**: a new folder `bfo-work/<application>/` at the
   workspace root. That folder is `<your-folder>` in `FILL-STEPS.md`. Run the kit's scripts from the skill folder,
   exactly as `FILL-STEPS.md` writes them, with `<skill>` replaced by the skill folder's path.
4. Pick the application's main business flow, the one whose case the business most depends on, unless the person
   named one. Step 11 covers one stage per run, and a flow is covered when every stage has had one. Unless the
   person named a stage, do Step 11 first for the stage where a case most often waits or can be left stranded. If
   the register already exists, do Step 11 for the next stage that has none. Say which flow and stage you did, and
   which stages still have no Step 11.
5. Do not stop to ask the person anything. Where the code does not say something, infer it and label it
   `proposed:` with the reason. Never edit a generated file: fix the register and generate again.
6. When you finish, report the folder, the flow and stage, the check results, and anything you could not do.

## What the person gets

`USE.md` in the skill folder is written for the person running this. It explains what comes out, how to read it,
and what to check before taking it to anyone. `KNOWN-GAPS.md` lists what the kit is known to get wrong. Point the
person at both when you finish.
