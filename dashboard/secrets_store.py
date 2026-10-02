"""Read-only lookup for locally-held API tokens the dev dashboard's status collectors
need (Vercel, Supabase). Never creates, writes, or logs a token value.

Lookup order for a given name (e.g. "VERCEL_TOKEN"):
  1. environment variable of that name
  2. `~/.claude/brain-dashboard/secrets.json` — a flat {"NAME": "value"} map, mode 600

No token exists yet for this project; `get()` returning None is the expected, handled
case everywhere it's called — callers must render a "not configured" state that names
the exact env var / file key and a link to create the token, never fail or expose a value.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SECRETS_PATH = Path.home() / ".claude" / "brain-dashboard" / "secrets.json"


def get(name: str) -> str | None:
    val = os.environ.get(name)
    if val:
        return val
    try:
        if SECRETS_PATH.exists():
            doc = json.loads(SECRETS_PATH.read_text())
            v = doc.get(name)
            if v:
                return v
    except Exception:
        pass
    return None
