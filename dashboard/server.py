"""Dashboard control server (D1).

FastAPI app that:
- serves the `web/` frontend,
- hosts a websocket hub for live events,
- subscribes to the voice core (127.0.0.1:8765) and re-broadcasts its events,
- enforces a local security boundary: a Host/Origin check (DNS-rebinding + cross-origin
  hardening) plus a same-origin-issued bearer token on the ws.

No agent-execution actions yet — those arrive in D4/D5. Read panels (roster/jobs/health) are
D3. Run:  ./voice/.venv/bin/python -m dashboard.server
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import secrets
import shutil
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import data, registry
from .process_manager import ProcessManager, SpawnError
from .voice_bridge import VoiceBridge

HOST = "127.0.0.1"
PORT = 8766
VOICE_WS = "ws://127.0.0.1:8765"
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
TOKEN_PATH = Path.home() / ".claude" / "brain-dashboard" / "token"
ALLOWED_HOSTS = {f"{HOST}:{PORT}", f"localhost:{PORT}"}
ALLOWED_ORIGINS = {f"http://{h}" for h in ALLOWED_HOSTS}


def _load_token() -> str:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text().strip()
    tok = secrets.token_urlsafe(32)
    TOKEN_PATH.write_text(tok)
    TOKEN_PATH.chmod(0o600)
    return tok


TOKEN = _load_token()


class Hub:
    """Fan-out to connected dashboard browsers."""

    def __init__(self):
        self._clients: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def broadcast(self, event: dict) -> None:
        if not self._clients:
            return
        payload = json.dumps(event)
        dead = []
        for c in list(self._clients):
            try:
                await c.send_text(payload)
            except Exception:
                dead.append(c)
        for c in dead:
            self._clients.discard(c)


hub = Hub()
bridge = VoiceBridge(VOICE_WS, hub.broadcast)
pm = ProcessManager(hub, claude_bin=shutil.which("claude") or "claude")


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(bridge.run())
    try:
        yield
    finally:
        await pm.stop_all()  # never leave spawned agents running past the server
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(lifespan=lifespan, title="brain dashboard")


@app.middleware("http")
async def guard(request: Request, call_next):
    """Only serve requests addressed to localhost, and reject foreign Origins.
    This is the core defense against DNS-rebinding and cross-origin abuse of a local API."""
    if request.headers.get("host", "") not in ALLOWED_HOSTS:
        return PlainTextResponse("forbidden host", status_code=403)
    origin = request.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        return PlainTextResponse("forbidden origin", status_code=403)
    # Bearer token required on every /api route except the bootstrap /api/config.
    path = request.url.path
    if path.startswith("/api/") and path != "/api/config":
        if request.headers.get("authorization") != f"Bearer {TOKEN}":
            return PlainTextResponse("unauthorized", status_code=401)
    return await call_next(request)


@app.get("/api/config")
async def config():
    # Same-origin readable; cross-origin JS cannot read the body (no CORS headers sent).
    return JSONResponse({"token": TOKEN, "voice_connected": bridge.connected})


@app.get("/api/health")
async def health():
    return JSONResponse({"ok": True, "voice_connected": bridge.connected, **data.read_health()})


@app.get("/api/agents")
async def agents():
    return JSONResponse(data.read_agents())


@app.get("/api/jobs")
async def jobs():
    return JSONResponse(data.read_jobs())


@app.get("/api/schedule")
async def schedule():
    return JSONResponse(data.read_schedule())


@app.get("/api/pipeline")
async def pipeline():
    return JSONResponse(data.read_pipeline())


@app.get("/api/runs")
async def runs():
    try:
        conn = registry.open_db()
        out = {"runs": registry.recent_runs(conn), "totals": registry.totals(conn),
               "active": pm.active(), "pending": pm.pending(), "queued": pm.queued()}
        conn.close()
        return JSONResponse(out)
    except Exception:
        return JSONResponse({"runs": [], "totals": {"runs": 0, "cost_usd": 0.0},
                             "active": [], "pending": [], "queued": []})


class SpawnReq(BaseModel):
    persona: str
    task: str
    add_dir: str | None = None


@app.post("/api/runs/spawn")
async def spawn_run(req: SpawnReq):
    try:
        return JSONResponse(await pm.spawn(req.persona, req.task, req.add_dir))
    except SpawnError as e:
        return JSONResponse({"error": str(e)}, status_code=e.status)


@app.post("/api/runs/propose")
async def propose_run(req: SpawnReq):
    try:
        return JSONResponse(await pm.propose(req.persona, req.task, req.add_dir))
    except SpawnError as e:
        return JSONResponse({"error": str(e)}, status_code=e.status)


@app.post("/api/runs/{run_id}/approve")
async def approve_run(run_id: str):
    try:
        return JSONResponse(await pm.approve(run_id))
    except SpawnError as e:
        return JSONResponse({"error": str(e)}, status_code=e.status)


@app.post("/api/runs/{run_id}/deny")
async def deny_run(run_id: str):
    ok = await pm.deny(run_id)
    return JSONResponse({"denied": ok}, status_code=200 if ok else 404)


@app.post("/api/runs/{run_id}/stop")
async def stop_run(run_id: str):
    ok = await pm.stop(run_id)
    return JSONResponse({"stopped": ok}, status_code=200 if ok else 404)


@app.post("/api/queue")
async def enqueue_task(req: SpawnReq):
    try:
        return JSONResponse(await pm.enqueue(req.persona, req.task, req.add_dir))
    except SpawnError as e:
        return JSONResponse({"error": str(e)}, status_code=e.status)


@app.post("/api/queue/{item_id}/remove")
async def remove_task(item_id: str):
    ok = pm.dequeue(item_id)
    return JSONResponse({"removed": ok}, status_code=200 if ok else 404)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    # ws upgrades bypass http middleware — re-check host/origin + require the token here.
    host = ws.headers.get("host", "")
    origin = ws.headers.get("origin")
    if host not in ALLOWED_HOSTS or (origin is not None and origin not in ALLOWED_ORIGINS):
        await ws.close(code=1008)
        return
    if ws.query_params.get("token") != TOKEN:
        await ws.close(code=1008)
        return
    await hub.connect(ws)
    try:
        await ws.send_text(json.dumps({"type": "hello", "msg": "dashboard"}))
        while True:
            await ws.receive_text()  # read-only display — ignore inbound
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(ws)


# Serve the frontend last, so /api/* and /ws take precedence over the static mount.
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


def main() -> None:
    import uvicorn

    print(f"[dashboard] http://{HOST}:{PORT}  (token at {TOKEN_PATH})")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
