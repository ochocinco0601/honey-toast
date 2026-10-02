import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
FX = HERE / "fixtures"
SCRIPT = HERE.parent / "dashcheck.py"


def run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


V1_ALLOW = ["--allow", "panels[id=2].targets[refId=A].expr", "--allow", "panels[id=2].title"]
V2_ALLOW = ["--allow", "elements.panel-2.spec.title",
            "--allow", "elements.panel-2.spec.data.spec.queries[refId=A].spec.query.spec.alias"]


def test_v1_declared_change_passes():
    code, out = run("check", FX / "v1_before.json", FX / "v1_after_clean.json", *V1_ALLOW)
    assert code == 0 and "RESULT: PASS" in out


def test_v1_undeclared_changes_fail_including_inside_a_collapsed_row():
    code, out = run("check", FX / "v1_before.json", FX / "v1_after_regressed.json", *V1_ALLOW)
    assert code == 1
    assert "!! panels[id=4].targets[refId=A].expr" in out
    assert "!! panels[id=1].datasource.uid" in out
    assert "$environment is used but no dashboard variable defines it" in out


def test_v1_panel_reorder_is_not_a_change():
    code, out = run("check", FX / "v1_before.json", FX / "v1_reordered.json")
    assert code == 0 and "CHANGES (0)" in out


def test_v1_clone_with_declared_uid_and_title_passes():
    code, _ = run("check", FX / "v1_before.json", FX / "v1_clone.json", "--allow", "uid", "--allow", "title")
    assert code == 0


def test_v2_declared_change_passes():
    code, out = run("check", FX / "v2_before.json", FX / "v2_after_clean.json", *V2_ALLOW)
    assert code == 0 and "FORMAT v2" in out


def test_v2_unplaced_panel_pinned_datasource_and_reorder_fail():
    code, out = run("check", FX / "v2_before.json", FX / "v2_after_regressed.json", *V2_ALLOW)
    assert code == 1
    assert "element 'panel-4' is not placed in the layout" in out
    assert "removed: layout.spec.rows[title=Details].spec.layout.spec.items[el=panel-4]" in out
    assert "!! variables.(order)" in out
    assert "names datasource 'PROM-PROD' directly" in out


def test_declared_change_not_made_fails():
    code, out = run("check", FX / "v2_before.json", FX / "v2_before.json", *V2_ALLOW)
    assert code == 1 and "declared but did not change" in out


def test_optional_declaration_may_stay_unchanged():
    code, _ = run("check", FX / "v2_before.json", FX / "v2_before.json", "--allow", "?elements.panel-2.spec.title")
    assert code == 0


def test_adding_a_variable_is_not_a_reorder_and_lists_its_panels():
    code, out = run("check", FX / "v2_before_add_variable.json", FX / "v2_after_add_variable.json",
                    "--allow", "variables[name=region].*",
                    "--allow", "elements.panel-1.spec.data.spec.queries[refId=A].spec.query.spec.alias")
    assert code == 0, out
    assert "(order)" not in out
    assert "panel-1 'Success rate'" in out


def test_mixed_formats_refused():
    code, out = run("check", FX / "v1_before.json", FX / "v2_before.json")
    assert code == 1 and "format changed" in out


def test_values_declared_change_passes_and_asks_the_user():
    code, out = run("values", FX / "v_before.json", FX / "v_good.json", "--changed", "2")
    assert code == 0 and "?? panel 2" in out


def test_values_changed_panel_gone_empty_fails():
    code, _ = run("values", FX / "v_before.json", FX / "v_empty.json", "--changed", "2")
    assert code == 1


def test_values_untouched_panel_moving_fails():
    code, out = run("values", FX / "v_before.json", FX / "v_side.json", "--changed", "2")
    assert code == 1 and "!! panel 4" in out


def test_values_different_ranges_refused():
    code, _ = run("values", FX / "v_before.json", FX / "v_shift.json", "--changed", "2")
    assert code == 1


def saved_pass(changes, name, before, after, allow):
    d = changes / name
    d.mkdir(parents=True)
    shutil.copy(FX / before, d / "before.json")
    shutil.copy(FX / after, d / "after.json")
    shutil.copy(FX / after, d / "live.json")
    (d / "allow.txt").write_text(allow, encoding="utf-8")
    return d


def edited_live(tmp_path, fixture, edit):
    live = json.loads((FX / fixture).read_text(encoding="utf-8"))
    edit(live["spec"])
    path = tmp_path / "live.json"
    path.write_text(json.dumps(live), encoding="utf-8")
    return path


