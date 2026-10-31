"""Tests for team templates (H7), using the real templates in agents/teams/ and the real workflow
definitions, with a fake SDK client (no usage spent).

Run:  ./voice/.venv/bin/python -m dashboard.harness.test_teams
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from . import library, store, teams
from .runtime import HarnessError
from .test_runtime import FakeClient, drain, make

P = {"scout", "builder", "reviewer", "operator"}


def run(fn):
    def t():
        with tempfile.TemporaryDirectory() as d:
            asyncio.run(fn(Path(d)))
    t.__name__ = fn.__name__
    return t


def test_every_template_resolves():
    names = {t["name"] for t in teams.list_templates()}
    assert names == {"pipeline", "debate", "project-team", "research"}, names
    for t in teams.list_templates():
        assert sum(m["lead"] for m in t["members"]) == 1, t["name"]
        for m in t["members"]:
            if m["from"] and m["from"].startswith("workflow/"):
                library.get("workflow", None, None, m["from"].split("/")[1])  # raises if missing


@run
async def test_pipeline_start(tmp):
    h, _, proj = make(tmp)
    out = await teams.start(h, "pipeline", "app", proj, P, inputs={"scope": "src", "test_command": "python -m pytest", "task": "ab12cd"})
    assert out["agents"] == ["app-planner", "app-builder", "app-reviewer"] and out["lead"] == "app-planner"
    v = {a["name"]: a for a in h.list()}
    assert v["app-builder"]["scope"] == [str((proj / "src").resolve())]
    assert v["app-builder"]["always"] == ["python -m pytest"] == v["app-reviewer"]["always"] and v["app-planner"]["always"] == []
    assert all(a["team"] == "app:pipeline" for a in v.values())
    assert "'builder' is app-builder" in v["app-planner"]["brief"] and "`python -m pytest`" in v["app-reviewer"]["brief"]
    assert v["app-planner"]["model"]["model"] == "claude-opus-5-5"
    assert out["kickoff"] == "Take task #ab12cd to review."
    await drain(h, "app-planner")
    assert FakeClient.instances[0].prompts == ["Take task #ab12cd to review."]


@run
async def test_kickoff_waits_for_its_input(tmp):
    h, _, proj = make(tmp)
    out = await teams.start(h, "debate", "app", proj, P, prefix="d1")
    assert out["kickoff"] is None and not FakeClient.instances
    out = await teams.start(h, "research", "app", proj, P, prefix="r1", inputs={"question": "Which queue?"})
    assert out["kickoff"].endswith("Which queue?") and len(out["agents"]) == 4


@run
async def test_project_team_generates_expert(tmp):
    h, _, proj = make(tmp)
    (proj / "CLAUDE.md").write_text("# app")
    out = await teams.start(h, "project-team", "app", proj, P, inputs={"scope": "src"})
    assert "app-expert" in out["agents"] and (proj / ".brain" / "agents" / "app-expert.md").exists()
    planner = next(a for a in h.list() if a["name"] == "app-planner")
    assert "list_tasks" in planner["brief"]


@run
async def test_all_or_nothing(tmp):
    h, _, proj = make(tmp)
    await h.create("other-builder", "builder", "app", scope=["src"])
    try:  # the team's builder would share src with an existing writer: lock refuses, whole team rolls back
        await teams.start(h, "pipeline", "app", proj, P, inputs={"scope": "src"})
        raise AssertionError("overlapping scope accepted")
    except HarnessError as e:
        assert e.status == 409
    assert [a["name"] for a in h.list()] == ["other-builder"]
    for bad in ({"test_command": "rm -rf build && pytest"}, {"test_command": "pytest && git push"}):
        try:
            await teams.start(h, "pipeline", "app", proj, P, prefix="x", inputs={"scope": "docs", **bad})
            raise AssertionError(f"accepted {bad}")
        except HarnessError:
            pass
    assert [a["name"] for a in h.list()] == ["other-builder"]


@run
async def test_name_clash_and_remove(tmp):
    h, _, proj = make(tmp)
    out = await teams.start(h, "debate", "app", proj, P)
    try:
        await teams.start(h, "debate", "app", proj, P)
        raise AssertionError("duplicate team accepted")
    except HarnessError as e:
        assert e.status == 409
    assert await teams.remove(h, out["team"]) == 3 and h.list() == []
    assert store.list_agents(h.conn) == []


TESTS = [test_every_template_resolves, test_pipeline_start, test_kickoff_waits_for_its_input,
         test_project_team_generates_expert, test_all_or_nothing, test_name_clash_and_remove]


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
