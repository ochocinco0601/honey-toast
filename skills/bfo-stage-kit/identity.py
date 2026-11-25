"""Read what each deployable is called, once, from its configuration and deployment files, before any reader.

Usage: python identity.py <register folder> [--workspace <folder>]

What it reads. For each surveyed service (survey.csv `kind` `service`, a deployable): its build folder's configuration
(`application*.yml`, `application*.properties`, `Dockerfile`, `.env`), and every survey row of kind `deployment or
configuration` (manifests, Helm charts and values, Kustomize components and overlays). Configuration and deployment
files only; never code.

What it writes, into `identity/` (outside the root the merge owns):
- `identity/identifiers.csv`: `deployable,ref,attribute,value,source,basis`, one row per identifier. `ref` is blank for
  the deployable itself, `store:<configuration key>` for a store or broker it uses, `external:<configuration key>` for
  an outside system. `attribute` is an OpenTelemetry attribute name (method/otel-attributes.csv lists each one's
  status and the deprecated alias some vendors still read), or `custom: <name>`. `basis` is `rule: read` (a cited file
  states it), `rule: derived` (by the rule named in `source`) or `not found: <where looked>`. A judgment is never
  written here: it is the model's, in `identity/merges.csv`, or in `identity/unmatched.csv` for the model to settle.
- `identity/merges.csv`: `candidates,decision,basis,evidence,what_would_change_it`, created empty when missing and
  never overwritten: each row is a judgment the model made (merge or apart, map ids `;`-joined), applied by the merge.
- `identity/unmatched.csv`: each workload whose image matches no build folder, or two, with its candidates, for one
  agent to join by judgment (writing an `identifiers.csv`-shaped row with basis `judgment: <evidence>`) or record
  `not found`.

How a workload is joined to its build folder: its image, normalised (registry host and path up to the last `/`, the
`:tag` and any `@sha256:` digest dropped, lower case), equal to the folder's service name.

A value that is a placeholder (`${X}`, `{{ .Values.x }}`, `$(X)`) is never a literal: the key it sits in stays
unresolved, and the row says so in its basis.
"""
import csv
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tables  # noqa: E402

COLS = ["deployable", "ref", "attribute", "value", "source", "basis"]
MERGE_COLS = ["candidates", "decision", "basis", "evidence", "what_would_change_it"]
UNMATCHED_COLS = ["workload", "image", "source", "candidates"]
DIR = "identity"
WORKLOADS = {"Deployment", "StatefulSet", "CronJob", "DeploymentConfig", "DaemonSet", "Job"}
PLACEHOLDER = re.compile(r"\$\{[^}]*\}|\{\{[^}]*\}\}|\$\([^)]*\)")
CONFIG = re.compile(r"(application[^/]*\.(ya?ml|properties)|bootstrap[^/]*\.(ya?ml|properties)|Dockerfile|\.env)$")
DEPLOY = re.compile(r"\.(ya?ml|json)$")
JDBC = re.compile(r"jdbc:(?P<sys>[a-z0-9]+):(?:(?:thin|oci8?):@)?(?://)?(?P<host>[^:/;@?]+)(?::(?P<port>\d+))?[/:]?(?P<db>[^?;\s]*)")
TNS = re.compile(r"jdbc:(?P<sys>[a-z0-9]+):thin:@\s*\(DESCRIPTION.*?\(HOST\s*=\s*(?P<host>[^)\s]+)\)"
                 r"(?:.*?\(PORT\s*=\s*(?P<port>\d+)\))?(?:.*?\(SERVICE_NAME\s*=\s*(?P<svc>[^)\s]+)\))?", re.I | re.S)
URLISH = re.compile(r"^(?P<scheme>[a-z][a-z0-9+.-]*)://(?P<host>[^:/?#]+)(?::(?P<port>\d+))?(?P<path>/[^?#]*)?")
PARAMS = re.compile(r"[?;#].*$", re.S)  # query and JDBC properties: where a user, password or token is passed
HOSTPORT = re.compile(r"^(?P<host>[A-Za-z0-9.-]+):(?P<port>\d+)$")
STORE_WORDS = (("redis", "cache", "redis"), ("memcache", "cache", "memcached"), ("mongo", "db", "mongodb"),
               ("postgres", "db", "postgresql"), ("mysql", "db", "mysql"), ("oracle", "db", "oracle"),
               ("kafka", "broker", "kafka"), ("rabbit", "broker", "rabbitmq"), ("amqp", "broker", "rabbitmq"),
               ("database", "db", ""), ("_db_", "db", ""))
