"""H0 spike: probe claude-agent-sdk against what the harness needs.

Each probe prints PASS/FAIL with evidence. Uses Haiku to keep usage small. Writes only inside a
throwaway project dir (default: a temp dir), never in a real repo.

    ./voice/.venv/bin/python -m dashboard.harness.probe_sdk            # all probes
    ./voice/.venv/bin/python -m dashboard.harness.probe_sdk auth gate  # just these

Re-run after upgrading the SDK or Claude Code.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, PermissionResultAllow,
                              PermissionResultDeny, ResultMessage, SystemMessage, TextBlock, ToolUseBlock,
                              create_sdk_mcp_server, tool)

LIGHT = "claude-haiku-5-5"
STANDARD = "claude-sonnet-5-5"
RESULTS: list[tuple[str, bool, str]] = []


def report(name: str, ok: bool, evidence: str) -> None:
    RESULTS.append((name, ok, evidence))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {evidence}", flush=True)


def opts(proj: Path, **kw) -> ClaudeAgentOptions:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    # The harness owns model choice: keep the model-router mod out of its sessions.
    settings = json.dumps({"enabledPlugins": {"model-router@brain": False}})
    return ClaudeAgentOptions(cwd=str(proj), model=kw.pop("model", LIGHT), env=env, settings=settings, **kw)


async def turn(client: ClaudeSDKClient, prompt: str) -> dict:
    """Send one turn; collect init data, models, text, tool calls and the result."""
    out = {"init": None, "models": set(), "text": "", "tools": [], "result": None}
    await client.query(prompt)
    async for m in client.receive_response():
        if isinstance(m, SystemMessage) and m.subtype == "init":
            out["init"] = m.data
        elif isinstance(m, AssistantMessage):
            out["models"].add(m.model)
            for b in m.content:
                if isinstance(b, TextBlock):
                    out["text"] += b.text
                elif isinstance(b, ToolUseBlock):
                    out["tools"].append((b.name, b.input))
        elif isinstance(m, ResultMessage):
            out["result"] = m
    return out


async def probe_auth(proj: Path) -> None:
    """Subscription login (no API key), persona via --agent, pinned model, init plugin list."""
    async with ClaudeSDKClient(opts(proj, extra_args={"agent": "scout"})) as c:
        t = await turn(c, "Reply with exactly: ok")
    init = t["init"] or {}
    report("auth", init.get("apiKeySource") in (None, "none") and bool(t["result"]) and not t["result"].is_error,
           f"apiKeySource={init.get('apiKeySource')!r} result={t['result'] and t['result'].subtype}")
    tools = init.get("tools", [])
    report("persona", "Write" not in tools and "Edit" not in tools and "Read" in tools,
           f"agent={init.get('agent')!r} write-tools-absent={'Write' not in tools}")
    report("pinned-model", t["models"] == {LIGHT}, f"models={sorted(t['models'])}")
    plugins = [p.get("name") for p in init.get("plugins", [])]
    print(f"       plugins loaded: {plugins}  cost=${t['result'].total_cost_usd if t['result'] else '?'}")


async def probe_tool(proj: Path) -> None:
    """In-process MCP tool: the model calls it and the dashboard sees the call."""
    seen: list[dict] = []

    @tool("send_message", "Send a message to another agent on the team.", {"to": str, "text": str})
    async def send_message(args):
        seen.append(args)
        return {"content": [{"type": "text", "text": f"delivered to {args['to']}"}]}

    bus = create_sdk_mcp_server("bus", tools=[send_message])
    o = opts(proj, mcp_servers={"bus": bus}, allowed_tools=["mcp__bus__send_message"])
    async with ClaudeSDKClient(o) as c:
        await turn(c, "Use the send_message tool to tell agent 'builder' the text 'start H1'. Then say done.")
    report("bus-tool", any(a.get("to") == "builder" for a in seen), f"calls={seen}")


async def probe_gate(proj: Path) -> None:
    """can_use_tool: allow a write inside scope, deny one outside."""
    scope = (proj / "scope").resolve()
    scope.mkdir(exist_ok=True)
    outside = Path(tempfile.mkdtemp(prefix="h0-outside-")).resolve()
    asked: list[tuple[str, str, str]] = []

    async def gate(name, inp, ctx):
        path = inp.get("file_path") or inp.get("path") or ""
        inside = bool(path) and Path(path).resolve().is_relative_to(scope)
        asked.append((name, path, "allow" if inside else "deny"))
        if name in ("Write", "Edit", "MultiEdit") and not inside:
            return PermissionResultDeny(message=f"{path} is outside your scope {scope}")
        return PermissionResultAllow()

    o = opts(proj, model=STANDARD, can_use_tool=gate, permission_mode="default",
             allowed_tools=["Read"], disallowed_tools=["Bash"], add_dirs=[str(outside)])
    async with ClaudeSDKClient(o) as c:
        await turn(c, f"Create {scope}/in.txt containing 'in'. Then create {outside}/out.txt containing 'out'. "
                      "Use the Write tool for both. If one is refused, just report it.")
    wrote_in, wrote_out = (scope / "in.txt").exists(), (outside / "out.txt").exists()
    report("gate", wrote_in and not wrote_out, f"in={wrote_in} out={wrote_out} decisions={asked}")


async def probe_switch_and_resume(proj: Path) -> None:
    """set_model mid-session, then resume the session in a fresh client and recall a fact."""
    async with ClaudeSDKClient(opts(proj)) as c:
        t1 = await turn(c, "Remember the codeword PELICAN-42. Reply: noted.")
        await c.set_model(STANDARD)
        t2 = await turn(c, "Reply with exactly: switched")
        sid = t1["result"].session_id
    report("set-model", t1["models"] == {LIGHT} and t2["models"] == {STANDARD},
           f"before={sorted(t1['models'])} after={sorted(t2['models'])}")
    async with ClaudeSDKClient(opts(proj, resume=sid)) as c:
        t3 = await turn(c, "What was the codeword? Reply with just it.")
    report("resume", "PELICAN-42" in t3["text"], f"session={sid[:8]} reply={t3['text'].strip()[:40]!r}")


async def probe_budget(proj: Path) -> None:
    """max_budget_usd stops a session once exceeded."""
    async with ClaudeSDKClient(opts(proj, max_budget_usd=0.000001)) as c:
        t1 = await turn(c, "Reply with: one")
        t2 = await turn(c, "Reply with: two")
    subs = [t["result"].subtype if t["result"] else None for t in (t1, t2)]
    report("budget", any(s and "budget" in s for s in subs), f"subtypes={subs}")


async def probe_router(proj: Path) -> None:
    """The model-router mod must not override a pinned harness model ('!deep' would escalate)."""
    async with ClaudeSDKClient(opts(proj)) as c:
        t = await turn(c, "!deep Reply with exactly: hi")
    report("router-skip", t["models"] == {LIGHT}, f"pinned={LIGHT} got={sorted(t['models'])}")


PROBES = {"auth": probe_auth, "tool": probe_tool, "gate": probe_gate, "resume": probe_switch_and_resume,
          "budget": probe_budget, "router": probe_router}


async def main(names: list[str]) -> int:
    proj = Path(tempfile.mkdtemp(prefix="h0-proj-"))
    for n in names or list(PROBES):
        try:
            await PROBES[n](proj)
        except Exception as e:  # a probe crashing is a finding, not a reason to stop the rest
            report(n, False, f"{type(e).__name__}: {e}")
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed" + (f" · failed: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
