"""Per-project dev servers and one-shot actions for the dev dashboard — start/stop/restart
declared services and run declared actions (tests, smoke, test-user seeding) from the Hub.

Declared by the project in `<project_root>/.brain/services.json`:

    {
      "services": [{"name": "web", "command": "npm run dev", "port": 5173}],
      "actions":  [{"name": "smoke", "group": "tests", "command": "npm run smoke", "needs": ["web"]},
                   {"name": "teardown test users", "group": "test-users",
                    "command": "npm run test-users -- --teardown",
                    "env": {"SUPABASE_URL": "https://…"}, "secrets": ["SUPABASE_SECRET_KEY"],
                    "confirm": "teardown"}]
    }

Trust boundary: the API names an entry and only commands declared in the project's own file
ever run — the browser never sends a command string. `secrets` are injected from
secrets_store by name and never returned. `confirm` is enforced here, not just in the UI.
Commands run in the user's interactive shell (`$SHELL -ilc`) so version managers like fnm
resolve the right Node — the dashboard's own PATH doesn't (and holds a stale node).

Each run is its own process group, so stop() takes down `npm` *and* the server it spawned.
Pids/exit codes persist in ~/.claude/brain-dashboard/runs/ so status survives a dashboard
restart (ceiling: liveness is a pgid signal check, so a recycled pid could read as alive —
fine for a single-user dev box; store process start time if that ever bites).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path

from . import secrets_store

DECL_SUBPATH = ".brain/services.json"
RUNS_DIR = Path.home() / ".claude" / "brain-dashboard" / "runs"
SHELL_ARGS = [os.environ.get("SHELL") or "/bin/zsh", "-ilc"]
STOP_GRACE_S = 5.0
BUILTIN_ACTIONS = [{"name": "git pull", "label": "Pull latest", "group": "Repo", "icon": "git",
                    "description": "Fast-forward this branch from its upstream. Refuses to merge.",
                    "command": "git pull --ff-only"}]
PARAM_TYPES = ("number", "text", "select")
_PARAM_NAME = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_FLAG = re.compile(r"^--?[a-z][a-z0-9-]*$")
_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_lock = threading.Lock()


class RunError(Exception):
    def __init__(self, msg: str, status: int = 400):
        super().__init__(msg)
        self.status = status


# ── declaration ──────────────────────────────────────────────────────────────
def _clean_param(p, owner: str, problems: list[str]) -> dict | None:
    """A form field an action takes. Values reach the command as separate argv entries
    (never spliced into the shell string), optionally after a `flag`."""
    if not isinstance(p, dict) or not isinstance(p.get("name"), str) or not _PARAM_NAME.match(p["name"]):
        problems.append(f"{owner}: each param needs a lowercase name")
        return None
    where = f"{owner}.{p['name']}"
    t = p.get("type", "text")
    if t not in PARAM_TYPES:
        problems.append(f"{where}: type must be one of {', '.join(PARAM_TYPES)}")
        return None
    flag = p.get("flag")
    if flag is not None and not (isinstance(flag, str) and _FLAG.match(flag)):
        problems.append(f"{where}: flag must look like --name")
        return None
    out = {"name": p["name"], "label": str(p.get("label") or p["name"]), "type": t, "flag": flag,
           "required": bool(p.get("required")), "default": p.get("default"), "help": str(p.get("help") or "")}
    if t == "number":
        out["min"] = p.get("min") if isinstance(p.get("min"), int) else None
        out["max"] = p.get("max") if isinstance(p.get("max"), int) else None
    elif t == "select":
        out["options"] = [str(o) for o in p.get("options") or []]
        if not out["options"]:
            problems.append(f"{where}: select needs options")
            return None
    else:
        out["maxlen"] = p.get("maxlen") if isinstance(p.get("maxlen"), int) else 120
        out["upper"] = bool(p.get("upper"))
        pat = p.get("pattern")
        try:
            out["pattern"] = re.compile(pat).pattern if isinstance(pat, str) and pat else None
        except re.error:
            problems.append(f"{where}: pattern is not a valid regex")
            return None
    return out


def _clean(e, kind: str, problems: list[str]) -> dict | None:
    if not isinstance(e, dict):
        problems.append(f"{kind} entry is not an object")
        return None
    name, cmd = e.get("name"), e.get("command")
    if not (isinstance(name, str) and name.strip() and isinstance(cmd, str) and cmd.strip()):
        problems.append(f"{kind} needs a non-empty name and command")
        return None
    out = {"name": name.strip(), "command": cmd.strip(), "group": str(e.get("group") or ""),
           "label": str(e.get("label") or name.strip()), "icon": str(e.get("icon") or ""),
           "description": str(e.get("description") or "")}
    params = [_clean_param(p, out["name"], problems) for p in e.get("params") or []] if kind == "action" else []
    out["params"] = [p for p in params if p]
    if kind == "service":
        port = e.get("port")
        if port is not None and not (isinstance(port, int) and 0 < port < 65536):
            problems.append(f"{name}: port must be an integer 1–65535")
            port = None
        out["port"] = port
        url = e.get("url")
        out["url"] = url if isinstance(url, str) else (f"http://localhost:{port}" if port else None)
    env = e.get("env")
    out["env"] = {str(k): str(v) for k, v in env.items()} if isinstance(env, dict) else {}
    out["secrets"] = [s for s in e.get("secrets") or [] if isinstance(s, str)]
    out["needs"] = [s for s in e.get("needs") or [] if isinstance(s, str)]
    c = e.get("confirm")
    out["confirm"] = c if isinstance(c, str) and c else None
    return out


def load(root: Path) -> dict:
    p = Path(root) / DECL_SUBPATH
    problems: list[str] = []
    try:
        doc = json.loads(p.read_text())
    except FileNotFoundError:
        doc = None
    except (OSError, ValueError) as e:
        doc, problems = {}, [f"unreadable {DECL_SUBPATH}: {e}"]
    doc = doc if isinstance(doc, dict) else {}
    services = [s for s in (_clean(e, "service", problems) for e in doc.get("services") or []) if s]
    actions = [a for a in (_clean(e, "action", problems) for e in doc.get("actions") or []) if a]
    names = [x["name"] for x in services + actions]
    dups = sorted({n for n in names if names.count(n) > 1})
    if dups:
        problems.append(f"duplicate names: {', '.join(dups)}")
    svc_names = {s["name"] for s in services}
    for a in actions:
        for n in a["needs"]:
            if n not in svc_names:
                problems.append(f"{a['name']}: needs unknown service {n!r}")
    for b in BUILTIN_ACTIONS:
        if b["name"] not in names:
            actions.append(_clean(b, "action", problems))
    return {"declared": p.exists(), "problems": problems, "services": services, "actions": actions}


def build_argv(entry: dict, args: dict | None) -> list[str]:
    """Validate submitted form values against the declared params → argv list. Every value is
    one argv element passed through "$@", so shell metacharacters stay literal; text values may
    not start with "-" so a value can't smuggle in an extra flag."""
    args = args or {}
    known = {p["name"] for p in entry["params"]}
    extra = sorted(set(args) - known)
    if extra:
        raise RunError(f"unknown field {', '.join(extra)}", 422)
    argv: list[str] = []
    for p in entry["params"]:
        raw = args.get(p["name"])
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            raw = p["default"]
        if raw is None or raw == "":
            if p["required"]:
                raise RunError(f"{p['label']} is required", 422)
            continue
        label = p["label"]
        if p["type"] == "number":
            s = str(raw).strip()
            if isinstance(raw, bool) or not re.fullmatch(r"-?\d+", s):
                raise RunError(f"{label} must be a whole number", 422)
            v = int(s)
            lo, hi = p["min"], p["max"]
            if (lo is not None and v < lo) or (hi is not None and v > hi):
                raise RunError(f"{label} must be between {lo if lo is not None else '…'} and {hi if hi is not None else '…'}", 422)
            val = str(v)
        else:
            val = str(raw).strip()
            if p["type"] == "text":
                if p["upper"]:
                    val = val.upper()
                if len(val) > p["maxlen"]:
                    raise RunError(f"{label} is longer than {p['maxlen']} characters", 422)
                if p["pattern"] and not re.fullmatch(p["pattern"], val):
                    raise RunError(f"{label} doesn't match the expected format", 422)
            elif val not in p["options"]:
                raise RunError(f"{label} must be one of {', '.join(p['options'])}", 422)
            if val.startswith("-") or any(ord(c) < 32 for c in val):
                raise RunError(f"{label} can't start with '-' or contain control characters", 422)
        argv += [p["flag"], val] if p["flag"] else [val]
    return argv


