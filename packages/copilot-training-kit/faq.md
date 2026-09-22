# Questions people ask

## I am not a coder. What am I supposed to do with this?

Use it on your own files. Nothing here requires you to write code, and the only reading of code
is checking that a file the assistant cited contains the words it claims; you do not need to
understand the code around them. Start with `README.md`. It ends by sending you to the lesson
that fits your work, and `how-to/` holds the chores you can come back for.

## Does what I type, or the files it reads, leave my computer? May I use it on customer data?

This is the first question to settle, and the answer is your organization's, not this kit's.
Until you have it, use the assistant on files that contain nothing you would not paste into an
email to a colleague. `[YOUR ORGANIZATION: what leaves the machine, what is retained, and which classes of data may be used with the assistant]`

## What if I mess up?

On your own machine the assistant can change what you can change, and it asks before it acts
unless you have allowed commands for the session. There is no undo button for a move, a rename or
a deletion it makes, so for anything that changes files, ask for a plan first and for a written
record of what it did; the organize-a-folder recipe shows the shape. With two folders open,
name the folder you mean in every request. In a repository, the local copy is yours to break. In
a normal setup nothing reaches the shared main copy without a review by other people.
`[YOUR ORGANIZATION: the review rule and process, by name]`

## Which kinds of files can it read?

Plain text, markdown and CSV files it reads directly. For Word or Excel files it may need to write
and run a small program to read them, and it will ask permission first; if that does not work in
your setup, save the file as text or CSV and try again. Pages in a notebook application have to
be exported to a file first.

## Do we have access to all repositories?

No. Access is per application. `[YOUR ORGANIZATION: how access is requested, and from whom]`

## Can we download skills? Is it safe?

A skill is a text file of instructions. The safety question is the same as for any file you bring
in: read it before you use it. Downloading from outside may be restricted. You can always ask the
assistant to write one for you; see `how-to/ask-for-a-skill.md`.
`[YOUR ORGANIZATION: the policy on external skills, and where internal shared skills are published]`

## Does disk space matter?

Delete a cloned folder when you are done with it; you can clone it again. If size matters, ask
the assistant how large the repository is before cloning. Ordinary housekeeping applies.
`[YOUR ORGANIZATION: any policy]`

## Can it reach our ticketing system, logs, or other systems directly?

That depends on connectors your organization has set up. Without one, export to a file and work on
the file. That is `how-to/analyze-an-export.md`, and it is the same work you do by hand today.
`[YOUR ORGANIZATION: current connectors and their status]`

## How did you get the chat panel there?

Layout is a personal setting. Everyone's screen differs. Ask the assistant: "How do I move the chat
panel to the right?" It will tell you the setting or change it for you.

## Will there be office hours or a follow-up session?

Ask whoever sent you this folder. `[YOUR ORGANIZATION: schedule and how to join]`

## Can we suggest what to cover next?

Yes. `[YOUR ORGANIZATION: where suggestions go]`

## Is there a hands-on guide?

This folder. Start with `README.md`, then the lesson it sends you to.

## Setup: nothing responds

In order. Is the assistant installed: menu View, then Extensions, and type Copilot in the search
box; it should show as installed. Is it signed in: the account icon at the bottom left of the
window shows your name. Do you have a licence: in many organizations the assistant needs one to
be granted to you before it will answer, and an unlicensed one fails silently or asks you to sign
in again. Is the chat panel open: menu View, then Chat. If any of these fails, stop here.
`[YOUR ORGANIZATION: how to get VS Code and the assistant installed, how a licence is requested, and who to ask]`

## Setup: it answers but never acts

The mode selector at the bottom of the chat box is not on Agent. Click it and choose Agent. In the
other modes the assistant only writes text; in Agent mode it can create files and run commands,
after asking you.

## Setup: the clone fails

Three usual causes: the version-control program, called git, is not installed on the machine; you
are not signed in to the place the repository lives, called the code host; or the network and
proxy settings from onboarding are not in place. Ask the assistant "Is git installed, am I signed
in to the code host, and is a proxy configured?" and it will check.
`[YOUR ORGANIZATION: how to install git, how to sign in to the code host, and the onboarding setup prompt]`
