"""Move dashboards between Grafana and files, and capture panel numbers. Standard library only.

Dashboard JSON travels by this script, never by an assistant retyping it.

  python dashio.py get UID OUT.json                     fetch through the v2 API (with metadata.resourceVersion)
  python dashio.py put IN.json "MESSAGE"                save; refused (409) if someone saved since IN.json was fetched
  python dashio.py create IN.json "MESSAGE"             create a new dashboard; refused if the name (uid) exists
  python dashio.py history UID                          list saved versions: generation, when, who, message
  python dashio.py version UID GENERATION OUT.json      fetch one past version (to compare with dashcheck.py check)
  python dashio.py probe OUT.md [FOLDER_UID]            first run on an instance: try what the skill relies on, on a
                                                        throwaway dashboard it creates and deletes; write the results
  python dashio.py values DASH.json OUT.json --from 2026-10-01T18:00:00Z --to 2026-10-01T19:00:00Z
                                                        run every panel's queries over a fixed range, write the values file

Environment: GRAFANA_URL (e.g. https://grafana.example.com), and GRAFANA_TOKEN (service account token)
or GRAFANA_USER + GRAFANA_PASSWORD. GRAFANA_NAMESPACE defaults to "default" (organization 1);
other organizations are "org-<id>". A company certificate authority is picked up from SSL_CERT_FILE,
and a proxy from HTTPS_PROXY / NO_PROXY.
"""
import base64
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

VAR_RE = re.compile(r"\$\{([A-Za-z_]\w*)(?::(\w+))?\}|\$([A-Za-z_]\w*)|\[\[([A-Za-z_]\w*)\]\]")


def base():
    url = os.environ.get("GRAFANA_URL")
    if not url:
        sys.exit("GRAFANA_URL is not set")
    return url.rstrip("/")


def dash_url(name=""):
    ns = os.environ.get("GRAFANA_NAMESPACE", "default")
    return f"{base()}/apis/dashboard.grafana.app/v2/namespaces/{ns}/dashboards" + (f"/{name}" if name else "")


