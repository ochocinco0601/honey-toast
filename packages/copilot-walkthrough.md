# Copilot Walkthrough

## Opening
- Your framing.
- Chat rule: setup problems go to chat, someone is watching there. Do not debug live.
- Named person on chat, confirmed at dry run. Presents nothing else. Watches for setup problems,
  pastes the step 5 prompt, pastes the full list at close.
- Preview the arc as questions, spoken not pasted: what does this thing do — what does it touch
  — what does it look like — where would I look — then write it down.
- Tell them the full list comes at the end, so nobody transcribes.
- Pre-empt wrong output. Copilot will sometimes be confidently wrong, and you will show it if it
  happens — because the skill being taught is *checking the answer against the repo*, not trusting
  it. Copilot cites the files it read; opening one and seeing whether the repo actually says that
  is the check. Free, and it is the whole competency. A wrong answer then lands as the lesson
  rather than as the demo failing. If nothing goes wrong, say what you would have checked.

## 0. Orientation, ~15 seconds
- File explorer panel — the cloned repo. Copilot is reading these files, not answering from
  general knowledge.
- Chat panel — where the prompt goes.

## 0.5 Setup check — hands-on
- Any trivial prompt that returns a response. Not a repo question.
- Fixed 60 seconds. Say beforehand you are running a clock and will move on regardless.

## 1. What is this thing — run live
- Model selection: auto picks for you; naming one gives you control. State your choice and why.
- *"What does this service do and who uses it?"*
- Narrate while it runs. The only response they watch arrive.
- State that steps 2–4 come from a session run earlier.

## 2. What does it touch — scrollback
- *"What does this service depend on, and what depends on it?"*
- Upstream, downstream, datastores, queues, external services. Answers who needs to be on the bridge.
- Spend the most time here.

## 3. Diagram — scrollback
- *"Diagram the dependencies."*
- Hover the Copilot icon: credits consumed against the allotment.
- Give them the number they actually want: what this costs **across a team**, not per answer.
  That is the manager's question.

## 4. Operational surface — scrollback
- *"How is this service configured, and what does it expose for monitoring?"*
- Config, health endpoints, logs, metrics.

## 5. Service overview document — hands-on
- Chat person pastes this prompt. The only one pasted mid-session.
- *"Create a service overview document for this repo."*
- Show yours, then they run it.
- Say before they run it that their output will differ from yours.
- State it is a first draft. A repo describes intent, not the running deployment.
- Skills menu: a dozen or more. Name two or three, do not tour them.

## Close
- Your framing.
- Chat person pastes all five prompts.
