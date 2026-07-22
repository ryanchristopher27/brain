"""Local event stream for the web/ visualizer.

Broadcasts voice-session state (listening / thinking / speaking, active persona, partial
transcript) over a local websocket. The web page subscribes; one backend, two frontends.

Two ways to run it:
- Standalone smoke test:      python -m voice.server   (async serve, blocks)
- Embedded in the daemon:     server.start_in_thread(); server.emit({...})  (thread-safe)
"""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

try:
    import websockets
except ImportError:  # keep import-safe before deps are installed
    websockets = None


class EventServer:
    """Fan-out hub. The daemon calls emit(); connected browsers receive."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    async def _handler(self, ws):
        self._clients.add(ws)
        try:
            await ws.send(json.dumps({"type": "hello", "msg": "voice event stream"}))
            async for _ in ws:  # visualizer is read-only; ignore inbound
                pass
        finally:
            self._clients.discard(ws)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Push a state event to every connected visualizer."""
        if not self._clients:
            return
        payload = json.dumps(event)
        await asyncio.gather(
            *(c.send(payload) for c in self._clients), return_exceptions=True
        )

    # ── standalone async mode ────────────────────────────────────────────────
    async def serve(self) -> None:
        if websockets is None:
            raise RuntimeError("pip install -r requirements.txt (websockets missing)")
        async with websockets.serve(self._handler, self.host, self.port):
            print(f"[voice.server] ws://{self.host}:{self.port} — waiting for visualizer")
            await asyncio.Future()  # run forever

    # ── embedded (threaded) mode, for the daemon ─────────────────────────────
    def start_in_thread(self) -> None:
        """Run the event loop in a background thread so sync code can emit()."""
        if websockets is None:
            raise RuntimeError("pip install -r requirements.txt (websockets missing)")
        ready = threading.Event()

        def run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            async def _boot():
                await websockets.serve(self._handler, self.host, self.port)
                ready.set()

            self._loop.run_until_complete(_boot())
            self._loop.run_forever()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        ready.wait(timeout=5)

    def emit(self, event: dict[str, Any]) -> None:
        """Thread-safe broadcast — callable from the hotkey/audio threads."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(event), self._loop)


if __name__ == "__main__":
    srv = EventServer()
    try:
        asyncio.run(srv.serve())
    except KeyboardInterrupt:
        print("\n[voice.server] stopped")