def call(method, url, body=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if os.environ.get("GRAFANA_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GRAFANA_TOKEN"]
    elif os.environ.get("GRAFANA_USER"):
        pair = f"{os.environ['GRAFANA_USER']}:{os.environ.get('GRAFANA_PASSWORD', '')}"
        headers["Authorization"] = "Basic " + base64.b64encode(pair.encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            body = json.loads(raw)
        except ValueError:
            body = {"message": raw.decode(errors="replace")[:500]}
        if e.code == 404 and "/namespaces/" in url and isinstance(body, dict):
            ns = os.environ.get("GRAFANA_NAMESPACE", "default")
            body["message"] = (f"{body.get('message') or 'not found'} [namespace '{ns}': if the dashboard is in "
                               "another organisation, set GRAFANA_NAMESPACE=org-<id> (see LOCAL.md)]")
        return e.code, body


def write(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def for_save(doc, message, create=False):
    m = doc.get("metadata") or {}
    keep = {k: m[k] for k in ("name", "namespace", "resourceVersion", "labels") if k in m}
    if create:
        keep.pop("resourceVersion", None)
        keep.pop("labels", None)
    notes = {k: v for k, v in (m.get("annotations") or {}).items() if k in ("grafana.app/folder",)}
    keep["annotations"] = {**notes, "grafana.app/message": message}
    return {"apiVersion": doc.get("apiVersion", "dashboard.grafana.app/v2"), "kind": "Dashboard", "metadata": keep, "spec": doc["spec"]}


def cmd_get(uid, out):
    code, doc = call("GET", dash_url(uid))
    if code != 200:
        sys.exit(f"GET failed ({code}): {doc.get('message')}")
    conversion = (doc.get("status") or {}).get("conversion") or {}
    if conversion.get("failed"):
        sys.exit(f"refusing: Grafana could not convert this dashboard to the v2 format ({conversion.get('error') or 'no detail'}). "
                 "Saving the v2 view would overwrite the stored dashboard. Change it in the browser or with the classic API instead.")
    write(out, doc)
    m = doc["metadata"]
    print(f"saved {out}: '{doc['spec'].get('title')}' resourceVersion {m.get('resourceVersion')} generation {m.get('generation')}"
          f" folder {(m.get('annotations') or {}).get('grafana.app/folder', '(root)')}"
          f" stored as {conversion.get('storedVersion', 'v2')}")


def cmd_put(path, message):
    doc = read(path)
    if not (doc.get("metadata") or {}).get("resourceVersion"):
        sys.exit("refusing to save: metadata.resourceVersion is missing, and without it Grafana overwrites any newer save")
    code, res = call("PUT", dash_url(doc["metadata"]["name"]), for_save(doc, message))
    if code == 409:
        sys.exit(f"CONFLICT: the dashboard was saved by someone else after {path} was fetched. Fetch again and start the change over.\n{res.get('message')}")
    if code != 200:
        sys.exit(f"PUT failed ({code}): {res.get('message')}")
    print(f"saved: resourceVersion {res['metadata'].get('resourceVersion')} generation {res['metadata'].get('generation')}")


def cmd_create(path, message):
    doc = read(path)
    body = for_save(doc, message, create=True)
    code, res = call("POST", dash_url(), body)
    if code == 409:
        sys.exit(f"refused: a dashboard named '{body['metadata'].get('name')}' already exists. Choose a new name (uid); never replace it.")
    if code not in (200, 201):
        sys.exit(f"create failed ({code}): {res.get('message')}")
    print(f"created '{res['metadata'].get('name')}' resourceVersion {res['metadata'].get('resourceVersion')}")


def history(uid):
    code, res = call("GET", dash_url() + f"?labelSelector=grafana.app/get-history=true&fieldSelector=metadata.name={uid}&limit=100")
    if code != 200:
        sys.exit(f"history failed ({code}): {res.get('message')}")
    return sorted(res.get("items") or [], key=lambda i: -int(i["metadata"].get("generation") or 0))


def cmd_history(uid):
    for item in history(uid):
        m = item["metadata"]
        a = m.get("annotations") or {}
        print(f"  generation {m.get('generation')}  {a.get('grafana.app/updatedTimestamp') or m.get('creationTimestamp')}"
              f"  {a.get('grafana.app/updatedBy') or a.get('grafana.app/createdBy')}  {a.get('grafana.app/message') or ''}")


def cmd_version(uid, generation, out):
    for item in history(uid):
        if str(item["metadata"].get("generation")) == str(generation):
            item["metadata"].pop("resourceVersion", None)
            write(out, item)
            print(f"saved {out}: generation {generation} (without resourceVersion, so it cannot be saved back by mistake)")
            return
    sys.exit(f"no generation {generation} in the history of {uid}")


# ---------- panel numbers ----------

def variable_values(spec, v1):
    vals = {}
    items = (spec.get("templating") or {}).get("list") or [] if v1 else spec.get("variables") or []
    for v in items:
        s = v if v1 else (v.get("spec") or {})
        cur = (s.get("current") or {}).get("value")
        vals[s.get("name")] = cur
    return vals


def interpolate(obj, vals, missing=None):
    if isinstance(obj, str):
        def sub(m):
            name, fmt = (m.group(1), m.group(2)) if m.group(1) else (m.group(3) or m.group(4), None)
            if name not in vals:
                return m.group(0)
            v = vals[name]
            if v is None or v == "" or v == []:
                if missing is not None:
                    missing.add(name)
                return m.group(0)
            if v in ("$__all", ["$__all"]):
                return ".*"
            if isinstance(v, list):
                return ("(" + "|".join(v) + ")") if fmt == "regex" else (",".join(v) if fmt == "csv" else "|".join(v))
            return str(v)
        return VAR_RE.sub(sub, obj)
    if isinstance(obj, dict):
        return {k: interpolate(v, vals, missing) for k, v in obj.items()}
    if isinstance(obj, list):
        return [interpolate(v, vals, missing) for v in obj]
    return obj


def default_datasource():
    code, res = call("GET", f"{base()}/api/datasources")
    for d in res if code == 200 and isinstance(res, list) else []:
        if d.get("isDefault"):
            return {"uid": d.get("uid"), "type": d.get("type")}
    return None


def panels_and_queries(doc):
    """Yield (key, title, queries or error) where queries are /api/ds/query entries."""
    spec = doc.get("spec", doc.get("dashboard", doc))
    v1 = "panels" in spec and "elements" not in spec
    vals = variable_values(spec, v1)
    for key, title, qs in _panels_and_queries(spec, v1, vals):
        if isinstance(qs, str):
            yield key, title, qs
            continue
        missing, resolved = set(), []
        for q in qs:
            q = interpolate(q, vals, missing)
            if not (q.get("datasource") or {}).get("uid"):
                q["datasource"] = default_datasource()
                if not q["datasource"]:
                    yield key, title, f"query {q.get('refId')} names no data source and there is no default"
                    break
            resolved.append(q)
        else:
            if missing:
                yield key, title, f"variable(s) {', '.join(sorted(missing))} have no saved value; set one, or capture with a value in a scratch copy"
            else:
                yield key, title, resolved


def _panels_and_queries(spec, v1, vals):
    if v1:
        def flat(ps):
            for p in ps:
                yield p
                yield from flat(p.get("panels") or [])
        for p in flat(spec.get("panels") or []):
            if p.get("type") == "row":
                continue
            if "libraryPanel" in p:
                yield str(p.get("id")), p.get("title", ""), "library panel: its queries live in the library element"
                continue
            qs = []
            for t in p.get("targets") or []:
                if t.get("hide"):
                    continue
                q = {k: v for k, v in t.items() if k != "datasource"}
                q["datasource"] = t.get("datasource") or p.get("datasource") or {}
                qs.append(q)
            yield str(p.get("id")), p.get("title", ""), qs
    else:
        for name, el in (spec.get("elements") or {}).items():
            s = el.get("spec") or {}
            if el.get("kind") == "LibraryPanel":
                yield name, s.get("title", ""), "library panel: its queries live in the library element"
                continue
            qs = []
            for pq in ((s.get("data") or {}).get("spec") or {}).get("queries") or []:
                ps = pq.get("spec") or {}
                if ps.get("hidden"):
                    continue
                query = ps.get("query") or {}
                q = dict(query.get("spec") or {})
                q["refId"] = ps.get("refId")
                ds_name = (query.get("datasource") or {}).get("name")
                q["datasource"] = {"uid": ds_name, "type": query.get("group")} if ds_name else {}
                qs.append(q)
            yield name, s.get("title", ""), qs


def summarize(result):
    """series = frames with rows; rows = rows returned (logs and tables count too); numbers from numeric fields."""
    nums, series, rows, last = [], 0, 0, None
    for frame in result.get("frames") or []:
        fields = (frame.get("schema") or {}).get("fields") or []
        columns = (frame.get("data") or {}).get("values") or []
        n = max((len(c) for c in columns), default=0)
        if n:
            series += 1
            rows += n
        for f, col in zip(fields, columns):
            if f.get("type") == "time":
                continue
            values = [v for v in col if isinstance(v, (int, float)) and not isinstance(v, bool)]
            nums += values
            if values and last is None:
                last = values[-1]
    return series, rows, nums, last


def cmd_values(dash_path, out, start, end):
    def ms(t):
        return str(int(datetime.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp() * 1000))
    doc = read(dash_path)
    panels = {}
    for key, title, qs in panels_and_queries(doc):
        if isinstance(qs, str) or not qs:
            panels[key] = {"title": title, "series": 0, "points": 0, "error": qs if isinstance(qs, str) else "no queries"}
            continue
        if any(str((q.get("datasource") or {}).get("uid", "")).startswith("-- ") for q in qs):
            panels[key] = {"title": title, "series": 0, "points": 0, "error": "uses another panel's or mixed data; check it in the browser"}
            continue
        code, res = call("POST", f"{base()}/api/ds/query", {"from": ms(start), "to": ms(end), "queries": qs})
        errors = [r.get("error") for r in (res.get("results") or {}).values() if r.get("error")]
        if code != 200 and not errors:
            errors = [res.get("message") or f"HTTP {code}"]
        series, rows, nums, last = 0, 0, [], None
        for r in (res.get("results") or {}).values():
            s, n, v, l = summarize(r)
            series, rows, nums = series + s, rows + n, nums + v
            last = l if last is None else last
        panels[key] = {"title": title, "series": series, "points": rows,
                       "min": min(nums) if nums else None, "max": max(nums) if nums else None,
                       "sum": round(sum(nums), 9) if nums else None, "last": last,
                       "error": "; ".join(map(str, errors)) or None}
    write(out, {"range": {"from": start, "to": end}, "panels": panels})
    bad = [k for k, v in panels.items() if v.get("error") or not v.get("points")]
    print(f"saved {out}: {len(panels)} panels" + (f"; empty or failing: {', '.join(bad)}" if bad else ""))


def cmd_probe(out, folder=None):
    """Try, on a throwaway dashboard, the Grafana behaviours the skill relies on; write what was observed."""
    rows, failed = [], False

    def rec(check, expected, observed, ok):
        nonlocal failed
        failed = failed or not ok
        rows.append(f"| {check} | {expected} | {observed} | {'yes' if ok else '**NO**'} |")

    code, health = call("GET", f"{base()}/api/health")
    version = health.get("version", f"unknown (HTTP {code})")
    name = f"grafana-dashboards-probe-{datetime.datetime.now(datetime.timezone.utc):%Y%m%d%H%M%S}"
    doc = read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "new-dashboard.json"))
    doc["metadata"] = {"name": name, "annotations": {"grafana.app/folder": folder} if folder else {}}
    doc["spec"]["title"] = "grafana-dashboards probe - safe to delete"
    doc["spec"]["elements"]["panel-1"]["spec"]["title"] = "probe panel"

    code, res = call("POST", dash_url(), for_save(doc, "probe: create", create=True))
    rec("Create through the v2 API", "201", code, code in (200, 201))
    if code in (200, 201):
        code, got = call("GET", dash_url(name))
        conv = (got.get("status") or {}).get("conversion") or {}
        rv1 = (got.get("metadata") or {}).get("resourceVersion")
        rec("Read back with a resourceVersion", "200 and a resourceVersion", f"{code}, {'present' if rv1 else 'missing'}", code == 200 and bool(rv1))
        rec("Stored format", "reported", conv.get("storedVersion", "v2 (no conversion)"), True)

        got["spec"]["title"] += " (edited)"
        code, res = call("PUT", dash_url(name), for_save(got, "probe: save with current resourceVersion"))
        rec("Save carrying the current resourceVersion", "200", code, code == 200)

        code, res = call("PUT", dash_url(name), for_save(got, "probe: save with a stale resourceVersion"))
        rec("Save carrying a stale resourceVersion is refused", "409", code, code == 409)

        items = history(name)
        who = {((i["metadata"].get("annotations") or {}).get("grafana.app/updatedBy")
                or (i["metadata"].get("annotations") or {}).get("grafana.app/createdBy")) for i in items}
        rec("Version history lists the saves", "2 or more", len(items), len(items) >= 2)
        rec("Saves are recorded under", "the assistant's own identity", ", ".join(sorted(map(str, who))), True)

        code, _ = call("DELETE", dash_url(name))
        rec("Delete the probe dashboard", "200", code, code == 200)

    report = [f"# Probe of {base()}", "",
              f"Grafana {version}, namespace `{os.environ.get('GRAFANA_NAMESPACE', 'default')}`, "
              f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC.", "",
              "| Check | Expected | Observed | Holds |", "|---|---|---|---|", *rows, ""]
    if failed:
        report.append("At least one behaviour the skill relies on does not hold here. Do not use the skill's save "
                      "steps until FOUNDATIONS.md is checked against this instance and the skill corrected.")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))
    return 1 if failed else 0


def main():
    a = sys.argv[1:]
    try:
        if a[:1] == ["get"] and len(a) == 3:
            return cmd_get(a[1], a[2])
        if a[:1] == ["put"] and len(a) == 3:
            return cmd_put(a[1], a[2])
        if a[:1] == ["create"] and len(a) == 3:
            return cmd_create(a[1], a[2])
        if a[:1] == ["history"] and len(a) == 2:
            return cmd_history(a[1])
        if a[:1] == ["version"] and len(a) == 4:
            return cmd_version(a[1], a[2], a[3])
        if a[:1] == ["probe"] and len(a) in (2, 3):
            return cmd_probe(a[1], a[2] if len(a) == 3 else None)
        if a[:1] == ["values"] and len(a) == 7 and a[3] == "--from" and a[5] == "--to":
            return cmd_values(a[1], a[2], a[4], a[6])
    except urllib.error.URLError as e:
        sys.exit(f"cannot reach Grafana at {base()}: {e.reason}")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
