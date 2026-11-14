# The launch

The first message of every run of this skill. The start step (`start.py`) prints it as the first part of its MESSAGE, with the last part filled from what the request gave (`--gave`), followed by the page line and the page's address; the session sends that MESSAGE as it is and never writes the launch itself.

<!-- launch -->
**Where things stand:** Starting · Nothing read yet · Next: a first look over the system · Waiting on you: nothing

**What this does.** It reads a system's code and documents and works out how to tell whether the business work the
system does is getting done, and what to do when it is not.

**What goes in.** The system's code, and any documents, diagrams or notes you have about it.

**What comes out.**
- A map of the system's business flows, on a page that opens in your browser.
- For the stages you choose: what to measure, the alerts, and a runbook (the steps a responder follows) for each alert.
- Every statement traced to the code, or marked as a proposal for someone to confirm.

**What the map is made of.**
- The *capability*: what the system does for the business, such as selling goods online.
- Its *business flows*: each one piece of work carried from start to end, such as placing an order.
- Each flow's *stages*, each stage's *steps*, and the services that carry each step.

**The steps.** I stop only where your choice is needed, with a recommendation.
1. Looking over the system. I stop for you to pick the first flow, unless your request already asked for every
   flow.
2. Describing the flow from the code.
3. Naming the capability and what to measure. I stop for your pick of how far each stage goes (unless your
   request already said), and to review the measures.
4. Alerts and runbooks for the stages you picked. I stop for your review of the alerts before any runbook.
5. Checking against the code and drawing the map.
6. Final check and report. Then I offer you the next flow.

Each message opens with a line like the one above: what has been drafted, what is next, and what waits on you. Your
tools may ask you to approve my reading files;
approving lets the work go on.

**What I need to begin.** {begin}
<!-- /launch -->

The last part, by what the request gave. `{system}` is the system's name as the person said it (`--system`), else "this system".

<!-- begin code -->
You have pointed me at {system} and its code; that is all I need to begin the first look.
<!-- /begin -->

<!-- begin name -->
You have named {system}. I will first look for its code in what is open here; if it is not here, I will propose where to look, and search only where you agree.
<!-- /begin -->

<!-- begin nothing -->
Which system should I look at? Tell me what you have, as much or as little as you know: its name or only an idea of it, some of its repositories or all of them, documents about it. For what is not here, I will propose where to look, and search only where you agree.
<!-- /begin -->
