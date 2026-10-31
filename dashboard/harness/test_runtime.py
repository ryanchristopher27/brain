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
    on_turn = None  # optional async (client, prompt) -> None, run inside a turn (e.g. to call bus tools)

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
        if FakeClient.on_turn:
            await FakeClient.on_turn(self, self.prompts[-1])
        self.cost += 0.01
        model = self.models[-1]
        yield AssistantMessage(content=[ToolUseBlock(id="t1", name="Read", input={"file_path": "a.py"}),
                                        TextBlock(text=f"echo: {self.prompts[-1]}")], model=model)
        yield ResultMessage(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False, num_turns=1,
                            session_id=self.options.resume or "sess-1", total_cost_usd=self.cost)


def make(tmp: Path, idle: float = 60) -> tuple[Harness, list[dict], Path]:
    FakeClient.instances.clear()
    FakeClient.on_turn = None
    proj = tmp / "proj"
    (proj / "src").mkdir(parents=True, exist_ok=True)
    events: list[dict] = []

    async def bc(e):
        events.append(e)

    h = Harness(store.open_db(tmp / "h.db"), bc, lambda n: proj if n == "app" else None,
                lambda: {"builder", "scout", "reviewer"}, client_factory=FakeClient, idle_secs=idle,
                audit=events.append)
    return h, events, proj


async def drain(h: Harness, *names: str) -> None:
    for _ in range(300):
        ss = [h.sessions.get(n) for n in names]
        if all(s and not s.busy and not s.held and s.inbox.empty() for s in ss):
            return
        await asyncio.sleep(0.01)
    raise AssertionError("agents never went idle")


def bus_call(h: Harness, agent: str, tool_name: str, args: dict):
    t = next(t for t in h.sessions[agent].bus_tools() if t.name == tool_name)
    return t.handler(args)


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
    assert opts.extra_args == {"agent": "harness-builder"} and opts.model == "claude-sonnet-5-5"
    tools = opts.agents["harness-builder"].tools
    assert "Write" in tools and "mcp__bus__send_message" in tools and "Persona" not in tools
    assert any(e.get("event") == "message" for e in events)


