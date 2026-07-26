"""File-based task tracker (T1) — the source of truth is git-versioned files per repo, so
state travels with `git pull`.

One task = one file: `<repo>/.brain/tasks/<id>-<slug>.md` — scalar YAML frontmatter (stdlib-
parseable, no YAML dep) + markdown body sections (## Brief, ## Acceptance, ## Runs, ## Updates).
See `.brain/README.md` for the format.

Stdlib-only, pure over the filesystem → unit-testable over a temp dir (test_tracker.py).
Serialization is deterministic (fixed field/section order) so read→write with no change is
byte-identical, keeping git diffs small.
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from . import data

TASKS_SUBDIR = ".brain/tasks"
TYPES = ("task", "issue", "bug")
STATUSES = ("backlog", "ready", "doing", "review", "done")

TRANSITIONS: dict[str, set[str]] = {
    "backlog": {"ready", "doing"},
    "ready": {"doing", "backlog"},
    "doing": {"review", "backlog"},
    "review": {"done", "doing", "backlog"},
    "done": {"backlog"},
}
AGENT_TERMINAL = "review"  # agents may advance to `review`, never close to `done`

SECTION_ORDER = ("Brief", "Acceptance", "Runs", "Updates")
FRONTMATTER_ORDER = ("id", "source", "title", "type", "status", "assignee", "scoped_dir",
                     "created", "updated")
_EDITABLE = {"title", "type", "assignee", "scoped_dir", "brief", "acceptance"}


class TrackerError(Exception):
    """Raised on invalid task ops (bad status transition, unknown task, etc.)."""


# ── trivial helpers ──────────────────────────────────────────────────────────
def _new_id() -> str:
    return secrets.token_hex(3)  # 6 hex chars, collision-free across offline devices


def _slug(title: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return (s[:maxlen].strip("-")) or "task"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tasks_dir(root: Path) -> Path:
    return Path(root) / TASKS_SUBDIR


def _find_file(root: Path, task_id: str) -> Path | None:
    d = _tasks_dir(root)
    if not d.is_dir():
        return None
    for p in d.glob(f"{task_id}-*.md"):
        return p
    return None


# ── parse / serialize (deterministic, inverse of each other) ─────────────────
def _parse(text: str) -> dict:
    lines = text.splitlines()
    fm: dict = {}
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            if ":" in lines[i]:
                k, _, v = lines[i].partition(":")
                fm[k.strip()] = v.strip()
            i += 1
        i += 1  # skip closing ---

    sections: dict[str, list[str]] = {}
    cur = None
    for line in lines[i:]:
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)

    def _items(name: str) -> list[str]:
        return [ln[2:] for ln in sections.get(name, []) if ln.rstrip().startswith("- ")]

    acceptance = [re.sub(r"^\[.\]\s*", "", a) for a in _items("Acceptance")]
    return {
        "id": fm.get("id", ""), "source": fm.get("source", ""),
        "title": fm.get("title", ""),
        "type": fm.get("type", "task"), "status": fm.get("status", "backlog"),
        "assignee": fm.get("assignee", ""), "scoped_dir": fm.get("scoped_dir", "."),
        "created": fm.get("created", ""), "updated": fm.get("updated", ""),
        "brief": "\n".join(sections.get("Brief", [])).strip(),
        "acceptance": acceptance,
        "runs": _items("Runs"),
        "updates": _items("Updates"),
    }


def _serialize(task: dict) -> str:
    out = ["---"]
    out += [f"{k}: {task.get(k, '')}" for k in FRONTMATTER_ORDER]
    out += ["---", "", "## Brief", task.get("brief", ""), ""]
    out.append("## Acceptance")
    out += [f"- [ ] {a}" for a in task.get("acceptance", [])]
    out += ["", "## Runs"]
    out += [f"- {r}" for r in task.get("runs", [])]
    out += ["", "## Updates"]
    out += [f"- {u}" for u in task.get("updates", [])]
    return "\n".join(out) + "\n"


def _write(root: Path, task: dict, path: Path | None = None) -> None:
    if path is None:
        path = _find_file(root, task["id"])
    if path is None:
        raise TrackerError(f"no file for task {task['id']}")
    path.write_text(_serialize(task))


def _require(root: Path, task_id: str) -> dict:
    t = read_task(root, task_id)
    if t is None:
        raise TrackerError(f"no task {task_id}")
    return t


# ── public API ───────────────────────────────────────────────────────────────
def list_tasks(root: Path) -> list[dict]:
    d = _tasks_dir(root)
    if not d.is_dir():
        return []
    return [_parse(p.read_text()) for p in sorted(d.glob("*.md"))]


def all_tasks(roots: list[Path] | None = None) -> list[dict]:
    if roots is None:
        roots = [p for _, p in data._project_roots()]
    out = []
    for root in roots:
        for t in list_tasks(root):
            out.append({**t, "project": Path(root).name, "root": str(root)})
    return out


def read_task(root: Path, task_id: str) -> dict | None:
    p = _find_file(root, task_id)
    return _parse(p.read_text()) if p else None


def create_task(root: Path, title: str, type: str = "task", brief: str = "",
                acceptance: list[str] | None = None, assignee: str = "",
                scoped_dir: str = ".", source: str = "") -> dict:
    now = _now_iso()
    task = {
        "id": _new_id(), "source": source, "title": title, "type": type, "status": "backlog",
        "assignee": assignee, "scoped_dir": scoped_dir, "created": now, "updated": now,
        "brief": brief, "acceptance": list(acceptance or []), "runs": [],
        "updates": [f"{now} · created"],
    }
    d = _tasks_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    _write(root, task, path=d / f"{task['id']}-{_slug(title)}.md")
    return task


def update_task(root: Path, task_id: str, **fields) -> dict:
    task = _require(root, task_id)
    changed = False
    for k, v in fields.items():
        if k in _EDITABLE and task.get(k) != v:
            task[k] = v
            changed = True
    if changed:
        task["updated"] = _now_iso()
    _write(root, task)  # no-op writes identical bytes (serialization is idempotent)
    return task


def add_update(root: Path, task_id: str, kind: str, detail: str) -> None:
    task = _require(root, task_id)
    now = _now_iso()
    task["updates"].append(f"{now} · {kind}: {detail}")
    task["updated"] = now
    _write(root, task)


def set_status(root: Path, task_id: str, new_status: str, actor: str, note: str = "") -> dict:
    task = _require(root, task_id)
    cur = task["status"]
    if new_status not in STATUSES:
        raise TrackerError(f"unknown status {new_status!r}")
    if new_status != cur and new_status not in TRANSITIONS.get(cur, set()):
        raise TrackerError(f"invalid transition {cur} → {new_status}")
    if actor == "agent" and new_status == "done":
        raise TrackerError("agents cannot close a task (done) — leave it at review")
    now = _now_iso()
    task["status"] = new_status
    line = f"{now} · status: {cur} → {new_status}"
    task["updates"].append(f"{line} ({note})" if note else line)
    task["updated"] = now
    _write(root, task)
    return task


def link_run(root: Path, task_id: str, run_id: str, result: str | None = None) -> None:
    task = _require(root, task_id)
    now = _now_iso()
    if run_id not in task["runs"]:
        task["runs"].append(run_id)
    task["updates"].append(
        f"{now} · result ({run_id}): {result}" if result else f"{now} · run linked: {run_id}")
    task["updated"] = now
    _write(root, task)


def find_by_source(root: Path, source: str) -> dict | None:
    if not source:
        return None
    for t in list_tasks(root):
        if t.get("source") == source:
            return t
    return None


def upsert_task(root: Path, source: str, title: str, **fields) -> dict:
    """Idempotent create-or-update keyed by `source` (e.g. 'plan:brain:T6'). Re-running a workflow
    phase updates the existing task's editable fields instead of duplicating."""
    existing = find_by_source(root, source)
    if existing:
        upd = {k: v for k, v in fields.items() if k in _EDITABLE}
        if title and title != existing["title"]:
            upd["title"] = title
        t = update_task(root, existing["id"], **upd) if upd else existing
        return {**t, "_created": False}
    t = create_task(root, title, source=source,
                    type=fields.get("type", "task"), brief=fields.get("brief", ""),
                    acceptance=fields.get("acceptance"), assignee=fields.get("assignee", ""),
                    scoped_dir=fields.get("scoped_dir", "."))
    return {**t, "_created": True}
