"""Writes what each step and part connects to, from the register alone, for the in-browser click check.

    python click_check.py REGISTER        -> out/<name>-relations.json

Then open the generated page in a browser (served over http, beside the JSON) and run CLICK_CHECK_JS in its console:
it clicks every step and part in every figure and compares what stays lit with the register's connections,
restricted to what that figure draws. It returns the number of clicks and every mismatch.
"""
import json
import pathlib
import sys

import capability_views as cv

CLICK_CHECK_JS = r"""
(async () => {
  const name = location.pathname.split('/').pop().replace('.html', '').split('-')[0];
  const rel = await (await fetch(name + '-relations.json')).json();
  const out = {clicks: 0, mismatches: []};
  for (const svg of document.querySelectorAll('svg')) {
    const fig = (svg.querySelector('pattern') || {id: '?'}).id.replace('na-', '');
    const groups = [...svg.querySelectorAll('g.sel')];
    const key = g => g.dataset.step ? 's:' + g.dataset.step : 'p:' + g.dataset.part;
    const drawn = new Set(groups.map(key));
    for (const g of groups) {
      g.dispatchEvent(new MouseEvent('click', {bubbles: true}));
      out.clicks++;
      const lit = new Set(groups.filter(x => !x.classList.contains('off')).map(key));
      const want = new Set([key(g), ...(rel[key(g)] || [])].filter(k => drawn.has(k)));
      const a = [...lit].sort().join(','), b = [...want].sort().join(',');
      if (a !== b) out.mismatches.push({fig, clicked: key(g), lit: a, register: b});
      g.dispatchEvent(new MouseEvent('click', {bubbles: true}));
      if (svg.querySelector('.off')) out.mismatches.push({fig, clicked: key(g), problem: 'second click did not clear'});
    }
  }
  return out;
})()
"""


def relations(M):
    """Step -> every part that takes part in it; component -> its steps and the external dependencies it calls;
    dependency -> the components that call it and the steps it reaches (its own, and those its calls are made in);
    inside each agent, a dependency reaches the steps its users perform."""
    rel = {}

    def link(a, b):
        rel.setdefault(a, set()).add(b)

    for s in M["step"].values():
        for sid, _ in s["_parts"]:
            link("s:" + s["step"], "p:" + sid)
            link("p:" + sid, "s:" + s["step"])
    for c, ds in M["uses"].items():
        for d in ds:
            link("p:" + c, "p:" + d)
            link("p:" + d, "p:" + c)
    carriers = {c["subject_id"] for c in M["comps"] + M["persons"]}
    for r in M["R"]["subjects"]:  # a component and the components it calls, one hop either way
        ends = (r.get("from_id"), r.get("to_id"))
        if r.get("kind") == "relationship" and ends[0] in carriers and ends[1] in carriers and ends[0] != ends[1]:
            link("p:" + ends[0], "p:" + ends[1])
            link("p:" + ends[1], "p:" + ends[0])
    for d in M["ext"]:  # a dependency reaches the steps its callers' calls to it are made in
        for st in cv.steps_of(M, d):
            link("p:" + d, "s:" + st)
            link("s:" + st, "p:" + d)
    for parent, kids in M["dep_parts"].items():  # a dependency and its own parts, and who calls them
        for k in kids:
            link("p:" + parent, "p:" + k["subject_id"])
            link("p:" + k["subject_id"], "p:" + parent)
            for c, ds in M["uses"].items():
                if k["subject_id"] in ds:
                    link("p:" + parent, "p:" + c)
    reach = carriers | set(M["ext"])
    for r in M["R"]["subjects"]:  # a step reaches both ends of the calls made in it
        ends = (r.get("from_id"), r.get("to_id"))
        if r.get("kind") == "relationship" and ends[0] in reach and ends[1] in reach:
            for h in cv.ids(r.get("step_hint")):
                for x in ends:
                    link("s:" + h, "p:" + x)
    for rows in M["agent_rows"].values():
        for r in rows:
            for p in cv.ids(r.get("performed_by")):
                link("s:" + r["id"], "p:" + p)
                link("p:" + p, "s:" + r["id"])
            for d in cv.ids(r.get("uses")):
                link("p:" + r["id"], "p:" + d)
                link("p:" + d, "p:" + r["id"])
    for rows in M["agent_rows"].values():
        for r in rows:
            for d in cv.ids(r.get("uses")):
                for st in [x for x in rel.get("p:" + r["id"], ()) if x.startswith("s:")]:
                    link("p:" + d, st)
                    link(st, "p:" + d)
    return {k: sorted(v) for k, v in rel.items()}


if __name__ == "__main__":
    reg = pathlib.Path(sys.argv[1])
    M = cv.model(cv.load(reg))
    out = cv.HERE / "out" / f"{reg.name}-relations.json"
    out.write_text(json.dumps(relations(M), indent=1), encoding="utf-8")
    print(out)
