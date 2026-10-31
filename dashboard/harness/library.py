"""Agent library (H6) — agent definitions as Markdown files in git, so they travel with the repos.

Two kinds, one format (frontmatter + role text, like the personas):
- workflow agents: `brain/agents/workflow/<name>.md` — one per workflow phase, usable on any project.
- project experts:  `<project>/.brain/agents/<name>.md` — bound to the project they live in.

A definition is a template: adding it to the team creates a live agent (runtime.Harness.create) with a
copy of its settings. Editing the definition later doesn't change agents already on the team.

    ---
    name: planner
    description: Team lead: breaks tasks down and hands them out
    persona: scout
    model: claude-opus-5-5      # or "auto"
    scope: .                    # comma-separated folders, relative to the project
    daily_usd: 2
    ---
    <role text: becomes the live agent's brief>
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .. import data
from ..tracker import _dump_scalar, _load_scalar  # same YAML-safe quoting as tasks (Obsidian reads .brain/)
from .runtime import MODEL_RE, NAME_RE, HarnessError

WORKFLOW_DIR = data.BRAIN_DIR / "agents" / "workflow"
KINDS = ("workflow", "expert")
FIELDS = ("name", "description", "persona", "model", "scope", "daily_usd")
BODY_MAX = 2000  # becomes the live agent brief, which runtime caps at 2000
DESC_MAX = 200


def _dir(kind: str, project_root: Path | None) -> Path:
    if kind == "workflow":
        return WORKFLOW_DIR
    if kind == "expert" and project_root is not None:
        return project_root / ".brain" / "agents"
    raise HarnessError("unknown library kind or project")


def _parse(path: Path, kind: str, project: str | None) -> dict:
    text = path.read_text()
    fm = {k: _load_scalar(v) for k, v in data._parse_frontmatter(text).items()}
    end = text.find("\n---", 3)
    body = text[end + 4:].strip() if text.startswith("---") and end != -1 else text.strip()
    return {"kind": kind, "project": project, "name": fm.get("name") or path.stem,
            "description": fm.get("description", ""), "persona": fm.get("persona", "scout"),
            "model": fm.get("model", "claude-sonnet-5-5"), "scope": fm.get("scope", "."),
            "daily_usd": float(fm.get("daily_usd") or 2), "role": body}


def list_library(project_roots: list[tuple[str, Path]]) -> list[dict]:
    out = []
    for kind, project, root in [("workflow", None, None), *[("expert", n, r) for n, r in project_roots]]:
        d = _dir(kind, root)
        for f in sorted(d.glob("*.md")) if d.is_dir() else []:
            try:
                out.append(_parse(f, kind, project))
            except (OSError, ValueError):
                continue  # an unreadable file shouldn't hide the rest of the library
    return out


def clean(defn: dict, personas: set[str]) -> dict:
    d = {k: defn.get(k) for k in (*FIELDS, "role")}
    if not NAME_RE.match(d["name"] or ""):
        raise HarnessError("name: lowercase letters, digits, dashes (2-32), starting with a letter")
    if d["persona"] not in personas:
        raise HarnessError("unknown persona")
    if d["model"] != "auto" and not MODEL_RE.match(d["model"] or ""):
        raise HarnessError("model must be a Claude model id or 'auto'")
    for k in ("description", "scope"):
        d[k] = str(d[k] or "").strip()
        if "\n" in d[k] or len(d[k]) > DESC_MAX:
            raise HarnessError(f"{k} must be one line of at most {DESC_MAX} characters")
    d["scope"] = d["scope"] or "."
    if any(Path(s.strip()).is_absolute() or ".." in Path(s.strip()).parts for s in d["scope"].split(",")):
        raise HarnessError("scope folders must be relative to the project, without '..'")
    try:
        d["daily_usd"] = float(d["daily_usd"] if d["daily_usd"] is not None else 2)
    except (TypeError, ValueError):
        raise HarnessError("daily_usd must be a number")
    if not 0 < d["daily_usd"] <= 100:
        raise HarnessError("daily_usd must be between 0 and 100")
    d["role"] = str(d["role"] or "").strip()
    if len(d["role"]) > BODY_MAX:
        raise HarnessError(f"role is longer than {BODY_MAX} characters")
    return d


def save(kind: str, project_root: Path | None, defn: dict, personas: set[str]) -> dict:
    d = clean(defn, personas)
    folder = _dir(kind, project_root)
    folder.mkdir(parents=True, exist_ok=True)
    daily = int(d["daily_usd"]) if d["daily_usd"].is_integer() else d["daily_usd"]
    fm = "\n".join(f"{k}: {_dump_scalar(str(v))}" for k, v in (("name", d["name"]), ("description", d["description"]),
                                             ("persona", d["persona"]), ("model", d["model"]),
                                             ("scope", d["scope"]), ("daily_usd", daily)))
    (folder / f"{d['name']}.md").write_text(f"---\n{fm}\n---\n\n{d['role']}\n")
    return d


def delete(kind: str, project_root: Path | None, name: str) -> None:
    if not NAME_RE.match(name or ""):
        raise HarnessError("bad name")
    f = _dir(kind, project_root) / f"{name}.md"
    if not f.exists():
        raise HarnessError("no such definition", 404)
    f.unlink()


def get(kind: str, project: str | None, project_root: Path | None, name: str) -> dict:
    if not NAME_RE.match(name or ""):
        raise HarnessError("bad name")
    f = _dir(kind, project_root) / f"{name}.md"
    if not f.exists():
        raise HarnessError("no such definition", 404)
    return _parse(f, kind, project)


# Files an expert should ground itself in, when they exist (relative to the project).
EXPERT_SOURCES = ["CLAUDE.md", "README.md", "docs/brainstorm.md", "docs/plan.md", "docs/review.md", "docs/reflect.md"]


def memory_index(root: Path) -> Path:
    """Claude Code's auto-memory index for a project folder."""
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(root)) / "memory" / "MEMORY.md"


