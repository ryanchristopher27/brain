"""Tests for the project registry (declared status) and the Obsidian projects-vault generator.

Run:  ./voice/.venv/bin/python -m dashboard.test_projects

Each test points the registry at a throwaway temp file so the real
~/.claude/brain/projects.json is never touched.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from . import data, projects, projects_vault, tracker


def _fresh_registry() -> Path:
    """Redirect both modules' registry path at a new temp file; return a usable project root."""
    reg = Path(tempfile.mkdtemp()) / "projects.json"
    reg.write_text("[]")                     # present-but-empty ⇒ "track nothing" (no auto-discovery)
    data.PROJECTS_REGISTRY = reg
    projects.REGISTRY = reg
    root = Path(tempfile.mkdtemp())          # a real dir so add_project's existence check passes
    return root


def test_add_and_list():
    root = _fresh_registry()
    projects.add_project("proj-a", str(root))
    rows = projects.list_projects()
    assert [r["name"] for r in rows] == ["proj-a"]
    assert rows[0]["status"] == "active" and rows[0]["exists"] is True


def test_add_rejects_bad_status_and_missing_dir():
    root = _fresh_registry()
    try:
        projects.add_project("x", str(root), status="nope")
        assert False, "bad status must raise"
    except projects.ProjectError:
        pass
    try:
        projects.add_project("x", str(root / "does-not-exist"))
        assert False, "missing dir must raise"
    except projects.ProjectError:
        pass


def test_add_rejects_duplicate():
    root = _fresh_registry()
    projects.add_project("dup", str(root))
    try:
        projects.add_project("dup", str(root))
        assert False, "duplicate name must raise"
    except projects.ProjectError:
        pass


def test_set_status_and_unknown():
    root = _fresh_registry()
    projects.add_project("p", str(root))
    projects.set_status("p", "shipped")
    assert projects.list_projects()[0]["status"] == "shipped"
    try:
        projects.set_status("ghost", "active")
        assert False, "unknown project must raise"
    except projects.ProjectError:
        pass


def test_remove():
    root = _fresh_registry()
    projects.add_project("p", str(root))
    projects.remove_project("p")
    assert projects.list_projects() == []
    try:
        projects.remove_project("p")
        assert False, "removing unknown must raise"
    except projects.ProjectError:
        pass


def test_enriched_reports_phase_and_task_counts():
    root = _fresh_registry()
    (root / "docs").mkdir()
    (root / "docs" / "plan.md").write_text("# plan")     # → phase detectable
    tracker.create_task(root, "do a thing")              # → 1 open task
    projects.add_project("p", str(root))
    row = next(r for r in projects.enriched() if r["name"] == "p")
    assert row["phase"] in data.PHASE_ORDER
    assert row["tasks_total"] == 1 and row["tasks_open"] == 1


def test_vault_generation_and_note_preservation():
    root = _fresh_registry()
    projects.add_project("proj-x", str(root), status="paused")
    vault = Path(tempfile.mkdtemp()) / "vault"

    projects_vault.generate(str(vault))
    base = (vault / "Projects.base").read_text()
    assert 'file.inFolder("projects")' in base and 'status == "paused"' in base
    card = vault / "projects" / "proj-x.md"
    text = card.read_text()
    assert "status: paused" in text and "## Notes" in text

    # user adds a note, regenerate, note survives while frontmatter refreshes
    card.write_text(text + "\nhand-written note\n")
    projects.set_status("proj-x", "shipped")
    projects_vault.generate(str(vault))
    regenerated = card.read_text()
    assert "hand-written note" in regenerated, "notes must survive regeneration"
    assert "status: shipped" in regenerated, "frontmatter must refresh"


def test_sync_registers_new_project():
    _fresh_registry()
    proj = Path(tempfile.mkdtemp())
    (proj / "package.json").write_text("{}")            # → looks like a project
    res = projects.sync_cwd(str(proj), regenerate=False)
    assert res["registered"] == proj.name
    assert proj.name in {p["name"] for p in projects.list_projects()}


def test_sync_skips_non_project():
    _fresh_registry()
    empty = Path(tempfile.mkdtemp())                     # no manifest / .git / docs
    res = projects.sync_cwd(str(empty), regenerate=False)
    assert res["registered"] is None and "not a" in (res["skipped"] or "")
    assert projects.list_projects() == []


def test_sync_skips_already_tracked():
    _fresh_registry()
    proj = Path(tempfile.mkdtemp())
    (proj / "pyproject.toml").write_text("")
    projects.add_project(proj.name, str(proj))
    res = projects.sync_cwd(str(proj), regenerate=False)
    assert res["registered"] is None and "already tracked" in (res["skipped"] or "")
    assert len(projects.list_projects()) == 1           # no duplicate


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
