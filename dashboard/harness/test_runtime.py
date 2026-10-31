"""Tests for the harness runtime + store (H1), with a fake SDK client — no usage spent.

Run:  ./voice/.venv/bin/python -m dashboard.harness.test_runtime

The live end-to-end path (real SDK, real model) is covered by probe_sdk.py.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock

from . import runtime, store
from .runtime import Harness, HarnessError, gate_decision, resolve_model


class FakeClient:
    instances: list["FakeClient"] = []

    def __init__(self, options):
        self.options, self.prompts, self.models, self.cost = options, [], [options.model], 0.0
        self.connected = False
        FakeClient.instances.append(self)

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.connected = False

    async def set_model(self, model):
        self.models.append(model)

    async def query(self, prompt):
        self.prompts.append(prompt)

    async def receive_response(self):
        self.cost += 0.01
        model = self.models[-1]
        yield AssistantMessage(content=[ToolUseBlock(id="t1", name="Read", input={"file_path": "a.py"}),
                                        TextBlock(text=f"echo: {self.prompts[-1]}")], model=model)
        yield ResultMessage(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False, num_turns=1,
                            session_id=self.options.resume or "sess-1", total_cost_usd=self.cost)


def make(tmp: Path, idle: float = 60) -> tuple[Harness, list[dict], Path]:
    FakeClient.instances.clear()
    proj = tmp / "proj"
    (proj / "src").mkdir(parents=True, exist_ok=True)
    events: list[dict] = []

    async def bc(e):
        events.append(e)

    h = Harness(store.open_db(tmp / "h.db"), bc, lambda n: proj if n == "app" else None,
                lambda: {"builder", "scout", "reviewer"}, client_factory=FakeClient, idle_secs=idle)
    return h, events, proj


async def drain(h: Harness, name: str) -> None:
    for _ in range(200):
        s = h.sessions.get(name)
        if s and not s.busy and s.inbox.empty():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("agent never went idle")


def run(coro_fn):
    def t():
        with tempfile.TemporaryDirectory() as d:
            asyncio.run(coro_fn(Path(d)))
    t.__name__ = coro_fn.__name__
    return t


@run
async def test_create_validates(tmp):
    h, _, proj = make(tmp)
    a = await h.create("planner", "builder", "app", brief="plans things", model={"model": "claude-opus-5-5"})
    assert a["scope"] == [str(proj.resolve())] and a["model"]["model"] == "claude-opus-5-5" and a["state"] == "new"
    for kw, why in [({"name": "Bad Name"}, "name"), ({"persona": "root"}, "persona"),
                    ({"project": "nope"}, "project"), ({"scope": ["../x"]}, "scope"),
                    ({"model": {"model": "gpt-4"}}, "model"), ({"model": {"floor": "deep", "ceiling": "light"}}, "floor")]:
        args = {"name": "x2", "persona": "builder", "project": "app", **kw}
        try:
            await h.create(**args)
            raise AssertionError(f"accepted bad {why}")
        except HarnessError:
            pass
    try:
        await h.create("planner", "scout", "app")
        raise AssertionError("duplicate accepted")
    except HarnessError as e:
        assert e.status == 409


@run
async def test_turn_logs_usage_and_session(tmp):
    h, events, _ = make(tmp)
    await h.create("builder", "builder", "app", scope=["src"])
    await h.send("builder", "add a test")
    await drain(h, "builder")
    msgs = store.messages(h.conn, "builder")
    assert [m["role"] for m in msgs] == ["user", "tool", "assistant"], msgs
    assert msgs[-1]["text"] == "echo: add a test" and abs(msgs[-1]["cost"] - 0.01) < 1e-9
    v = h.view("builder")
    assert v["session_id"] == "sess-1" and v["state"] == "live" and abs(v["usage_usd"] - 0.01) < 1e-9
    opts = FakeClient.instances[0].options
    assert "ANTHROPIC_API_KEY" not in opts.env and "model-router@brain" in opts.settings
    assert opts.extra_args == {"agent": "builder"} and opts.model == "claude-sonnet-5-5"
    assert any(e.get("event") == "message" for e in events)


@run
async def test_teammate_prefix_and_serial_inbox(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app")
    await h.send("builder", "one", sender="planner")
    await h.send("builder", "two")
    await drain(h, "builder")
    assert FakeClient.instances[0].prompts == ["[from planner]\none", "two"]
    assert len(FakeClient.instances) == 1  # one connection serves the queue


@run
async def test_model_change_switches_live(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app")
    await h.send("builder", "hi")
    await drain(h, "builder")
    await h.update("builder", model={"model": "claude-haiku-5-5"})
    await h.send("builder", "again")
    await drain(h, "builder")
    c = FakeClient.instances[-1]
    assert len(FakeClient.instances) == 1 and c.models == ["claude-sonnet-5-5", "claude-haiku-5-5"]
    assert store.messages(h.conn, "builder")[-1]["model"] == "claude-haiku-5-5"


@run
async def test_idle_close_then_resume(tmp):
    h, _, _ = make(tmp, idle=0.05)
    await h.create("scout", "scout", "app")
    await h.send("scout", "remember X")
    await drain(h, "scout")
    await asyncio.sleep(0.15)
    assert h.view("scout")["state"] == "asleep" and not FakeClient.instances[0].connected
    await h.send("scout", "what was it")
    await drain(h, "scout")
    assert len(FakeClient.instances) == 2 and FakeClient.instances[1].options.resume == "sess-1"


@run
async def test_pause_holds_inbox(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app")
    await h.pause("builder")
    await h.send("builder", "wait for me")
    await asyncio.sleep(0.05)
    assert not FakeClient.instances and h.view("builder")["state"] == "paused"
    await h.resume("builder")
    await drain(h, "builder")
    assert FakeClient.instances[0].prompts == ["wait for me"]


@run
async def test_delete_stops_and_forgets(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app")
    await h.send("builder", "hi")
    await drain(h, "builder")
    await h.delete("builder")
    assert not FakeClient.instances[0].connected and store.get_agent(h.conn, "builder") is None
    assert store.messages(h.conn, "builder") == []


def test_resolve_model_auto_clamps():
    m = {**runtime.default_model("builder"), "mode": "auto", "floor": "standard"}
    assert resolve_model(m, "light") == ("claude-sonnet-5-5", "standard")
    assert resolve_model(m, "deep") == ("claude-opus-5-5", "deep")
    assert resolve_model({**m, "ceiling": "standard"}, "deep") == ("claude-sonnet-5-5", "standard")
    assert resolve_model(runtime.default_model("scout")) == ("claude-haiku-5-5", "pinned")


def test_gate_policy():
    cwd, scope = "/p", ["/p/src"]
    assert gate_decision("Read", {"file_path": "/etc/hosts"}, cwd, scope)[0]
    assert gate_decision("Write", {"file_path": "src/a.py"}, cwd, scope)[0]
    assert not gate_decision("Write", {"file_path": "README.md"}, cwd, scope)[0]
    assert not gate_decision("Edit", {"file_path": "src/../../etc/x"}, cwd, scope)[0]
    assert gate_decision("Bash", {"command": "git diff HEAD~1"}, cwd, scope)[0]
    for cmd in ("git push", "git diff; rm -rf /", "git log | sh", "rm -rf src", "git status $(id)"):
        assert not gate_decision("Bash", {"command": cmd}, cwd, scope)[0], cmd
    assert not gate_decision("Task", {}, cwd, scope)[0]
    assert gate_decision("mcp__bus__send_message", {}, cwd, scope)[0]


TESTS = [test_create_validates, test_turn_logs_usage_and_session, test_teammate_prefix_and_serial_inbox,
         test_model_change_switches_live, test_idle_close_then_resume, test_pause_holds_inbox,
         test_delete_stops_and_forgets, test_resolve_model_auto_clamps, test_gate_policy]


def main() -> int:
    passed = failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"  PASS    {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL    {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR   {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed · {failed} failed  (of {len(TESTS)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