def seed_expert(project: str, root: Path, personas: set[str]) -> dict:
    """Write a project-expert definition grounded in the files that project actually has."""
    sources = [s for s in EXPERT_SOURCES if (root / s).is_file()]
    mem = memory_index(root)
    lines = [f"You are the resident expert on {project} ({root}). Teammates and the user come to you with "
             "questions about how it works, why it's built the way it is, and what's in flight.",
             "", "Before your first answer in a conversation, ground yourself by reading:"]
    lines += [f"- {s}" for s in sources]
    if (root / ".brain" / "tasks").is_dir():
        lines.append("- the open tracker tasks in .brain/tasks/ (skip status: done)")
    if mem.is_file():
        lines.append(f"- the project's memory index {mem} and the memory files it links to that matter")
    lines += ["", "Answer from the code and those files, cite file paths, and say plainly when something isn't "
              "written down. Keep answers short; teammates act on them."]
    name = re.sub(r"[^a-z0-9]+", "-", project.lower()).strip("-")[:25] + "-expert"
    if not re.match(r"[a-z]", name):
        name = "p" + name
    return save("expert", root, {"name": name, "description": f"Knows {project}: code, plans, tasks and history",
                                 "persona": "scout", "model": "claude-sonnet-5-5", "scope": ".", "daily_usd": 2,
                                 "role": "\n".join(lines)}, personas)


def to_agent(defn: dict) -> dict:
    """Arguments for Harness.create from a definition."""
    model = {"mode": "auto"} if defn["model"] == "auto" else {"mode": "pinned", "model": defn["model"]}
    return {"persona": defn["persona"], "brief": defn["role"][:2000],
            "scope": [s.strip() for s in defn["scope"].split(",") if s.strip()] or ["."],
            "model": model, "limits": {"daily_usd": defn["daily_usd"]}}
