"""Tests for the per-project dev dashboard: resources schema/seed generator, status
collectors (mocked HTTP, no real network), secret-safety, and caching.

Run:  ./voice/.venv/bin/python -m dashboard.test_devdash
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from . import devstatus, resources, secrets_store


# ── resources: schema ────────────────────────────────────────────────────────
def test_validate_accepts_well_formed_doc():
    doc = {"resources": [{"name": "Vercel", "category": "hosting", "purpose": "hosting"}]}
    assert resources.validate(doc) == []


def test_validate_rejects_missing_fields_and_bad_category():
    doc = {"resources": [{"category": "nope"}]}
    problems = resources.validate(doc)
    assert any("missing required field 'name'" in p for p in problems)
    assert any("missing required field 'purpose'" in p for p in problems)
    assert any("unknown category" in p for p in problems)


def test_validate_rejects_non_list_resources():
    assert resources.validate({"resources": "nope"}) == ["'resources' must be a list"]


# ── resources: load (project file vs seed fallback) ─────────────────────────
def test_load_prefers_project_file_over_seed():
    root = Path(tempfile.mkdtemp())
    (root / ".brain").mkdir()
    doc = {"resources": [{"name": "Own", "category": "other", "purpose": "p"}]}
    (root / ".brain" / "resources.json").write_text(json.dumps(doc))
    out = resources.load(root, "whatever-seed-name")
    assert out["source"] == "project"
    assert out["resources"][0]["name"] == "Own"


def test_load_falls_back_to_seed_then_none():
    root = Path(tempfile.mkdtemp())
    out = resources.load(root, "trip-planner")  # real seed shipped in dashboard/seed/
    assert out["source"] == "seed"
    assert any(r["name"] == "Vercel" for r in out["resources"])
    out2 = resources.load(root, "no-such-project-xyz")
    assert out2["source"] == "none" and out2["resources"] == []


def test_load_reports_invalid_json_without_raising():
    root = Path(tempfile.mkdtemp())
    (root / ".brain").mkdir()
    (root / ".brain" / "resources.json").write_text("{not json")
    out = resources.load(root, "x")
    assert out["resources"] == [] and out["problems"]


# ── resources: seed generator ────────────────────────────────────────────────
def _fixture_project() -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "vercel.json").write_text("{}")
    (root / "package.json").write_text(json.dumps({
        "dependencies": {"@supabase/supabase-js": "^2.0.0"},
    }))
    (root / ".env.example").write_text(
        "VITE_SUPABASE_URL=\nVITE_SUPABASE_ANON_KEY=\nANTHROPIC_API_KEY=\nMY_RANDOM_THING=\n")
    src = root / "src"
    src.mkdir()
    (src / "geocode.js").write_text("const ENDPOINT = 'https://nominatim.openstreetmap.org/search'\n")
    return root


def test_generate_seed_finds_known_services_and_env_vars():
    root = _fixture_project()
    out = resources.generate_seed(root)
    names = {r["name"] for r in out["resources"]}
    assert "Vercel" in names  # from vercel.json
    assert "Supabase" in names  # from package.json dep + env var naming
    assert "Nominatim / OpenStreetMap" in names  # from hostname in source
    supabase = next(r for r in out["resources"] if r["name"] == "Supabase")
    assert "VITE_SUPABASE_URL" in supabase["env_vars"]
    assert "MY_RANDOM_THING" in out["unmatched_env_vars"]


def test_generate_seed_on_empty_dir_is_empty():
    root = Path(tempfile.mkdtemp())
    out = resources.generate_seed(root)
    assert out["resources"] == [] and out["unmatched_env_vars"] == []


# ── devstatus: git / tracker (no network) ────────────────────────────────────
def test_git_status_not_a_repo():
    root = Path(tempfile.mkdtemp())
    out = devstatus.git_status(root)
    assert out == {"configured": False, "reason": "not a git repository"}


def test_git_status_reports_branch_and_uncommitted():
    import subprocess
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=root)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root)
    (root / "f.txt").write_text("hi")
    subprocess.run(["git", "add", "."], cwd=root)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root)
    (root / "f.txt").write_text("changed")
    out = devstatus.git_status(root)
    assert out["configured"] is True
    assert out["uncommitted"] == 1
    assert len(out["commits"]) == 1


def test_tracker_status_groups_by_status():
    from . import tracker
    root = Path(tempfile.mkdtemp())
    t = tracker.create_task(root, "a task")
    tracker.set_status(root, t["id"], "doing", actor="user")
    out = devstatus.tracker_status(root)
    assert out["by_status"]["doing"] == 1
    assert out["total"] == 1
    assert out["in_review"] == []


# ── devstatus: secrets_store ──────────────────────────────────────────────────
def test_secrets_store_env_then_file_then_none(monkeypatch):
    monkeypatch.delenv("SOME_TOKEN_X", raising=False)
    monkeypatch.setattr(secrets_store, "SECRETS_PATH", Path("/no/such/file"))
    assert secrets_store.get("SOME_TOKEN_X") is None
    monkeypatch.setenv("SOME_TOKEN_X", "abc123")
    assert secrets_store.get("SOME_TOKEN_X") == "abc123"


# ── devstatus: vercel / supabase / uptime (mocked HTTP, no real network) ────
def _run(coro):
    return asyncio.run(coro)


def test_vercel_status_not_configured_without_token(monkeypatch):
    monkeypatch.setattr(secrets_store, "get", lambda name: None)
    devstatus.clear_cache()
    out = _run(devstatus.vercel_status("proj"))
    assert out == {"configured": False, "reason": "no VERCEL_TOKEN", "setup": devstatus.VERCEL_TOKEN_SETUP}


def test_vercel_status_ok_with_mocked_response(monkeypatch):
    monkeypatch.setattr(secrets_store, "get", lambda name: "fake-token" if name == "VERCEL_TOKEN" else None)
    devstatus.clear_cache()

    class FakeResp:
        status_code = 200
        def json(self):
            return {"deployments": [{"state": "READY", "createdAt": 1700000000000,
                                     "url": "x.vercel.app", "meta": {"githubCommitSha": "abcdef1234"}}]}

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=FakeResp())):
        out = _run(devstatus.vercel_status("proj"))
    assert out["configured"] is True and out["ok"] is True
    assert out["deployment"]["state"] == "READY"
    assert out["deployment"]["commit"] == "abcdef1"
    assert "fake-token" not in json.dumps(out)  # token never leaks into the response


def test_vercel_status_handles_api_error(monkeypatch):
    monkeypatch.setattr(secrets_store, "get", lambda name: "tok")
    devstatus.clear_cache()
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=RuntimeError("boom"))):
        out = _run(devstatus.vercel_status("proj"))
    assert out["configured"] is True and out["ok"] is False and "boom" in out["error"]


def test_vercel_status_is_cached(monkeypatch):
    monkeypatch.setattr(secrets_store, "get", lambda name: "tok")
    devstatus.clear_cache()
    calls = {"n": 0}

    class FakeResp:
        status_code = 200
        def json(self_inner):
            calls["n"] += 1
            return {"deployments": []}

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=FakeResp())):
        _run(devstatus.vercel_status("proj"))
        _run(devstatus.vercel_status("proj"))
    assert calls["n"] == 1  # second call served from cache, not a second fetch


def test_supabase_status_not_configured_without_token(monkeypatch):
    monkeypatch.setattr(secrets_store, "get", lambda name: None)
    devstatus.clear_cache()
    out = _run(devstatus.supabase_status("ref123"))
    assert out["configured"] is False and "SUPABASE_ACCESS_TOKEN" in out["reason"]


def test_supabase_status_ok_with_mocked_response(monkeypatch):
    monkeypatch.setattr(secrets_store, "get", lambda name: "tok")
    devstatus.clear_cache()

    class FakeResp:
        status_code = 200
        def json(self):
            return {"status": "ACTIVE_HEALTHY", "region": "us-east-1", "name": "trip-planner"}

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=FakeResp())):
        out = _run(devstatus.supabase_status("ref123"))
    assert out["ok"] is True and out["status"] == "ACTIVE_HEALTHY"


def test_uptime_check_ok_and_error():
    devstatus.clear_cache()

    class FakeResp:
        status_code = 200
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=FakeResp())):
        out = _run(devstatus.uptime_check("https://example.com"))
    assert out["ok"] is True and out["status_code"] == 200 and "elapsed_ms" in out

    devstatus.clear_cache()
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=RuntimeError("timeout"))):
        out = _run(devstatus.uptime_check("https://example.com"))
    assert out["ok"] is False and "timeout" in out["error"]


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]


class _FakeMonkeypatch:
    """Minimal pytest-monkeypatch-alike so these tests run under the repo's plain
    `python -m dashboard.test_X` convention (no pytest installed in voice/.venv)."""
    def __init__(self):
        self._undo = []

    def setattr(self, obj, name, value):
        self._undo.append((obj, name, getattr(obj, name, None), "set"))
        setattr(obj, name, value)

    def setenv(self, name, value):
        import os
        had = name in os.environ
        self._undo.append((os, name, os.environ.get(name) if had else None, "env" if had else "delenv"))
        os.environ[name] = value

    def delenv(self, name, raising=False):
        import os
        if name in os.environ:
            self._undo.append((os, name, os.environ[name], "env"))
            del os.environ[name]

    def undo(self):
        import os
        for obj, name, old, kind in reversed(self._undo):
            if kind == "set":
                setattr(obj, name, old)
            elif kind == "env":
                os.environ[name] = old
            elif kind == "delenv":
                os.environ.pop(name, None)


def main() -> int:
    import inspect
    passed = failed = 0
    for fn in TESTS:
        mp = _FakeMonkeypatch()
        try:
            if "monkeypatch" in inspect.signature(fn).parameters:
                fn(mp)
            else:
                fn()
            print(f"  PASS    {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL    {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR   {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
        finally:
            mp.undo()
    print(f"\n{passed} passed · {failed} failed  (of {len(TESTS)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
