"""Headless Claude Code bridge.

Drives `claude -p` so the voice surface inherits every brain subagent + MCP. Defaults to the
read-only Scout persona (verified: `--agent scout` yields a Read/Grep/Glob/Web-only session,
so it cannot write even in the default permission mode). Session id is captured from the
stream and replayed via `--resume` to keep one rolling conversation.

Verified against claude 2.1.167 stream-json:
  {"type":"system","subtype":"init","session_id":...,"tools":[...],"agents":[...]}
  {"type":"assistant","message":{"content":[{"type":"text","text":...}]}, ...}
  {"type":"result","subtype":"success","result":"...","session_id":...}
Everything else (hook_started/hook_response, rate_limit_event) is ignored.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Iterator


class ClaudeBridge:
    def __init__(self, default_persona: str = "scout", resume_session: bool = True):
        self.default_persona = default_persona
        self.resume_session = resume_session
        self._session_id: str | None = None
        self._bin = shutil.which("claude") or "claude"

    def _command(self, text: str, persona: str) -> list[str]:
        cmd = [
            self._bin, "-p", text,
            "--agent", persona,
            "--output-format", "stream-json",
            "--verbose",  # required for stream-json events under --print
        ]
        if self.resume_session and self._session_id:
            cmd += ["--resume", self._session_id]
        return cmd

    def ask(self, text: str, persona: str | None = None) -> Iterator[dict]:
        """Send a turn to Claude Code headless; yield events:
        {"type":"session","id":...} · {"type":"text","text":...} ·
        {"type":"final","text":...} · {"type":"error","text":...}
        """
        persona = persona or self.default_persona
        proc = subprocess.Popen(
            self._command(text, persona),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue  # non-JSON logging noise

                etype = evt.get("type")
                if etype == "system" and evt.get("subtype") == "init":
                    self._session_id = evt.get("session_id", self._session_id)
                    yield {"type": "session", "id": self._session_id}
                elif etype == "assistant":
                    for block in evt.get("message", {}).get("content", []):
                        if block.get("type") == "text" and block.get("text"):
                            yield {"type": "text", "text": block["text"]}
                elif etype == "result":
                    self._session_id = evt.get("session_id", self._session_id)
                    if evt.get("is_error"):
                        yield {"type": "error", "text": evt.get("result", "unknown error")}
                    else:
                        yield {"type": "final", "text": evt.get("result", "")}
            proc.wait()
            if proc.returncode not in (0, None):
                err = (proc.stderr.read() or "").strip() if proc.stderr else ""
                yield {"type": "error", "text": err or f"claude exited {proc.returncode}"}
        finally:
            if proc.poll() is None:
                proc.terminate()
