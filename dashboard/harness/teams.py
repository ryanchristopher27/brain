"""Team templates (H7) — one-click teams from `brain/agents/teams/<name>.json`.

A template lists members, each either taken from the library (`"from": "workflow/<name>"`, or
`"expert"` for the project's expert, generated if it has none) or defined inline (persona, model,
role). Starting a team creates every member as a live agent named `<prefix>-<as>`, tagged with the
team, and sends the lead an optional kickoff message. Roles talk about teammates by their short
names ("send builder…"), so each brief gets a roster line mapping short names to real ones.

Inputs a template can ask for: scope (the builder's folder), test_command (pre-approved for the
builder and reviewer, and named in their briefs), task (tracker id), question (free text).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .. import data
from . import library
from .runtime import NAME_RE, Harness, HarnessError

TEAMS_DIR = data.BRAIN_DIR / "agents" / "teams"
INPUTS = ("scope", "test_command", "task", "question")


def list_templates() -> list[dict]:
    out = []
    for f in sorted(TEAMS_DIR.glob("*.json")) if TEAMS_DIR.is_dir() else []:
        try:
            t = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        out.append({k: t.get(k) for k in ("name", "order", "label", "description", "inputs", "kickoff")} |
                   {"members": [{"as": m["as"], "lead": bool(m.get("lead")), "from": m.get("from")} for m in t["members"]]})
    return sorted(out, key=lambda t: (t.get("order") or 99, t["name"]))


def _template(name: str) -> dict:
    if not NAME_RE.match(name or ""):
        raise HarnessError("unknown team template", 404)
    f = TEAMS_DIR / f"{name}.json"
    if not f.exists():
        raise HarnessError("unknown team template", 404)
    return json.loads(f.read_text())


def _member_def(m: dict, project: str, root: Path, personas: set[str]) -> dict:
    src = m.get("from")
    if src == "expert":
        experts = [d for d in library.list_library([(project, root)]) if d["kind"] == "expert"]
        return experts[0] if experts else library.seed_expert(project, root, personas)
    if src:
        kind, _, name = src.partition("/")
        if kind != "workflow":
            raise HarnessError(f"template member {m['as']}: 'from' must be workflow/<name> or expert")
        return library.get("workflow", None, None, name)
    return library.clean({"name": re.sub(r"[^a-z0-9-]", "", m["as"]), "description": "", "persona": m["persona"],
                          "model": m["model"], "scope": m.get("scope", "."), "daily_usd": m.get("daily_usd", 2),
                          "role": m["role"]}, personas)


async def start(h: Harness, template: str, project: str, root: Path, personas: set[str], prefix: str = "",
                inputs: dict | None = None) -> dict:
    t = _template(template)
    inputs = {k: str(v).strip() for k, v in (inputs or {}).items() if k in INPUTS and v is not None and str(v).strip()}
    prefix = (prefix or re.sub(r"[^a-z0-9]+", "-", project.lower()).strip("-")[:12]).strip("-")
    if not prefix or not prefix[0].isalpha():
        prefix = "t" + prefix
    names = {m["as"]: f"{prefix}-{m['as']}" for m in t["members"]}
    for n in names.values():
        if not NAME_RE.match(n):
            raise HarnessError(f"'{n}' isn't a valid agent name; use a shorter prefix")
        if any(a["name"] == n for a in h.list()):
            raise HarnessError(f"an agent named {n} already exists; pick another prefix", 409)
    team = f"{prefix}:{template}"
    roster = "On this team: " + ", ".join(f"'{short}' is {real}" for short, real in names.items()) + \
             ". Use the real names with send_message."
    test = inputs.get("test_command")
    created: list[str] = []
    try:
        for m in t["members"]:
            d = _member_def(m, project, root, personas)
            args = library.to_agent(d)
            extra = [m.get("extra", ""), roster]
            if m.get("scope") == "ask":
                args["scope"] = [s.strip() for s in inputs.get("scope", ".").split(",") if s.strip()] or ["."]
            always = None
            if test and d["persona"] in ("builder", "reviewer"):
                always = [test]
                extra.append(f"Run the tests with exactly `{test}` (pre-approved, so it runs without asking).")
            args["brief"] = "\n\n".join(x for x in [args["brief"], *extra] if x)[:2000]
            await h.create(names[m["as"]], project=project, always=always, team=team, **args)
            created.append(names[m["as"]])
    except Exception:
        for n in created:  # all or nothing: don't leave half a team behind
            await h.delete(n)
        raise
    lead = next((m for m in t["members"] if m.get("lead")), t["members"][0])
    kickoff = t.get("kickoff") or ""
    sent = rec = None
    if kickoff and all(f"{{{k}}}" not in kickoff or k in inputs for k in INPUTS):
        sent = kickoff.format(**{k: inputs.get(k, "") for k in INPUTS})
        rec = await h.send(names[lead["as"]], sent)
    return {"team": team, "agents": [names[m["as"]] for m in t["members"]], "lead": names[lead["as"]], "kickoff": sent,
            "message": {"id": rec["id"], "thread": rec["thread"]} if rec else None}


async def remove(h: Harness, team: str) -> int:
    members = [a["name"] for a in h.list() if a.get("team") == team]
    if not members:
        raise HarnessError("no such team", 404)
    for n in members:
        await h.delete(n)
    return len(members)
