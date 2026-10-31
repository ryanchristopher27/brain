"""Harness runtime (H1) — named, long-lived Claude Code agents on the Python Agent SDK.

Each agent is a ClaudeSDKClient that is connected on demand, handles its inbox one turn at a
time, closes after IDLE_SECS without work, and resumes by session id on the next message (H0
verified resume keeps full context). Model settings are per agent and editable live: pinned
(one model) or auto (tier map with floor/ceiling; per-turn classification arrives in H2).

Safety baseline (H3 extends it with Hub approvals and scope locks): a PreToolUse hook — not an
allow list, which H0 showed can shadow can_use_tool — permits read tools, read-only git, and
writes inside the agent's scope folders; everything else is denied with a reason the agent sees.
Sessions never get ANTHROPIC_API_KEY (keeps usage on the claude.ai subscription) and run with the
model-router mod disabled (H0: it overrode pinned models).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, HookMatcher, ResultMessage,
                              TextBlock, ToolUseBlock)

from . import store

IDLE_SECS = 600
TEXT_MAX = 20_000
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
MODEL_RE = re.compile(r"^(opus|sonnet|haiku|claude-[a-z0-9.-]{3,60})$")
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
TIERS = ["light", "standard", "deep"]
DEFAULT_TIERS = {"light": "claude-haiku-5-5", "standard": "claude-sonnet-5-5", "deep": "claude-opus-5-5"}
PERSONA_MODEL = {"scout": "claude-haiku-5-5", "operator": "claude-haiku-5-5"}  # others: standard

READ_TOOLS = {"Read", "Grep", "Glob", "LS", "WebFetch", "WebSearch", "TodoWrite", "NotebookRead"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
GIT_READ_RE = re.compile(r"^\s*git\s+(log|diff|show|status|branch|blame)\b[^;&|`$<>]*$")
SESSION_SETTINGS = json.dumps({"enabledPlugins": {"model-router@brain": False}})


class HarnessError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# ── model settings ──────────────────────────────────────────────────────────────────────────
def default_model(persona: str) -> dict:
    return {"mode": "pinned", "model": PERSONA_MODEL.get(persona, DEFAULT_TIERS["standard"]), "effort": None,
            "tiers": dict(DEFAULT_TIERS), "floor": None, "ceiling": None}


def clean_model(raw: dict, base: dict) -> dict:
    """Validate a (partial) model-settings update against the current settings."""
    m = {**base, **{k: v for k, v in raw.items() if k in base}}
    if m["mode"] not in ("pinned", "auto"):
        raise HarnessError("model mode must be pinned or auto")
    if not isinstance(m["model"], str) or not MODEL_RE.match(m["model"]):
        raise HarnessError("unknown model")
    if m["effort"] is not None and m["effort"] not in EFFORTS:
        raise HarnessError(f"effort must be one of {sorted(EFFORTS)}")
    if not isinstance(m["tiers"], dict) or set(m["tiers"]) != set(TIERS) or \
            not all(isinstance(v, str) and MODEL_RE.match(v) for v in m["tiers"].values()):
        raise HarnessError("tiers must map light/standard/deep to models")
    for k in ("floor", "ceiling"):
        if m[k] is not None and m[k] not in TIERS:
            raise HarnessError(f"{k} must be one of {TIERS}")
    if m["floor"] and m["ceiling"] and TIERS.index(m["floor"]) > TIERS.index(m["ceiling"]):
        raise HarnessError("floor is above ceiling")
    return m


def resolve_model(m: dict, tier: str = "standard") -> tuple[str, str]:
    """(model, tier) for a turn. Auto clamps the requested tier into [floor, ceiling]."""
    if m["mode"] == "pinned":
        return m["model"], "pinned"
    i = TIERS.index(tier)
    if m["floor"]:
        i = max(i, TIERS.index(m["floor"]))
    if m["ceiling"]:
        i = min(i, TIERS.index(m["ceiling"]))
    return m["tiers"][TIERS[i]], TIERS[i]


# ── tool gate ───────────────────────────────────────────────────────────────────────────────
def gate_decision(tool: str, inp: dict, cwd: str, scope: list[str]) -> tuple[bool, str]:
    if tool in READ_TOOLS or tool.startswith("mcp__bus__"):
        return True, ""
    if tool in WRITE_TOOLS:
        raw = inp.get("file_path") or inp.get("notebook_path") or ""
        target = (Path(cwd) / raw).resolve() if raw else None
        if target and any(target.is_relative_to(Path(s)) for s in scope):
            return True, ""
        return False, f"{raw or 'that path'} is outside your scope ({', '.join(scope)})."
    if tool == "Bash" and GIT_READ_RE.match(inp.get("command", "")):
        return True, ""
    return False, f"{tool} isn't available to harness agents yet (approvals arrive in H3)."


def make_gate(cwd: str, scope: list[str], on_deny: Callable[[str, str], None]):
    async def gate(input_data: dict, tool_use_id: str | None, context: Any) -> dict:
        tool, inp = input_data.get("tool_name", ""), input_data.get("tool_input", {}) or {}
        ok, reason = gate_decision(tool, inp, cwd, scope)
        if not ok:
            on_deny(tool, reason)
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                       "permissionDecision": "allow" if ok else "deny",
                                       "permissionDecisionReason": reason or "within harness policy"}}
    return gate


# ── sessions ────────────────────────────────────────────────────────────────────────────────
class Session:
    def __init__(self, h: "Harness", name: str):
        self.h, self.name = h, name
        self.client: ClaudeSDKClient | None = None
        self.model: str | None = None      # model the live client is on
        self.cost_seen = 0.0               # cumulative cost reported by the live client
        self.inbox: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self.unpaused = asyncio.Event()
        self.busy = False
        self.worker: asyncio.Task | None = None
        self.idle: asyncio.TimerHandle | None = None

    def state(self, a: dict) -> str:
        if a["paused"]:
            return "paused"
        if self.busy or not self.inbox.empty():
            return "busy"
        return "live" if self.client else ("asleep" if a["session_id"] else "new")

    def start(self, paused: bool) -> None:
        (self.unpaused.clear if paused else self.unpaused.set)()
        if not self.worker or self.worker.done():
            self.worker = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            sender, text = await self.inbox.get()
            self.busy = True  # holding a message counts as work, even while paused
            await self.unpaused.wait()
            if self.idle:
                self.idle.cancel()
                self.idle = None
            await self.h._changed(self.name)
            try:
                await self._turn(sender, text)
            except Exception as e:  # a failed turn is logged; the agent stays usable
                await self.h._log(self.name, "system", "harness", f"turn failed: {type(e).__name__}: {e}")
                await self.close()
            finally:
                self.busy = False
                if self.inbox.empty() and self.client:
                    self.idle = asyncio.get_running_loop().call_later(
                        self.h.idle_secs, lambda: asyncio.ensure_future(self.close()))
                await self.h._changed(self.name)

    async def _connect(self, a: dict, model: str) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        cwd = a["scope_root"]
        identity = (f"You are '{a['name']}', a long-lived agent on the user's brain team, working in {cwd}. "
                    f"You may write only inside: {', '.join(a['scope'])}. "
                    "Messages from teammates arrive prefixed with [from <name>]; messages from the user are unprefixed.")
        if a["brief"]:
            identity += f"\nYour role: {a['brief']}"
        opts = ClaudeAgentOptions(
            cwd=cwd, model=model, effort=a["model"]["effort"], env=env, settings=SESSION_SETTINGS,
            extra_args={"agent": a["persona"]}, resume=a["session_id"], permission_mode="default",
            system_prompt={"type": "preset", "preset": "claude_code", "append": identity},
            hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[
                make_gate(cwd, a["scope"], lambda t, r: self.h._spawn_log(self.name, "system", "gate",
                                                                            f"denied {t}: {r}"))])]})
        self.client = self.h.client_factory(opts)
        await self.client.connect()
        self.model, self.cost_seen = model, 0.0

    async def _turn(self, sender: str, text: str) -> None:
        a = self.h._agent(self.name)
        model, _tier = resolve_model(a["model"])
        if self.client is None:
            await self._connect(a, model)
        elif model != self.model:
            await self.client.set_model(model)
            self.model = model
        prompt = text if sender == "you" else f"[from {sender}]\n{text}"
        await self.client.query(prompt)
        reply, seen_model = [], model
        async for m in self.client.receive_response():
            if isinstance(m, AssistantMessage):
                seen_model = m.model or seen_model
                for b in m.content:
                    if isinstance(b, TextBlock) and b.text.strip():
                        reply.append(b.text)
                    elif isinstance(b, ToolUseBlock):
                        await self.h._log(self.name, "tool", self.name, _tool_summary(b), seen_model)
            elif isinstance(m, ResultMessage):
                cost = max(0.0, (m.total_cost_usd or 0.0) - self.cost_seen)
                self.cost_seen = m.total_cost_usd or self.cost_seen
                store.add_usage(self.h.conn, self.name, cost)
                if m.session_id and m.session_id != a["session_id"]:
                    store.update_agent(self.h.conn, self.name, session_id=m.session_id)
                if m.is_error:
                    await self.h._log(self.name, "system", "harness", f"turn ended: {m.subtype}")
                await self.h._log(self.name, "assistant", self.name, "\n\n".join(reply) or "(no reply)",
                                  seen_model, cost)

    async def close(self) -> None:
        if self.idle:
            self.idle.cancel()
            self.idle = None
        client, self.client, self.model = self.client, None, None
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
        if self.name in self.h.sessions:
            await self.h._changed(self.name)

    async def shutdown(self) -> None:
        if self.worker:
            self.worker.cancel()
        await self.close()


def _tool_summary(b: ToolUseBlock) -> str:
    inp = b.input or {}
    detail = inp.get("file_path") or inp.get("command") or inp.get("pattern") or inp.get("url") or ""
    return f"{b.name} {str(detail)[:160]}".strip()


class Harness:
    def __init__(self, conn, broadcast: Callable[[dict], Awaitable[None]],
                 project_root: Callable[[str], Path | None], personas: Callable[[], set[str]],
                 client_factory=ClaudeSDKClient, idle_secs: float = IDLE_SECS):
        self.conn, self.broadcast = conn, broadcast
        self.project_root, self.personas = project_root, personas
        self.client_factory, self.idle_secs = client_factory, idle_secs
        self.sessions: dict[str, Session] = {}

    # views
    def _agent(self, name: str) -> dict:
        a = store.get_agent(self.conn, name)
        if a is None:
            raise HarnessError("unknown agent", 404)
        root = self.project_root(a["project"])
        a["scope_root"] = str(root) if root else a["scope"][0]
        return a

    def view(self, name: str) -> dict:
        a = self._agent(name)
        s = self.sessions.get(name)
        model, tier = resolve_model(a["model"])
        return {**{k: a[k] for k in ("name", "persona", "project", "brief", "scope", "model", "paused",
                                     "usage_usd", "session_id")},
                "state": s.state(a) if s else ("paused" if a["paused"] else ("asleep" if a["session_id"] else "new")),
                "current_model": (s.model if s and s.model else model), "tier": tier,
                "queued": s.inbox.qsize() if s else 0}

    def list(self) -> list[dict]:
        return [self.view(a["name"]) for a in store.list_agents(self.conn)]

    # roster
    def _clean_scope(self, project: str, scope: list[str] | None) -> list[str]:
        root = self.project_root(project)
        if root is None:
            raise HarnessError("unknown project")
        root = root.resolve()
        out = []
        for s in scope or [str(root)]:
            p = (root / s).resolve()
            if not p.is_relative_to(root):
                raise HarnessError(f"scope {s} is outside the project")
            out.append(str(p))
        return out

    async def create(self, name: str, persona: str, project: str, brief: str = "",
                     scope: list[str] | None = None, model: dict | None = None) -> dict:
        if not NAME_RE.match(name or ""):
            raise HarnessError("name: lowercase letters, digits, dashes (2-32), starting with a letter")
        if store.get_agent(self.conn, name):
            raise HarnessError("an agent with that name exists", 409)
        if persona not in self.personas():
            raise HarnessError("unknown persona")
        if len(brief) > 2000:
            raise HarnessError("brief is too long")
        m = clean_model(model or {}, default_model(persona))
        store.create_agent(self.conn, name, persona, project, brief, self._clean_scope(project, scope), m)
        await self._changed(name)
        return self.view(name)

    async def update(self, name: str, brief: str | None = None, scope: list[str] | None = None,
                     model: dict | None = None) -> dict:
        a = self._agent(name)
        fields: dict = {}
        if brief is not None:
            if len(brief) > 2000:
                raise HarnessError("brief is too long")
            fields["brief"] = brief
        if scope is not None:
            fields["scope"] = self._clean_scope(a["project"], scope)
        if model is not None:
            fields["model"] = clean_model(model, a["model"])
        store.update_agent(self.conn, name, **fields)
        s = self.sessions.get(name)
        if s and ("brief" in fields or "scope" in fields or
                  (model and model.get("effort", a["model"]["effort"]) != a["model"]["effort"])):
            await s.close()  # identity, scope and effort are fixed per connection: reconnect (resume) next turn
        await self._changed(name)
        return self.view(name)

    async def delete(self, name: str) -> None:
        self._agent(name)
        s = self.sessions.pop(name, None)
        if s:
            await s.shutdown()
        store.delete_agent(self.conn, name)
        await self.broadcast({"type": "harness", "event": "deleted", "name": name})

    # conversation
    def _session(self, name: str) -> Session:
        a = self._agent(name)
        s = self.sessions.get(name)
        if s is None:
            s = self.sessions[name] = Session(self, name)
        s.start(a["paused"])
        return s

    async def send(self, name: str, text: str, sender: str = "you") -> dict:
        text = (text or "").strip()
        if not text or len(text) > TEXT_MAX:
            raise HarnessError(f"message must be 1-{TEXT_MAX} characters")
        s = self._session(name)
        rec = await self._log(name, "user", sender, text)
        s.inbox.put_nowait((sender, text))
        await self._changed(name)
        return rec

    async def pause(self, name: str) -> dict:
        store.update_agent(self.conn, name, paused=True)
        if name in self.sessions:
            self.sessions[name].unpaused.clear()
        await self._changed(name)
        return self.view(name)

    async def resume(self, name: str) -> dict:
        store.update_agent(self.conn, name, paused=False)
        self._session(name)
        await self._changed(name)
        return self.view(name)

    async def stop(self, name: str) -> dict:
        """Close the process now; context is kept and the next message resumes it."""
        if name in self.sessions:
            await self.sessions[name].close()
        return self.view(name)

    async def stop_all(self) -> None:
        for s in list(self.sessions.values()):
            await s.shutdown()
        self.sessions.clear()

    # events
    async def _log(self, name: str, role: str, sender: str, text: str, model: str | None = None,
                   cost: float | None = None) -> dict:
        rec = store.log_message(self.conn, name, role, sender, text, model, cost)
        await self.broadcast({"type": "harness", "event": "message", "message": rec})
        return rec

    def _spawn_log(self, *args) -> None:
        asyncio.ensure_future(self._log(*args))

    async def _changed(self, name: str) -> None:
        try:
            await self.broadcast({"type": "harness", "event": "agent", "agent": self.view(name)})
        except HarnessError:
            pass
