"""Tests for the per-project server/action runner (dashboard/services.py).

Run:  ./voice/.venv/bin/python -m dashboard.test_services

Each test points RUNS_DIR at a temp dir and swaps the interactive login shell for /bin/sh,
so nothing touches ~/.claude or depends on the user's shell rc. Real processes are spawned.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import services

PY = sys.executable


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait(pred, timeout=8.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.1)
    return False


def _project(decl: dict) -> Path:
    services.RUNS_DIR = Path(tempfile.mkdtemp()) / "runs"
    services.SHELL_ARGS = ["/bin/sh", "-c"]
    global _ROOT
    root = _ROOT = Path(tempfile.mkdtemp())
    (root / ".brain").mkdir()
    (root / ".brain" / "services.json").write_text(json.dumps(decl))
    return root


_ROOT = None


def _state(decl, name, kind="action"):
    st = services.status("p", _ROOT, decl)
    return next(x for x in st["services" if kind == "service" else "actions"] if x["name"] == name)


def test_load_declared_adds_builtin_git_pull():
    root = _project({"services": [{"name": "web", "command": "x", "port": 5173}],
                     "actions": [{"name": "test", "command": "npm test"}]})
    d = services.load(root)
    assert d["declared"] and not d["problems"]
    assert [s["name"] for s in d["services"]] == ["web"]
    assert {a["name"] for a in d["actions"]} == {"test", "git pull"}
    assert d["services"][0]["url"] == "http://localhost:5173"


def test_load_reports_problems_and_drops_bad_entries():
    root = _project({"services": [{"name": "web", "command": "x", "port": 99999},
                                  {"name": "", "command": "y"}],
                     "actions": [{"name": "web", "command": "z"},
                                 {"name": "smoke", "command": "s", "needs": ["nope"]}]})
    d = services.load(root)
    joined = " | ".join(d["problems"])
    assert "port must be" in joined and "non-empty name" in joined
    assert "duplicate names: web" in joined and "unknown service 'nope'" in joined
    assert d["services"][0]["port"] is None


def test_missing_file_is_undeclared_with_only_builtins():
    services.RUNS_DIR = Path(tempfile.mkdtemp())
    d = services.load(Path(tempfile.mkdtemp()))
    assert not d["declared"] and d["services"] == [] and [a["name"] for a in d["actions"]] == ["git pull"]


def test_only_declared_names_can_run():
    root = _project({"actions": [{"name": "test", "command": "true"}]})
    d = services.load(root)
    try:
        services.run_action("p", root, d, "rm -rf ~")
        assert False, "an undeclared name must never run"
    except services.RunError as e:
        assert e.status == 404


def test_confirm_is_enforced_server_side():
    root = _project({"actions": [{"name": "teardown", "command": "true", "confirm": "teardown"}]})
    d = services.load(root)
    for bad in (None, "yes", "TEARDOWN"):
        try:
            services.run_action("p", root, d, "teardown", confirm=bad)
            assert False, f"confirm={bad!r} must be rejected"
        except services.RunError as e:
            assert e.status == 428
    services.run_action("p", root, d, "teardown", confirm="teardown")
    assert _wait(lambda: _state(d, "teardown")["state"] == "passed")


def test_missing_secret_blocks_and_spawns_nothing():
    os.environ.pop("BRAIN_TEST_ABSENT", None)
    root = _project({"actions": [{"name": "seed", "command": "true", "secrets": ["BRAIN_TEST_ABSENT"]}]})
    d = services.load(root)
    assert _state(d, "seed")["missing_secrets"] == ["BRAIN_TEST_ABSENT"]
    try:
        services.run_action("p", root, d, "seed")
        assert False, "must refuse without the secret"
    except services.RunError as e:
        assert e.status == 412 and "BRAIN_TEST_ABSENT" in str(e)
    assert _state(d, "seed")["state"] == "idle"


def test_secret_and_env_are_injected():
    os.environ["BRAIN_TEST_SECRET"] = "s3cret-value"
    root = _project({"actions": [{"name": "seed", "command": 'echo "$URL $BRAIN_TEST_SECRET"',
                                  "env": {"URL": "https://x.test"}, "secrets": ["BRAIN_TEST_SECRET"]}]})
    d = services.load(root)
    services.run_action("p", root, d, "seed")
    assert _wait(lambda: _state(d, "seed")["state"] == "passed")
    assert "https://x.test s3cret-value" in services.log_tail("p", "action", "seed")


def test_action_exit_codes_map_to_passed_failed():
    root = _project({"actions": [{"name": "bad", "command": "echo hi; exit 3"},
                                 {"name": "good", "command": "true"}]})
    d = services.load(root)
    services.run_action("p", root, d, "bad")
    services.run_action("p", root, d, "good")
    assert _wait(lambda: _state(d, "bad")["state"] == "failed")
    assert _state(d, "bad")["exit_code"] == 3 and "hi" in services.log_tail("p", "action", "bad")
    assert _wait(lambda: _state(d, "good")["state"] == "passed")


def test_service_start_stop_kills_whole_process_group():
    port = _free_port()
    # a background child + the server: stop must take down both (process-group kill)
    cmd = f"sleep 300 & {PY} -m http.server {port} --bind 127.0.0.1"
    root = _project({"services": [{"name": "web", "command": cmd, "port": port}]})
    d = services.load(root)
    run = services.start_service("p", root, d, "web")
    assert _wait(lambda: _state(d, "web", "service")["state"] == "running")
    services.stop_service("p", root, d, "web")
    assert not services.port_open(port)
    try:
        os.killpg(run["pgid"], 0)
        assert False, "process group should be gone"
    except ProcessLookupError:
        pass
    assert _state(d, "web", "service")["state"] == "stopped"   # user stop ≠ crash


def test_external_server_detected_and_needs_explicit_stop():
    port = _free_port()
    root = _project({"services": [{"name": "web", "command": "true", "port": port}]})
    ext = subprocess.Popen([PY, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=root,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        d = services.load(root)
        assert _wait(lambda: services.port_open(port))
        assert _state(d, "web", "service")["state"] == "external"
        for op in (lambda: services.start_service("p", root, d, "web"),
                   lambda: services.stop_service("p", root, d, "web")):
            try:
                op()
                assert False, "start/stop on an external server must not silently proceed"
            except services.RunError as e:
                assert e.status == 409
        services.stop_service("p", root, d, "web", external=True)
        assert _wait(lambda: not services.port_open(port))
    finally:
        ext.kill()


def test_needs_blocks_until_service_is_up():
    port = _free_port()
    root = _project({"services": [{"name": "web", "command": "true", "port": port}],
                     "actions": [{"name": "smoke", "command": "true", "needs": ["web"]}]})
    d = services.load(root)
    try:
        services.run_action("p", root, d, "smoke")
        assert False, "smoke must wait for web"
    except services.RunError as e:
        assert e.status == 409 and "web" in str(e)


def test_log_tail_strips_ansi():
    root = _project({"actions": [{"name": "color", "command": r"printf '\033[32mgreen\033[0m\n'"}]})
    d = services.load(root)
    services.run_action("p", root, d, "color")
    assert _wait(lambda: _state(d, "color")["state"] == "passed")
    tail = services.log_tail("p", "action", "color")
    assert "green" in tail and "\x1b" not in tail


PROMO = {"name": "promo", "command": "printf '[%s]\\n'", "params": [
    {"name": "credits", "label": "AI credits", "flag": "--credits", "type": "number", "min": 1, "max": 2000, "required": True},
    {"name": "uses", "label": "Max uses", "flag": "--uses", "type": "number", "default": 20},
    {"name": "note", "label": "Note", "flag": "--note", "type": "text", "maxlen": 20},
    {"name": "code", "label": "Code", "type": "text", "upper": True, "pattern": "TF-[A-Z0-9-]{4,20}"},
    {"name": "tier", "label": "Tier", "type": "select", "options": ["plus", "pro"]}]}


def test_params_build_argv_with_flags_defaults_and_positionals():
    root = _project({"actions": [PROMO]})
    d = services.load(root)
    e = services.find(d, "action", "promo")
    assert not d["problems"]
    argv = services.build_argv(e, {"credits": "200", "code": "tf-abcd-efgh", "tier": "pro"})
    assert argv == ["--credits", "200", "--uses", "20", "TF-ABCD-EFGH", "pro"]  # default + upper


def test_params_reject_bad_values():
    root = _project({"actions": [PROMO]})
    e = services.find(services.load(root), "action", "promo")
    cases = [({}, "required"), ({"credits": "abc"}, "whole number"), ({"credits": "5000"}, "between"),
             ({"credits": "1", "note": "x" * 21}, "longer"), ({"credits": "1", "code": "nope"}, "format"),
             ({"credits": "1", "tier": "free"}, "one of"), ({"credits": "1", "note": "--days 999"}, "start with"),
             ({"credits": "1", "bogus": "1"}, "unknown field")]
    for args, why in cases:
        try:
            services.build_argv(e, args)
            assert False, f"{args} should be rejected ({why})"
        except services.RunError as err:
            assert err.status == 422 and why in str(err), f"{args}: {err}"


def test_param_values_are_never_shell_interpreted():
    root = _project({"actions": [PROMO]})
    d = services.load(root)
    evil = "x; touch pwned $(id) `id`"
    services.run_action("p", root, d, "promo", args={"credits": "7", "note": evil[:20]})
    assert _wait(lambda: _state(d, "promo")["state"] == "passed")
    log = services.log_tail("p", "action", "promo")
    assert f"[{evil[:20]}]" in log, log      # arrived as one literal argv element
    assert not (root / "pwned").exists()


def test_bad_param_declarations_are_reported():
    root = _project({"actions": [{"name": "a", "command": "true", "params": [
        {"name": "Bad Name"}, {"name": "x", "type": "date"}, {"name": "y", "flag": "rm -rf"},
        {"name": "z", "type": "select"}, {"name": "w", "pattern": "("}]}]})
    probs = " | ".join(services.load(root)["problems"])
    for frag in ("lowercase name", "type must be", "flag must", "select needs options", "valid regex"):
        assert frag in probs, probs


def test_other_apps_server_on_our_port_is_a_conflict_and_never_stopped():
    port = _free_port()
    elsewhere = tempfile.mkdtemp()  # another app's folder
    other = subprocess.Popen([PY, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=elsewhere,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        root = _project({"services": [{"name": "web", "command": "true", "port": port}],
                         "actions": [{"name": "smoke", "command": "true", "needs": ["web"]}]})
        d = services.load(root)
        assert _wait(lambda: services.port_open(port))
        assert _state(d, "web", "service")["state"] == "conflict"
        for op in (lambda: services.start_service("p", root, d, "web"),
                   lambda: services.stop_service("p", root, d, "web", external=True),
                   lambda: services.run_action("p", root, d, "smoke")):
            try:
                op()
                assert False, "must refuse while another app holds the port"
            except services.RunError as e:
                assert e.status == 409
        assert other.poll() is None, "the other app's server must still be running"
    finally:
        other.kill()


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]


def main() -> int:
    passed = failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"  PASS    {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL    {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR   {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed · {failed} failed  (of {len(TESTS)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
