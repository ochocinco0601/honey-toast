---
name: skill-creator
description: >
  Create new Copilot skills or improve existing ones, and help the user think
  about how a skill could be tested. Use this skill whenever authoring a new
  `.github/skills/<name>/SKILL.md` file, revising an existing skill, evaluating
  whether a skill is well-constructed, or when the user asks how to test a
  skill. Triggers on "create a skill", "new skill", "write a skill for",
  "improve this skill", "is this skill well-written", "how could I test this
  skill", "skill template", "author a skill", or proactively when Copilot
  detects skill authoring or skill evaluation work. Encodes skill authoring
  principles from Anthropic's skill-creator plugin and the Claude Code team's
  skill taxonomy — adapted for GitHub Copilot's runtime.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Try the skill on a few realistic prompts
- Help the user evaluate the results qualitatively
- Rewrite the skill based on feedback from the user
- Repeat until you're satisfied

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress through these stages. So for instance, maybe they're like "I want to make a skill for X". You can help narrow down what they mean, write a draft, think about how it could be tested, try it on realistic prompts, and iterate.

On the other hand, maybe they already have a draft of the skill. In this case you can go straight to the iterate part of the loop.

Of course, you should always be flexible and if the user is like "I don't need to run a bunch of tests, just vibe with me", you can do that instead.

Cool? Cool.

## Communicating with the user

The skill creator is liable to be used by people across a wide range of familiarity with coding jargon. If you haven't heard, there's a trend now where the power of AI is inspiring plumbers to open up their terminals, parents and grandparents to google "how to install npm". On the other hand, the bulk of users are probably fairly computer-literate.

So please pay attention to context cues to understand how to phrase your communication! In the default case, just to give you some idea:

- "evaluation" and "benchmark" are borderline, but OK
- for "JSON" and "assertion" you want to see serious cues from the user that they know what those things are before using them without explaining them

It's OK to briefly explain terms if you're in doubt, and feel free to clarify terms with a short definition if you're unsure if the user will get it.

---

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding to the next step.

1. What should this skill enable Copilot to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.

### Classify the skill

Every good skill fits cleanly into one of these 9 categories. Name the category early in the interview. If the skill straddles multiple categories, that's a design smell — consider splitting into separate skills.

1. **Library / API Reference** — how to correctly use a library, CLI, or SDK. Often includes a folder of reference code snippets and a list of gotchas.
2. **Product Verification** — how to test or verify that code is working. Often paired with an external tool.
3. **Data Fetching & Analysis** — connecting to data stacks, canonical table/field references, common query patterns.
4. **Business Process & Team Automation** — repetitive workflows packaged as one command. Usually simple instructions but may have dependencies on other skills.
5. **Code Scaffolding & Templates** — framework boilerplate generation. Especially useful when scaffolding has natural language requirements that can't be purely covered by code.
6. **Code Quality & Review** — style enforcement, review patterns, quality checks.
7. **CI/CD & Deployment** — fetch, push, deploy workflows. May reference other skills to collect data.
8. **Runbooks** — take a symptom (alert, error, Slack thread), walk through a multi-tool investigation, produce a structured report.
9. **Infrastructure Operations** — routine maintenance and operational procedures, often with guardrails for destructive actions.

The best skills fit cleanly into one; the more confusing ones straddle several.

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until you've got this part ironed out.

