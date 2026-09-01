"""Artifact archive — brain is the canonical home for the *markdown* artifacts of every
project. Code and working files stay in each repo; their markdown thinking-artifacts are
copied into `brain/artifacts/<project>/` so the whole body of AI-assisted work lives in one
version-controlled place.

Per project we collect:
  docs/           ← copies of the project's docs/*.md (workflow + design docs)
  tasks/          ← copies of the project's .brain/tasks/*.md (task history)
  sessions.md     ← this project's entries extracted from updates/queue.md
  deliverables/   ← files you explicitly `mark`
  INDEX.md        ← per-project manifest (sources + counts + sync time)

Originals are the source of truth; these are brain's copies of record, refreshed on every
SessionStart (see projects.sync_cwd). Stdlib-only, pure over the filesystem → testable.
"""
from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import data

ARTIFACTS_DIR = data.BRAIN_DIR / "artifacts"
QUEUE = data.BRAIN_DIR / "updates" / "queue.md"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _safe(name: str) -> str:
    return name.replace("/", "-")


def _copy_glob(src_dir: Path, pattern: str, dest_dir: Path) -> list[str]:
    copied = []
    if not src_dir.is_dir():
        return copied
    dest_dir.mkdir(parents=True, exist_ok=True)
    kept = set()
    for f in sorted(src_dir.glob(pattern)):
        if f.is_file() and f.name != ".gitkeep":
            shutil.copy2(f, dest_dir / f.name)
            kept.add(f.name)
            copied.append(f.name)
    # prune stale copies whose source was deleted/renamed (mirror semantics)
    for existing in dest_dir.glob("*.md"):
        if existing.name not in kept:
            existing.unlink()
    return copied


def _project_sessions(name: str) -> tuple[str, int]:
    """Extract this project's `## DATE — project` blocks from updates/queue.md (lenient name
    match, so 'prediction_market_bot' matches registry 'prediction-market-bot')."""
    if not QUEUE.exists():
        return "", 0
    parts = re.split(r"(?m)^(## .+)$", QUEUE.read_text())
    reg = _norm(name)
    blocks: list[str] = []
    i = 1
    while i < len(parts):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        m = re.match(r"##\s*(\d{4}-\d{2}-\d{2})\s*[—-]+\s*(.+)", header)
        if m:
            proj = _norm(m.group(2))
            if reg and (reg == proj or reg in proj or proj.startswith(reg)):
                blocks.append(header.strip() + "\n" + body.rstrip())
        i += 2
    return "\n\n".join(blocks).strip(), len(blocks)


def sync_project(name: str, root: Path) -> dict:
    """Copy a single project's markdown artifacts into brain. Never raises."""
    root = Path(root).expanduser()
    dest = ARTIFACTS_DIR / _safe(name)
    result = {"project": name, "docs": 0, "tasks": 0, "sessions": 0, "deliverables": 0}
    try:
        docs = _copy_glob(root / "docs", "*.md", dest / "docs")
        tasks = _copy_glob(root / ".brain" / "tasks", "*.md", dest / "tasks")
        sessions_text, n_sessions = _project_sessions(name)
        if sessions_text:
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "sessions.md").write_text(
                f"# {name} — session summaries\n\n"
                f"_Extracted from brain's `updates/queue.md`._\n\n{sessions_text}\n"
            )
        deliv = sorted((dest / "deliverables").glob("*")) if (dest / "deliverables").is_dir() else []
        result.update(docs=len(docs), tasks=len(tasks), sessions=n_sessions, deliverables=len(deliv))
        if any([docs, tasks, sessions_text, deliv]):
            _write_index(name, root, dest, result)
    except Exception as e:  # never break a caller/session
        result["error"] = str(e)
    return result


