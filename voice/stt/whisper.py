"""Local STT via whisper.cpp (pywhispercpp). Metal-accelerated on Apple Silicon.

The model is lazy-loaded on first transcribe so constructing the daemon stays instant; the
ggml weights auto-download to pywhispercpp's cache on first use.
"""
from __future__ import annotations

import numpy as np

from .base import STT

TARGET_SR = 16000  # whisper.cpp expects 16 kHz mono float32


class WhisperSTT(STT):
    def __init__(self, model: str = "base.en", **_):
        self.model_name = model
        self._model = None  # lazy

    def _ensure_model(self):
        if self._model is None:
            from pywhispercpp.model import Model
            # Quiet the native logs; only surface the text.
            self._model = Model(self.model_name, print_realtime=False, print_progress=False)
        return self._model

    def warm(self) -> None:
        """Preload the model (Metal init + weights) so the first utterance isn't slow."""
        self._ensure_model()

    def transcribe(self, audio, sample_rate: int) -> str:
        audio = np.asarray(audio, dtype="float32").reshape(-1)
        if audio.size == 0:
            return ""
        if sample_rate != TARGET_SR:
            audio = _resample(audio, sample_rate, TARGET_SR)
        model = self._ensure_model()
        segments = model.transcribe(audio)
        return "".join(seg.text for seg in segments).strip()


def _resample(audio: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Lightweight linear resample — adequate for speech STT."""
    if sr_in == sr_out or audio.size == 0:
        return audio
    n_out = int(round(audio.size * sr_out / sr_in))
    if n_out <= 0:
        return np.zeros(0, dtype="float32")
    x_old = np.linspace(0.0, 1.0, num=audio.size, endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
    return np.interp(x_new, x_old, audio).astype("float32")
