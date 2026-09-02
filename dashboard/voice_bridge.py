"""Subscribe to the voice core's websocket and forward its events to the dashboard hub.

Per the D1 recon decision, the dashboard is a *subscriber* to voice — voice stays unchanged
and runs standalone on 127.0.0.1:8765. This keeps all integration complexity in the dashboard
and leaves the working voice loop untouched. Reconnects with backoff if voice isn't up.
"""
from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable

try:
    import websockets
except ImportError:  # keep import-safe before deps are installed
    websockets = None


class VoiceBridge:
    def __init__(self, url: str, forward: Callable[[dict], Awaitable[None]]):
        self.url = url
        self._forward = forward
        self.connected = False
        self._ws = None  # live voice socket, for sending control commands upstream

    async def send(self, msg: dict) -> bool:
        """Forward a control message (e.g. dashboard mic → record_toggle) to the voice core.
        Returns False when voice isn't connected. The voice daemon only acts on it if it has
        registered a command handler; otherwise it's ignored, so this stays safe."""
        if self._ws is None or not self.connected:
            return False
        try:
            await self._ws.send(json.dumps(msg))
            return True
        except Exception:
            return False

    async def run(self) -> None:
        if websockets is None:
            print("[dashboard] websockets missing — voice bridge disabled")
            return
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    self.connected = True
                    self._ws = ws
                    print(f"[dashboard] voice connected: {self.url}")
                    async for raw in ws:
                        try:
                            evt = json.loads(raw)
                        except (ValueError, TypeError):
                            continue
                        await self._forward(evt)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass  # voice not up / dropped — retry
            finally:
                self.connected = False
                self._ws = None
            await asyncio.sleep(2)  # reconnect backoff
