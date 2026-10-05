"""Per-project test accounts for the dev dashboard's "Test accounts" panel.

Declared by the project in `<project_root>/.brain/test-users.json` (non-secret: who each
test user is, what they have, how to seed them):

    {
      "summary": "free text",
      "users": [{"username": "ava.plans", "email": "ava@…", "has": "…", "friends": "…"}],
      "commands": {"seed": "…", "teardown": "…"},
      "credentials_file": "scripts/test-users/.credentials.json"   # optional, git-ignored
    }

`load()` never returns passwords — only whether the credentials file exists and when it
was seeded. `credentials()` reads passwords for the separate, explicitly-requested
endpoint, and only from a file inside the project root.

Stdlib-only, pure over the filesystem so it's unit-testable without a server.
"""
from __future__ import annotations

import json
from pathlib import Path

DECL_SUBPATH = ".brain/test-users.json"


def _creds_path(root: Path, decl: dict) -> Path | None:
    rel = decl.get("credentials_file")
    if not isinstance(rel, str) or not rel:
        return None
    p = (root / rel).resolve()
    try:
        p.relative_to(root.resolve())   # stays inside the project (no ../ escapes)
    except ValueError:
        return None
    return p


def _read_json(p: Path):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def load(root: Path) -> dict:
    decl = _read_json(Path(root) / DECL_SUBPATH)
    if not isinstance(decl, dict):
        return {"declared": False}
    users = [
        {k: str(u.get(k, "")) for k in ("username", "email", "has", "friends")}
        for u in decl.get("users") or [] if isinstance(u, dict)
    ]
    cp = _creds_path(Path(root), decl)
    creds = _read_json(cp) if cp and cp.is_file() else None
    return {
        "declared": True,
        "summary": str(decl.get("summary", "")),
        "users": users,
        "commands": {k: str(v) for k, v in (decl.get("commands") or {}).items()},
        "credentials": {
            "file": decl.get("credentials_file") if cp else None,
            "exists": bool(creds),
            "seeded_at": (creds or {}).get("seededAt") if isinstance(creds, dict) else None,
        },
    }


def credentials(root: Path) -> list[dict]:
    """[{email, password}] from the project's git-ignored credentials file, or []."""
    decl = _read_json(Path(root) / DECL_SUBPATH)
    if not isinstance(decl, dict):
        return []
    cp = _creds_path(Path(root), decl)
    data = _read_json(cp) if cp and cp.is_file() else None
    users = (data or {}).get("users") if isinstance(data, dict) else None
    return [{"email": str(u.get("email", "")), "password": str(u.get("password", ""))}
            for u in users or [] if isinstance(u, dict)]
