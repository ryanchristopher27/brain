"""Tests for the artifact archive (copy each project's markdown artifacts into brain).

Run:  ./voice/.venv/bin/python -m dashboard.test_artifacts

Redirects artifacts.ARTIFACTS_DIR and artifacts.QUEUE at temp paths so the real
brain/artifacts and updates/queue.md are never touched.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from . import artifacts


def _sandbox() -> Path:
    """Point the archive + queue at throwaway temp locations; return an empty project root."""
    base = Path(tempfile.mkdtemp())
    artifacts.ARTIFACTS_DIR = base / "artifacts"
    artifacts.QUEUE = base / "queue.md"
    proj = base / "proj"
    (proj / "docs").mkdir(parents=True)
    (proj / ".brain" / "tasks").mkdir(parents=True)
    return proj


def test_sync_copies_docs_and_tasks_and_writes_index():
    proj = _sandbox()
    (proj / "docs" / "plan.md").write_text("# plan")
    (proj / "docs" / "reflect.md").write_text("# reflect")
    (proj / ".brain" / "tasks" / "abc-thing.md").write_text("---\ntitle: t\n---\n")
    (proj / ".brain" / "tasks" / ".gitkeep").write_text("")
    r = artifacts.sync_project("proj", proj)
    dest = artifacts.ARTIFACTS_DIR / "proj"
    assert r["docs"] == 2 and r["tasks"] == 1                 # .gitkeep excluded
    assert (dest / "docs" / "plan.md").read_text() == "# plan"
    assert (dest / "tasks" / "abc-thing.md").exists()
    assert "Workflow docs:** 2" in (dest / "INDEX.md").read_text()


def test_sync_prunes_removed_source():
    proj = _sandbox()
    (proj / "docs" / "plan.md").write_text("# plan")
    (proj / "docs" / "old.md").write_text("# old")
    artifacts.sync_project("proj", proj)
    (proj / "docs" / "old.md").unlink()                       # source removed
    artifacts.sync_project("proj", proj)
    dest = artifacts.ARTIFACTS_DIR / "proj" / "docs"
    assert (dest / "plan.md").exists() and not (dest / "old.md").exists()


def test_sessions_extracted_with_lenient_name_match():
    proj = _sandbox()
    artifacts.QUEUE.write_text(
        "# queue\n\n"
        "## 2026-06-05 — prediction_market_bot\n- did a thing\n\n"
        "## 2026-06-06 — other-project\n- unrelated\n"
    )
    # registry name uses hyphens; queue uses underscores — must still match
    r = artifacts.sync_project("prediction-market-bot", proj)
    assert r["sessions"] == 1
    text = (artifacts.ARTIFACTS_DIR / "prediction-market-bot" / "sessions.md").read_text()
    assert "did a thing" in text and "unrelated" not in text


def test_mark_copies_deliverable_and_logs():
    proj = _sandbox()
    f = proj / "spec.md"
    f.write_text("# spec")
    r = artifacts.mark("proj", str(f), note="the spec")
    dest = artifacts.ARTIFACTS_DIR / "proj" / "deliverables"
    assert (dest / "spec.md").read_text() == "# spec"
    assert "the spec" in (dest / "_deliverables.md").read_text()


def test_catalog_lists_synced_projects():
    proj = _sandbox()
    (proj / "docs" / "plan.md").write_text("# plan")
    artifacts.sync_project("proj", proj)
    artifacts.write_catalog()
    readme = (artifacts.ARTIFACTS_DIR / "README.md").read_text()
    assert "[proj](proj/INDEX.md)" in readme


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
