# Change many files at once

**You end with:** updated copies of a folder of files, with the originals unchanged.

**You need:** the copilot-practice folder open in VS Code. If another folder is open, on the **File** menu, select **Open Recent**, and then select
`copilot-practice`.

**When:** the same change is needed in many files, such as a new phone number, a renamed team or
a replaced term.

## 1. Have Copilot create practice notices

Five of the notices give the same phone number, so you know how many files should change.

1. If the control at the bottom of the chat box doesn't show **Agent**, select the control, and
   then select **Agent**.
2. In the chat box, enter:

> In the copilot-practice folder, create a folder named notices.
> In it, write eight short, made-up notices to staff about office services.
> In five of them, give the service desk's phone number as 555-0100.
> Add or change no other file.

Check: `notices` holds eight files. If it holds a different number, expect that number below.

## 2. Ask what would change, and change nothing yet

Seeing which files a change touches lets you catch a wrong match before anything changes.

1. Enter:

> In the notices folder of the copilot-practice folder, list each file that gives the phone number 555-0100, with the sentence it's in.
> Don't change any file yet.

Check: the reply lists five files. If it lists a different number of files, expect that number below.

## 3. Make the change on copies

Working on copies leaves the originals as they were.

1. Enter:

> In the copilot-practice folder, create a folder named notices-updated.
> Copy every file from the notices folder into it.
> In the copies, replace 555-0100 with 555-0199, and change nothing else in them.
> Tell me how many files you copied and how many you changed.
> Add or change no other file.

2. If a permission request appears, allow it if it copies files from `notices` and changes only
   files in `notices-updated`.

Check: Copilot reports eight files copied and five changed, and `notices-updated` holds eight
files. Open one of the five in `notices-updated`. It gives 555-0199. Open the same file in
`notices`. It still gives 555-0100.

To use your own folder: open the folder that holds it. Send the same requests, except the one that
creates practice files. Use your folder's name in place of notices and your change in place of the
phone numbers, and leave out the practice folder names.

If it does not work: [Help](../../troubleshooting.md).
