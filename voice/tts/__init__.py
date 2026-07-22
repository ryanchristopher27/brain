"""Text-to-speech backends. Select via config.toml [tts].backend."""
from .base import TTS


def get_tts(backend: str, **kwargs) -> TTS:
    """Factory: return the TTS backend named in config."""
    if backend == "say":
        from .say import SayTTS
        return SayTTS(**kwargs)
    # B3: elif backend == "piper": ...
    # B5: elif backend in ("elevenlabs", "openai"): ...
    raise ValueError(f"unknown TTS backend: {backend!r}")
