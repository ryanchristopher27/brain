# web — voice visualizer

A local page that is a **live visual embodiment of the voice agent** you're talking to:
agent state (listening / thinking / speaking), the active persona, and a rolling transcript.

It **reflects** the voice session — it is **not** a chat box and **not** a control panel.
It subscribes (read-only) to the event stream that [`../voice/server.py`](../voice/server.py)
broadcasts. One backend, two frontends (audio + visual).

## Run

**Watch a real turn without a mic** (easiest — uses `--demo`):
```sh
# terminal 1: serve this page
cd web && python3 -m http.server 5173      # open http://127.0.0.1:5173

# terminal 2: drive one prompt through the loop
cd voice && ./.venv/bin/python -m voice.daemon --demo "what is in the voice directory?"
# open the page first, then press Enter — watch the orb go thinking → speaking
```

**Live push-to-talk** (needs mic + Accessibility): run `python -m voice.daemon` in terminal 2
instead, then hold the hotkey. The orb and transcript follow every utterance.

The page reconnects on its own, so you can start it before or after the daemon.

## Event vocabulary (consumed)
| Event | Effect |
|-------|--------|
| `{type:"state", value:"listening\|thinking\|speaking\|idle"}` | Orb color + label |
| `{type:"persona", name:"scout"}` | Active-persona line |
| `{type:"transcript", text, final}` | Rolling transcript |

The authoritative vocabulary is defined by the voice bridge in B4.

## Status → milestones
- **C1 ✅** subscribes + renders state (orb + label), persona, and a role-tagged rolling
  transcript; connection badge; auto-reconnect. Event contract verified end-to-end. Done
- **C2 ✅** the orb is alive: idle *breathes*, **listening reacts to real mic level**
  (`level` events, compressive curve), thinking sweeps, speaking pulses; per-persona ring +
  label identity (scout/reviewer/builder/operator); OKLCH tokens; full `prefers-reduced-motion`
  path. Detector audit: 0 findings. Done (built via `/design`)

Tuning: the orb's reactivity lives in `rms_level(sensitivity=1.8)` in `../voice/audio.py` —
raise for a livelier orb, lower for calmer.
