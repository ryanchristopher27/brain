"""voice core — entry point.

Wires the pipeline: push-to-talk hotkey -> mic capture -> STT -> Claude bridge -> TTS,
emitting session-state events to the visualizer along the way.

    hotkey ▸ capture ▸ whisper(STT) ▸ claude -p(bridge) ▸ say/Piper(TTS)
                         └────────── server.emit(state) ──────────┘

B1 (this): hotkey + mic capture + live event stream. Hold the push-to-talk key to record;
release to stop — the visualizer flips listening→idle and the captured audio is measured.
STT/bridge/TTS (B2–B4) plug into the released buffer next.

    python -m voice.daemon           # run the push-to-talk loop (needs mic + accessibility)
    python -m voice.daemon --check   # assemble + start server, verify, exit (no hotkey/mic)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from .audio import Recorder
from .bridge import ClaudeBridge
from .server import EventServer
from .stt import get_stt
from .tts import get_tts

CONFIG_PATH = Path(__file__).with_name("config.toml")


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def build(cfg: dict):
    """Construct the pipeline components from config (no I/O yet)."""
    stt = get_stt(cfg["stt"]["backend"], model=cfg["stt"].get("model", "base.en"))
    tts = get_tts(cfg["tts"]["backend"], voice=cfg["tts"].get("voice", "Samantha"))
    bridge = ClaudeBridge(
        default_persona=cfg["bridge"].get("default_persona", "scout"),
        resume_session=cfg["bridge"].get("resume_session", True),
    )
    server = EventServer(cfg["server"]["host"], cfg["server"]["port"])
    return stt, tts, bridge, server


def parse_hotkey(name: str):
    """Map a config key name (e.g. 'alt_r', 'f13', 'x') to a pynput key."""
    from pynput import keyboard

    key = getattr(keyboard.Key, name, None)
    if key is not None:
        return key
    if len(name) == 1:
        return keyboard.KeyCode.from_char(name)
    raise ValueError(f"unknown push_to_talk key: {name!r}")


def _run_bridge(bridge, text: str) -> str:
    """Drive one bridge turn; return the assistant's reply text."""
    reply = ""
    try:
        for ev in bridge.ask(text):
            if ev["type"] == "text":
                reply += ev["text"]
            elif ev["type"] == "final":
                reply = ev["text"] or reply
            elif ev["type"] == "error":
                print(f"[voice] bridge error: {ev['text']}")
    except Exception as e:  # keep the loop alive on a bad turn
        print(f"[voice] bridge exception: {type(e).__name__}: {e}")
    return reply.strip()


def _print_ready(cfg, bridge, server):
    print("[voice] core assembled:")
    print(f"  hotkey  : hold {cfg['hotkey']['push_to_talk']}")
    print(f"  stt     : {cfg['stt']['backend']} ({cfg['stt'].get('model')})")
    print(f"  tts     : {cfg['tts']['backend']}")
    print(f"  persona : {bridge.default_persona} (voice default)")
    print(f"  events  : ws://{server.host}:{server.port}")


def run(cfg: dict) -> int:
    from pynput import keyboard

    stt, tts, bridge, server = build(cfg)
    server.start_in_thread()
    recorder = Recorder(samplerate=16000)
    ptt = parse_hotkey(cfg["hotkey"]["push_to_talk"])

    _print_ready(cfg, bridge, server)
    server.emit({"type": "state", "value": "idle"})
    server.emit({"type": "persona", "name": bridge.default_persona})

    # Preload the STT model in the background so the first utterance isn't slow.
    if hasattr(stt, "warm"):
        import threading
        threading.Thread(target=stt.warm, daemon=True).start()

    print(f"[voice] ready — hold {cfg['hotkey']['push_to_talk']} to talk. Ctrl-C to quit.")

    def on_press(key):
        if key == ptt and not recorder.is_recording:
            recorder.start()
            server.emit({"type": "state", "value": "listening"})
            print("[voice] ● listening…")

    def on_release(key):
        if key == ptt and recorder.is_recording:
            audio = recorder.stop()
            dur = len(audio) / recorder.samplerate if len(audio) else 0.0
            if len(audio) == 0:
                server.emit({"type": "state", "value": "idle"})
                return
            server.emit({"type": "state", "value": "thinking"})
            print(f"[voice] … transcribing {dur:.1f}s")
            try:
                text = stt.transcribe(audio, recorder.samplerate)
            except Exception as e:  # keep the loop alive on a bad turn
                text = ""
                print(f"[voice] STT error: {type(e).__name__}: {e}")
            server.emit({"type": "transcript", "text": text, "final": True, "role": "user"})
            print(f"[voice] ✓ heard: {text!r}")
            if not text:
                server.emit({"type": "state", "value": "idle"})
                return
            # B4: send to Claude (headless, default persona) and speak the reply.
            reply = _run_bridge(bridge, text)
            print(f"[voice] ↳ claude: {reply!r}")
            if reply:
                server.emit({"type": "transcript", "text": reply,
                             "final": True, "role": "assistant"})
                server.emit({"type": "state", "value": "speaking"})
                tts.speak(reply)
            server.emit({"type": "state", "value": "idle"})

    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n[voice] stopped")
    return 0


def check(cfg: dict) -> int:
    """Non-interactive self-test: assemble, start the event server, verify a client can
    connect and receive an emitted event. No hotkey listener, no mic."""
    import asyncio

    import websockets

    stt, tts, bridge, server = build(cfg)
    server.start_in_thread()
    _print_ready(cfg, bridge, server)

    async def roundtrip():
        uri = f"ws://{server.host}:{server.port}"
        async with websockets.connect(uri) as ws:
            hello = await asyncio.wait_for(ws.recv(), timeout=3)
            server.emit({"type": "state", "value": "listening"})
            evt = await asyncio.wait_for(ws.recv(), timeout=3)
            return hello, evt

    hello, evt = asyncio.run(roundtrip())
    print(f"[voice] --check: server hello={hello}")
    print(f"[voice] --check: received emitted event={evt}")
    print("[voice] --check OK — event stream live. Hotkey/mic path needs a real session.")
    return 0


def ask_once(cfg: dict, question: str) -> int:
    """Text-in / voice-out: skip the mic, send one prompt through the bridge, speak the
    reply. Verifies the Claude path without microphone or Accessibility perms."""
    if not question:
        print('usage: python -m voice.daemon --ask "your question"')
        return 2
    _, tts, bridge, _ = build(cfg)
    print(f"[voice] → {bridge.default_persona}: {question!r}")
    reply = _run_bridge(bridge, question)
    print(f"[voice] ↳ {reply!r}")
    if reply:
        tts.speak(reply)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    cfg = load_config()
    if "--check" in argv:
        return check(cfg)
    if "--ask" in argv:
        i = argv.index("--ask")
        question = argv[i + 1] if i + 1 < len(argv) else ""
        return ask_once(cfg, question)
    return run(cfg)


if __name__ == "__main__":
    sys.exit(main())
