"""Generate a standalone Obsidian vault that boards every tracked project by status.

Unlike the per-repo task vault (brain/.brain), projects live in different repos, so Obsidian
can't aggregate them natively — we materialize one markdown *card* per project (frontmatter =
declared status + auto-detected phase + task counts) into a dedicated vault, plus a Bases board.

Idempotent + regenerable: re-run any time (`python -m dashboard.projects_cli vault`). The auto
block is rewritten each run; anything you write under `## Notes` is preserved.

  Default vault:  ~/Desktop/Code/brain-projects-vault
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import projects, tracker

DEFAULT_VAULT = Path.home() / "Desktop" / "Code" / "brain-projects-vault"

_CORE_PLUGINS = {
    "file-explorer": True, "global-search": True, "switcher": True, "graph": True,
    "backlink": True, "outgoing-link": True, "tag-pane": True, "properties": True,
    "page-preview": True, "outline": True, "bookmarks": True, "command-palette": True,
    "bases": True,
}

_APP_JSON = '{\n  "showFrontmatter": true,\n  "readableLineLength": true\n}\n'

_PROJECTS_BASE = """filters:
  and:
    - file.inFolder("projects")
    - file.ext == "md"
properties:
  title:
    displayName: Project
  status:
    displayName: Status
  phase:
    displayName: Phase
  tasks_open:
    displayName: Open
  tasks_total:
    displayName: Total
  updated:
    displayName: Refreshed
views:
  - type: table
    name: All projects
    order: [title, status, phase, tasks_open, tasks_total]
    sort:
      - property: status
        direction: ASC
      - property: phase
        direction: ASC
{status_views}"""

_STATUS_VIEW = """  - type: table
    name: {label}
    filters:
      and:
        - status == "{status}"
    order: [title, phase, tasks_open, tasks_total, path]
    sort:
      - property: phase
        direction: ASC
"""

_NOTES_MARKER = "## Notes"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _card(p: dict, generated: str) -> str:
    q = tracker._dump_scalar  # reuse the valid-YAML scalar quoter
    fm = [
        "---",
        f"title: {q(p['name'])}",
        f"status: {q(p['status'])}",
        f"phase: {q(p.get('phase') or '')}",
        f"path: {q(p['root_path'])}",
        f"tasks_open: {p.get('tasks_open', 0)}",
        f"tasks_total: {p.get('tasks_total', 0)}",
        f"iterating: {'true' if p.get('iterating') else 'false'}",
        f"exists: {'true' if p.get('exists') else 'false'}",
        f"updated: {q(generated)}",
        "---",
    ]
    detected = ", ".join(p.get("detected") or []) or "—"
    body = [
        "",
        f"# {p['name']}",
        "",
        "## Overview",
        f"- **Status:** {p['status']}",
        f"- **Workflow phase:** {p.get('phase') or '—'}"
        + ("  _(iterating)_" if p.get("iterating") else ""),
        f"- **Phases reached:** {detected}",
        f"- **Open tasks:** {p.get('tasks_open', 0)} / {p.get('tasks_total', 0)}",
        f"- **Path:** `{p['root_path']}`" + ("" if p.get("exists") else "  ⚠ missing on disk"),
        "",
        "*Auto-generated. Set status with `python -m dashboard.projects_cli status "
        f"--name {p['name']} --to <status>`. Notes below are preserved on regeneration.*",
        "",
    ]
    return "\n".join(fm + body)


def _merge_notes(path: Path, generated_card: str) -> str:
    """Keep everything from the first `## Notes` heading onward if the card already exists."""
    preserved = f"{_NOTES_MARKER}\n"
    if path.exists():
        old = path.read_text()
        idx = old.find(_NOTES_MARKER)
        if idx != -1:
            preserved = old[idx:]
    return generated_card.rstrip() + "\n\n" + preserved


def generate(vault_path: str | None = None) -> Path:
    vault = Path(vault_path).expanduser() if vault_path else DEFAULT_VAULT
    (vault / ".obsidian").mkdir(parents=True, exist_ok=True)
    (vault / "projects").mkdir(parents=True, exist_ok=True)

    import json
    (vault / ".obsidian" / "core-plugins.json").write_text(json.dumps(_CORE_PLUGINS, indent=2) + "\n")
    (vault / ".obsidian" / "app.json").write_text(_APP_JSON)
    (vault / ".obsidian" / ".gitignore").write_text("workspace.json\nworkspace-mobile.json\ncache/\n")

    generated = _now()
    rows = projects.enriched()

    # Project cards (preserve user notes).
    keep = set()
    for p in rows:
        fname = p["name"].replace("/", "-") + ".md"
        keep.add(fname)
        fp = vault / "projects" / fname
        fp.write_text(_merge_notes(fp, _card(p, generated)))

    # Prune cards for projects no longer registered (but never touch notes-bearing orphans).
    for existing in (vault / "projects").glob("*.md"):
        if existing.name not in keep and _NOTES_MARKER not in existing.read_text():
            existing.unlink()

    # Bases board.
    status_views = "".join(
        _STATUS_VIEW.format(label=s.capitalize(), status=s) for s in projects.STATUSES
    )
    (vault / "Projects.base").write_text(_PROJECTS_BASE.format(status_views=status_views))

    # Landing note.
    counts: dict[str, int] = {}
    for p in rows:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    summary = " · ".join(f"{n} {s}" for s, n in counts.items()) or "no projects yet"
    (vault / "Home.md").write_text(
        "# Projects\n\n"
        f"Cross-project status board over every project brain tracks. **{summary}.**\n\n"
        "Open **Projects.base** for the board (tabs per status). Cards live in `projects/`.\n\n"
        "This vault is generated from `~/.claude/brain/projects.json` — the same registry the "
        "web dashboard reads. Refresh with:\n\n"
        "```\npython -m dashboard.projects_cli vault\n```\n\n"
        f"_Last refreshed {generated}._\n"
    )
    return vault
