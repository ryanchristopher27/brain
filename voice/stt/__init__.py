"""Speech-to-text backends. Select via config.toml [stt].backend."""
from .base import STT


def get_stt(backend: str, **kwargs) -> STT:
    """Factory: return the STT backend named in config."""
    if backend == "whisper":
        from .whisper import WhisperSTT
        return WhisperSTT(**kwargs)
    # B5: elif backend == "deepgram": from .deepgram import DeepgramSTT ...
    raise ValueError(f"unknown STT backend: {backend!r}")
