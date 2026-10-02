# What this skill rests on

Every Grafana behaviour the skill depends on, where it came from, how far it was checked, and what
to do if it stops holding. When something in the skill turns out wrong, start here: find the fact
it relied on, check it on your instance, then fix the skill (see `MAINTAINING.md`).

**Checked against:** Grafana Enterprise 13.0.10, live, 2026-10-01/02 ("live" below). Grafana source
at tag v13.2.3 (`[G]` = `github.com/grafana/grafana/blob/v13.2.3/`), gcx v1.3.1
(`[X]` = `github.com/grafana/gcx/blob/v1.3.1/`), mcp-grafana v2.0.0
(`[M]` = `github.com/grafana/mcp-grafana/blob/v2.0.0/`). Grafana's HTTP API documentation lives at
`[G] docs/sources/developer-resources/api-reference/http-api/`.

**Checked column:** `live` means tested on a running Grafana 13.0.10; `probe` means `dashio.py probe`
re-tests it; `source only` means read in the source at the tags above and not tested on a running
instance, so it is true of those versions and may differ on yours.

**Re-check on a new instance or after an upgrade:** `python dashio.py probe <file>` tries items 1-5
on a throwaway dashboard. The others are re-checked as described in each row.

| # | Fact | The skill uses it for | Source | Checked | If it does not hold |
|---|---|---|---|---|---|
| 1 | Dashboards are read, created and saved at `/apis/dashboard.grafana.app/v2/namespaces/<ns>/dashboards[/<uid>]`; `<ns>` is `default` for the first organisation, `org-<id>` otherwise | every `dashio.py` call | `[G] docs/.../http-api/dashboard.md` (paths given for v1; v2 the same) | live; probe | Find the served versions at `<GRAFANA_URL>/apis`; change `dash_url()` in `dashio.py` |
| 2 | A save carrying a stale `metadata.resourceVersion` is refused with 409 | the conflict check on every save | `[G] pkg/storage/unified/apistore/store.go` L689-702 | live; probe | The skill's save is not safe on this instance: stop saving through it and tell the user |
| 3 | A save without `resourceVersion` is accepted and overwrites whatever is there | why `dashio.py put` refuses a file without it | `[G] pkg/apiserver/registry/generic/strategy.go` L107 | live | Nothing to change; the refusal is harmless |
| 4 | Version history is listed with `?labelSelector=grafana.app/get-history=true&fieldSelector=metadata.name=<uid>`, each entry a full dashboard with `generation`, who and when | `held` forensics, `dashio.py history` and `version` | `[G] docs/.../http-api/resource-history.md` | live; probe | Fall back to Dashboard settings, Versions, in the browser |
| 5 | A save's history note is the annotation `grafana.app/message`; the folder is `grafana.app/folder` | messages and folders on save | facts read from responses | live | Check a fetched dashboard's `metadata.annotations` and adjust `for_save()` |
| 6 | v2 shape: `elements` map; `layout` of kind GridLayout, RowsLayout, TabsLayout or AutoGridLayout; `variables` as `{kind, spec}`; a panel query at `elements.<name>.spec.data.spec.queries[].spec.query.spec`; a query variable's query at `spec.query.spec.query` | every path `dashcheck.py` prints, and the examples in SKILL.md step 2 | `[G] apps/dashboard/kinds/v2/dashboard_spec.cue`; real responses in `tests/fixtures/` | live | Run `dashcheck.py paths` on a fetched dashboard, compare with SKILL.md step 2, add a fixture and test for the new shape |
| 7 | Classic and v2 are views of one dashboard; a v2 read reports `status.conversion` (`storedVersion`, `failed`). Dashboards created classic stay classic after v2 and browser saves; ones created through v2 are stored as v2 | `dashio.py get` reporting the format and refusing a failed conversion | `[G] apps/dashboard/kinds/dashboard.cue` | live | If `dashio.py get` refuses, change that dashboard in the browser or with the classic API |
| 8 | Creating a dashboard from a copy that keeps `metadata.labels` gives it the source's legacy internal id | why `dashio.py create` drops labels | observed in `/api/search` | live | None needed while labels are dropped |
| 9 | `POST /api/ds/query` runs panel queries given a data source uid and a time range; variables are not filled in by the server | the numbers check (`dashio.py values` fills them itself) | Grafana HTTP API, data source query | live (TestData); Prometheus with no data | If a data source returns nothing for a query the browser shows, compare the request the browser sends (developer tools, network tab) with the one `dashio.py` sends |
| 10 | In the browser editor, "updated by another session" then "Continue editing" and Save overwrites the newer save | the possible-causes list for an undone fix | `[G] public/app/features/dashboard/api/v2.ts` L158-162 | live, in a browser | Remove it from the causes list |
| 11 | A browser save fills in panel defaults, so versions compared across one show many changes | the trap in reference.md | observed | live | Remove the trap |
| 12 | `gcx resources push` copies the live `resourceVersion` onto your file, so it overwrites; `gcx resources validate` is a server dry run, schema checked with unknown fields ignored; `gcx dashboards snapshot` needs the Image Renderer | the gcx section of reference.md | `[X] internal/resources/remote/pusher.go` L295-303; `cmd/gcx/resources/validate.go`; `docs/reference/cli/gcx_dashboards_snapshot.md` | source only | Test on a scratch dashboard before relying on gcx; correct reference.md |
| 13 | The reference Grafana MCP server saves classic dashboards with overwrite on, writes v2 back from a fetch in the same call, exposes no `resourceVersion`, and accepts only numeric indexes in patch paths | the MCP route in reference.md | `[M] tools/dashboard.go` L339, L348-374, and the `update_dashboard` description | source only | Your MCP server may be a different build: read its tool descriptions and test one patch on a scratch dashboard |
| 14 | In classic JSON, expanding a collapsed row and saving moves its panels to the top level; in v2 only the row's `collapse` flag changes | the trap in reference.md; `_inRow` in `dashcheck.py` | `[G]` `transformSceneToSaveModel.ts` L483-486 (front-end serialiser; search the repo for the file) | source only | Correct the trap |
| 15 | A multi-value or All variable inside a regex or `=~` matcher needs `${var:regex}` | the variables section of SKILL.md | Grafana docs, variable syntax (advanced formatting); `[M]` `update_dashboard` description | source only | Correct SKILL.md |
| 16 | A library panel is a reference in the dashboard; its definition is a library element at `/api/library-elements/<uid>` shared by every dashboard using it | the library panel section of reference.md | `[G] apps/dashboard/kinds/v2/dashboard_spec.cue` (LibraryPanelKind) | source only | Correct reference.md |
