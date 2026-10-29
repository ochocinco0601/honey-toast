import json, os, subprocess, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "page_ask.py")

# A proxy set in the environment would otherwise carry the test client's loopback requests.
os.environ["NO_PROXY"] = ",".join(filter(None, [os.environ.get("NO_PROXY"), "127.0.0.1", "localhost"]))
os.environ["no_proxy"] = os.environ["NO_PROXY"]


def start(tmp_path, mode):
    p = subprocess.Popen([sys.executable, "-u", SCRIPT, mode, str(tmp_path)],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p


def wait_line(p, prefix, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        line = p.stdout.readline()
        if line.startswith(prefix):
            return line.strip()
    raise AssertionError("no %s line" % prefix)


def post(url, body, origin):
    req = urllib.request.Request(url + "answers", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Origin": origin})
    try:
        return urllib.request.urlopen(req, timeout=5).status
    except urllib.error.HTTPError as e:
        return e.code


def test_serve_saves_answers_from_own_origin_only(tmp_path):
    (tmp_path / "index.html").write_text("<title>t</title>", encoding="utf-8")
    p = start(tmp_path, "serve")
    try:
        url = wait_line(p, "READY ").split(" ", 1)[1]
        assert (tmp_path / "url.txt").read_text(encoding="utf-8") == url
        origin = url.rstrip("/")
        assert urllib.request.urlopen(url + "index.html", timeout=5).status == 200
        assert urllib.request.urlopen(url + "page-kit.js", timeout=5).status == 200

        assert post(url, b'{"answers": {"a": "x"}}', "http://evil.example") == 403
        assert post(url, b"not json", origin) == 400
        assert post(url, b"[1]", origin) == 400
        assert post(url, b'{"answers": {"a": "x"}}', origin) == 204

        saved = wait_line(p, "SAVED ").split(" ", 1)[1]
        assert json.load(open(saved, encoding="utf-8")) == {"answers": {"a": "x"}}
        assert len(list((tmp_path / "answers").glob("*.json"))) == 1
    finally:
        p.kill()


def get(url, host=None):
    req = urllib.request.Request(url, headers={"Host": host} if host else {})
    try:
        return urllib.request.urlopen(req, timeout=5).status
    except urllib.error.HTTPError as e:
        return e.code


def test_serve_refuses_foreign_host_and_never_serves_answers(tmp_path):
    (tmp_path / "index.html").write_text("<title>t</title>", encoding="utf-8")
    p = start(tmp_path, "serve")
    try:
        url = wait_line(p, "READY ").split(" ", 1)[1]
        origin = url.rstrip("/")
        assert get(url + "index.html", host="attacker.example:80") == 403
        assert post(url, b'{"a": 1}', origin) == 204
        name = os.path.basename(wait_line(p, "SAVED ").split(" ", 1)[1])
        assert get(url + "answers/" + name) == 404
        assert get(url + "answers/") == 404
    finally:
        p.kill()


def test_serve_shows_only_the_page_and_its_script(tmp_path):
    (tmp_path / "index.html").write_text("<title>t</title>", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("private", encoding="utf-8")
    (tmp_path / "resume.md").write_text("private", encoding="utf-8")
    p = start(tmp_path, "serve")
    try:
        url = wait_line(p, "READY ").split(" ", 1)[1]
        assert get(url + "index.html") == 200
        assert get(url + "page-kit.js") == 200
        assert get(url) == 404
        assert get(url + "notes.txt") == 404
        assert get(url + "resume.md") == 404
        assert get(url + "url.txt") == 404
    finally:
        p.kill()


def test_two_posts_in_one_instant_keep_both(tmp_path):
    p = start(tmp_path, "serve")
    try:
        url = wait_line(p, "READY ").split(" ", 1)[1]
        origin = url.rstrip("/")
        import threading
        threading.Thread(target=p.stdout.read, daemon=True).start()
        for _ in range(50):
            assert post(url, b'{"a": 1}', origin) == 204
        assert len(list((tmp_path / "answers").glob("*.json"))) == 50
    finally:
        p.kill()


def test_serve_removes_a_stale_url_file_before_ready(tmp_path):
    (tmp_path / "url.txt").write_text("http://127.0.0.1:1/", encoding="utf-8")
    p = start(tmp_path, "serve")
    try:
        url = wait_line(p, "READY ").split(" ", 1)[1]
        assert (tmp_path / "url.txt").read_text(encoding="utf-8") == url
    finally:
        p.kill()


NODE_HARNESS = r"""
const handlers = {};
const els = JSON.parse(process.argv[2]);
global.document = {
  title: 'T',
  addEventListener: (t, f) => { handlers[t] = f; },
  querySelectorAll: (sel) => sel.startsWith('input') ? els : [],
};
const kit = require(process.argv[1]);
let prevented = false;
handlers.submit({ preventDefault: () => { prevented = true; }, target: {} });
console.log(JSON.stringify({ answers: kit.collect(), prevented, status: kit.SENT }));
"""


def run_kit(elements):
    out = subprocess.run(["node", "-e", NODE_HARNESS, os.path.join(HERE, "page-kit.js"), json.dumps(elements)],
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_page_kit_stops_a_form_submitting_the_page():
    assert run_kit([])["prevented"] is True


def test_page_kit_keeps_every_value_of_a_repeated_name():
    got = run_kit([
        {"name": "ruling", "type": "text", "value": "keep"},
        {"name": "ruling", "type": "text", "value": "cut"},
        {"name": "ruling", "type": "text", "value": "fix"},
        {"name": "note", "type": "textarea", "value": "hi"},
        {"name": "v", "type": "radio", "value": "a", "checked": False},
        {"name": "v", "type": "radio", "value": "b", "checked": True},
        {"name": "c", "type": "checkbox", "value": "x", "checked": True},
    ])["answers"]
    assert got == {"ruling": ["keep", "cut", "fix"], "note": "hi", "v": "b", "c": ["x"]}


def test_page_kit_sent_message_does_not_promise_a_wake():
    status = run_kit([])["status"]
    assert "read it" in status


def test_watch_announces_each_file_once_across_restarts(tmp_path):
    answers = tmp_path / "answers"
    answers.mkdir()
    (answers / "answers-1.json").write_text("{}", encoding="utf-8")
    p = start(tmp_path, "watch")
    try:
        assert wait_line(p, "ANSWERS ").endswith("answers-1.json")
    finally:
        p.kill()
    (answers / "answers-2.json").write_text("{}", encoding="utf-8")
    p = start(tmp_path, "watch")
    try:
        assert wait_line(p, "ANSWERS ").endswith("answers-2.json")
    finally:
        p.kill()


def test_watch_records_a_file_before_announcing_it(tmp_path):
    answers = tmp_path / "answers"
    answers.mkdir()
    (answers / "answers-1.json").write_text("{}", encoding="utf-8")
    p = start(tmp_path, "watch")
    try:
        wait_line(p, "ANSWERS ")
        assert "answers-1.json" in (answers / ".announced").read_text(encoding="utf-8")
    finally:
        p.kill()


def run_poll(tmp_path, *args):
    return subprocess.run([sys.executable, "-u", SCRIPT, "poll", str(tmp_path), *args],
                          capture_output=True, text=True, timeout=30)


def test_poll_announces_every_unseen_file_and_exits(tmp_path):
    answers = tmp_path / "answers"
    answers.mkdir()
    (answers / "answers-1.json").write_text("{}", encoding="utf-8")
    (answers / "answers-2.json").write_text("{}", encoding="utf-8")
    out = run_poll(tmp_path, "10")
    assert out.returncode == 0
    lines = out.stdout.split()
    assert [l for l in lines if l.endswith(".json")] == [
        str(answers / "answers-1.json"), str(answers / "answers-2.json")]


def test_poll_skips_what_was_announced_and_times_out(tmp_path):
    answers = tmp_path / "answers"
    answers.mkdir()
    (answers / "answers-1.json").write_text("{}", encoding="utf-8")
    assert run_poll(tmp_path, "10").returncode == 0
    start_t = time.time()
    out = run_poll(tmp_path, "1")
    assert out.returncode == 0
    assert out.stdout.startswith("TIMEOUT")
    assert "ANSWERS" not in out.stdout
    assert time.time() - start_t < 10


def test_poll_wakes_on_a_file_arriving_while_it_waits(tmp_path):
    p = subprocess.Popen([sys.executable, "-u", SCRIPT, "poll", str(tmp_path), "20"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        time.sleep(1)
        (tmp_path / "answers" / "answers-9.json").write_text("{}", encoding="utf-8")
        assert wait_line(p, "ANSWERS ").endswith("answers-9.json")
        assert p.wait(timeout=10) == 0
    finally:
        p.kill()


def test_poll_with_a_bad_timeout_prints_the_usage(tmp_path):
    for bad in ("soon", "0", "-5"):
        out = run_poll(tmp_path, bad)
        assert out.returncode != 0
        assert "Traceback" not in out.stderr
        assert "poll DIR SECONDS" in out.stderr
