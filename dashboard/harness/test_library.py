"""Tests for the agent library (H6): definition files, validation, expert seeding, adding to a team.

Run:  ./voice/.venv/bin/python -m dashboard.harness.test_library
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from . import library
from .runtime import HarnessError
from .test_runtime import make

P = {"scout", "builder", "reviewer"}
GOOD = {"name": "planner", "description": "Team lead: plans # and delegates", "persona": "scout",
        "model": "claude-opus-5-5", "scope": "src, docs", "daily_usd": 1.5, "role": "Lead the team.\n\nBe brief."}


def with_tmp(fn):
    def t():
        with tempfile.TemporaryDirectory() as d:
            old = library.WORKFLOW_DIR
            library.WORKFLOW_DIR = Path(d) / "workflow"
            try:
                fn(Path(d))
            finally:
                library.WORKFLOW_DIR = old
    t.__name__ = fn.__name__
    return t


@with_tmp
def test_round_trip_quotes_yaml_specials(tmp):
    library.save("workflow", None, GOOD, P)
    text = (tmp / "workflow" / "planner.md").read_text()
    assert 'description: "Team lead: plans # and delegates"' in text  # a bare colon breaks YAML (Obsidian)
    got = library.list_library([])[0]
    assert {k: got[k] for k in GOOD} == {**GOOD}, got
    assert got["kind"] == "workflow" and got["project"] is None


@with_tmp
def test_validation(tmp):
    bad = [{"name": "Bad"}, {"persona": "root"}, {"model": "gpt-4"}, {"scope": "../x"}, {"scope": "/etc"},
           {"daily_usd": 0}, {"daily_usd": 500}, {"description": "two\nlines"}, {"role": "x" * 2001}]
    for b in bad:
        try:
            library.save("workflow", None, {**GOOD, **b}, P)
            raise AssertionError(f"accepted {b}")
        except HarnessError:
            pass
    library.save("workflow", None, {**GOOD, "model": "auto"}, P)  # auto is allowed
    try:
        library.delete("workflow", None, "../planner")
        raise AssertionError("traversal accepted")
    except HarnessError:
        pass


@with_tmp
def test_experts_live_in_their_project(tmp):
    proj = tmp / "app"
    (proj / "docs").mkdir(parents=True)
    (proj / "CLAUDE.md").write_text("# app")
    (proj / "docs" / "plan.md").write_text("plan")
    (proj / ".brain" / "tasks").mkdir(parents=True)
    d = library.seed_expert("My App", proj, P)
    assert d["name"] == "my-app-expert" and (proj / ".brain" / "agents" / "my-app-expert.md").exists()
    assert "- CLAUDE.md" in d["role"] and "- docs/plan.md" in d["role"] and "README.md" not in d["role"]
    assert ".brain/tasks" in d["role"]
    lib = library.list_library([("My App", proj)])
    assert [(x["kind"], x["project"], x["name"]) for x in lib] == [("expert", "My App", "my-app-expert")]
    library.delete("expert", proj, "my-app-expert")
    assert library.list_library([("My App", proj)]) == []


def test_memory_index_path():
    p = library.memory_index(Path("/Users/me/Desktop/Code/trip-planner"))
    assert p == Path.home() / ".claude/projects/-Users-me-Desktop-Code-trip-planner/memory/MEMORY.md"


@with_tmp
def test_add_definition_to_team(tmp):
    async def go():
        h, _, proj = make(tmp)
        library.save("workflow", None, {**GOOD, "persona": "builder", "scope": "src", "model": "auto"}, P)
        defn = library.get("workflow", None, None, "planner")
        a = await h.create("planner-app", project="app", **library.to_agent(defn))
        assert a["scope"] == [str((proj / "src").resolve())] and a["model"]["mode"] == "auto"
        assert a["limits"]["daily_usd"] == 1.5 and a["brief"].startswith("Lead the team.")
    asyncio.run(go())


TESTS = [test_round_trip_quotes_yaml_specials, test_validation, test_experts_live_in_their_project,
         test_memory_index_path, test_add_definition_to_team]


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
