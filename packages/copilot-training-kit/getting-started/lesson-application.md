# Have Copilot explain code you didn't write

Copilot can explain code you didn't write: what an application does, which file does what, and
where a particular thing happens. In this unit, Copilot builds a small practice application, and
you ask it about the code. Start with the practice folder open and the chat set to **Agent**, as
at the end of [Make your first request to Copilot](start-here.md).

## 1. Have Copilot build a small tip calculator

You need an application to ask about, so Copilot makes one.

1. In the chat box, enter:

> In the copilot-practice folder, create a folder named tip-calculator.
> In it, make a small web page that works out a tip from a bill and a percentage: index.html, style.css and script.js.
> Keep the code short and plain.
> Change nothing else.

2. In the list on the left, open `tip-calculator`.

Check: `tip-calculator` holds `index.html`, `style.css` and `script.js`.

<!-- more: Do I need to read the code? -->
You don't need to read the code yourself. These three files are the usual parts of a web page:
the page, how it looks, and what it does. Copilot writes the code fresh each time, so yours won't
match anyone else's.
<!-- /more -->

## 2. Ask Copilot what the tip calculator does

Start by asking, in plain words, what the application does.

1. Enter:

> Explain the application in the tip-calculator folder for someone who doesn't write code.
> Say what it does, and what each file is for.

Check: the reply names all three files, each with what it's for.

## 3. Ask Copilot which lines work out the tip

Ask for the file and the line numbers, and you can go straight to the code.

1. Enter:

> Read the files in the tip-calculator folder.
> Tell me where the tip is worked out.
> Name the file and the line numbers, and quote those lines.

2. In the list on the left, select the file it names. It opens in the middle of the window, with line numbers
   down its left edge.

Check: the lines it quoted are at the line numbers it named.

<!-- more: If the lines don't match -->
Tell it:

> Those lines aren't at the line numbers you gave.
> Look again, and quote only what's in the file.
<!-- /more -->

## On your own work

The same questions work on a real application's code. On the **File** menu, select **Open
Folder**, and choose the application's folder. If VS Code asks whether you trust the authors, select **Yes, I trust the
authors** only when the code comes from a source you trust, as for any folder you open. Then ask what it does, and where something
you care about happens.

## What you did

You had Copilot build a small application, explain it in plain words, and point you to the lines
that do a particular job.
