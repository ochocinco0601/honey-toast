"""Tests for capability_views.py. Run: python -m unittest test_capability_views (from this folder)."""
import csv
import os
import pathlib
import re
import shutil
import tempfile
import unittest

import capability_views as cv

HERE = pathlib.Path(__file__).resolve().parent
REGISTERS = sorted(p for p in (HERE / "registers").iterdir() if (p / "about.csv").exists()
                   and (not os.environ.get("CV_REGISTERS") or p.name in os.environ["CV_REGISTERS"].split(",")))


def names_in(reg):
    """Every name a register gives its system, capabilities, flows, stages, steps, parts and agent elements."""
    R = cv.load(reg)
    out = {R["about"][0].get("system", "")}
    for t, col in [("capabilities", "name"), ("flows", "name"), ("stages", "name"), ("steps", "name"),
                   ("subjects", "name"), ("agent-system", "name")]:
        out |= {r.get(col, "") for r in R[t]}
    columns = set()  # a name that is also a template column ("order") names the schema, not the instance
    for t in cv.TABLES:
        with (HERE / "register-template" / f"{t}.csv").open(encoding="utf-8") as f:
            columns |= {c.lower() for c in next(csv.reader(f))}
    return {n for n in out if len(n) >= 5 and n.lower() not in columns}


def build(reg, *args):
    out = pathlib.Path(tempfile.mkdtemp()) / "page.html"
    assert cv.main([str(reg), "--out", str(out), *args]) == 0
    return out.read_text(encoding="utf-8")


class TheProgramNamesNoInstance(unittest.TestCase):
    def test_no_register_name_appears_in_the_program(self):
        src = (HERE / "capability_views.py").read_text(encoding="utf-8").lower()
        self.assertTrue(REGISTERS, "no registers to test against")
        for reg in REGISTERS:
            for n in names_in(reg):
                self.assertIsNone(re.search(r"\b" + re.escape(n.lower()) + r"\b", src),
                                  f"{reg.name}: the program names {n!r}")


class EveryRegisterDraws(unittest.TestCase):
    def test_check_passes_and_the_page_draws_from_the_register_alone(self):
        for reg in REGISTERS:
            with self.subTest(reg.name):
                err, _ = cv.check(cv.load(reg))
                self.assertEqual(err, [])
                page = build(reg)
                M = cv.model(cv.load(reg))
                for f in M["flows"]:
                    self.assertIn(cv.esc(f["name"]), page)
                for a in M["agents"]:
                    self.assertIn(f'<title>{cv.esc(a["name"])}</title>', page)

    def test_every_step_nothing_carries_is_drawn_as_not_assessed_in_the_overview(self):
        for reg in REGISTERS:
            with self.subTest(reg.name):
                M = cv.model(cv.load(reg))
                page = build(reg)
                overview = page[page.index("Overview: every stage opened"):]
                na = sum(1 for s in M["step"].values() if not s["_parts"])
                hatched = re.findall(r'<rect x="%d" [^>]*fill:url\(#na-m9\)' % cv.PX, overview)
                self.assertEqual(len(hatched), na)

    def test_an_ai_agent_is_on_the_map_whichever_stage_is_opened(self):
        for reg in REGISTERS:
            M = cv.model(cv.load(reg))
            for a in M["agents"]:
                other = next((st["stage"] for st in M["stage"].values()
                              if not any(sid == a["subject_id"] for s in st["_steps"] for sid, _ in s["_parts"])), None)
                if not other:
                    continue
                with self.subTest(reg.name):
                    svg = cv.figure_map(M, "map", "t", opened={other})
                    self.assertIn(f'<title>{cv.esc(a["name"])}</title>', svg)

    def test_a_step_carried_another_way_is_not_read_as_stopped(self):
        M = small()
        provider = next(d["subject_id"] for d in M["deps"] if any(c for c, ds in M["uses"].items() if d["subject_id"] in ds
                                                                  and M["family"](M["subj"][c]) == "agent"))
        ways = {s: cv.other_ways(M, provider, s) for s in cv.steps_of(M, provider)}
        self.assertTrue(any(ways.values()), "no step reads as still carried another way when the model provider fails")

    def test_design_time_only_no_reading_is_drawn(self):
        for reg in REGISTERS:
            page = build(reg)
            self.assertIn("They hold no live values", page)


