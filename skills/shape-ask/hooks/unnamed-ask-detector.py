#!/usr/bin/env python
"""UserPromptSubmit hook: make the shape-ask skill fire when an ask arrives without its name.

Why a hook: the skill's main failure is not firing. A skill description is a
request that the session notice something; an imprecise ask that is easy to
answer literally gets answered literally, and an explicit request phrase, not the
imprecision, is what reliably fires a skill. This hook places
the signal in the turn itself, so noticing is not left to the session.

Two signals, both deliberately conservative:

ASK-SHAPE -- the person can describe a thing by its function but cannot name it.
That is the vocabulary problem (Furnas et al., 1987: spontaneous agreement on a
term runs under 20%). Naming is activation -- the name binds the session to a
body of practice -- so the missing name is a missing instruction, not a missing
word.

DIRECTION -- the prompt carries a hedge ("or something like that", "off the
cuff", "don't hold me to it"). A hedged statement is direction, not a decision,
and a session that records it as a ruling or requirement turns a passing remark
into a constraint.

Silent when nothing matches. A false positive costs one playback; a false
negative costs a session executing the literal words, which is the failure this
exists to prevent. The hook never blocks a prompt: it always exits 0.
"""
import json
import re
import sys

TELLS = [
    # cannot produce the name
    r"\b(?:i )?do(?:n'?t| not) know (?:exactly )?(?:what|how) to (?:call|name|describe|say|ask|phrase|word|tell)",
    r"\b(?:i )?do(?:n'?t| not) know the (?:word|words|name|term|vocabulary|language|shape|structure|method|discipline)",
    r"\bdon'?t have the (?:word|words|vocabulary|language|term)",
    r"\bnot sure (?:how to|what to) (?:call|name|describe|articulate|ask|say|phrase)",
    r"\b(?:i'?m |im )?unsure what to ask",
    r"\bhow do i (?:ask|say|describe|phrase) (?:for )?(?:that|this|it)\b",
    r"\bwhat(?:'?s| is) (?:the )?(?:right |correct |proper )?(?:word|term|name) for\b",
    # explicitly disclaiming expertise / precision
    r"\bmy words are imprecise\b",
    r"\b(?:i'?m |im )not the expert\b",
    r"\b(?:i )?(?:am |'?m )?(?:just )?(?:fumbling|groping|grasping|stumbling)\b",
    r"\bdon'?t take (?:what i'?m saying|this|me) literally\b",
    # asking the other party to supply the shape
    r"\bany idea what (?:i'?m|im) (?:pointing|getting|driving) (?:to|at)\b",
    r"\bdo you (?:understand|see|know) what (?:i'?m|im) (?:saying|describing|talking about|trying)",
    r"\byou'?ll have to (?:elicit|synthesize|figure out|work out)\b",
    r"\b(?:try to |please )?elicit (?:that |this |it )?from me\b",
    r"\bhelp me (?:articulate|describe|figure out what|shape)\b",
    r"\bwhat is this an instance of\b",
    # inferring the thing must exist without knowing it
    r"\bsurely (?:that|this|there)(?:'?s| is)? not (?:a |some )?(?:new |novel )?bespoke\b",
    r"\bwouldn'?t there be (?:a |some )?(?:standard|framework|practice|model|method)\b",
    r"\b(?:there )?must be (?:a |some )?(?:standard|framework|practice|established|industry)\b",
    r"\b(?:i'?m |im )(?:just )?making (?:this|it) up\b",
]

DIRECTIVE = (
    "ASK-SHAPE SIGNAL: this prompt contains a tell that the ask cannot carry its own "
    "instructions -- the person can describe the thing by function but not name it. "
    "Run the shape-ask move BEFORE any work, tool call, or file read: (1) what you "
    "heard, (2) which mode -- do a known thing vs work out what the thing is, "
    "(3) how you're reading it, (4) where the reading could be wrong, then STOP on "
    "one question naming only what they asked for, answerable from their own intent "
    "(never \"is that reading right?\", which reads as a request to validate the whole "
    "analysis). After the confirm, every name ships with its CUT "
    "(which part, what depth, producing what), with WHO CAN CHECK IT, and with what it "
    "SWITCHES ON stated behaviourally -- then produce the work rather than another "
    "checkpoint. Writing the specification is yours; do not hand it back."
)

# Unambiguous hedges only.
HEDGE_TELLS = [
    r"\bor at least\b",
    r"\bthe premise of (?:that|this|it)\b",
    r"\b(?:or )?something like (?:that|this)\b",
    r"\bor something\b",
    r"\boff the cuff\b",
    r"\bdirectional (?:comment|statement|input)",
    r"\bjust directional\b",
    r"\bdon'?t hold me to\b",
    r"\b(?:loosely|roughly) speaking\b",
    r"\btake (?:that|this) loosely\b",
    r"\bi'?m not deciding\b",
    r"\bnot a decision\b",
]

DIRECTION_DIRECTIVE = (
    "DIRECTION SIGNAL: this prompt carries a hedge, so it is a directional "
    "statement, not a decision. It GOVERNS NOTHING. Do not record it as a ruling, "
    "requirement, decision or constraint, do not let it close a question, and do "
    "not build on it. The hedge is evidence, not noise -- keep it. To make it "
    "govern, state back in plain words: (1) what the user said VERBATIM, hedge "
    "included; (2) the need underneath it, stated as a problem THE FIELD ALREADY "
    "NAMES, citing an established source or saying plainly that none was found -- "
    "never as the user's inconvenience, and drop whatever solution they happened "
    "to name; (3) how anyone would know it is satisfied, measurably. You draft all "
    "three and the user corrects them; the user is never asked to supply them. It "
    "governs only after the user confirms that playback, and the playback and the "
    "confirmation both get written down. Specify no more than is essential "
    "(Cherns, minimal critical specification): over-specifying the user's words "
    "is the failure this exists to prevent."
)

# Both signals speak about the user's own words, so they are only true of a turn
# the user typed. Turns injected by another session or handed back by a subagent
# open with a harness frame tag; a hedge quoted inside one must not be promoted
# to the user's words. Matched against the raw prompt: the harness emits these
# tags in a fixed case. Harmless where the tags never appear.
NOT_THE_USER = re.compile(r"<cross-session-message\b|<agent-message\b")


def read_prompt():
    # Read bytes and decode as UTF-8 explicitly: on Windows the default stdin
    # encoding is the locale code page, which fails on non-ASCII prompts.
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    payload = json.loads(raw)
    prompt = payload.get("prompt") if isinstance(payload, dict) else None
    return prompt if isinstance(prompt, str) else ""


def main() -> None:
    prompt = read_prompt()
    if not prompt.strip() or NOT_THE_USER.search(prompt):
        return
    # Curly apostrophes (pasted or autocorrected text) would miss every "don'?t".
    lowered = prompt.replace("’", "'").replace("‘", "'").lower()
    signals = []
    if any(re.search(p, lowered) for p in TELLS):
        signals.append(DIRECTIVE)
    if any(re.search(p, lowered) for p in HEDGE_TELLS):
        signals.append(DIRECTION_DIRECTIVE)
    if not signals:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n\n".join(signals),
        },
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never block or break the user's prompt over a detector failure.
        pass
    sys.exit(0)
