"""Read-only, best-effort "how is the app doing" status for one project — the data
behind the dev dashboard's Hosting / Traffic / Database / Repo / Uptime cards.

Every source is optional and fails soft: no token / no network / an API error all
render as a clean `{"configured": False, "reason": "...", "setup": "..."}` (or, for repo/
tracker which need no credentials, just an empty result) — never a 500. Nothing here
ever logs or returns a secret value; collectors look up tokens via `secrets_store.get`
and use them only as an Authorization header on an outbound request.

Remote calls (Vercel, Supabase, uptime) are cached for CACHE_TTL seconds so repeated
dashboard loads don't hammer external APIs or need a token round-trip every time.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

from . import secrets_store

CACHE_TTL = 120  # seconds
_cache: dict[str, tuple[float, dict]] = {}


async def _cached(key: str, ttl: float, fetch) -> dict:
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = await fetch()
    _cache[key] = (now, value)
    return value


def clear_cache() -> None:
    """Test/dev helper — drop all cached status results."""
    _cache.clear()


# ── Git ──────────────────────────────────────────────────────────────────────
def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def git_status(root: Path) -> dict:
    """Branch, last commits, uncommitted count, ahead/behind the upstream — no network."""
    root = Path(root)
    if not (root / ".git").exists():
        return {"configured": False, "reason": "not a git repository"}
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD") or ""
    log = _git(root, "log", "-5", "--pretty=%h %ad %s", "--date=short") or ""
    commits = [line for line in log.splitlines() if line.strip()]
    status_porcelain = _git(root, "status", "--porcelain") or ""
    uncommitted = len([l for l in status_porcelain.splitlines() if l.strip()])
    ahead = behind = None
    counts = _git(root, "rev-list", "--left-right", "--count", "@{u}...HEAD")
    if counts:
        parts = counts.split()
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            behind, ahead = int(parts[0]), int(parts[1])
    return {
        "configured": True, "branch": branch, "commits": commits,
        "uncommitted": uncommitted, "ahead": ahead, "behind": behind,
        "has_upstream": ahead is not None,
    }


# ── Tracker (reuses dashboard.tracker) ──────────────────────────────────────
def tracker_status(root: Path) -> dict:
    from . import tracker
    tasks = tracker.list_tasks(Path(root))
    by_status: dict[str, int] = {s: 0 for s in tracker.STATUSES}
    for t in tasks:
        by_status[t.get("status", "backlog")] = by_status.get(t.get("status", "backlog"), 0) + 1
    in_review = [t for t in tasks if t.get("status") == "review"]
    return {"configured": True, "by_status": by_status, "total": len(tasks),
            "in_review": [{"id": t["id"], "title": t["title"]} for t in in_review]}


# ── Vercel ───────────────────────────────────────────────────────────────────
VERCEL_TOKEN_SETUP = "Create a token at https://vercel.com/account/tokens (Vercel tokens aren't read-only: scope it to your team and give it an expiry) and set VERCEL_TOKEN (env var) or add it to ~/.claude/brain-dashboard/secrets.json"


async def vercel_status(project_slug: str, team_id: str | None = None) -> dict:
    token = secrets_store.get("VERCEL_TOKEN")
    if not token:
        return {"configured": False, "reason": "no VERCEL_TOKEN", "setup": VERCEL_TOKEN_SETUP}

    async def fetch():
        params = {"projectId": project_slug, "limit": 1, "target": "production"}
        if team_id:
            params["teamId"] = team_id
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get("https://api.vercel.com/v6/deployments",
                                     headers={"Authorization": f"Bearer {token}"}, params=params)
            if r.status_code != 200:
                return {"configured": True, "ok": False, "error": f"vercel api {r.status_code}"}
            deployments = r.json().get("deployments", [])
            if not deployments:
                return {"configured": True, "ok": True, "deployment": None}
            d = deployments[0]
            return {"configured": True, "ok": True, "deployment": {
                "state": d.get("state") or d.get("readyState"),
                "commit": (d.get("meta") or {}).get("githubCommitSha", "")[:7],
                "created": d.get("createdAt"),
                "url": d.get("url"),
            }}
        except Exception as e:
            return {"configured": True, "ok": False, "error": str(e)}

    return await _cached(f"vercel:{project_slug}", CACHE_TTL, fetch)


# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_TOKEN_SETUP = "Create an access token at https://supabase.com/dashboard/account/tokens (it has full access to your Supabase account — keep it local, give it an expiry) and set SUPABASE_ACCESS_TOKEN (env var) or add it to ~/.claude/brain-dashboard/secrets.json"


async def supabase_status(project_ref: str) -> dict:
    token = secrets_store.get("SUPABASE_ACCESS_TOKEN")
    if not token:
        return {"configured": False, "reason": "no SUPABASE_ACCESS_TOKEN", "setup": SUPABASE_TOKEN_SETUP}

    async def fetch():
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"https://api.supabase.com/v1/projects/{project_ref}",
                                     headers={"Authorization": f"Bearer {token}"})
            if r.status_code != 200:
                return {"configured": True, "ok": False, "error": f"supabase api {r.status_code}"}
            doc = r.json()
            return {"configured": True, "ok": True, "status": doc.get("status"),
                    "region": doc.get("region"), "name": doc.get("name")}
        except Exception as e:
            return {"configured": True, "ok": False, "error": str(e)}

    return await _cached(f"supabase:{project_ref}", CACHE_TTL, fetch)


# ── Uptime ───────────────────────────────────────────────────────────────────
async def uptime_check(url: str) -> dict:
    """Unauthenticated GET to a public production URL — no token needed or used."""
    async def fetch():
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                r = await client.get(url)
            elapsed_ms = round((time.monotonic() - start) * 1000)
            return {"configured": True, "ok": r.status_code < 400, "status_code": r.status_code,
                    "elapsed_ms": elapsed_ms}
        except Exception as e:
            elapsed_ms = round((time.monotonic() - start) * 1000)
            return {"configured": True, "ok": False, "error": str(e), "elapsed_ms": elapsed_ms}

    return await _cached(f"uptime:{url}", CACHE_TTL, fetch)