If useful for research (searching docs, finding similar skills, looking up best practices), research inline. Come prepared with context to reduce burden on the user.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism — include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: Copilot has a tendency to "undertrigger" skills — to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal data.", you might write "How to build a simple fast dashboard to display internal data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    └── references/ - Docs loaded into context as needed
```

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited)

These word counts are approximate and you can feel free to go longer if needed.

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Copilot reads only the relevant reference file.

#### Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** - You can do it like this:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** - It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

#### Degrees of freedom

For each instruction in a skill, choose a level of freedom:

- **High freedom** (prose) — multiple valid approaches, Copilot decides based on context
- **Medium freedom** (pseudocode or parameters) — preferred pattern, some variation OK
- **Low freedom** (exact scripts) — fragile operations only, consistency critical

Default to high. Use low only where variance actually breaks things. Analogy: narrow bridge with cliffs (low freedom) vs. open field (high freedom). Don't put cliffs where there aren't any. If you find yourself writing all-caps MUSTs, that's a yellow flag — you've chosen low freedom; verify the operation actually needs it.

#### Build a named Gotchas section

The highest-signal content in any skill is the Gotchas section — specific failure modes the skill has hit, not general advice. Every skill should have a named `## Gotchas` section even if it starts empty with a note like "Populate as failures are observed." When the skill fails in a new way, update this section before doing anything else. Gotchas are the compounding interest of a skill: captured failures prevent recurrence, uncaptured failures recur forever.

### Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

**Don't state the obvious.** Copilot already knows a lot about coding and common patterns. Only add content that pushes Copilot out of its default way of thinking. For every paragraph in a skill draft, ask: "Does Copilot already know this?" If yes, cut it. Anti-example: a skill that says "use descriptive variable names" wastes context — Copilot already does this. Focus on what pushes the model beyond its defaults.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?"

**What realistic test prompts look like.** The queries must be realistic and something a real user would actually type. Not abstract requests, but requests that are concrete and specific and have a good amount of detail. For instance, file paths, personal context about the user's job or situation, column names and values, company names, URLs. A little bit of backstory. Some might be in lowercase or contain abbreviations or typos or casual speech. Use a mix of different lengths, and focus on edge cases rather than making them clear-cut.

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

**Coverage across test prompts.** Think about different phrasings of the same intent — some formal, some casual. Include cases where the user doesn't explicitly name the skill or file type but clearly needs it. Throw in some uncommon use cases. If you're testing description accuracy specifically, also write some **near-miss negatives** — queries that share keywords or concepts with the skill but actually need something different. Think adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't, and cases where the query touches on something the skill does but in a context where another tool is more appropriate. Don't make negatives obviously irrelevant; that doesn't test anything.

**Running the test cases.** For each test case, read the skill's SKILL.md and follow its instructions to accomplish the test prompt yourself. Do them one at a time. This is less rigorous than independent runs (you wrote the skill and you're also running it, so you have full context), but it's a useful sanity check — and the human review step compensates.

**Reviewing results.** Present results directly in the conversation. For each test case, show the prompt and the output. If the output is a file the user needs to see (like a .docx or .xlsx), save it to the filesystem and tell them where it is so they can download and inspect it. Ask for feedback inline: "How does this look? Anything you'd change?" Focus on qualitative feedback — what worked, what didn't, what you'd change about the skill's behavior.

### How skill triggering works

Understanding the triggering mechanism helps design better test prompts and descriptions. Skills appear in Copilot's available skills list with their name + description, and Copilot decides whether to consult a skill based on that description. The important thing to know is that Copilot only consults skills for tasks it can't easily handle on its own — simple, one-step queries like "read this PDF" may not trigger a skill even if the description matches perfectly, because Copilot can handle them directly with basic tools. Complex, multi-step, or specialized queries reliably trigger skills when the description matches.

This means your test prompts should be substantive enough that Copilot would actually benefit from consulting the skill. Simple queries like "read file X" are poor test cases — they won't trigger skills regardless of description quality.

---

## Improving the skill

This is the heart of the loop. You've tried the skill on test prompts, the user has reviewed the results, and now you need to make the skill better based on their feedback.

### How to think about improvements

1. **Generalize from the feedback.** The big picture thing that's happening here is that we're trying to create skills that can be used a million times (maybe literally, maybe even more who knows) across many different prompts. Here you and the user are iterating on only a few examples over and over again because it helps move faster. The user knows these examples in and out and it's quick for them to assess new outputs. But if the skill you and the user are codeveloping works only for those examples, it's useless. Rather than put in fiddly overfitty changes, or oppressively constrictive MUSTs, if there's some stubborn issue, you might try branching out and using different metaphors, or recommending different patterns of working. It's relatively cheap to try and maybe you'll land on something great.

