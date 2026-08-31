"""Project registry — the list of projects brain tracks, with a declared lifecycle
status per project (active / paused / blocked / shipped / archived), orthogonal to the
auto-detected workflow phase (see data._detect_phase).

Source of truth: `~/.claude/brain/projects.json` — a JSON array of
{name, root_path, status}. Read paths live in data.py (`_projects_meta`); this module
owns the *write* side plus enrichment (phase + task counts) for views.

Stdlib-only, pure over the filesystem so it is unit-testable over a temp registry.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import data


class ProjectError(Exception):
    """Invalid project op (unknown name, bad status, duplicate, missing path)."""


REGISTRY = data.PROJECTS_REGISTRY
STATUSES = data.PROJECT_STATUSES
DEFAULT_STATUS = data.DEFAULT_PROJECT_STATUS


def _load_raw() -> list[dict]:
    if not REGISTRY.exists():
        return []
    try:
        entries = json.loads(REGISTRY.read_text())
        return entries if isinstance(entries, list) else []
    except Exception:
        return []


def _save_raw(entries: list[dict]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(entries, indent=2) + "\n")


def list_projects() -> list[dict]:
    """Every tracked project with declared status, resolved absolute root, existence."""
    out = []
    for m in data._projects_meta():
        root = m["root"]
        out.append({
            "name": m["name"],
            "root_path": str(root),
            "status": m["status"],
            "exists": root.is_dir(),
        })
    return out


def add_project(name: str, root_path: str, status: str = DEFAULT_STATUS) -> dict:
    if status not in STATUSES:
        raise ProjectError(f"status must be one of {STATUSES}")
    root = Path(root_path).expanduser().resolve()
    if not root.is_dir():
        raise ProjectError(f"no such directory: {root}")
    entries = _load_raw()
    if any(e.get("name") == name for e in entries):
        raise ProjectError(f"project {name!r} already registered")
    entry = {"name": name, "root_path": str(root), "status": status}
    entries.append(entry)
    _save_raw(entries)
    return entry


def set_status(name: str, status: str) -> dict:
    if status not in STATUSES:
        raise ProjectError(f"status must be one of {STATUSES}")
    entries = _load_raw()
    for e in entries:
        if e.get("name") == name:
            e["status"] = status
            _save_raw(entries)
            return e
    raise ProjectError(f"unknown project {name!r}")


def remove_project(name: str) -> None:
    entries = _load_raw()
    kept = [e for e in entries if e.get("name") != name]
    if len(kept) == len(entries):
        raise ProjectError(f"unknown project {name!r}")
    _save_raw(kept)


def _git_toplevel(path: str | Path) -> Path | None:
    try:
        out = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except Exception:
        pass
    return None


def _looks_like_project(root: Path) -> bool:
    """A directory worth auto-tracking: a git repo, a brain-workflow repo, or one with a
    recognized build manifest. Excludes $HOME and the generated projects vault."""
    if not root.is_dir() or root == Path.home():
        return False
    from . import projects_vault
    if root.resolve() == projects_vault.DEFAULT_VAULT.resolve():
        return False
    if (root / ".git").exists() or (root / ".brain").is_dir():
        return True
    if (root / "docs" / "plan.md").exists() or (root / "docs" / "brainstorm.md").exists():
        return True
    return any((root / m).exists() for m in data._MANIFESTS)


def sync_cwd(path: str = ".", regenerate: bool = True) -> dict:
    """Auto-register the project at `path` (git toplevel when available) if it's a real,
    not-yet-tracked project, then refresh the Obsidian vault. Called by the SessionStart
    hook on every project you open — never raises, so it can't break a session."""
    result: dict = {"registered": None, "skipped": None, "vault": None, "artifacts": None}
    proj_name = None
    proj_root = None
    try:
        root = _git_toplevel(path) or Path(path).expanduser().resolve()
        if not _looks_like_project(root):
            result["skipped"] = "not a tracked-worthy project"
        else:
            proj_root = root
            tracked = None
            for m in data._projects_meta():
                mroot = m["root"].expanduser()
                try:
                    if root == mroot or root.is_relative_to(mroot):
                        tracked = m["name"]
                        break
                except AttributeError:  # py<3.9 has no is_relative_to
                    if str(root).startswith(str(mroot)):
                        tracked = m["name"]
                        break
            if tracked:
                proj_name = tracked
                result["skipped"] = f"already tracked ({tracked})"
            elif root.name in {m["name"] for m in data._projects_meta()}:
                result["skipped"] = f"name {root.name!r} already used — add manually with a unique name"
            else:
                add_project(root.name, str(root))
                proj_name = root.name
                result["registered"] = root.name
    except Exception as e:  # never break a session
        result["skipped"] = f"error: {e}"
    # Copy this project's markdown artifacts into brain (best-effort).
    if proj_name and proj_root:
        try:
            from . import artifacts
            r = artifacts.sync_project(proj_name, proj_root)
            artifacts.write_catalog()
            result["artifacts"] = f"{r['docs']}d/{r['tasks']}t/{r['sessions']}s"
        except Exception as e:
            result["artifacts"] = f"error: {e}"
    if regenerate:
        try:
            from . import projects_vault
            projects_vault.generate()
            result["vault"] = "refreshed"
        except Exception as e:
            result["vault"] = f"error: {e}"
    return result


def enriched() -> list[dict]:
    """Projects joined with auto-detected phase and open/total task counts — the shape
    the dashboard API and the Obsidian vault generator both consume."""
    from . import tracker
    out = []
    for m in data._projects_meta():
        root = m["root"]
        try:
            phase = data._detect_phase(root)
        except Exception:
            phase = {"phase": "", "detected": [], "iterating": False, "override": False}
        try:
            tasks = tracker.list_tasks(root)
        except Exception:
            tasks = []
        open_tasks = [t for t in tasks if t.get("status") not in ("done",)]
        out.append({
            "name": m["name"],
            "root_path": str(root),
            "status": m["status"],
            "exists": root.is_dir(),
            "phase": phase["phase"],
            "detected": phase["detected"],
            "iterating": phase["iterating"],
            "tasks_total": len(tasks),
            "tasks_open": len(open_tasks),
        })
    return out