def _write_index(name: str, root: Path, dest: Path, counts: dict) -> None:
    lines = [
        f"# {name} — artifacts",
        "",
        f"_Brain's copies of `{name}`'s markdown artifacts. Source: `{root}`._",
        "",
        f"- **Workflow docs:** {counts['docs']}  (`docs/`)",
        f"- **Task records:** {counts['tasks']}  (`tasks/`)",
        f"- **Session summaries:** {counts['sessions']} entries  (`sessions.md`)",
        f"- **Marked deliverables:** {counts['deliverables']}  (`deliverables/`)",
        "",
        "> Originals live in the project; edit them there. These are refreshed automatically "
        "on SessionStart.",
    ]
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "INDEX.md").write_text("\n".join(lines) + "\n")


def mark(project: str, file: str, note: str = "") -> dict:
    """Copy a specific file into a project's artifact deliverables and log it."""
    src = Path(file).expanduser()
    if not src.is_file():
        raise FileNotFoundError(f"no such file: {src}")
    dest = ARTIFACTS_DIR / _safe(project) / "deliverables"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest / src.name)
    log = dest / "_deliverables.md"
    entry = f"- {_now()} · **{src.name}** ← `{src}`" + (f" — {note}" if note else "")
    prior = log.read_text() if log.exists() else "# Marked deliverables\n\n"
    log.write_text(prior + entry + "\n")
    return {"project": project, "file": src.name, "dest": str(dest / src.name)}


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def list_items() -> list[dict]:
    """Flat list of archived artifacts for the dashboard's Artifacts view, newest first."""
    items: list[dict] = []
    if not ARTIFACTS_DIR.is_dir():
        return items
    for sub in sorted(p for p in ARTIFACTS_DIR.iterdir() if p.is_dir()):
        project = sub.name
        for kind, folder in (("doc", "docs"), ("task", "tasks"), ("deliverable", "deliverables")):
            d = sub / folder
            if d.is_dir():
                for f in sorted(d.glob("*.md")):
                    if f.name.startswith("_"):
                        continue
                    st = f.stat()
                    items.append({"name": f.stem, "kind": kind, "project": project,
                                  "modified": _iso(st.st_mtime), "size": st.st_size})
        sess = sub / "sessions.md"
        if sess.exists():
            items.append({"name": "session summaries", "kind": "sessions", "project": project,
                          "modified": _iso(sess.stat().st_mtime), "size": sess.stat().st_size})
    items.sort(key=lambda x: x["modified"], reverse=True)
    return items


def sync_all() -> list[dict]:
    results = [sync_project(m["name"], m["root"]) for m in data._projects_meta()]
    write_catalog()
    return results


def write_catalog() -> None:
    """Top-level README cataloging every project's archived artifacts."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for sub in sorted(p for p in ARTIFACTS_DIR.iterdir() if p.is_dir()):
        docs = len(list((sub / "docs").glob("*.md"))) if (sub / "docs").is_dir() else 0
        tasks = len(list((sub / "tasks").glob("*.md"))) if (sub / "tasks").is_dir() else 0
        sess = "yes" if (sub / "sessions.md").exists() else "—"
        deliv = len([f for f in (sub / "deliverables").glob("*") if f.is_file()]) \
            if (sub / "deliverables").is_dir() else 0
        rows.append(f"| [{sub.name}]({sub.name}/INDEX.md) | {docs} | {tasks} | {sess} | {deliv} |")
    table = "\n".join(rows) if rows else "| _none yet_ | | | | |"
    (ARTIFACTS_DIR / "README.md").write_text(
        "# Brain Artifacts Archive\n\n"
        "Central, version-controlled home for the **markdown artifacts** of every project brain "
        "tracks — workflow docs, task history, session summaries, and marked deliverables. Code "
        "and working files stay in each project; these are brain's copies of record, refreshed "
        "automatically on SessionStart.\n\n"
        "| Project | Docs | Tasks | Sessions | Deliverables |\n"
        "|---------|-----:|------:|:--------:|-------------:|\n"
        f"{table}\n\n"
        "_Regenerate: `python -m dashboard.artifacts_cli sync --all` · push: `/sync`._\n"
    )