CLIENT_KEY = re.compile(r"(base[-_.]?url|base[-_.]?uri|endpoint|[-_.]url|[-_.]uri)$", re.I)


def norm_image(image):
    """`registry.example/team/cartservice:1.2@sha256:..` -> `cartservice`."""
    img = (image or "").strip().strip("'\"").split("@")[0]
    img = img.rsplit("/", 1)[-1]
    return img.split(":")[0].lower()


def placeholder(value):
    return bool(PLACEHOLDER.search(value or ""))


def literal(value):
    return (value or "").strip().strip("'\"")


class Reader:
    def __init__(self, ws):
        self.ws = pathlib.Path(ws)
        self.rows, self.seen = [], set()

    def add(self, dep, ref, attr, value, source, basis):
        key = (dep, ref, attr, value)
        if key in self.seen or not value:
            return
        self.seen.add(key)
        self.rows.append({"deployable": dep, "ref": ref, "attribute": attr, "value": value, "source": source,
                          "basis": basis})

    def rel(self, p):
        try:
            return p.relative_to(self.ws).as_posix()
        except ValueError:
            return p.as_posix()


def files_under(ws, rel_paths, pattern):
    out = []
    for rp in rel_paths:
        base = ws / rp
        cands = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
        out += [p for p in cands if p.is_file() and pattern.search(p.name)]
    return out


def lines_of(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def workloads(path, lines):
    """[{kind, name, line, images: [(image, line)], env: {NAME: (value, line)}, jvm: [(text, line)]}] from one YAML
    file's lines: every workload a manifest, chart or Kustomize patch declares (line-based, documents and inline
    patches alike)."""
    out, cur, want_name, env_name = [], None, False, None
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        m = re.match(r"^-?\s*kind:\s*(\w+)\s*$", s)
        if m:
            cur, want_name, env_name = None, m.group(1) in WORKLOADS, None
            kind = m.group(1)
            continue
        if want_name and re.match(r"^name:\s*\S", s) and cur is None:
            cur = {"kind": kind, "name": literal(s.split(":", 1)[1]), "line": i, "images": [], "env": {}, "jvm": []}
            out.append(cur)
            want_name = False
            continue
        if cur is None:
            continue
        m = re.match(r"^-?\s*image:\s*(\S.*)$", s)
        if m:
            cur["images"].append((literal(m.group(1)), i))
            continue
        m = re.match(r"^-\s*name:\s*(\S+)\s*$", s)
        if m:
            env_name = literal(m.group(1))
            continue
        m = re.match(r"^value:\s*(.*)$", s)
        if m and env_name:
            cur["env"].setdefault(env_name, (literal(m.group(1)), i))
            env_name = None
            continue
        if "-Dotel.service.name=" in s:
            cur["jvm"].append((s, i))
    return out


def props(path, lines):
    """{dotted key: (value, line)} from a .properties, .env or simple YAML file (nested keys joined by dots)."""
    out, stack = {}, []
    yaml = path.suffix in (".yml", ".yaml")
    for i, raw in enumerate(lines, 1):
        if not raw.strip() or raw.lstrip().startswith("#") or raw.strip() == "---":
            continue
        if not yaml:
            m = re.match(r"^\s*(?:export\s+)?([\w.\-\[\]]+)\s*[=:]\s*(.*)$", raw)
            if m:
                out.setdefault(m.group(1), (literal(m.group(2)), i))
            continue
        m = re.match(r"^(\s*)([\w.\-]+):\s*(.*)$", raw)
        if not m:
            continue
        ind = len(m.group(1))
        while stack and stack[-1][0] >= ind:
            stack.pop()
        key = ".".join([k for _, k in stack] + [m.group(2)])
        val = m.group(3).strip()
        if val and not val.startswith(("|", ">")):
            out.setdefault(key, (literal(val.split(" #")[0]), i))
        else:
            stack.append((ind, m.group(2)))
    return out


def store_kind(name, value=""):
    text = f"_{name}_{value}_".lower()
    for word, kind, system in STORE_WORDS:
        if word in text:
            return kind, system
    return None, ""


SAFE = {"server.address": re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,252}[A-Za-z0-9])?$"),
        "server.port": re.compile(r"^\d{1,5}$"), "db.namespace": re.compile(r"^[A-Za-z0-9_.$-]{1,128}$"),
        "url.path": re.compile(r"^/(?!(?:[^/]*\d){4})[a-z][a-z0-9._-]{0,31}$")}  # a word, never a key-shaped token