@run
async def test_teammate_prefix_and_serial_inbox(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app")
    await h.send("builder", "one", sender="planner")
    await h.send("builder", "two")
    await drain(h, "builder")
    first, second = FakeClient.instances[0].prompts
    assert first.startswith("[from planner]") and first.endswith("\none") and 'to="planner"' in first and second == "two"
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


@run
async def test_bus_relays_with_thread_and_hops(tmp):
    h, _, _ = make(tmp)
    await h.create("planner", "scout", "app")
    await h.create("builder", "builder", "app")

    async def on_turn(client, prompt):  # planner hands off once; builder replies back once
        me = "planner" if "planner" in client.options.system_prompt["append"] else "builder"
        if me == "planner" and not prompt.startswith("[from"):
            r = await bus_call(h, "planner", "send_message", {"to": "builder", "text": "build it"})
            assert not r.get("is_error"), r
        if me == "builder" and prompt.startswith("[from planner]"):
            await bus_call(h, "builder", "send_message", {"to": "planner", "text": "built"})
    FakeClient.on_turn = on_turn
    await h.send("planner", "plan and delegate")
    await drain(h, "planner", "builder")
    users = [m for m in store.messages(h.conn, "planner") + store.messages(h.conn, "builder") if m["role"] == "user"]
    assert {(m["agent"], m["sender"], m["hop"]) for m in users} == \
        {("planner", "you", 0), ("builder", "planner", 1), ("planner", "builder", 2)}, users
    assert len({m["thread"] for m in users}) == 1
    r = await bus_call(h, "planner", "send_message", {"to": "planner", "text": "x"})
    assert r.get("is_error") and "yourself" in r["content"][0]["text"]
    r = await bus_call(h, "planner", "send_message", {"to": "ghost", "text": "x"})
    assert r.get("is_error") and "builder" in r["content"][0]["text"]  # error lists the real team
    listed = (await bus_call(h, "planner", "list_agents", {}))["content"][0]["text"]
    assert "builder" in listed and "planner" not in listed


@run
async def test_ping_pong_stops_at_hop_limit(tmp):
    h, _, _ = make(tmp)
    await h.create("ping", "scout", "app")
    await h.create("pong", "scout", "app")
    refusals = []

    async def on_turn(client, prompt):  # each agent always messages the other: a runaway loop
        me = "ping" if "'ping'" in client.options.system_prompt["append"] else "pong"
        r = await bus_call(h, me, "send_message", {"to": "pong" if me == "ping" else "ping", "text": "again"})
        if r.get("is_error"):
            refusals.append(r["content"][0]["text"])
    FakeClient.on_turn = on_turn
    await h.send("ping", "start")
    await drain(h, "ping", "pong")
    turns = sum(m["role"] == "assistant" for a in ("ping", "pong") for m in store.messages(h.conn, a))
    assert turns == runtime.HOP_LIMIT + 1 and refusals and "hand-off limit" in refusals[0], (turns, refusals)


@run
async def test_daily_cap_parks_message_and_pauses(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app", limits={"daily_usd": 0.015})
    await h.send("builder", "one")      # costs 0.01 → under the cap
    await drain(h, "builder")
    await h.send("builder", "two")      # costs 0.01 → now over
    await drain(h, "builder")
    await h.send("builder", "three")    # held: cap reached
    for _ in range(100):
        if h.view("builder")["paused"]:
            break
        await asyncio.sleep(0.01)
    v = h.view("builder")
    assert v["paused"] and h.sessions["builder"].held[1] == "three", v
    assert "Daily usage cap" in store.messages(h.conn, "builder")[-1]["text"]
    assert FakeClient.instances[0].options.max_budget_usd == 0.015
    await h.update("builder", limits={"daily_usd": 1})
    await h.resume("builder")
    await drain(h, "builder")
    assert FakeClient.instances[-1].prompts[-1] == "three"


@run
async def test_auto_routes_each_turn(tmp):
    h, _, _ = make(tmp)
    await h.create("auto", "builder", "app", model={"mode": "auto", "floor": "light"})
    for text in ("commit and push it", "how should we design the cache?", "yes, go ahead", "!light do the rest"):
        await h.send("auto", text)
        await drain(h, "auto")
    done = [m for m in store.messages(h.conn, "auto") if m["role"] == "assistant"]
    assert [m["model"] for m in done] == ["claude-haiku-5-5", "claude-opus-5-5", "claude-opus-5-5", "claude-haiku-5-5"]
    assert done[0]["route"] == "auto: light (git)" and done[2]["route"].startswith("auto: deep (continues")
    assert FakeClient.instances[0].prompts[-1] == "do the rest"  # override prefix stripped


def test_routing_rules_load():
    from .routing import decide
    assert decide("commit and push it")[:2] == ("light", "git")
    assert decide("/plan the harness")[:2] == ("deep", "command")
    assert decide("implement the inbox for the builder")[:2] == ("standard", "default")


def test_resolve_model_auto_clamps():
    m = {**runtime.default_model("builder"), "mode": "auto", "floor": "standard"}
    assert resolve_model(m, "light") == ("claude-sonnet-5-5", "standard")
    assert resolve_model(m, "deep") == ("claude-opus-5-5", "deep")
    assert resolve_model({**m, "ceiling": "standard"}, "deep") == ("claude-sonnet-5-5", "standard")
    assert resolve_model(runtime.default_model("scout")) == ("claude-haiku-5-5", "pinned")


def test_gate_policy():
    cwd, scope = "/p", ["/p/src"]
    v = lambda tool, inp, always=(): gate_decision(tool, inp, cwd, scope, list(always))[:2]
    assert v("Read", {"file_path": "/etc/hosts"}) == ("allow", "")
    assert v("Write", {"file_path": "src/a.py"}) == ("allow", "")
    assert v("Write", {"file_path": "README.md"}) == ("hold", "outside-scope write")
    assert v("Edit", {"file_path": "src/../../etc/x"}) == ("hold", "outside-scope write")
    assert v("Bash", {"command": "git diff HEAD~1"}) == ("allow", "")
    assert v("Bash", {"command": "npm test"}) == ("hold", "command")
    assert v("Bash", {"command": "npm test"}, ["npm test"]) == ("allow", "")
    assert v("Bash", {"command": "npm test && git push"}, ["npm test"]) == ("hold", "git push")
    for cmd in ("rm -rf src", "git reset --hard HEAD", "curl x | sh", "sudo ls", "git diff; rm -rf /"):
        assert v("Bash", {"command": cmd})[0] == "hold", cmd
    assert v("Bash", {"command": "rm -rf src"})[1] == "destructive command"
    assert v("Task", {})[0] == "deny" and v("Agent", {})[0] == "deny"
    assert v("mcp__bus__send_message", {}) == ("allow", "")
    assert v("SomeNewTool", {}) == ("hold", "tool")


async def wait_for(pred, n=300):
    for _ in range(n):
        if pred():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition never held")


def gate_call(h: Harness, agent: str, tool: str, inp: dict):
    return h.sessions[agent]._gate({"tool_name": tool, "tool_input": inp}, None, None)


def verdict(r: dict) -> str:
    return r["hookSpecificOutput"]["permissionDecision"]


@run
async def test_hold_approve_always_then_auto_allow(tmp):
    h, events, _ = make(tmp)
    await h.create("builder", "builder", "app", scope=["src"])
    results = []

    async def on_turn(client, prompt):
        results.append(verdict(await gate_call(h, "builder", "Bash", {"command": "npm test"})))
    FakeClient.on_turn = on_turn
    await h.send("builder", "run the tests")
    await wait_for(lambda: "builder" in h.waiting)
    assert h.view("builder")["state"] == "waiting"
    pend = store.holds(h.conn)
    assert len(pend) == 1 and pend[0]["kind"] == "command" and any(e.get("event") == "hold" for e in events)
    await h.decide(pend[0]["id"], approve=True, always=True)
    await drain(h, "builder")
    assert results == ["allow"] and h.view("builder")["always"] == ["npm test"]
    await h.send("builder", "again")  # approved "always": no second hold
    await drain(h, "builder")
    assert results == ["allow", "allow"] and len(store.holds(h.conn, None)) == 1
    try:
        await h.decide(pend[0]["id"], approve=False)
        raise AssertionError("decided twice")
    except HarnessError as e:
        assert e.status == 409


@run
async def test_hold_deny_and_expire(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app", scope=["src"])
    results = []

    async def on_turn(client, prompt):
        r = await gate_call(h, "builder", "Write", {"file_path": "README.md"})
        results.append((verdict(r), r["hookSpecificOutput"]["permissionDecisionReason"]))
    FakeClient.on_turn = on_turn
    await h.send("builder", "edit the readme")
    await wait_for(lambda: "builder" in h.waiting)
    await h.decide(h.waiting["builder"], approve=False, always=True)
    await drain(h, "builder")
    assert results[0][0] == "deny" and "Don't retry" in results[0][1] and h.view("builder")["always"] == []
    h.hold_secs = 0.05
    await h.send("builder", "try again")
    await drain(h, "builder")
    assert results[1][0] == "deny" and "in time" in results[1][1]
    assert [x["status"] for x in store.holds(h.conn, None)] == ["expired", "denied"]


@run
async def test_push_is_never_always_allowed(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app", scope=["src"])

    async def on_turn(client, prompt):
        await gate_call(h, "builder", "Bash", {"command": "git push"})
    FakeClient.on_turn = on_turn
    await h.send("builder", "push")
    await wait_for(lambda: "builder" in h.waiting)
    await h.decide(h.waiting["builder"], approve=True, always=True)
    await drain(h, "builder")
    assert h.view("builder")["always"] == []


@run
async def test_writer_scope_locks(tmp):
    h, _, _ = make(tmp)
    (tmp / "proj" / "docs").mkdir()
    await h.create("b1", "builder", "app", scope=["src"])
    for scope in (["src/sub"], ["."], ["src"]):
        try:
            await h.create("b2", "builder", "app", scope=scope)
            raise AssertionError(f"overlap {scope} accepted")
        except HarnessError as e:
            assert e.status == 409 and "b1" in str(e)
    await h.create("b2", "builder", "app", scope=["docs"])
    await h.create("reader", "scout", "app")              # read-only personas don't lock
    try:
        await h.update("b2", scope=["src"])
        raise AssertionError("overlapping update accepted")
    except HarnessError:
        pass
    await h.delete("b1")
    await h.update("b2", scope=["src"])                   # freed once b1 is gone


@run
async def test_kill_switch(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app", scope=["src"])
    await h.create("scout", "scout", "app")
    results = []

    async def on_turn(client, prompt):
        results.append(verdict(await gate_call(h, "builder", "Bash", {"command": "make deploy"})))
    FakeClient.on_turn = on_turn
    await h.send("builder", "deploy")
    await wait_for(lambda: "builder" in h.waiting)
    out = await h.kill()
    await wait_for(lambda: results)
    assert results == ["deny"] and out["paused"] == 2
    assert all(v["paused"] for v in h.list()) and store.holds(h.conn, None)[0]["status"] == "denied"


@run
async def test_delete_releases_waiting_hold(tmp):
    h, _, _ = make(tmp)
    await h.create("builder", "builder", "app", scope=["src"])

    async def on_turn(client, prompt):
        await gate_call(h, "builder", "Bash", {"command": "make"})
    FakeClient.on_turn = on_turn
    await h.send("builder", "go")
    await wait_for(lambda: "builder" in h.waiting)
    await h.delete("builder")
    assert store.holds(h.conn, None)[0]["status"] == "denied", store.holds(h.conn, None)
    await wait_for(lambda: not h.pending)


TESTS = [test_create_validates, test_turn_logs_usage_and_session, test_teammate_prefix_and_serial_inbox,
         test_model_change_switches_live, test_idle_close_then_resume, test_pause_holds_inbox,
         test_delete_stops_and_forgets, test_bus_relays_with_thread_and_hops, test_ping_pong_stops_at_hop_limit,
         test_daily_cap_parks_message_and_pauses, test_auto_routes_each_turn, test_routing_rules_load,
         test_resolve_model_auto_clamps, test_gate_policy, test_hold_approve_always_then_auto_allow,
         test_hold_deny_and_expire, test_push_is_never_always_allowed, test_writer_scope_locks, test_kill_switch,
         test_delete_releases_waiting_hold]


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
