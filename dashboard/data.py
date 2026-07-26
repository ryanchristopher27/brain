"""Read-only data sources for the dashboard panels (D3).

Pure functions over the filesystem / launchctl so they can be unit-tested without a server:
- read_agents()   — persona roster from agents/
- read_jobs()     — background run history from ~/.claude/brain-bg-logs/
- read_schedule() — launchd jobs (loaded) + installable templates
- read_health()   — configured MCP servers + whether their tokens are set
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent
BG_LOG_DIR = Path.home() / ".claude" / "brain-bg-logs"
SETTINGS = Path.home() / ".claude" / "settings.json"
PROJECTS_REGISTRY = Path.home() / ".claude" / "brain" / "projects.json"

# Workflow columns, least → most advanced (the tiebreak order from the fleet recon).
PHASE_ORDER = ["brainstorm", "plan", "scaffold", "build", "review", "reflect"]
_SRC_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".c", ".cpp"}
_SKIP_DIR = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
_MANIFESTS = ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml", "setup.py")

# MCP name → the env var its config references (None = no auth needed)
MCP_TOKEN_ENV = {"github": "GITHUB_PAT", "notion": "NOTION_TOKEN", "playwright": None}


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm: dict = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def read_agents() -> list[dict]:
    agents = []
    for category, sub in (("persona", "personas"), ("background", "background")):
        for f in sorted((BRAIN_DIR / "agents" / sub).glob("*.md")):
            fm = _parse_frontmatter(f.read_text())
            if not fm.get("name"):
                continue
            tools = [t.strip() for t in fm.get("tools", "").split(",") if t.strip()]
            agents.append({
                "name": fm["name"],
                "description": fm.get("description", ""),
                "model": fm.get("model", ""),
                "tools": tools,
                "category": category,
                # writer only if it has Write/Edit or a *bare* (unscoped) Bash;
                # scoped Bash(git log:*) etc. stays read-only.
                "read_only": not any(t in {"Write", "Edit", "Bash"} for t in tools),
            })
    return agents


def read_jobs(limit: int = 20) -> list[dict]:
    if not BG_LOG_DIR.exists():
        return []
    jobs = []
    for report in sorted(BG_LOG_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        stem = report.stem  # <label>_<YYYYMMDD_HHMMSS>
        label, _, ts = stem.rpartition("_")
        if "_" in label:  # ts is date_time, so split once more
            label, _, d = label.rpartition("_")
            ts = f"{d}_{ts}"
        log = report.with_suffix(".log")
        status = "unknown"
        if log.exists():
            body = log.read_text()
            status = "done" if "✓" in body else ("failed" if "✗" in body else "unknown")
        jobs.append({
            "label": label or stem,
            "timestamp": ts,
            "status": status,
            "report_preview": report.read_text()[:240].strip(),
            "report_file": report.name,
        })
    return jobs


def read_schedule() -> dict:
    loaded = []
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines():
            if "brain" in line.lower():
                parts = line.split()
                loaded.append({"label": parts[-1], "pid": parts[0], "status": parts[1]})
    except Exception:
        pass
    templates = [p.name for p in (BRAIN_DIR / "agents" / "background").glob("*.plist.example")]
    return {"loaded": loaded, "installable": templates}


def _has_source(root: Path) -> bool:
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR and not d.startswith(".")]
        for f in filenames:
            if os.path.splitext(f)[1] in _SRC_EXT:
                count += 1
                if count >= 3:
                    return True
    return False


def _newest_source_mtime(root: Path) -> float:
    newest = 0.0
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR and not d.startswith(".")]
        for f in filenames:
            if os.path.splitext(f)[1] in _SRC_EXT:
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(dirpath, f)))
                except OSError:
                    pass
                seen += 1
                if seen >= 2000:  # bound the walk
                    return newest
    return newest


def _detect_phase(root: Path) -> dict:
    docs = root / "docs"
    times: dict[str, float] = {}  # phase → mtime of its most recent artifact

    for phase, fn in (("brainstorm", "brainstorm.md"), ("plan", "plan.md"),
                      ("review", "review.md"), ("reflect", "reflect.md")):
        doc = docs / fn
        if doc.exists():
            times[phase] = doc.stat().st_mtime

    manifests = [root / m for m in _MANIFESTS if (root / m).exists()]
    manifests += [root / d for d in ("src", "app") if (root / d).is_dir()]
    if manifests:
        times["scaffold"] = max(m.stat().st_mtime for m in manifests)
        src_mtime = _newest_source_mtime(root)
        if src_mtime:
            times["build"] = src_mtime

    detected = [p for p in PHASE_ORDER if p in times]
    review = docs / "review.md"
    iterating = review.exists() and "Resolved This Session" in review.read_text(errors="ignore")

    override_file = root / ".brain-phase"
    if override_file.exists():
        ph = override_file.read_text().strip()
        phase = ph if ph in PHASE_ORDER else (detected[-1] if detected else "brainstorm")
        return {"phase": phase, "detected": detected, "iterating": iterating, "override": True}

    # Column = most-recently-active phase; badges (detected) = all phases reached.
    phase = max(times, key=times.get) if times else "brainstorm"
    return {"phase": phase, "detected": detected, "iterating": iterating, "override": False}


def _project_roots() -> list[tuple[str, Path]]:
    roots: list[tuple[str, Path]] = []
    if PROJECTS_REGISTRY.exists():
        try:
            for e in json.loads(PROJECTS_REGISTRY.read_text()):
                roots.append((e["name"], Path(e["root_path"]).expanduser()))
        except Exception:
            pass
    if not roots:
        # Default: sibling dirs that use the brain workflow (have docs/plan|brainstorm).
        for d in sorted(BRAIN_DIR.parent.iterdir()):
            if d.is_dir() and ((d / "docs" / "plan.md").exists() or (d / "docs" / "brainstorm.md").exists()):
                roots.append((d.name, d))
        if not any(r[1] == BRAIN_DIR for r in roots):
            roots.append((BRAIN_DIR.name, BRAIN_DIR))
    return roots


def read_pipeline() -> dict:
    projects = []
    for name, root in _project_roots():
        try:
            projects.append({"name": name, **_detect_phase(root)})
        except Exception:
            pass
    return {"columns": PHASE_ORDER, "projects": projects}


def read_health() -> dict:
    mcps = []
    try:
        import json
        cfg = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
        for name in sorted((cfg.get("mcpServers") or {}).keys()):
            env = MCP_TOKEN_ENV.get(name, "unknown")
            mcps.append({
                "name": name,
                "needs_token": bool(env),
                "token_set": (env is None) or bool(os.environ.get(env or "", "")),
            })
    except Exception:
        pass
    return {"mcps": mcps}