def strip_credentials(value):
    """A connection value with everything up to its last @ dropped (a host never holds one), so no user or password
    is read, then its query and properties."""
    if "@" in value:
        head, tail = value.rsplit("@", 1)
        m = re.match(r"^(.*?://)", head) or re.match(r"^(jdbc:[a-z0-9]+:[a-z0-9]+:)", head, re.I)
        value = (m.group(1) + ("" if m.group(1).endswith("//") else "@") + tail) if m else tail
    return PARAMS.sub("", value)


class Shaped:
    """Writes an address row only when its value has the plain shape of its attribute: a value that does not (a
    credential, a token, an unparsed form) is never written."""
    def __init__(self, r):
        self.r = r

    def add(self, dep, ref, attr, value, source, basis):
        if attr not in SAFE or SAFE[attr].match(value or ""):
            self.r.add(dep, ref, attr, value, source, basis)


def address_rows(r, dep, ref, value, source, system="", kind=None):
    """The address rows of one store, broker or outside system, from a URL, a JDBC URL or host:port."""
    value, r = strip_credentials(value), Shaped(r)
    if placeholder(value):
        names = " ".join(re.sub(r"[:=].*", "", p.strip("${}()")).strip() for p in PLACEHOLDER.findall(value))
        r.r.add(dep, ref, "server.address", f"not set here ({names})", source,
                "not found: a placeholder, so the key is unresolved")
        if system:
            r.add(dep, ref, "messaging.system.name" if kind == "broker" else "db.system.name", system, source,
                  "rule: derived: from the configuration key's name")
        return
    d = TNS.match(value)  # an Oracle descriptor: its HOST, PORT and SERVICE_NAME, read as the plain URL form
    if d:
        value = f"jdbc:{d['sys']}:thin:@{d['host']}" + (f":{d['port']}" if d["port"] else "") + (
            f"/{d['svc']}" if d["svc"] else "")
    m = JDBC.match(value)
    if m:
        r.add(dep, ref, "db.system.name", m.group("sys"), source, "rule: read")
        r.add(dep, ref, "server.address", m.group("host"), source, "rule: read")
        if m.group("port"):
            r.add(dep, ref, "server.port", m.group("port"), source, "rule: read")
        if m.group("db"):
            r.add(dep, ref, "db.namespace", m.group("db"), source, "rule: read")
        return
    m = URLISH.match(value) or HOSTPORT.match(value)
    if not m:
        return
    attr_sys = "messaging.system.name" if kind == "broker" else "db.system.name"
    scheme = m.groupdict().get("scheme")
    if kind in ("db", "cache", "broker"):
        sysname = system or (scheme if scheme not in ("http", "https", "tcp") else "")
        if sysname:
            r.add(dep, ref, attr_sys, sysname, source, "rule: read" if scheme == sysname else
                  "rule: derived: from the configuration key's name")
    r.add(dep, ref, "server.address", m.group("host"), source, "rule: read")
    if m.group("port"):
        r.add(dep, ref, "server.port", m.group("port"), source, "rule: read")
    if kind is None and m.groupdict().get("path"):
        r.add(dep, ref, "url.path", "/" + m.group("path").strip("/").split("/")[0], source, "rule: read")  # first segment: a token sits deeper


