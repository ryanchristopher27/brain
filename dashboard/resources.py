"""Per-project external resources — the declared list of services a project depends on
(hosting, database, auth, payments, data/API, assets, analytics, monitoring, source,
package registry…), read by the dev dashboard's Resources panel.

Source of truth per project: `<project_root>/.brain/resources.json` (stdlib JSON — no
YAML dependency installed in this repo's venv). If a project hasn't adopted that file yet,
fall back to a brain-side seed at `dashboard/seed/<project>.resources.json`, so a project
can be documented here first and migrated into its own repo later.

A resource entry:
    {
      "name": "Vercel",
      "category": "hosting",               # see CATEGORIES
      "urls": {"console": "...", "docs": "..."},
      "purpose": "free text",
      "plan": "free text — plan/cost/limits, or 'unverified'",
      "env_vars": ["VITE_SUPABASE_URL", ...],   # names only, never values
      "status_check": {"type": "none|http|vercel|supabase", "config": {...}} ,
      "verified": true|false,               # confirmed against the project's own code
      "notes": "optional free text"
    }

Stdlib-only, pure over the filesystem so it's unit-testable without a server.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CATEGORIES = (
    "hosting", "database", "auth", "payments", "data-api", "assets",
    "analytics", "monitoring", "source", "package-registry", "bot-protection",
    "ai", "other",
)
STATUS_CHECK_TYPES = ("none", "http", "vercel", "supabase")
RESOURCES_SUBPATH = ".brain/resources.json"
SEED_DIR = Path(__file__).resolve().parent / "seed"

REQUIRED_FIELDS = ("name", "category", "purpose")


class ResourcesError(Exception):
    """Invalid resources file (bad schema)."""


def _normalize(entry: dict) -> dict:
    return {
        "name": entry.get("name", ""),
        "category": entry.get("category", "other"),
        "urls": {k: v for k, v in (entry.get("urls") or {}).items() if v},
        "purpose": entry.get("purpose", ""),
        "plan": entry.get("plan", ""),
        "env_vars": list(entry.get("env_vars") or []),
        "status_check": entry.get("status_check") or {"type": "none", "config": {}},
        "verified": bool(entry.get("verified", False)),
        "notes": entry.get("notes", ""),
    }


def validate(doc: dict) -> list[str]:
    """Return a list of schema problems (empty = valid). Never raises."""
    problems = []
    if not isinstance(doc, dict):
        return ["document must be a JSON object"]
    resources = doc.get("resources")
    if not isinstance(resources, list):
        return ["'resources' must be a list"]
    for i, r in enumerate(resources):
        if not isinstance(r, dict):
            problems.append(f"resources[{i}] must be an object")
            continue
        for f in REQUIRED_FIELDS:
            if not r.get(f):
                problems.append(f"resources[{i}] missing required field {f!r}")
        cat = r.get("category")
        if cat and cat not in CATEGORIES:
            problems.append(f"resources[{i}] unknown category {cat!r} (expected one of {CATEGORIES})")
        sc = r.get("status_check")
        if sc and sc.get("type") not in STATUS_CHECK_TYPES:
            problems.append(f"resources[{i}] unknown status_check.type {sc.get('type')!r}")
    return problems


def _resources_file(root: Path) -> Path | None:
    p = Path(root) / RESOURCES_SUBPATH
    return p if p.exists() else None


def _seed_file(project_name: str) -> Path | None:
    p = SEED_DIR / f"{project_name}.resources.json"
    return p if p.exists() else None


def load(root: Path, project_name: str | None = None) -> dict:
    """Load a project's resources: its own `.brain/resources.json` first, else brain's
    seed file for that project name. Returns {"source": "project"|"seed"|"none",
    "problems": [...], "resources": [...]}."""
    name = project_name or Path(root).name
    path = _resources_file(root)
    source = "project"
    if path is None:
        path = _seed_file(name)
        source = "seed"
    if path is None:
        return {"source": "none", "path": None, "problems": [], "resources": []}
    try:
        doc = json.loads(path.read_text())
    except Exception as e:
        return {"source": source, "path": str(path), "problems": [f"invalid JSON: {e}"], "resources": []}
    problems = validate(doc)
    resources = [_normalize(r) for r in doc.get("resources", [])] if isinstance(doc.get("resources"), list) else []
    return {"source": source, "path": str(path), "problems": problems, "resources": resources}


# ── seed generator ────────────────────────────────────────────────────────────
# Proposes candidate resource entries by scanning a project directory for known
# signals (package.json deps, .env*.example var names, vercel.json, known hostnames
# in source). Output is a *proposal* — always human-reviewed before being trusted.

_KNOWN_HOSTS = {
    "vercel.app": ("Vercel", "hosting"),
    "supabase.co": ("Supabase", "database"),
    "supabase.com": ("Supabase", "database"),
    "api.anthropic.com": ("Anthropic", "ai"),
    "ai-gateway.vercel.sh": ("Vercel AI Gateway", "ai"),
    "nominatim.openstreetmap.org": ("Nominatim / OpenStreetMap", "data-api"),
    "api.openverse.org": ("Openverse", "assets"),
    "en.wikipedia.org": ("Wikipedia", "assets"),
    "en.wikivoyage.org": ("Wikivoyage", "data-api"),
    "open-meteo.com": ("Open-Meteo", "data-api"),
    "challenges.cloudflare.com": ("Cloudflare Turnstile", "bot-protection"),
    "ignav.com": ("Ignav", "data-api"),
}

_KNOWN_DEPS = {
    "@supabase/supabase-js": ("Supabase", "database"),
    "vercel": ("Vercel", "hosting"),
}

_ENV_NAME_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=")
_URL_RE = re.compile(r"https?://([A-Za-z0-9.\-]+)")
_SKIP_DIR = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", "venv", ".venv"}


def _scan_env_names(root: Path) -> set[str]:
    names = set()
    for p in root.rglob(".env*"):
        if any(part in _SKIP_DIR for part in p.parts):
            continue
        if p.name.endswith((".example", ".sample")) or p.name in (".env",):
            try:
                for line in p.read_text(errors="ignore").splitlines():
                    m = _ENV_NAME_RE.match(line.strip())
                    if m:
                        names.add(m.group(1))
            except Exception:
                pass
    return names


def _scan_hostnames(root: Path, max_files: int = 4000) -> set[str]:
    hosts = set()
    seen = 0
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in _SKIP_DIR for part in p.parts):
            continue
        if p.suffix not in {".js", ".mjs", ".ts", ".tsx", ".jsx", ".json"}:
            continue
        seen += 1
        if seen > max_files:
            break
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for m in _URL_RE.finditer(text):
            hosts.add(m.group(1).lower())
    return hosts


def generate_seed(root: Path) -> dict:
    """Scan a project directory and propose resource entries. Best-effort, stdlib-only;
    always returns {"resources": [...], "unmatched_env_vars": [...]} for human review —
    nothing here is written automatically."""
    root = Path(root)
    pkg = root / "package.json"
    deps: dict[str, str] = {}
    if pkg.exists():
        try:
            doc = json.loads(pkg.read_text())
            deps = {**doc.get("dependencies", {}), **doc.get("devDependencies", {})}
        except Exception:
            pass

    env_names = _scan_env_names(root)
    hostnames = _scan_hostnames(root)

    found: dict[str, dict] = {}  # name -> resource

    if (root / "vercel.json").exists() or "vercel" in deps:
        found["Vercel"] = {"name": "Vercel", "category": "hosting",
                           "urls": {"console": "https://vercel.com/dashboard"},
                           "purpose": "Hosting / deploys", "plan": "", "env_vars": [],
                           "status_check": {"type": "vercel", "config": {}}, "verified": False}

    for dep, (name, cat) in _KNOWN_DEPS.items():
        if dep in deps:
            found.setdefault(name, {"name": name, "category": cat, "urls": {}, "purpose": "",
                                     "plan": "", "env_vars": [], "status_check": {"type": "none", "config": {}},
                                     "verified": False})

    matched_env: set[str] = set()
    for host, (name, cat) in _KNOWN_HOSTS.items():
        if any(h == host or h.endswith("." + host) for h in hostnames):
            r = found.setdefault(name, {"name": name, "category": cat, "urls": {}, "purpose": "",
                                         "plan": "", "env_vars": [], "status_check": {"type": "none", "config": {}},
                                         "verified": False})
            r["verified"] = True  # found a literal reference in source

    # Attribute env var names to services by naming convention.
    for ev in sorted(env_names):
        low = ev.lower()
        target = None
        if "supabase" in low:
            target = "Supabase"
        elif "vercel" in low:
            target = "Vercel"
        elif "anthropic" in low or low.startswith("ai_"):
            target = "Anthropic"
        elif "turnstile" in low:
            target = "Cloudflare Turnstile"
        elif "ignav" in low:
            target = "Ignav"
        elif "lemonsqueezy" in low or low.startswith("ls_"):
            target = "Lemon Squeezy"
        if target:
            r = found.setdefault(target, {"name": target, "category": "other", "urls": {}, "purpose": "",
                                           "plan": "", "env_vars": [], "status_check": {"type": "none", "config": {}},
                                           "verified": False})
            r["env_vars"].append(ev)
            matched_env.add(ev)
        else:
            # Leave unmatched — surfaced for the human reviewer below.
            pass

    return {
        "resources": sorted(found.values(), key=lambda r: r["name"]),
        "unmatched_env_vars": sorted(env_names - matched_env),
    }
