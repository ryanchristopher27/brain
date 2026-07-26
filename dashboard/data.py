"""Read-only data sources for the dashboard panels (D3).

Pure functions over the filesystem / launchctl so they can be unit-tested without a server:
- read_agents()   — persona roster from agents/
- read_jobs()     — background run history from ~/.claude/brain-bg-logs/
- read_schedule() — launchd jobs (loaded) + installable templates
- read_health()   — configured MCP servers + whether their tokens are set
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent
BG_LOG_DIR = Path.home() / ".claude" / "brain-bg-logs"
SETTINGS = Path.home() / ".claude" / "settings.json"

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