def read(reg, ws=None):
    """(identifier rows, unmatched workloads) for the register's surveyed services."""
    reg = pathlib.Path(reg)
    import reading_check as rc
    survey = tables.dicts(reg / "survey.csv")
    services = [s for s in survey if (s.get("kind") or "").strip() == "service"]
    deploy = [s for s in survey if (s.get("kind") or "").strip() == "deployment or configuration"]
    all_paths = [(s.get("path") or "").strip() for s in survey if (s.get("path") or "").strip()]
    ws = pathlib.Path(ws) if ws else rc.workspace(reg.resolve(), all_paths)
    settings = {}
    try:
        settings = json.loads((reg / "run-settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    app_attr = (settings.get("app_id_attribute") or "").strip()
    r = Reader(ws)
    names = {(s.get("service") or "").strip().lower(): (s.get("service") or "").strip() for s in services}
    by_path = {}  # a folder name on a service's build path, when only one service has it (`src/cartservice/src`)
    for s in services:
        for seg in {x.lower() for x in (s.get("path") or "").strip().split("/") if x}:
            by_path.setdefault(seg, set()).add((s.get("service") or "").strip())
    for seg, deps in by_path.items():
        if len(deps) == 1 and seg not in names:
            names[seg] = next(iter(deps))
    hosts = set(names)

    found = {}  # deployable -> [workload]
    unmatched = []
    # every surveyed folder: a Kustomize component or a manifest can sit in a folder the survey classed as a service
    for f in files_under(ws, sorted(set(all_paths), key=lambda x: (x.count("/"), x)), DEPLOY):
        for w in workloads(f, lines_of(f)):
            if placeholder(w["name"]):
                continue
            imgs = [(norm_image(i), ln) for i, ln in w["images"] if not placeholder(i)]
            hit = {names[n] for n, _ in imgs if n in names}
            if len(hit) == 1:
                found.setdefault(hit.pop(), []).append((f, w))
            elif w["images"] or hit:
                unmatched.append({"workload": w["name"], "image": "; ".join(i for i, _ in w["images"]),
                                  "source": f"{r.rel(f)}:{w['line']}", "candidates": "; ".join(sorted(hit))})
            else:  # a patch naming the workload with no image: joined by the workload's own name, when it is one
                key = w["name"].lower()
                if key in names:
                    found.setdefault(names[key], []).append((f, w))
    hosts |= {w["name"].lower() for got in found.values() for _, w in got}  # only workloads that run a deployable
    for s in services:
        dep = (s.get("service") or "").strip()
        src_dir = (s.get("path") or "").strip()
        if not deploy:
            r.add(dep, "", "custom: finding", "deployment files not given", "survey.csv: no deployment or "
                  "configuration row", "not found: survey.csv lists no deployment or configuration folder")
        service_name = None
        for f, w in found.get(dep, []):
            src = r.rel(f)
            attr = "k8s.deployment.name" if w["kind"] == "Deployment" else f"custom: {w['kind']} name"
            if w["images"]:
                r.add(dep, "", attr, w["name"], f"{src}:{w['line']}", "rule: read")
            for img, ln in w["images"]:
                if not placeholder(img):
                    r.add(dep, "", "container.image.name", norm_image(img), f"{src}:{ln}", "rule: read")
            env = w["env"]
            if "OTEL_SERVICE_NAME" in env and not placeholder(env["OTEL_SERVICE_NAME"][0]):
                service_name = service_name or (env["OTEL_SERVICE_NAME"][0], f"{src}:{env['OTEL_SERVICE_NAME'][1]}")
            for text, ln in w["jvm"]:
                m = re.search(r"-Dotel\.service\.name=(\S+)", text)
                if m and not placeholder(m.group(1)):
                    service_name = service_name or (literal(m.group(1)), f"{src}:{ln}")
            if "OTEL_RESOURCE_ATTRIBUTES" in env:
                val, ln = env["OTEL_RESOURCE_ATTRIBUTES"]
                for pair in val.split(","):
                    k, _, v = pair.partition("=")
                    k, v = k.strip(), v.strip()
                    if not v or placeholder(v):
                        continue
                    if k == "service.name":
                        service_name = service_name or (v, f"{src}:{ln}")
                    elif k == "service.namespace":
                        r.add(dep, "", "service.namespace", v, f"{src}:{ln}", "rule: read")
                    elif k == "deployment.environment.name":
                        r.add(dep, "", "deployment.environment.name", v, f"{src}:{ln}", "rule: read")
                    elif app_attr and k == app_attr:
                        r.add(dep, "", "custom: app id", v, f"{src}:{ln} ({app_attr}, run-settings.json "
                              "app_id_attribute)", "rule: read")
            for name, (val, ln) in env.items():
                stores_and_clients(r, dep, name, val, f"{src}:{ln}", hosts)
        cfg = {}
        for f in files_under(ws, [src_dir], CONFIG):
            if f.name == "Dockerfile":
                for i, line in enumerate(lines_of(f), 1):
                    m = re.search(r"-Dotel\.service\.name=([^\s\"']+)", line)
                    if m and not placeholder(m.group(1)):
                        service_name = service_name or (m.group(1), f"{r.rel(f)}:{i}")
                continue
            for k, (v, ln) in props(f, lines_of(f)).items():
                cfg.setdefault(k, (v, f"{r.rel(f)}:{ln}"))
        for k, (v, src) in cfg.items():
            low = k.lower()
            if low in ("spring.datasource.url", "spring.datasource.jdbc-url", "spring.r2dbc.url"):
                address_rows(r, dep, "store:spring.datasource", v, src, kind="db")
            elif low in ("spring.datasource.username",) and v and not placeholder(v):
                r.add(dep, "store:spring.datasource", "custom: schema", v, src,
                      "rule: derived: an Oracle user is its schema, where no currentSchema is set")
            elif low.endswith("currentschema") and v and not placeholder(v):
                r.add(dep, "store:spring.datasource", "custom: schema", v, src, "rule: read")
            elif low in ("spring.redis.host", "spring.data.redis.host"):
                r.add(dep, "store:spring.redis", "db.system.name", "redis", src, "rule: derived: spring.redis")
                address_rows(r, dep, "store:spring.redis", v, src, "redis", "cache")
            elif low in ("spring.data.mongodb.uri",):
                address_rows(r, dep, "store:spring.data.mongodb", v, src, "mongodb", "db")
            elif low in ("spring.kafka.bootstrap-servers",):
                r.add(dep, "store:spring.kafka", "messaging.system.name", "kafka", src, "rule: derived: spring.kafka")
                address_rows(r, dep, "store:spring.kafka", v.split(",")[0], src, "kafka", "broker")
            elif low in ("spring.rabbitmq.host",):
                r.add(dep, "store:spring.rabbitmq", "messaging.system.name", "rabbitmq", src,
                      "rule: derived: spring.rabbitmq")
                address_rows(r, dep, "store:spring.rabbitmq", v, src, "rabbitmq", "broker")
            elif not low.startswith(("spring.", "management.", "logging.", "server.")):
                stores_and_clients(r, dep, k, v, src, hosts)
        if service_name:
            r.add(dep, "", "service.name", service_name[0], service_name[1], "rule: read")
        elif "spring.application.name" in cfg and not placeholder(cfg["spring.application.name"][0]):
            v, src = cfg["spring.application.name"]
            r.add(dep, "", "service.name", v, src, "rule: derived: spring.application.name, as the Spring Boot "
                  "OpenTelemetry starter takes it when nothing else sets the service name")
        else:
            r.add(dep, "", "service.name", "not set (the SDK default unknown_service:<process> applies)",
                  "OTEL_SERVICE_NAME, OTEL_RESOURCE_ATTRIBUTES, -Dotel.service.name, spring.application.name",
                  "not found: none set in the deployment or configuration files read")
    return r.rows, unmatched


def stores_and_clients(r, dep, name, value, source, hosts):
    """One configuration key or environment variable that holds an address: a store, a broker, or an outside system.
    An address whose host is another surveyed deployable or workload is a call between parts, not a part."""
    if not value or not re.search(r"(url|uri|addr|address|host|endpoint|servers)$", name, re.I):
        return
    host = ""
    m = URLISH.match(value) or HOSTPORT.match(value)
    if m:
        host = m.group("host").lower()
    elif not placeholder(value) and re.fullmatch(r"[A-Za-z0-9.-]+", value):
        host = value.lower()
    if host and host.split(".")[0] in hosts:
        return
    kind, system = store_kind(name, value)
    if kind:
        ref = f"store:{name}"
        if system:
            attr = "messaging.system.name" if kind == "broker" else "db.system.name"
            r.add(dep, ref, attr, system, source, "rule: derived: from the configuration key's name")
        address_rows(r, dep, ref, value, source, system, kind)
    elif CLIENT_KEY.search(name) or m:
        address_rows(r, dep, f"external:{name}", value, source)


def write(reg, ws=None):
    """identity/identifiers.csv and identity/unmatched.csv written afresh; identity/merges.csv created when missing."""
    reg = pathlib.Path(reg)
    rows, unmatched = read(reg, ws)
    out = reg / DIR
    out.mkdir(exist_ok=True)
    tables.write(out / "identifiers.csv", COLS, rows)
    tables.write(out / "unmatched.csv", UNMATCHED_COLS, unmatched)
    if not (out / "merges.csv").is_file():
        tables.write(out / "merges.csv", MERGE_COLS, [])
    return rows, unmatched


def load(reg):
    """{(deployable lower, ref): [identifier row]} from identity/identifiers.csv, or None when the register has none."""
    p = pathlib.Path(reg) / DIR / "identifiers.csv"
    if not p.is_file():
        return None
    out = {}  # the script's rows, then the model's judged ones (identity/judged-identifiers.csv), never rewritten here
    for r in tables.dicts(p) + tables.dicts(pathlib.Path(reg) / DIR / "judged-identifiers.csv"):
        out.setdefault(((r.get("deployable") or "").strip().lower(), (r.get("ref") or "").strip()), []).append(r)
    return out


def value(rows, attr):
    return next(((r.get("value") or "").strip() for r in rows or [] if (r.get("attribute") or "").strip() == attr
                 and not (r.get("basis") or "").startswith("not found")), "")


def resolved(rows):
    """A store's or outside system's resolved key, or None: every part a literal read from a cited file."""
    if not rows or any((r.get("basis") or "").startswith("not found") for r in rows
                       if r.get("attribute") == "server.address"):
        return None
    host = value(rows, "server.address")
    if not host:
        return None
    return tuple(value(rows, a) for a in ("db.system.name", "messaging.system.name", "server.address", "server.port",
                                         "db.namespace", "custom: schema", "url.path"))


def store_class(rows):
    """`db`, `cache` or `broker` for a store's identifier rows."""
    if value(rows, "messaging.system.name"):
        return "broker"
    return "cache" if value(rows, "db.system.name") in ("redis", "memcached") else "db"


def store_name(rows):
    """A store's, broker's or outside system's `name`: its host as its configuration states it (the resource's own
    name), with the database's namespace where one is read; "" when the address is a placeholder or missing."""
    if not resolved(rows):
        return ""
    host, ns, schema = value(rows, "server.address"), value(rows, "db.namespace"), value(rows, "custom: schema")
    return "/".join(x for x in (host, ns, schema) if x)


def part_name(rows, folder):
    """A deployable's `name` (register-template REGISTER.md): its deployment's name, else its image's, else its folder."""
    for attr in ("k8s.deployment.name", "custom: DeploymentConfig name", "custom: StatefulSet name",
                 "custom: CronJob name", "container.image.name"):
        v = value(rows, attr)
        if v:
            return v, attr
    return folder, "folder"


def main(argv):
    argv = list(argv)
    ws = None
    if "--workspace" in argv:
        i = argv.index("--workspace")
        ws = argv[i + 1]
        del argv[i:i + 2]
    if len(argv) != 1:
        print(__doc__)
        return 2
    import run_lock  # the register is written by one run at a time
    run_lock.refuse_unless_register(argv)
    run_lock.guard(argv[0])
    rows, unmatched = write(argv[0], ws)
    print(f"identity: {len(rows)} identifier row(s) for {len({r['deployable'] for r in rows})} deployable(s); "
          f"{len(unmatched)} workload(s) left for the model to join (identity/unmatched.csv)")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