class ClickingAPartOrAStep(unittest.TestCase):
    def test_every_line_a_click_can_light_is_a_connection_in_the_register(self):
        import click_check
        for reg in REGISTERS:
            with self.subTest(reg.name):
                M = cv.model(cv.load(reg))
                rel = click_check.relations(M)
                page = build(reg)
                lines = re.findall(r'class="ln link" data-step="([^"]+)" data-part="([^"]+)"', page)
                deps = re.findall(r'class="ln link" data-part="([^"]+)" data-dep="([^"]+)"', page)
                self.assertTrue(lines)
                for s, p in lines:
                    self.assertIn("p:" + cv.html.unescape(p), rel.get("s:" + cv.html.unescape(s), []))
                for c, d in deps:
                    self.assertIn("p:" + cv.html.unescape(d), rel.get("p:" + cv.html.unescape(c), []))

    def test_the_page_carries_its_own_click_script_with_no_outside_library(self):
        page = build(REGISTERS[0])
        self.assertIn("<script>", page)
        self.assertNotIn("<script src", page)


SMALL = HERE / "fixtures" / "small"


def small():
    return cv.model(cv.load(SMALL))


def group(svg, attr):
    """The text inside the clickable group with this data attribute, e.g. data-part="D1"."""
    m = re.search(r'<g class="sel"[^>]*' + re.escape(attr) + r'[^>]*>(.*?)</g>', svg, re.S)
    return m.group(1) if m else ""


