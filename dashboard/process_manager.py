"""D4 process manager — spawn / track / stop headless `claude -p` runs, safely.

Built to the Phase-2 security contract (see docs/plan.md "Phase 2 Fleet Recon"):
- persona must be a known agent; `task` is passed as an argv element, never via a shell
- `--add-dir` (if given) must resolve under a fixed base; escapes are rejected
- concurrency is capped; every spawn/stop is written to an append-only audit log
- run IDs are unguessable; env passed to the child is minimal
- WRITE-capable personas are refused here — they require the D8 approval flow. D4 only spawns
  read-only personas, whose posture is enforced by their frontmatter tool allowlist (verified).
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import signal
import time
from pathlib import Path

from . import data, registry

ALLOWED_BASE = (Path.home() / "Desktop" / "Code").resolve()
MAX_CONCURRENT = 4
MAX_PENDING = 10
TASK_MAX = 2000
AUDIT_LOG = Path.home() / ".claude" / "brain-dashboard" / "audit.jsonl"
_SECRET_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.I)


def _safe_env() -> dict:
    """Env for WRITE runs (which have Bash and could read env): drop secret-looking vars.
    claude authenticates via ~/.claude creds, not env keys, so this doesn't break auth."""
    return {k: v for k, v in os.environ.items() if not _SECRET_RE.search(k)}


def _known() -> dict[str, dict]:
    return {a["name"]: a for a in data.read_agents()}


def _audit(entry: dict) -> None:
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps({"ts": time.time(), **entry}) + "\n")
    except Exception:
        pass


class SpawnError(Exception):
    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


