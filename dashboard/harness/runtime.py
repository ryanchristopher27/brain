"""Harness runtime (H1) — named, long-lived Claude Code agents on the Python Agent SDK.

Each agent is a ClaudeSDKClient that is connected on demand, handles its inbox one turn at a
time, closes after IDLE_SECS without work, and resumes by session id on the next message (H0
verified resume keeps full context). Model settings are per agent and editable live: pinned
(one model) or auto (tier map with floor/ceiling; per-turn classification arrives in H2).

Agents talk through an in-process bus (H2): `send_message` and `list_agents` tools, delivered
into the target's inbox with the sender's thread id and hop count. Limits are enforced here, not
by prompt: hop limit per hand-off chain, turn cap per thread, and a daily usage cap per agent
(also passed to the SDK as max_budget_usd so a single turn can't overrun it). Auto-mode agents
route each turn with the model-router mod's rules (routing.py).

Permission gate (H3): a PreToolUse hook — not an allow list, which H0 showed can shadow
can_use_tool — sorts every tool call three ways. Allowed: read tools, bus tools, read-only git,
writes inside the agent's scope, and commands you approved "always" for that agent. Held: writes
outside scope, other commands (git push and destructive ones flagged), any other tool — the turn
waits while the Hub shows an approval; unanswered holds expire as denied. Denied: spawning
subagents. Writer agents can't share a scope (checked when scopes are set), and a kill switch
pauses everything and denies anything waiting. Decisions go to the dashboard audit log.
Sessions never get ANTHROPIC_API_KEY (keeps usage on the claude.ai subscription) and run with the
model-router mod disabled (H0: it overrode pinned models).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any, Awaitable, Callable

from claude_agent_sdk import (AgentDefinition, AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, HookMatcher, ResultMessage,
                              TextBlock, ToolUseBlock, create_sdk_mcp_server, tool)

from .. import data, tracker
from ..process_manager import _audit
from . import routing, store

IDLE_SECS = 600
HOP_LIMIT = 8            # agent-to-agent hand-offs allowed after a user message
THREAD_TURN_CAP = 20     # agent turns allowed per thread, across all agents
DEFAULT_LIMITS = {"daily_usd": 2.0}
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
GIT_PUSH_RE = re.compile(r"\bgit\s+push\b")
DESTRUCTIVE_RE = re.compile(r"\brm\s+-\w*[rf]|\bgit\s+(reset\s+--hard|clean\s+-\w*f|checkout\s+--\s|branch\s+-D)|"
                            r"\bsudo\b|\bchmod\s+-R|\bmkfs|\bdd\s+if=|\|\s*(sh|bash|zsh)\b|\bdrop\s+(table|database)\b",
                            re.I)
DENY_TOOLS = {"Task", "Agent"}  # agents don't spawn agents in v1
HOLD_SECS = 900
SESSION_SETTINGS = json.dumps({"enabledPlugins": {"model-router@brain": False}})
BUS_TOOLS = ["mcp__bus__send_message", "mcp__bus__list_agents", "mcp__bus__read_task", "mcp__bus__post_update"]
AGENT_STATUSES = ("doing", "review")  # agents move work along; only the user closes it


def persona_agent(persona: str) -> AgentDefinition:
    """A session-local copy of a brain persona with the bus tools added to its tool list (a
    persona's `tools:` is an allowlist, so without this the agent can't reach its teammates)."""
    for sub in ("personas", "background"):
        f = data.BRAIN_DIR / "agents" / sub / f"{persona}.md"
        if f.exists():
            text = f.read_text()
            fm = data._parse_frontmatter(text)
            body = text[text.find("\n---", 3) + 4:].strip()
            tools = [t.strip() for t in fm.get("tools", "").split(",") if t.strip()]
            return AgentDefinition(description=fm.get("description", persona), prompt=body, tools=tools + BUS_TOOLS)
    raise HarnessError("unknown persona")


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


def clean_limits(raw: dict, base: dict) -> dict:
    lim = {**base, **{k: v for k, v in raw.items() if k in DEFAULT_LIMITS}}
    if not isinstance(lim["daily_usd"], (int, float)) or not 0 < lim["daily_usd"] <= 100:
        raise HarnessError("daily_usd must be between 0 and 100")
    return lim


def day_start() -> float:
    t = time.localtime()
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, -1))


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
def gate_decision(tool: str, inp: dict, cwd: str, scope: list[str],
                  always: list[str] = ()) -> tuple[str, str, str]:
    """(verdict, kind, reason) with verdict allow | hold | deny."""
    if tool in READ_TOOLS or tool.startswith("mcp__bus__"):
        return "allow", "", ""
    if tool in DENY_TOOLS:
        return "deny", "tool", "Harness agents don't start subagents; message a teammate instead."
    if tool in WRITE_TOOLS:
        raw = inp.get("file_path") or inp.get("notebook_path") or ""
        target = (Path(cwd) / raw).resolve() if raw else None
        if target and any(target.is_relative_to(Path(s)) for s in scope):
            return "allow", "", ""
        return "hold", "outside-scope write", f"{raw or 'that path'} is outside your scope ({', '.join(scope)})."
    if tool == "Bash":
        cmd = inp.get("command", "")
        if GIT_READ_RE.match(cmd) or cmd.strip() in always:
            return "allow", "", ""
        if GIT_PUSH_RE.search(cmd):
            return "hold", "git push", "Pushing needs your approval."
        if DESTRUCTIVE_RE.search(cmd):
            return "hold", "destructive command", "This command can destroy work; it needs your approval."
        return "hold", "command", "Commands need your approval."
    return "hold", "tool", f"{tool} needs your approval."


def _decision(ok: bool, reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow" if ok else "deny",
                                   "permissionDecisionReason": reason or "within harness policy"}}


# ── sessions ────────────────────────────────────────────────────────────────────────────────
class Session:
    def __init__(self, h: "Harness", name: str):
        self.h, self.name = h, name
        self.client: ClaudeSDKClient | None = None
        self.model: str | None = None      # model the live client is on
        self.cost_seen = 0.0               # cumulative cost reported by the live client
        self.inbox: asyncio.Queue[tuple[str, str, str, int]] = asyncio.Queue()  # sender, text, thread, hop
        self.held: tuple[str, str, str, int] | None = None  # a message parked by a usage cap
        self.thread, self.hop = "", 0      # what the current turn is answering (for outgoing sends)
        self.last_tier = "standard"
        self.unpaused = asyncio.Event()
        self.busy = False
        self.worker: asyncio.Task | None = None
        self.idle: asyncio.TimerHandle | None = None

    def state(self, a: dict) -> str:
        if self.name in self.h.waiting:
            return "waiting"
        if a["paused"]:
            return "paused"
        if self.busy or self.held or not self.inbox.empty():
            return "busy"
        return "live" if self.client else ("asleep" if a["session_id"] else "new")

    def start(self, paused: bool) -> None:
        (self.unpaused.clear if paused else self.unpaused.set)()
        if not self.worker or self.worker.done():
            self.worker = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            item = self.held = self.held or await self.inbox.get()  # parked here while paused
            await self.unpaused.wait()
            self.held, self.busy = None, True
            if self.idle:
                self.idle.cancel()
                self.idle = None
            sender, text, thread, hop = item
            if self.h.remaining(self.name) <= 0:
                self.held, self.busy = item, False
                await self.h._log(self.name, "system", "harness", "Daily usage cap reached. Paused; raise the cap "
                                  "or resume tomorrow to deliver the held message.", thread=thread, hop=hop)
                await self.h.pause(self.name)
                continue
            if store.thread_turns(self.h.conn, thread) >= THREAD_TURN_CAP:
                self.busy = False
                await self.h._log(self.name, "system", "harness", f"Thread turn cap ({THREAD_TURN_CAP}) reached; "
                                  "message not delivered.", thread=thread, hop=hop)
                continue
            await self.h._changed(self.name)
            try:
                self.thread, self.hop = thread, hop
                await self._turn(sender, text)
            except Exception as e:  # a failed turn is logged; the agent stays usable
                await self.h._log(self.name, "system", "harness", f"turn failed: {type(e).__name__}: {e}",
                                  thread=thread, hop=hop)
                await self.close()
            finally:
                self.busy = False
                if self.inbox.empty() and not self.held and self.client:
                    self.idle = asyncio.get_running_loop().call_later(
                        self.h.idle_secs, lambda: asyncio.ensure_future(self.close()))
                await self.h._changed(self.name)

    async def _connect(self, a: dict, model: str) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        cwd = a["scope_root"]
        identity = (f"You are '{a['name']}', a long-lived agent on the user's brain team, working in {cwd}. "
                    f"You may write only inside: {', '.join(a['scope'])}. "
                    "Messages from teammates arrive prefixed with [from <name>]; messages from the user are unprefixed. "
                    "Your plain replies are shown to the user only. To reach a teammate, call the send_message "
                    "tool; list_agents shows who is on the team. Message a teammate only when it moves the work "
                    "forward: hand-off chains and threads have hard limits. read_task and post_update work on this "
                    "project's tracker; post progress there, and never claim a task is done (the user closes tasks).")
        if a["brief"]:
            identity += f"\nYour role: {a['brief']}"
        opts = ClaudeAgentOptions(
            cwd=cwd, model=model, effort=a["model"]["effort"], env=env, settings=SESSION_SETTINGS,
            agents={f"harness-{a['persona']}": persona_agent(a["persona"])},
            extra_args={"agent": f"harness-{a['persona']}"}, resume=a["session_id"], permission_mode="default",
            mcp_servers={"bus": self._bus()}, max_budget_usd=max(self.h.remaining(self.name), 0.01),
            system_prompt={"type": "preset", "preset": "claude_code", "append": identity},
            hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[self._gate], timeout=HOLD_SECS + 60)]})
        self.client = self.h.client_factory(opts)
        await self.client.connect()
        self.model, self.cost_seen = model, 0.0

    async def _gate(self, input_data: dict, tool_use_id: str | None, context: Any) -> dict:
        tool, inp = input_data.get("tool_name", ""), input_data.get("tool_input", {}) or {}
        a = self.h._agent(self.name)
        verdict, kind, reason = gate_decision(tool, inp, a["scope_root"], a["scope"], a["always"])
        if verdict == "hold":
            ok, why = await self.h.hold(self.name, tool, inp, kind, reason)
            return _decision(ok, why)
        if verdict == "deny":
            await self.h._log(self.name, "system", "gate", f"denied {tool}: {reason}", thread=self.thread, hop=self.hop)
            self.h.audit({"harness": "deny", "agent": self.name, "tool": tool, "reason": reason})
        return _decision(verdict == "allow", reason)

    def _bus(self):
        return create_sdk_mcp_server("bus", tools=self.bus_tools())

    def bus_tools(self) -> list:
        @tool("send_message", "Send a message to a teammate agent. It is delivered to their inbox and they "
              "act on it in their own turn; their reply comes back to you as a message.", {"to": str, "text": str})
        async def send_message(args):
            try:
                await self.h.deliver(self.name, args.get("to", ""), args.get("text", ""), self.thread, self.hop + 1)
                return {"content": [{"type": "text", "text": f"Delivered to {args['to']}."}]}
            except HarnessError as e:
                return {"content": [{"type": "text", "text": f"Not delivered: {e}"}], "is_error": True}

        @tool("list_agents", "List the agents on the team with their role and state.", {})
        async def list_agents(_args):
            rows = [f"{v['name']} ({v['persona']}, {v['state']}): {v['brief'] or 'no brief'}"
                    for v in self.h.list() if v["name"] != self.name]
            return {"content": [{"type": "text", "text": "\n".join(rows) or "No other agents yet."}]}

        def task_root() -> Path:
            return Path(self.h._agent(self.name)["scope_root"])

        def text(msg: str, error: bool = False) -> dict:
            return {"content": [{"type": "text", "text": msg}], **({"is_error": True} if error else {})}

        @tool("read_task", "Read a task from this project's tracker by its id (e.g. 'a1b2c3').", {"task": str})
        async def read_task(args):
            t = tracker.read_task(task_root(), str(args.get("task", "")).lstrip("#"))
            if t is None:
                return text(f"No task {args.get('task')!r} in this project.", True)
            body = [f"#{t['id']} {t['title']} [{t['status']}]", t["brief"] or "(no brief)"]
            if t["acceptance"]:
                body += ["Acceptance:", *[f"- {x}" for x in t["acceptance"]]]
            body += ["Recent updates:", *t["updates"][-5:]]
            return text("\n".join(body))

        @tool("post_update", "Add an update to a tracker task, optionally moving it to 'doing' or 'review'. "
              "Agents can't close tasks; the user moves them to done.",
              {"type": "object", "properties": {"task": {"type": "string"}, "text": {"type": "string"},
                                                "status": {"type": "string", "enum": list(AGENT_STATUSES)}},
               "required": ["task", "text"]})
        async def post_update(args):
            tid, note, status = str(args.get("task", "")).lstrip("#"), str(args.get("text", "")).strip(), args.get("status")
            if not note or len(note) > 4000:
                return text("Update text must be 1-4000 characters.", True)
            if status and status not in AGENT_STATUSES:
                return text(f"Agents can only move tasks to {', '.join(AGENT_STATUSES)}.", True)
            try:
                tracker.add_update(task_root(), tid, f"agent {self.name}", note)
                if status:
                    tracker.set_status(task_root(), tid, status, actor="agent")
            except tracker.TrackerError as e:
                return text(str(e), True)
            await self.h._log(self.name, "system", "tracker", f"#{tid}: {note[:200]}" + (f" → {status}" if status else ""),
                              thread=self.thread, hop=self.hop)
            return text(f"Updated #{tid}" + (f" and moved it to {status}." if status else "."))

        return [send_message, list_agents, read_task, post_update]

    async def _turn(self, sender: str, text: str) -> None:
        a = self.h._agent(self.name)
        tier, why = "standard", ""
        if a["model"]["mode"] == "auto":
            tier, why, text = routing.decide(text, self.last_tier)
            self.last_tier = tier
        model, used = resolve_model(a["model"], tier)
        route = ("pinned" if used == "pinned" else f"auto: {used} ({why})" if used == tier
                 else f"auto: {used} ({why} → {tier}, limited by floor/ceiling)")
        if self.client is None:
            await self._connect(a, model)
        elif model != self.model:
            await self.client.set_model(model)
            self.model = model
        prompt = text if sender == "you" else (
            f"[from {sender}] (your plain reply goes to the user's timeline, not to {sender}: "
            f"answer them with send_message to=\"{sender}\")\n{text}")
        await self.client.query(prompt)
        reply, seen_model = [], model
        async for m in self.client.receive_response():
            if isinstance(m, AssistantMessage):
                seen_model = m.model or seen_model
                for b in m.content:
                    if isinstance(b, TextBlock) and b.text.strip():
                        reply.append(b.text)
                    elif isinstance(b, ToolUseBlock):
                        await self.h._log(self.name, "tool", self.name, _tool_summary(b), seen_model,
                                          thread=self.thread, hop=self.hop)
            elif isinstance(m, ResultMessage):
                cost = max(0.0, (m.total_cost_usd or 0.0) - self.cost_seen)
                self.cost_seen = m.total_cost_usd or self.cost_seen
                store.add_usage(self.h.conn, self.name, cost)
                if m.session_id and m.session_id != a["session_id"]:
                    store.update_agent(self.h.conn, self.name, session_id=m.session_id)
                if m.is_error:
                    await self.h._log(self.name, "system", "harness", f"turn ended: {m.subtype}",
                                      thread=self.thread, hop=self.hop)
                await self.h._log(self.name, "assistant", self.name, "\n\n".join(reply) or "(no reply)",
                                  seen_model, cost, thread=self.thread, hop=self.hop, route=route)
                if m.subtype == "error_max_budget_usd":
                    await self.close()  # the session's budget is spent; reconnect with today's remainder

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


def _hold_summary(h: dict) -> str:
    inp = h["input"]
    return f"{h['kind']}: {h['tool']} {inp.get('command') or inp.get('file_path') or ''}".strip()


def _tool_summary(b: ToolUseBlock) -> str:
    inp = b.input or {}
    detail = inp.get("file_path") or inp.get("command") or inp.get("pattern") or inp.get("url") or ""
    return f"{b.name} {str(detail)[:160]}".strip()


class Harness:
    def __init__(self, conn, broadcast: Callable[[dict], Awaitable[None]],
                 project_root: Callable[[str], Path | None], personas: Callable[[], set[str]],
                 client_factory=ClaudeSDKClient, idle_secs: float = IDLE_SECS, audit=_audit):
        self.conn, self.broadcast = conn, broadcast
        self.project_root, self.personas = project_root, personas
        self.client_factory, self.idle_secs, self.audit = client_factory, idle_secs, audit
        self.sessions: dict[str, Session] = {}
        self.pending: dict[int, asyncio.Future] = {}   # hold id → decision future
        self.waiting: dict[str, int] = {}              # agent → hold id it's blocked on
        self.hold_secs = HOLD_SECS

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
        return {**{k: a[k] for k in ("name", "persona", "project", "brief", "scope", "scope_root", "model", "limits", "always", "paused",
                                     "usage_usd", "session_id")},
                "usage_today": round(store.usage_since(self.conn, name, day_start()), 4),
                "state": s.state(a) if s else ("paused" if a["paused"] else ("asleep" if a["session_id"] else "new")),
                "hold": self.waiting.get(name),
                "current_model": (s.model if s and s.model else model), "tier": tier,
                "queued": s.inbox.qsize() if s else 0}

    def list(self) -> list[dict]:
        return [self.view(a["name"]) for a in store.list_agents(self.conn)]

    # roster
    def _writer(self, persona: str) -> bool:
        return any(not p["read_only"] for p in data.read_agents() if p["name"] == persona)

    def _check_lock(self, name: str, persona: str, scope: list[str]) -> None:
        """Writer agents can't share folders: one writer per scope, no nesting either way."""
        if not self._writer(persona):
            return
        for other in store.list_agents(self.conn):
            if other["name"] == name or not self._writer(other["persona"]):
                continue
            for mine in map(Path, scope):
                for theirs in map(Path, other["scope"]):
                    if mine.is_relative_to(theirs) or theirs.is_relative_to(mine):
                        raise HarnessError(f"{mine} overlaps {other['name']}'s scope ({theirs}); two writers "
                                           "can't share a folder. Narrow one scope or remove that agent.", 409)

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
                     scope: list[str] | None = None, model: dict | None = None, limits: dict | None = None) -> dict:
        if not NAME_RE.match(name or ""):
            raise HarnessError("name: lowercase letters, digits, dashes (2-32), starting with a letter")
        if store.get_agent(self.conn, name):
            raise HarnessError("an agent with that name exists", 409)
        if persona not in self.personas():
            raise HarnessError("unknown persona")
        if len(brief) > 2000:
            raise HarnessError("brief is too long")
        m = clean_model(model or {}, default_model(persona))
        lim = clean_limits(limits or {}, DEFAULT_LIMITS)
        sc = self._clean_scope(project, scope)
        self._check_lock(name, persona, sc)
        store.create_agent(self.conn, name, persona, project, brief, sc, m, lim)
        await self._changed(name)
        return self.view(name)

    async def update(self, name: str, brief: str | None = None, scope: list[str] | None = None,
                     model: dict | None = None, limits: dict | None = None) -> dict:
        a = self._agent(name)
        fields: dict = {}
        if brief is not None:
            if len(brief) > 2000:
                raise HarnessError("brief is too long")
            fields["brief"] = brief
        if scope is not None:
            fields["scope"] = self._clean_scope(a["project"], scope)
            self._check_lock(name, a["persona"], fields["scope"])
        if model is not None:
            fields["model"] = clean_model(model, a["model"])
        if limits is not None:
            fields["limits"] = clean_limits(limits, {**DEFAULT_LIMITS, **a["limits"]})
        store.update_agent(self.conn, name, **fields)
        s = self.sessions.get(name)
        if s and ("brief" in fields or "scope" in fields or "limits" in fields or
                  (model and model.get("effort", a["model"]["effort"]) != a["model"]["effort"])):
            await s.close()  # identity, scope and effort are fixed per connection: reconnect (resume) next turn
        await self._changed(name)
        return self.view(name)

    async def delete(self, name: str) -> None:
        self._agent(name)
        self._deny_pending(name)
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

    def remaining(self, name: str) -> float:
        a = self._agent(name)
        cap = {**DEFAULT_LIMITS, **a["limits"]}["daily_usd"]
        return cap - store.usage_since(self.conn, name, day_start())

    async def send(self, name: str, text: str, sender: str = "you", thread: str | None = None,
                   hop: int = 0) -> dict:
        """A message from the user starts a new thread; teammates' messages go through deliver()."""
        text = (text or "").strip()
        if not text or len(text) > TEXT_MAX:
            raise HarnessError(f"message must be 1-{TEXT_MAX} characters")
        s = self._session(name)
        thread = thread or secrets.token_hex(6)
        rec = await self._log(name, "user", sender, text, thread=thread, hop=hop)
        s.inbox.put_nowait((sender, text, thread, hop))
        await self._changed(name)
        return rec

    async def deliver(self, sender: str, to: str, text: str, thread: str, hop: int) -> dict:
        """Agent-to-agent hand-off, with the limits checked before anything is queued."""
        if to == sender:
            raise HarnessError("you can't message yourself")
        if store.get_agent(self.conn, to) is None:
            names = ", ".join(a["name"] for a in store.list_agents(self.conn) if a["name"] != sender)
            raise HarnessError(f"no agent named '{to}'. Team: {names or 'nobody else yet'}")
        if hop > HOP_LIMIT:
            raise HarnessError(f"hand-off limit ({HOP_LIMIT}) reached for this thread; report back to the user instead")
        if store.thread_turns(self.conn, thread) >= THREAD_TURN_CAP:
            raise HarnessError(f"thread turn cap ({THREAD_TURN_CAP}) reached; report back to the user instead")
        return await self.send(to, text, sender=sender, thread=thread, hop=hop)

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

    async def hold(self, name: str, tool: str, inp: dict, kind: str, reason: str) -> tuple[bool, str]:
        """Park a tool call until the user decides in the Hub (or it expires as denied)."""
        h = store.create_hold(self.conn, name, tool, inp, kind, reason)
        fut = asyncio.get_running_loop().create_future()
        self.pending[h["id"]], self.waiting[name] = fut, h["id"]
        s = self.sessions.get(name)
        await self._log(name, "system", "gate", f"waiting for approval: {_hold_summary(h)}",
                        thread=s.thread if s else None, hop=s.hop if s else 0)
        await self.broadcast({"type": "harness", "event": "hold", "hold": h})
        await self._changed(name)
        try:
            ok = await asyncio.wait_for(asyncio.shield(fut), self.hold_secs)
        except asyncio.TimeoutError:
            store.decide_hold(self.conn, h["id"], "expired")
            ok = False
        finally:
            self.pending.pop(h["id"], None)
            self.waiting.pop(name, None)
        status = store.get_hold(self.conn, h["id"])["status"]
        self.audit({"harness": "hold", "agent": name, "tool": tool, "kind": kind, "input": inp, "status": status})
        await self.broadcast({"type": "harness", "event": "hold", "hold": store.get_hold(self.conn, h["id"])})
        await self._changed(name)
        return ok, ("Approved by the user." if ok else
                    "The user didn't approve this" + (" in time." if status == "expired" else ".") +
                    " Don't retry it; continue without it or ask the user.")

    async def decide(self, hold_id: int, approve: bool, always: bool = False) -> dict:
        h = store.get_hold(self.conn, hold_id)
        if h is None:
            raise HarnessError("unknown hold", 404)
        if h["status"] != "pending" or hold_id not in self.pending:
            raise HarnessError(f"already {h['status']}", 409)
        h = store.decide_hold(self.conn, hold_id, "approved" if approve else "denied")
        if approve and always and h["tool"] == "Bash" and h["kind"] == "command":
            a = self._agent(h["agent"])  # only plain commands; push and destructive ones are asked every time
            store.update_agent(self.conn, h["agent"], always=sorted({*a["always"], h["input"].get("command", "").strip()}))
        self.pending[hold_id].set_result(approve)
        return h

    def _deny_pending(self, agent: str | None = None) -> None:
        for hold_id, fut in list(self.pending.items()):
            if agent is None or self.waiting.get(agent) == hold_id:
                store.decide_hold(self.conn, hold_id, "denied")
                if not fut.done():
                    fut.set_result(False)

    async def kill(self) -> dict:
        """Kill switch: deny everything waiting, pause every agent, stop live turns."""
        self._deny_pending()
        for a in store.list_agents(self.conn):
            await self.pause(a["name"])
        for s in self.sessions.values():
            if s.client and s.busy:
                try:
                    await s.client.interrupt()
                except Exception:
                    pass
            await s.close()
        self.audit({"harness": "kill"})
        return {"paused": len(store.list_agents(self.conn))}

    async def stop_all(self) -> None:
        self._deny_pending()
        for s in list(self.sessions.values()):
            await s.shutdown()
        self.sessions.clear()

    # events
    async def _log(self, name: str, role: str, sender: str, text: str, model: str | None = None,
                   cost: float | None = None, thread: str | None = None, hop: int = 0,
                   route: str | None = None) -> dict:
        rec = store.log_message(self.conn, name, role, sender, text, model, cost, thread, hop, route)
        await self.broadcast({"type": "harness", "event": "message", "message": rec})
        return rec

    def _spawn_log(self, *args) -> None:
        asyncio.ensure_future(self._log(*args))

    async def _changed(self, name: str) -> None:
        try:
            await self.broadcast({"type": "harness", "event": "agent", "agent": self.view(name)})
        except HarnessError:
            pass