2. **Keep the prompt lean.** Remove things that aren't pulling their weight. Make sure to read back through how you used the skill, not just the final outputs — if it looks like the skill is making the model waste a bunch of time doing things that are unproductive, you can try getting rid of the parts of the skill that are making it do that and seeing what happens.

3. **Explain the why.** Try hard to explain the **why** behind everything you're asking the model to do. Today's LLMs are *smart*. They have good theory of mind and when given a good harness can go beyond rote instructions and really make things happen. Even if the feedback from the user is terse or frustrated, try to actually understand the task and why the user is writing what they wrote, and what they actually wrote, and then transmit this understanding into the instructions. If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a yellow flag — if possible, reframe and explain the reasoning so that the model understands why the thing you're asking for is important. That's a more humane, powerful, and effective approach.

4. **Look for repeated work across test cases.** Read back through how you used the skill and notice if it repeatedly produced similar helper outputs or took the same multi-step approach to something. If all 3 test cases resulted in the skill producing a similar structure, a similar helper script, or a similar explanation, that's a strong signal the skill should bundle that pattern — either as explicit content in the skill itself, or as a reference file the skill points to. Write it once, put it in the skill, and tell the skill to use it. This saves every future invocation from reinventing the wheel.

This task is pretty important (we are trying to create billions a year in economic value here!) and your thinking time is not the blocker; take your time and really mull things over. I'd suggest writing a draft revision and then looking at it anew and making improvements. Really do your best to get into the head of the user and understand what they want and need.

### The iteration loop

After improving the skill:

1. Apply your improvements to the skill
2. Try the test prompts again and show the user the new results
3. Ask for feedback
4. Improve again, repeat

Keep going until:
- The user says they're happy
- The feedback is all satisfied
- You're not making meaningful progress

---

## Anti-patterns to avoid

When authoring skills, avoid these patterns:

- **Windows-style paths** — use forward slashes everywhere
- **Time-sensitive information** — "as of Q1 2025..." silently goes stale
- **Inconsistent terminology** — pick one term per concept and reuse it throughout the skill
- **Deeply nested references** — Copilot only partially reads files more than one level down from SKILL.md. Keep reference files flat.
- **Magic numbers without explanation** — always explain why the number
- **Assuming tools are installed** — state the dependency explicitly
- **Too many options** — provide a default with an escape hatch rather than a menu of choices

---

## Core loop recap

Repeating one more time the core loop here for emphasis:

- Figure out what the skill is about
- Classify it into one of the 9 categories
- Draft or edit the skill
- Try the skill on realistic test prompts
- With the user, review the outputs qualitatively
- Repeat until you and the user are satisfied

Please add steps to your TodoList, if you have such a thing, to make sure you don't forget.

Good luck!

---

## Gotchas

Failure modes Copilot hits when authoring skills, despite the directives above:

1. **Writes an essay instead of an instruction.** Skills are directives, not explanations. If a section reads like documentation, it is probably wasted context budget. Cut it or convert it to imperatives.
2. **Description is a summary, not a trigger.** "This skill explains X" fails to tell Copilot when to invoke it. Description must name the specific situations that should activate the skill, and be a little pushy to counteract the undertriggering tendency.
3. **Copies an existing skill wholesale as a starting point.** Inherited content rarely pulls its weight — each paragraph from the template should be evaluated against the "don't state the obvious" test before keeping it.
4. **Skips classification because the skill feels like it fits everywhere.** Every useful skill maps to one primary category. "Everything" is a sign the skill is too broad and should be split.
5. **Never updates the Gotchas section after observed failures.** The Gotchas section is the compounding interest of a skill. Failures that are not captured will recur forever.
6. **Tests the skill only on easy prompts.** Simple queries like "read file X" don't exercise the skill and may not even trigger it. Test prompts should be substantive enough that Copilot would actually benefit from consulting the skill.