def test_held_catches_an_undone_change_from_any_earlier_pass(tmp_path):
    changes = tmp_path / "changes"
    saved_pass(changes, "001", "v2_before.json", "v2_after_clean.json", "elements.panel-2.spec.title\n")
    saved_pass(changes, "002", "v2_before_add_variable.json", "v2_after_add_variable.json", "variables[name=region].*\n")

    code, _ = run("held", changes, FX / "v2_after_add_variable.json")
    assert code == 0

    def undo(spec):
        spec["elements"]["panel-2"]["spec"]["title"] = "Latency p95"
    code, out = run("held", changes, edited_live(tmp_path, "v2_after_add_variable.json", undo))
    assert code == 1 and "set by 001" in out


def test_held_ignores_a_pass_that_was_never_saved(tmp_path):
    changes = tmp_path / "changes"
    saved_pass(changes, "001", "v2_before.json", "v2_after_clean.json", "elements.panel-2.spec.title\n")
    abandoned = changes / "002"
    abandoned.mkdir()
    shutil.copy(FX / "v2_after_add_variable.json", abandoned / "after.json")
    (abandoned / "allow.txt").write_text("variables[name=region].*\n", encoding="utf-8")
    code, out = run("held", changes, FX / "v2_after_clean.json")
    assert code == 0, out


def test_held_released_paths_stop_raising_alarms(tmp_path):
    changes = tmp_path / "changes"
    first = saved_pass(changes, "001", "v2_before.json", "v2_after_clean.json", "elements.panel-2.spec.title\n")

    def retitle(spec):
        spec["elements"]["panel-2"]["spec"]["title"] = "Latency (renamed in the browser on purpose)"
    live = edited_live(tmp_path, "v2_after_clean.json", retitle)
    assert run("held", changes, live)[0] == 1
    (first / "released.txt").write_text("elements.panel-2.spec.title\n", encoding="utf-8")
    assert run("held", changes, live)[0] == 0


def test_held_catches_a_removal_put_back(tmp_path):
    changes = tmp_path / "changes"
    saved_pass(changes, "001", "v2_after_add_variable.json", "v2_before_add_variable.json", "variables[name=region].*\n")
    code, out = run("held", changes, FX / "v2_after_add_variable.json")
    assert code == 1 and "variables[name=region]" in out


def test_held_orders_passes_by_number_not_text(tmp_path):
    changes = tmp_path / "changes"
    saved_pass(changes, "9-old", "v2_before.json", "v2_after_clean.json", "elements.panel-2.spec.title\n")
    newer = saved_pass(changes, "10-new", "v2_after_clean.json", "v2_before.json", "elements.panel-2.spec.title\n")
    assert newer.name == "10-new"
    code, out = run("held", changes, FX / "v2_before.json")
    assert code == 0, out


def test_values_declared_panel_still_empty_fails(tmp_path):
    before = json.loads((FX / "v_before.json").read_text(encoding="utf-8"))
    before["panels"]["2"].update(series=0, points=0)
    b = tmp_path / "b.json"
    b.write_text(json.dumps(before), encoding="utf-8")
    code, out = run("values", b, b, "--changed", "2")
    assert code == 1 and "still empty" in out


def test_values_changed_accepts_several_panels_after_one_flag():
    code, out = run("values", FX / "v_before.json", FX / "v_good.json", "--changed", "2", "4")
    assert code == 0 and "?? panel 4" in out, out


def test_renaming_a_panel_does_not_turn_old_problems_into_new_ones(tmp_path):
    def rename(spec):
        spec["elements"]["panel-1"]["spec"]["title"] = "Success rate (renamed)"
    after = edited_live(tmp_path, "v2_after_regressed.json", rename)
    code, out = run("check", FX / "v2_after_regressed.json", after, "--allow", "elements.panel-1.spec.title")
    assert code == 0, out


def test_adding_to_an_empty_list_is_one_change(tmp_path):
    def tag(spec):
        spec["tags"] = ["payments"]
    after = edited_live(tmp_path, "v2_before.json", tag)
    code, out = run("check", FX / "v2_before.json", after, "--allow", "tags*")
    assert code == 0, out
    assert "CHANGES (1)" in out and "ok tags[0]" in out


def test_query_variable_path_in_v2():
    code, out = run("paths", FX / "v2_query_variable.json", "variables[name=job].spec.query")
    assert "variables[name=job].spec.query.spec.query = " in out


def test_paths_lists_declarable_paths():
    code, out = run("paths", FX / "v2_before.json", "panel-2")
    assert code == 0 and "elements.panel-2.spec.title = " in out
