# voice — talk to your Claude Code fleet

A local, self-contained voice core. Push-to-talk → local speech-to-text → **headless
Claude Code** (`claude -p`) → speech. Because it drives Claude Code, it inherits every brain
subagent and MCP for free. Defaults to the read-only **Scout** persona; autonomous personas
are summoned by explicit spoken command.

It also emits session-state events over a local websocket that the [`../web`](../web)
visualizer subscribes to — one backend, two frontends.

```
hotkey ▸ mic capture ▸ whisper.cpp (STT) ▸ claude -p (bridge) ▸ say/Piper (TTS)
                        └──────────── server.broadcast(state) ───────────┘
```

## Layout
| Path | Role |
|------|------|
| `daemon.py` | Entry point — assembles and runs the pipeline |
| `server.py` | Local websocket event stream for the visualizer |
| `bridge/claude.py` | Headless `claude -p` wrapper (persona-aware, session-resuming) |
| `stt/` | Pluggable STT — `whisper` (local, default); cloud in B5 |
| `tts/` | Pluggable TTS — `say` (local, default); Piper/cloud later |
| `config.toml` | Hotkey + backend selection |
| `.env.example` | Cloud-backend keys (only if you enable them) |

## Setup (macOS, Apple Silicon)
```sh
# System deps
brew install portaudio          # for sounddevice
brew install whisper-cpp        # or rely on pywhispercpp's bundled build

# Python env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
Grant the terminal **Microphone** and **Accessibility** permissions (System Settings →
Privacy & Security) — Accessibility is needed for the global push-to-talk hotkey.

## Run
All commands use the venv created above (`./.venv/bin/python`, or activate it first).
```sh
python -m voice.daemon --check          # self-test: event stream live, then exit (no mic/claude)
python -m voice.daemon --ask "hi there" # text-in / voice-out: skip the mic, talk to Claude, hear reply
python -m voice.daemon --demo "hi there"# mic-free, but drives the web visualizer (open web/ then Enter)
python -m voice.daemon                  # full push-to-talk loop — hold the hotkey (needs perms)
python -m voice.server                  # standalone event stream only (Ctrl-C to stop)
```
`--ask` is the mic-free way to exercise the whole Claude path (bridge → TTS) — no Microphone
or Accessibility grants needed.
`--check` needs no mic or permissions. The real loop needs **Microphone + Accessibility**
grants for the terminal (the hotkey is a global listener). Hold the push-to-talk key
(`alt_r` by default) to record; release to stop — the console prints the captured duration
and the visualizer flips listening→idle.

Watch it visually:
```sh
python -m voice.daemon &                    # runs the event stream + hotkey loop
cd ../web && python3 -m http.server 5173    # open http://127.0.0.1:5173
```

## Status → milestones
- **B1 ✅** hotkey + mic capture (`audio.py`) + live event stream (`server.py`) — done
- **B2 ✅** whisper.cpp transcription (`stt/whisper.py`, Metal-accelerated) wired into the
  release handler; model pre-warms on startup — done
- **B3 ✅** `say` playback (`tts/say.py`) — done
- **B4 ✅** headless Claude bridge (`bridge/claude.py`) — `claude -p --agent scout
  --output-format stream-json --verbose` with `--resume` for session continuity. Wired into
  the release handler (echo replaced) and exposed via `--ask`. Verified: two-turn resume +
  read-only Scout enforcement. **Done — voice now reaches the full fleet.**
- **B5** optional cloud STT/TTS backends

### Full loop (B1–B4)
`hold alt_r → whisper STT → claude -p (Scout, all personas+MCPs) → say TTS`, with the visualizer
mirroring listening → thinking → speaking. Voice defaults to the read-only Scout persona;
`bridge/claude.py` never passes `--dangerously-skip-permissions`. Summoning an autonomous
persona (Builder/Operator) by voice is deferred — writes need a permission strategy headless
`-p` can't prompt for.

Installed in the venv: `sounddevice numpy pynput websockets tomli` (B1) + `pywhispercpp cmake`
(B2). The `base.en` model (~141 MB) auto-downloads on first transcription to
`~/Library/Application Support/pywhispercpp/models/`.

Full loop now: hold hotkey → record → release → **transcribe** → console prints the text and
the visualizer shows it. Sending that text to Claude + speaking the reply is **B4**.