def find(decl: dict, kind: str, name: str) -> dict:
    pool = decl["services"] if kind == "service" else decl["actions"]
    e = next((x for x in pool if x["name"] == name), None)
    if e is None:
        raise RunError(f"no {kind} named {name!r} is declared", 404)
    return e


# ── state + processes ────────────────────────────────────────────────────────
def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-") or "x"


def _key(project: str, kind: str, name: str) -> str:
    return f"{project}/{kind}/{name}"


def _log_path(project: str, kind: str, name: str) -> Path:
    return RUNS_DIR / _slug(project) / f"{kind}-{_slug(name)}.log"


def _read_state() -> dict:
    try:
        return json.loads((RUNS_DIR / "state.json").read_text())
    except (OSError, ValueError):
        return {}


def _write_state(st: dict) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = RUNS_DIR / "state.json.tmp"
    tmp.write_text(json.dumps(st, indent=1))
    tmp.replace(RUNS_DIR / "state.json")


def _update(key: str, **fields) -> None:
    with _lock:
        st = _read_state()
        st[key] = {**st.get(key, {}), **fields}
        _write_state(st)


def _alive(pgid) -> bool:
    if not pgid:
        return False
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _running(cur: dict) -> bool:
    return bool(cur) and cur.get("finished") is None and _alive(cur.get("pgid"))