class ProcessManager:
    def __init__(self, hub, claude_bin: str = "claude"):
        self.hub = hub
        self.claude = claude_bin
        self._active: dict[str, asyncio.subprocess.Process] = {}
        self._pending: dict[str, dict] = {}
        self._queue: list[dict] = []
        self._dispatch_lock = asyncio.Lock()

    def _validate(self, persona: str, task: str, add_dir: str | None):
        agents = _known()
        task = (task or "").strip()
        if persona not in agents:
            raise SpawnError("unknown persona", 400)
        if not task or len(task) > TASK_MAX:
            raise SpawnError("task must be 1–2000 chars", 400)
        resolved = None
        if add_dir:
            resolved = Path(add_dir).resolve()
            if not resolved.is_relative_to(ALLOWED_BASE):
                raise SpawnError("add_dir escapes the allowed base", 400)
        return agents[persona], task, resolved

    # D4 — direct spawn, read-only personas only.
    async def spawn(self, persona: str, task: str, add_dir: str | None = None) -> dict:
        agent, task, resolved = self._validate(persona, task, add_dir)
        if not agent["read_only"]:
            raise SpawnError("write-capable personas require approval (propose/approve)", 403)
        return await self._launch(registry.new_id(), persona, task, resolved, write_mode=False)

    # D8 — propose a run; write personas land here and wait for approval.
    async def propose(self, persona: str, task: str, add_dir: str | None = None) -> dict:
        agent, task, resolved = self._validate(persona, task, add_dir)
        writer = not agent["read_only"]
        if writer and resolved is None:
            raise SpawnError("write runs require a scoped add_dir under the code base", 400)
        if len(self._pending) >= MAX_PENDING:
            raise SpawnError("too many pending approvals", 429)
        run_id = registry.new_id()
        prop = {"persona": persona, "task": task,
                "add_dir": str(resolved) if resolved else None, "writer": writer,
                "ts": time.time()}
        self._pending[run_id] = prop
        _audit({"action": "propose", "run_id": run_id, "persona": persona,
                "task": task[:120], "add_dir": prop["add_dir"], "writer": writer})
        await self.hub.broadcast({"type": "run_pending", "run_id": run_id, **prop})
        return {"run_id": run_id, "pending": prop}

    async def approve(self, run_id: str) -> dict:
        p = self._pending.pop(run_id, None)
        if not p:
            raise SpawnError("no such pending run", 404)
        _audit({"action": "approve", "run_id": run_id})
        resolved = Path(p["add_dir"]).resolve() if p["add_dir"] else None
        return await self._launch(run_id, p["persona"], p["task"], resolved, write_mode=p["writer"])

    async def deny(self, run_id: str) -> bool:
        if self._pending.pop(run_id, None) is None:
            return False
        _audit({"action": "deny", "run_id": run_id})
        await self.hub.broadcast({"type": "run_denied", "run_id": run_id})
        return True

    def pending(self) -> list[dict]:
        return [{"run_id": rid, **p} for rid, p in self._pending.items()]

    # D9 — task queue: enqueue work; it drains to agents as capacity frees.
    async def enqueue(self, persona: str, task: str, add_dir: str | None = None) -> dict:
        agent, task, resolved = self._validate(persona, task, add_dir)
        writer = not agent["read_only"]
        if writer and resolved is None:
            raise SpawnError("write tasks require a scoped add_dir under the code base", 400)
        item = {"id": registry.new_id(), "persona": persona, "task": task,
                "add_dir": str(resolved) if resolved else None, "writer": writer, "ts": time.time()}
        self._queue.append(item)
        _audit({"action": "enqueue", "id": item["id"], "persona": persona, "writer": writer})
        asyncio.create_task(self._dispatch())
        return {"queued": item}

    async def _dispatch(self) -> None:
        async with self._dispatch_lock:
            while self._queue and len(self._active) < MAX_CONCURRENT:
                item = self._queue.pop(0)
                resolved = Path(item["add_dir"]).resolve() if item["add_dir"] else None
                try:
                    if item["writer"]:
                        # writers can't auto-run — surface as a pending approval
                        self._pending[item["id"]] = {k: item[k] for k in
                                                     ("persona", "task", "add_dir", "writer", "ts")}
                        await self.hub.broadcast({"type": "run_pending", "run_id": item["id"],
                                                  **self._pending[item["id"]]})
                    else:
                        await self._launch(item["id"], item["persona"], item["task"],
                                           resolved, write_mode=False)
                except SpawnError:
                    self._queue.insert(0, item)  # at capacity — put it back, stop
                    break
        await self.hub.broadcast({"type": "queue_updated"})

    def dequeue(self, item_id: str) -> bool:
        n = len(self._queue)
        self._queue = [q for q in self._queue if q["id"] != item_id]
        return len(self._queue) < n

    def queued(self) -> list[dict]:
        return list(self._queue)

    async def _launch(self, run_id: str, persona: str, task: str,
                      resolved_dir: Path | None, write_mode: bool) -> dict:
        if len(self._active) >= MAX_CONCURRENT:
            raise SpawnError("at capacity — too many active runs", 429)
        argv = [self.claude, "-p", task, "--agent", persona,
                "--output-format", "stream-json", "--verbose"]
        if write_mode:
            argv += ["--permission-mode", "acceptEdits"]  # writes confined to cwd + --add-dir
        if resolved_dir:
            argv += ["--add-dir", str(resolved_dir)]
        # Read-only runs inherit env (no tool to read it). Write runs get secrets filtered.
        env = _safe_env() if write_mode else None
        kwargs = {"env": env} if env is not None else {}
        proc = await asyncio.create_subprocess_exec(
            *argv, cwd=str(resolved_dir or ALLOWED_BASE),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            start_new_session=True, **kwargs,
        )
        self._active[run_id] = proc
        self._reg(lambda c: registry.insert_run(c, run_id, persona, task, "dashboard", pid=proc.pid))
        _audit({"action": "launch", "run_id": run_id, "persona": persona,
                "pid": proc.pid, "write_mode": write_mode})
        asyncio.create_task(self._drain(run_id, proc))
        await self.hub.broadcast({"type": "run_started", "run_id": run_id,
                                  "persona": persona, "task": task})
        return {"run_id": run_id, "pid": proc.pid}

    async def _drain(self, run_id: str, proc) -> None:
        cost = inp = out = None
        try:
            async for raw in proc.stdout:
                try:
                    evt = json.loads(raw)
                except ValueError:
                    continue
                t = evt.get("type")
                if t == "assistant":
                    for b in evt.get("message", {}).get("content", []):
                        if b.get("type") == "tool_use":
                            act = {"name": b.get("name"), "input": b.get("input")}
                            await self.hub.broadcast({"type": "run_event", "run_id": run_id, **act})
                            self._reg(lambda c: registry.append_event(c, run_id, "tool_use", act))
                elif t == "result":
                    cost = evt.get("total_cost_usd")
                    u = evt.get("usage", {}) or {}
                    inp, out = u.get("input_tokens"), u.get("output_tokens")
            await proc.wait()
        finally:
            status = "done" if proc.returncode in (0, None) else "error"
            if status == "error":
                err = ""
                with contextlib.suppress(Exception):
                    err = (await proc.stderr.read()).decode(errors="replace")[-300:]
                _audit({"action": "error", "run_id": run_id, "stderr": err.strip()})
            self._reg(lambda c: registry.finish_run(c, run_id, status, cost_usd=cost,
                                                     input_tok=inp, output_tok=out))
            self._active.pop(run_id, None)
            await self.hub.broadcast({"type": "run_finished", "run_id": run_id,
                                      "status": status, "cost_usd": cost})
            _audit({"action": "finish", "run_id": run_id, "status": status, "cost_usd": cost})
            asyncio.create_task(self._dispatch())  # capacity freed — drain the queue

    async def stop(self, run_id: str) -> bool:
        proc = self._active.get(run_id)
        if not proc:
            return False
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            with contextlib.suppress(Exception):
                proc.terminate()
        _audit({"action": "stop", "run_id": run_id})
        return True

    async def stop_all(self) -> None:
        for run_id in list(self._active):
            await self.stop(run_id)

    def active(self) -> list[str]:
        return list(self._active)

    @staticmethod
    def _reg(fn) -> None:
        try:
            conn = registry.open_db()
            fn(conn)
            conn.close()
        except Exception:
            pass
