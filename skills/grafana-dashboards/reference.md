# grafana-dashboards: reference

The occasional cases. The everyday procedure, and the meaning of the steps referred to here, is in
`SKILL.md`.

## Creating a dashboard

Start from `new-dashboard.json` beside this file (a v2 dashboard Grafana 13 accepts) or from a
copy of an existing dashboard the user names; never write v2 JSON from memory. Replace every
`REPLACE` value; the name (uid) must be new. Set or remove the folder in
`metadata.annotations["grafana.app/folder"]`. Write `DESIGN.md` first. Then:
`python $SKILL/dashcheck.py check after.json` until it passes; `dashio.py values` from the file and
show the user every panel's numbers; `python $SKILL/dashio.py create after.json "<what it is>"`,
which refuses a name that exists, so an existing dashboard is never replaced; then steps 7 and 8.
Queries use the dashboard's data source variable, not a pinned data source.

## Cloning a dashboard

A clone is a create from a copy: new `metadata.name`, new title, the target folder. `dashio.py
create` drops the source's `resourceVersion` and labels, so the clone gets its own internal id.
Then look for what still points at the source, because none of it changes on its own: links to the
source's uid (dashboard, panel and data links); pinned data source uids; each variable's saved
`current` value; library panels, which stay shared. Alert rules are not copied.

A clone is a separate copy from then on: a later fix to the source does not reach it. If the clones
are meant to stay alike (the same dashboard for another service, environment or data source), say so
before cloning and offer one dashboard with a variable for what differs. After fixing a query, tell
the user that dashboards they know were cloned from this one may carry the same mistake; change them
only if asked.

## When a fix has come undone

`held` fails when something an earlier saved pass set is no longer there. Do not just make it again.

1. `python $SKILL/dashio.py history <uid>` lists generations with time, who saved and message.
   Find the first generation after the earlier pass where the value changed, fetch it and the one
   before it (`python $SKILL/dashio.py version <uid> <generation> v<generation>.json`), and
   `python $SKILL/dashcheck.py check v<generation-1>.json v<generation>.json` shows what that save
   changed. Delete these scratch files afterwards.
2. Tell the user who saved it, when, with what message, and what else it changed. Report that
   evidence; do not name a cause the history does not show. Things it can turn out to be: a later
   assistant pass or session working from an older file or regenerating content; a browser tab opened
   before the fix (Grafana 13 warns "the dashboard has been updated by another session", and
   "Continue editing" then Save overwrites the newer save); provisioning or Git Sync applying its own
   copy; a script or `gcx resources push` (both overwrite without a conflict check).
3. If the user says the later state is what they want, list those paths in `released.txt` in the
   earlier pass's folder; `held` stops checking them. If they want the fix back, it is a new pass.

## When you only have an MCP server

The scripts need files, and an MCP result reaches you as text; do not save it to a file by retyping.
Instead:

- Read with summary and single-property tools; change with the server's patch operations, one call
  per pass, addressing a panel by position only after reading the panel at that position.
- A patch save does not check for a newer save: the reference Grafana MCP server saves classic
  dashboards with overwrite on, and for v2 fetches and writes back within one call without exposing
  `resourceVersion`. Read the version immediately before and after the patch; if it moved by more
  than one, a save happened in between: tell the user.
- After saving, read back each changed property and its neighbours and compare with what you read
  before; ask the user to compare the two versions in Grafana (Dashboard settings, Versions, select
  both, Compare), the one diff your reading cannot corrupt.
- Record each declared path with its new value in `LOG.md` (`path = value`). At the start of a later
  pass, read those properties back; that is the MCP route's check that earlier fixes hold.
- Run changed queries with the server's query tools if it has them (some are off by default),
  reading only the number of series, the number of rows and the last value.
- Tell the user these checks are weaker, and that terminal access to the HTTP API enables the full
  ones.

## Grafana's own tools

If `gcx` is installed and configured, use it alongside the steps, not instead of them:

- `gcx resources validate` (run `gcx resources validate --help` for how it wants files laid out) is
  a dry run against the live server that checks the dashboard against Grafana's schema, ignoring
  unknown fields: add it to step 4.
- `gcx dashboards snapshot <name> --panel <id>` renders a panel as an image, if the Grafana Image
  Renderer is installed on the server: use it in step 7 to look at a display change yourself.
- **Never save with `gcx resources push`.** It copies the live dashboard's `resourceVersion` onto
  your file before saving, so a save made after your fetch is overwritten without a conflict.

`grafana/dashboard-linter` and `gcx dev lint` check dashboards for common mistakes without running
them. None of these replaces the declaration check: they judge whether a dashboard is valid, not
whether only the asked change was made.

## Library panels

The dashboard holds only a reference (`libraryPanel` in classic JSON, a `LibraryPanel` element in
v2), so editing it in the dashboard changes nothing. Its definition is a library element shared by
every dashboard that uses it (`/api/library-elements/<uid>`): changing it changes all of them, so
say so and get a yes first. To change it for this dashboard only, replace the reference with a
normal panel holding a copy of the definition, declared as one pass.

## Dashboards managed from files or git

Provisioned and Git Sync dashboards revert or reject API saves (`check` warns). Change them at their
source with the same declare, edit and check steps run on the files there; the save is the commit
or pull request, and Grafana applies it. Then fetch and do step 7.

## Traps

- **Classic and v2 are two views of one dashboard.** Grafana 13 serves both. How a dashboard is
  stored depends on how it was created and on the instance's settings; `dashio.py get` reports it
  ("stored as") and refuses one whose conversion to v2 failed. Within one pass, fetch and save in the
  same format; `check` refuses to compare a classic file with a v2 file.
- **"Export for sharing externally"** replaces data sources with placeholders; never use it as a
  before copy.
- **Saved variable values and time range**: saving after looking at another environment or range
  changes the default for everyone. They show as `current` and `timeSettings` paths in `check`.
- **A browser save writes defaults.** Saving in the browser fills in panel defaults (options,
  thresholds, field settings), so comparing two versions across a browser save shows many changes
  nobody chose. They are not regressions by themselves.
- **Classic rows move panels when expanded.** In classic JSON, expanding a collapsed row and saving
  moves its panels out of the row into the top level; `check` shows `_inRow` changes. In v2 only the
  row's `collapse` flag changes.