def port_open(port) -> bool:
    if not port:
        return False
    try:  # "localhost" so both 127.0.0.1 and ::1 listeners count (Vite binds ::1 on new Node)
        with socket.create_connection(("localhost", port), timeout=0.25):
            return True
    except OSError:
        return False


def _listen_pids(port: int) -> list[int]:
    out = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                         capture_output=True, text=True).stdout
    return sorted({int(x) for x in out.split() if x.isdigit()})


def _reap(proc: subprocess.Popen, key: str) -> None:
    code = proc.wait()
    _update(key, exit_code=code, finished=time.time())


def _killpg(pgid: int) -> None:
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + STOP_GRACE_S
    while time.time() < deadline:
        if not _alive(pgid):
            return
        time.sleep(0.1)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _spawn(project: str, root: Path, entry: dict, kind: str, argv: list[str] | None = None) -> dict:
    key = _key(project, kind, entry["name"])
    env = {**os.environ, **entry["env"]}
    missing = []
    for s in entry["secrets"]:
        v = secrets_store.get(s)
        if v is None:
            missing.append(s)
        else:
            env[s] = v
    if missing:
        raise RunError(f"missing secret {', '.join(missing)} — set it as an env var or add it "
                       f"to {secrets_store.SECRETS_PATH}", 412)
    with _lock:
        if _running(_read_state().get(key, {})):
            raise RunError(f"{entry['name']} is already running", 409)
        log = _log_path(project, kind, entry["name"])
        log.parent.mkdir(parents=True, exist_ok=True)
        argv = argv or []
        # Params ride in as positional args ("$@" → $1…), never interpolated into the string.
        script = entry["command"] + (' "$@"' if entry["params"] else "")
        with open(log, "w") as f:
            f.write(f"$ {entry['command']}{' ' + shlex.join(argv) if argv else ''}\n")
            f.flush()
            proc = subprocess.Popen([*SHELL_ARGS, script, "hub", *argv], cwd=str(root),
                                    stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT,
                                    env=env, start_new_session=True)
        st = _read_state()
        st[key] = {"pid": proc.pid, "pgid": proc.pid, "started": time.time(),
                   "finished": None, "exit_code": None, "stopped": False}
        _write_state(st)
    threading.Thread(target=_reap, args=(proc, key), daemon=True).start()
    return st[key]


