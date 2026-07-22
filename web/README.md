# web — voice visualizer

A local page that is a **live visual embodiment of the voice agent** you're talking to:
agent state (listening / thinking / speaking), the active persona, and a rolling transcript.

It **reflects** the voice session — it is **not** a chat box and **not** a control panel.
It subscribes (read-only) to the event stream that [`../voice/server.py`](../voice/server.py)
broadcasts. One backend, two frontends (audio + visual).

## Run
```sh
# 1. start the voice event stream
cd ../voice && python -m voice.server

# 2. serve this page (any static server)
cd ../web && python3 -m http.server 5173
# open http://127.0.0.1:5173
```
With only `voice.server` running you'll see it connect and sit idle. Live state appears once
the voice bridge emits events (milestone **B4**).

## Event vocabulary (consumed)
| Event | Effect |
|-------|--------|
| `{type:"state", value:"listening\|thinking\|speaking\|idle"}` | Orb color + label |
| `{type:"persona", name:"scout"}` | Active-persona line |
| `{type:"transcript", text, final}` | Rolling transcript |

The authoritative vocabulary is defined by the voice bridge in B4.

## Status → milestones
- **C1** subscribe + render state/persona/transcript (this scaffold)
- **C2** animated orb/waveform tied to audio level; per-persona visual identity (via `/design`)
