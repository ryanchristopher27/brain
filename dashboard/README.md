# dashboard — local agent control server

A FastAPI app that serves the `web/` frontend, aggregates live events, and (later) lets you
act on agents. It is the central hub: it **subscribes** to the voice core and re-broadcasts,
so voice stays unchanged and standalone.

```
  voice daemon (8765) ──▶ dashboard (8766) ──▶ web/ frontend
   background runner  ──▶   hub · API · (D4 actions) · (D6 registry)
```

## Security (D1, mandatory)
- Binds `127.0.0.1` only.
- **Host check** on every request (DNS-rebinding protection) — non-localhost `Host` → 403.
- **Origin check** — a present, foreign `Origin` → 403.
- **Token**: a random token (`~/.claude/brain-dashboard/token`, mode 600) is issued via
  `/api/config` (same-origin readable only) and required on the `/ws` upgrade. Future action
  endpoints (D4) will require it too. Cross-origin pages can't read the token (no CORS headers).

## Run
```sh
./voice/.venv/bin/python -m dashboard.server     # http://127.0.0.1:8766
```
Open the URL in a browser. Optionally run `python -m voice.daemon` too — the dashboard picks
up the voice session automatically (the orb reflects it). Without voice, the dashboard still
serves; the voice panel just shows disconnected.

## Endpoints (D1)
| Route | Purpose |
|-------|---------|
| `GET /` | the `web/` frontend |
| `GET /api/config` | `{token, voice_connected}` (same-origin) |
| `GET /api/health` | `{ok, voice_connected}` |
| `WS  /ws?token=…` | live event hub (voice events re-broadcast) |

## Status → milestones
- **D1 ✅** server + Host/Origin/token security + voice-subscribe proxy
- **D3** read panels: roster · jobs · health · activity
- **D2** orb absorbed as the active-session panel
- **D7** work-pipeline board