# ── public operations ────────────────────────────────────────────────────────
def start_service(project: str, root: Path, decl: dict, name: str) -> dict:
    e = find(decl, "service", name)
    if e["port"] and port_open(e["port"]):
        raise RunError(f"port {e['port']} is already in use — {name} may be running outside the "
                       "dashboard; stop it first", 409)
    return _spawn(project, root, e, "service")


def stop_service(project: str, decl: dict, name: str, external: bool = False) -> dict:
    e = find(decl, "service", name)
    key = _key(project, "service", name)
    cur = _read_state().get(key, {})
    if _running(cur):
        _update(key, stopped=True)
        _killpg(cur["pgid"])
        return {"stopped": "dashboard"}
    if e["port"] and port_open(e["port"]):
        if not external:
            raise RunError(f"{name} is running outside the dashboard (port {e['port']}); "
                           "confirm to stop it anyway", 409)
        pids = _listen_pids(e["port"])
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        return {"stopped": "external", "pids": pids}
    raise RunError(f"{name} isn't running", 409)


def restart_service(project: str, root: Path, decl: dict, name: str, external: bool = False) -> dict:
    try:
        stop_service(project, decl, name, external)
    except RunError as e:
        if e.status != 409 or "isn't running" not in str(e):
            raise
    e = find(decl, "service", name)
    deadline = time.time() + STOP_GRACE_S
    while e["port"] and port_open(e["port"]) and time.time() < deadline:
        time.sleep(0.1)  # let the old listener release the port
    return start_service(project, root, decl, name)


def run_action(project: str, root: Path, decl: dict, name: str, confirm: str | None = None,
               args: dict | None = None) -> dict:
    e = find(decl, "action", name)
    argv = build_argv(e, args)
    if e["confirm"] and confirm != e["confirm"]:
        raise RunError(f'type "{e["confirm"]}" to confirm', 428)
    for need in e["needs"]:
        svc = find(decl, "service", need)
        if not port_open(svc["port"]):
            raise RunError(f"start {need} first", 409)
    return _spawn(project, root, e, "action", argv)


def stop_action(project: str, decl: dict, name: str) -> dict:
    find(decl, "action", name)
    key = _key(project, "action", name)
    cur = _read_state().get(key, {})
    if not _running(cur):
        raise RunError(f"{name} isn't running", 409)
    _update(key, stopped=True)
    _killpg(cur["pgid"])
    return {"stopped": "dashboard"}


def status(project: str, decl: dict) -> dict:
    st = _read_state()

    def item(e: dict, kind: str) -> dict:
        cur = st.get(_key(project, kind, e["name"]), {})
        ours = _running(cur)
        if kind == "service":
            up = port_open(e["port"])
            if ours:
                state = "running" if (up or not e["port"]) else "starting"
            elif up:
                state = "external"
            elif cur.get("finished") and not cur.get("stopped") and cur.get("exit_code") not in (0, None):
                state = "crashed"
            else:
                state = "stopped"
        else:
            if ours:
                state = "running"
            elif cur.get("finished"):
                state = "stopped" if cur.get("stopped") else ("passed" if cur.get("exit_code") == 0 else "failed")
            else:
                state = "idle"
        out = {k: e[k] for k in ("name", "label", "icon", "description", "group", "needs", "confirm",
                                 "params", "command")}
        out.update(state=state, secrets=e["secrets"],
                   missing_secrets=[s for s in e["secrets"] if secrets_store.get(s) is None],
                   started=cur.get("started"), finished=cur.get("finished"),
                   exit_code=cur.get("exit_code"), pid=cur.get("pid") if ours else None)
        if kind == "service":
            out.update(port=e["port"], url=e["url"])
        return out

    return {"services": [item(s, "service") for s in decl["services"]],
            "actions": [item(a, "action") for a in decl["actions"]]}


def log_tail(project: str, kind: str, name: str, lines: int = 80) -> str:
    p = _log_path(project, kind, name)
    try:
        with open(p, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 65536))
            text = f.read().decode(errors="replace")
    except OSError:
        return ""
    text = _ANSI.sub("", text).replace("\r\n", "\n")
    return "\n".join(text.split("\n")[-lines:])