class WhatTheDrawingSays(unittest.TestCase):
    """Each claim a view makes is one the register holds."""

    def test_only_the_failing_part_is_named_the_cause(self):
        M = small()
        svg = cv.figure_map(M, "reach", "t", fails="D1")
        self.assertEqual(svg.count("fails: the cause"), 1)
        self.assertIn("fails: the cause", group(svg, 'data-part="D1"'))
        self.assertNotIn("fails: the cause", group(svg, 'data-part="P2"'))

    def test_a_flow_measure_on_a_shared_case_counts_only_for_the_flow_it_names(self):
        M = small()
        self.assertEqual([m["handle"] for m in M["m_flow"].get("F1", [])], ["M1"])
        self.assertEqual(M["m_flow"].get("F2", []), [])
        _, warn = cv.check(cv.load(SMALL))
        self.assertTrue(any("M2" in w and "flow" in w for w in warn))

    def test_a_cost_written_for_one_cause_is_not_shown_for_another(self):
        M = small()
        by_p1 = cv.figure_map(M, "reach", "t", fails="P1")
        self.assertIn("things done wrong by part one", by_p1)
        self.assertIn("still carried the other way (agent)", by_p1)
        self.assertNotIn("things not done", by_p1)  # step 1 does not stop: the agent way still carries it
        by_p3 = cv.figure_map(M, "reach", "t", fails="P3")
        self.assertNotIn("things done wrong by part one", by_p3)
        self.assertIn("not assessed for this cause", by_p3)

    def test_a_part_failing_on_one_way_still_shows_what_its_own_failure_does(self):
        svg = cv.figure_map(small(), "reach", "t", fails="P2")
        self.assertIn("still carried the other way (form)", svg)
        self.assertIn("wrong answers from the agent", svg)

    def test_a_dependency_reaches_its_own_steps_and_the_steps_its_calls_are_made_in(self):
        self.assertEqual(cv.steps_of(small(), "D1"), {"1"})  # its caller P2 also carries step 4, without calling it

    def test_the_agent_view_never_says_a_delivered_capability_is_undelivered(self):
        M = small()
        self.assertNotIn("no flow here delivers it", cv.figure_agent(M, M["subj"]["P2"], "t"))

    def test_an_agent_step_names_the_flow_of_the_step_it_serves(self):
        M = small()
        self.assertIn("serves: Step one (Flow one)", cv.figure_agent(M, M["subj"]["P2"], "t"))

    def test_an_external_dependency_in_a_step_is_numbered_on_the_step(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST1"})
        n = re.search(r'class="sx">(\d+) · Provider<', group(svg, 'data-part="D1"'))
        self.assertTrue(n, "the dependency carries no number")
        self.assertRegex(group(svg, 'data-step="1"'), r'text-anchor="end"[^>]*>[^<]*\b%s\b' % n.group(1))

    def test_a_capability_with_an_agent_draws_the_agent_failing_and_what_it_calls_failing(self):
        page = build(SMALL)
        self.assertIn("Agent part fails", page)
        self.assertIn("Provider fails", page)

    def test_a_dependency_called_only_at_start_up_reaches_no_step(self):
        self.assertEqual(cv.steps_of(small(), "D2"), set())

    def test_a_dependency_with_its_own_way_hurts_only_that_way(self):
        self.assertEqual(cv.other_ways(small(), "D3", "1"), ["form"])

    def test_the_hurt_way_says_its_cost_is_not_assessed_when_no_row_names_this_cause(self):
        svg = cv.figure_map(small(), "reach", "t", fails="D1")
        self.assertIn("impact on the agent way: not assessed", svg)

    def test_every_cost_row_for_the_failing_part_is_shown(self):
        svg = cv.figure_map(small(), "reach", "t", fails="P2")
        for unit in ("wrong answers from the agent", "slow answers from the agent", "answers on the wrong topic"):
            self.assertIn(unit, svg)

    def test_a_call_between_components_is_drawn_and_shown_on_click(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST1"})
        self.assertRegex(svg, r'<path [^>]*class="call[^"]*"[^>]*data-from="P1" data-to="P3"')
        self.assertNotRegex(svg, r'class="call on"[^>]*data-from="P1"')  # hidden until P1 or P3 is clicked
        overview = cv.figure_map(small(), "map", "o", opened={"ST1", "ST2", "ST3"}, calls="all")
        self.assertRegex(overview, r'class="call on handoff"[^>]*data-from="P1" data-to="P3"')  # Team A to Team B

    def test_a_call_made_only_at_start_up_is_labelled(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST1", "ST2"})
        self.assertIn("at start-up", svg)

    def test_clicking_a_component_reaches_the_components_it_calls_and_that_call_it(self):
        import click_check
        rel = click_check.relations(small())
        self.assertIn("p:P3", rel["p:P1"])
        self.assertIn("p:P1", rel["p:P3"])

    def test_a_long_step_name_wraps_whole_beside_its_numbers(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST3"})
        text = " ".join(re.findall(r'class="sx">([^<]*)<', group(svg, 'data-step="4"')))
        self.assertIn("in its box", text)
        self.assertNotIn("…", text)

    def test_calls_to_parts_the_view_does_not_draw_are_counted(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST3"})  # Part one is drawn, Store part (it calls) is not
        self.assertIn("+2 calls to or from parts not drawn here", svg)

    def test_a_stage_nothing_carries_is_hatched_on_the_map(self):
        M = small()
        svg = cv.figure_map(M, "map", "t", opened={"ST1"})
        self.assertRegex(svg, r'fill:url\(#na-t\)[^>]*>(?:<title>[^<]*</title>)?</rect><text[^>]*>2\. Stage two')

    def test_an_agent_step_names_the_business_step_it_serves(self):
        M = small()
        svg = cv.figure_agent(M, M["subj"]["P2"], "t")
        self.assertIn("serves: Step one", svg)
        self.assertNotIn("serves step 1", svg)

    def test_a_step_lists_every_measure_on_record_at_it(self):
        M = small()
        svg = cv.figure_map(M, "reports", "t", opened={"ST1"})
        self.assertIn("on record: 1 application", group(svg, 'data-step="2"'))

    def test_the_same_register_draws_the_same_page_every_time(self):
        import subprocess
        import sys
        outs = []
        for seed in ("1", "2"):
            out = pathlib.Path(tempfile.mkdtemp()) / "p.html"
            subprocess.run([sys.executable, str(HERE / "capability_views.py"), str(REGISTERS[0]), "--out", str(out)],
                           check=True, capture_output=True, env=dict(os.environ, PYTHONHASHSEED=seed))
            outs.append(out.read_text(encoding="utf-8").split("-->", 1)[1])
        self.assertEqual(outs[0], outs[1])

    def test_clicking_an_external_dependency_reaches_its_steps_and_callers(self):
        import click_check
        rel = click_check.relations(small())
        self.assertIn("s:1", rel["p:D1"])
        self.assertIn("p:P2", rel["p:D1"])
        self.assertIn("p:D1", rel["s:1"])
        svg = cv.figure_map(small(), "map", "t", opened={"ST1"})
        self.assertRegex(svg, r'data-part="D1"[^>]*data-steps="[^"]*\b1\b')


class OutsideServicesAndHandoffs(unittest.TestCase):
    """Depth varies per dependency; a step can take a chain of calls; handoffs may carry contracts."""

    def test_a_dependencys_own_parts_are_drawn_inside_it_and_calls_reach_the_part(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST1"})
        self.assertIn("<title>Embedder index</title>", group(svg, 'data-part="E1"') or svg)
        self.assertRegex(svg, r'data-part="P4" data-dep="E1"')
        d3 = re.search(r'<g class="sel"[^>]*data-part="D3"[^>]*><rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg)
        e1 = re.search(r'<g class="sel"[^>]*data-part="E1"[^>]*><rect x="([\d.]+)" y="([\d.]+)"', svg)
        x, y, w, h = map(float, d3.groups())
        self.assertTrue(x < float(e1.group(1)) < x + w and y < float(e1.group(2)) < y + h, "E1 is not inside D3's box")

    def test_a_dependency_with_its_owners_map_links_to_it(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST1"})
        self.assertIn('href="https://example.invalid/provider-map"', svg)

    def test_a_steps_chain_of_calls_is_numbered_in_order(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST1"})
        labels = re.findall(r'class="call[^"]* seq"[^>]*data-steps="([^"]*)" data-seq="(\d+)"', svg)
        self.assertEqual(sorted(seq for steps, seq in labels if steps == "2"), ["1", "2"])

    def test_a_call_made_in_several_steps_has_its_order_in_each(self):
        r = {"step_hint": "1; 2", "sequence": "1:3; 2:1"}
        self.assertEqual((cv.seq_for(r, "1"), cv.seq_for(r, "2")), ("3", "1"))
        self.assertEqual(cv.seq_for({"step_hint": "2", "sequence": "4"}, "2"), "4")

    def test_clicking_a_step_reaches_the_parts_its_calls_join(self):
        import click_check
        self.assertIn("p:P4", click_check.relations(small())["s:2"])

    @unittest.skip("contracts at handoffs are not built yet")
    def test_a_handoff_shows_its_contract_or_that_none_is_on_record(self):
        svg = cv.figure_map(small(), "map", "t", opened={"ST1"})
        self.assertIn("contract: 99% of answers within 5 s", group(svg, 'data-part="D1"'))
        self.assertIn("no contract on record", group(svg, 'data-part="D3"'))
        self.assertRegex(svg, r'class="call[^"]*handoff nocontract"[^>]*data-from="P1" data-to="P3"')


class HowTheMapWasMade(unittest.TestCase):
    def test_the_page_draws_the_registers_own_run_and_the_check_it_passed(self):
        page = build(SMALL)
        part = page[page.index("How this map was made"):]
        self.assertIn("Write the steps as business outcomes", part)
        self.assertIn("model drafting", part)
        self.assertIn("person confirming", part)
        self.assertIn("by hand", part)
        self.assertRegex(part, r"0 errors")

    def test_each_pass_is_shown_in_order_with_the_sources_it_added(self):
        page = build(SMALL)
        part = page[page.index("How this map was made"):]
        self.assertLess(part.index("PASS 1"), part.index("PASS 2"))
        self.assertIn("an architecture page found later", part)
        self.assertIn("added the store part the code did not name", part)

    def test_a_how_made_row_names_a_pass_the_sources_list_has(self):
        tmp = pathlib.Path(tempfile.mkdtemp()) / "reg"
        shutil.copytree(SMALL, tmp)
        p = tmp / "how-made.csv"
        p.write_text(p.read_text(encoding="utf-8") + "3,6,x,y,z,tool,\n", encoding="utf-8")
        self.assertTrue(any("pass 3" in e for e in cv.check(cv.load(tmp))[0]))

    def test_a_register_that_does_not_record_its_run_says_so(self):
        tmp = pathlib.Path(tempfile.mkdtemp()) / "reg"
        shutil.copytree(SMALL, tmp)
        (tmp / "how-made.csv").unlink()
        page = build(tmp)
        self.assertIn("does not record how it was made", page)

    def test_who_did_a_step_is_one_of_the_closed_list(self):
        tmp = pathlib.Path(tempfile.mkdtemp()) / "reg"
        shutil.copytree(SMALL, tmp)
        (tmp / "how-made.csv").write_text("step,name,went_in,came_out,done_by,note\n1,x,y,z,magic,\n", encoding="utf-8")
        self.assertTrue(any("done_by" in e for e in cv.check(cv.load(tmp))[0]))


class OnALaptop(unittest.TestCase):
    def test_a_figure_fits_the_width_and_zooms_inside_its_frame(self):
        page = build(SMALL)
        self.assertNotIn("min-width:1100px", page)
        self.assertIn('data-zoom="in"', page)
        self.assertIn('data-zoom="fit"', page)
        self.assertIn('data-zoom="selection"', page)


class TheCheck(unittest.TestCase):
    def broken(self, table, row, col, value):
        tmp = pathlib.Path(tempfile.mkdtemp()) / "reg"
        shutil.copytree(REGISTERS[0], tmp)
        p = tmp / f"{table}.csv"
        with p.open(encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            cols, rows = r.fieldnames, list(r)
        rows[row][col] = value
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        return cv.check(cv.load(tmp))[0]

    def test_a_step_in_no_stage_is_refused(self):
        self.assertTrue(any("is not a stage" in e for e in self.broken("steps", 0, "stage", "NOPE")))

    def test_a_layer_outside_the_method_is_refused(self):
        self.assertTrue(any("layer" in e for e in self.broken("measures", 0, "layer", "vibes")))

    def test_a_part_kind_outside_the_method_is_refused(self):
        self.assertTrue(any("part_kind" in e for e in self.broken("subjects", 1, "part_kind", "gizmo")))

    def test_the_blank_template_has_every_column_the_program_reads(self):
        src = (HERE / "capability_views.py").read_text(encoding="utf-8")
        read = set(re.findall(r'\.get\("([a-z_]+)"', src)) | set(re.findall(r'\["([a-z_]+)"\]', src))
        cols = set()
        for t in cv.TABLES:
            with (HERE / "register-template" / f"{t}.csv").open(encoding="utf-8") as f:
                cols |= set(next(csv.reader(f)))
        method = set()
        for p in (HERE / "method").glob("*.csv"):
            with p.open(encoding="utf-8") as f:
                method |= set(next(csv.reader(f)))
        internal = {"step_id", "family"} | set(small()) | set(cv.load(SMALL)) | set(cv.load(SMALL)["method"])  # the program's own keys
        missing = {c for c in read if c not in cols | method | internal and not c.startswith("_")}
        self.assertEqual(missing, set())

    def test_the_program_has_no_special_case_for_one_register(self):
        src = (HERE / "capability_views.py").read_text(encoding="utf-8")
        self.assertNotIn('"n/a"', src)


if __name__ == "__main__":
    unittest.main()
