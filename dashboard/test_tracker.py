"""T1 acceptance tests for the file-based task tracker.

These encode the T1 acceptance criteria (docs/plan.md → "T1 Deep Dive"). They run over a temp
repo dir — no server, no git, no network. Currently RED (tracker.py is stubbed); /build makes
them green.

Run:  ./voice/.venv/bin/python -m dashboard.test_tracker
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from . import tracker


def _repo() -> Path:
    return Path(tempfile.mkdtemp())


def test_create_read_roundtrip():
    root = _repo()
    t = tracker.create_task(root, "Fix login redirect loop", brief="stop the loop",
                            acceptance=["no loop", "session persists"])
    assert t["id"] and t["status"] == "backlog" and t["type"] == "task"
    back = tracker.read_task(root, t["id"])
    assert back["title"] == "Fix login redirect loop"
    assert back["acceptance"] == ["no loop", "session persists"]


def test_serialize_idempotent():
    root = _repo()
    t = tracker.create_task(root, "Idempotent write")
    f = next(tracker._tasks_dir(root).glob(f"{t['id']}-*.md"))
    before = f.read_bytes()
    tracker.update_task(root, t["id"])          # no-op update
    assert f.read_bytes() == before, "no-op re-serialize must be byte-identical"


def test_status_transitions():
    root = _repo()
    t = tracker.create_task(root, "Move me")
    tracker.set_status(root, t["id"], "doing", actor="user")
    assert tracker.read_task(root, t["id"])["status"] == "doing"
    try:
        tracker.set_status(root, t["id"], "done", actor="user")  # doing→done not allowed
        assert False, "invalid transition should raise"
    except tracker.TrackerError:
        pass


def test_agent_cannot_close():
    root = _repo()
    t = tracker.create_task(root, "Agent work")
    tracker.set_status(root, t["id"], "doing", actor="agent")
    tracker.set_status(root, t["id"], "review", actor="agent")
    try:
        tracker.set_status(root, t["id"], "done", actor="agent")
        assert False, "agents must not close tasks"
    except tracker.TrackerError:
        pass


def test_add_update_bumps():
    root = _repo()
    t = tracker.create_task(root, "Log me")
    before = tracker.read_task(root, t["id"])["updated"]
    tracker.add_update(root, t["id"], "comment", "looked into it")
    after = tracker.read_task(root, t["id"])
    assert any("looked into it" in u for u in after["updates"])
    assert after["updated"] >= before


def test_link_run():
    root = _repo()
    t = tracker.create_task(root, "Run linked")
    tracker.link_run(root, t["id"], "r_abc123", result="patched it")
    back = tracker.read_task(root, t["id"])
    assert "r_abc123" in back["runs"]
    assert any("r_abc123" in u for u in back["updates"])


def test_all_tasks_cross_project():
    a, b = _repo(), _repo()
    tracker.create_task(a, "task in A")
    tracker.create_task(b, "task in B")
    tracker.create_task(b, "second in B")
    tasks = tracker.all_tasks(roots=[a, b])
    assert len(tasks) == 3
    assert {t["project"] for t in tasks} == {a.name, b.name}


def test_missing_tracker_dir_is_empty():
    assert tracker.list_tasks(_repo()) == []   # repo with no .brain/tasks/ → [], no error


def test_source_roundtrip_and_find():
    root = _repo()
    t = tracker.create_task(root, "Sourced", source="plan:x:M1")
    assert tracker.read_task(root, t["id"])["source"] == "plan:x:M1"
    assert tracker.find_by_source(root, "plan:x:M1")["id"] == t["id"]
    assert tracker.find_by_source(root, "nope") is None


def test_upsert_idempotent():
    root = _repo()
    a = tracker.upsert_task(root, "plan:x:M2", "First title", brief="b1")
    b = tracker.upsert_task(root, "plan:x:M2", "Updated title", brief="b2")
    assert a["_created"] is True and b["_created"] is False and b["id"] == a["id"]
    assert len(tracker.list_tasks(root)) == 1        # no duplicate
    assert tracker.read_task(root, a["id"])["title"] == "Updated title"


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]


def main() -> int:
    passed = pending = failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"  PASS    {fn.__name__}")
            passed += 1
        except NotImplementedError as e:
            print(f"  pending {fn.__name__}  ({e})")
            pending += 1
        except AssertionError as e:
            print(f"  FAIL    {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR   {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed · {pending} pending · {failed} failed  (of {len(TESTS)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
