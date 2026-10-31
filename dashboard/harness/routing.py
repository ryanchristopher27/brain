"""Auto model routing for harness agents (H2) — the model-router mod's rules, read from its
`hooks/rules.ts` so both route the same way.

Unlike the mod, an undecided message goes to `standard` rather than a classifier call: in the
harness a classifier would mean another Claude Code session start per turn (H1 measured those
at several cents), which costs more than it saves.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

RULES_TS = Path(__file__).resolve().parents[2] / "mods" / "model-router" / "hooks" / "rules.ts"


def _re(r: dict) -> re.Pattern:
    return re.compile(r["source"], re.I if "i" in r["flags"] else 0)


@lru_cache(maxsize=1)
def rules() -> dict:
    src = RULES_TS.read_text()
    d = json.loads(src[src.index("\nexport default ") + len("\nexport default "):])
    return {"override": _re(d["override"]), "override_tier": d["override_tier"],
            "deep_command": _re(d["deep_command"]), "light_command": _re(d["light_command"]),
            "deep": _re(d["deep"]), "light": [(_re(r), r["why"]) for r in d["light"]],
            "light_max": d["light_max_chars"], "continue": _re(d["continue"])}


def decide(text: str, previous: str = "standard") -> tuple[str, str, str]:
    """(tier, why, text) — text has any !override prefix removed."""
    r = rules()
    if m := r["override"].match(text):
        k = m.group(1).lower()
        return r["override_tier"].get(k, "standard"), f"!{k}", text[m.end():]
    if r["deep_command"].match(text):
        return "deep", "command", text
    if r["light_command"].match(text):
        return "light", "command", text
    if r["continue"].match(text):
        return previous, "continues last request", text
    if m := r["deep"].search(text):
        return "deep", m.group(0).lower(), text
    if len(text) <= r["light_max"]:
        for rx, why in r["light"]:
            if rx.search(text):
                return "light", why, text
    return "standard", "default", text
