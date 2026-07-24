"""Push-to-talk mic capture (sounddevice / PortAudio).

Recorder.start() opens a mono input stream and buffers frames on the PortAudio callback
thread; stop() closes it and returns the captured audio as a flat float32 numpy array,
ready for the STT backend in B2.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import sounddevice as sd


def rms_level(block: np.ndarray, sensitivity: float = 1.8) -> float:
    """Normalized 0..1 loudness of an audio block — drives the visualizer's reactive orb.

    Uses a compressive (sqrt) curve so quiet speech is still visible and loud speech doesn't
    peg to 1.0 instantly. Raise `sensitivity` for a livelier orb, lower it for a calmer one.
    """
    if block.size == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(np.square(block.astype(np.float64)))))
    return max(0.0, min(1.0, (rms ** 0.5) * sensitivity))


class Recorder:
    def __init__(self, samplerate: int = 16000, channels: int = 1,
                 on_level: Callable[[float], None] | None = None):
        self.samplerate = samplerate
        self.channels = channels
        self._on_level = on_level
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []

    # PortAudio thread — keep it minimal: buffer, and report loudness for the visualizer.
    def _callback(self, indata, frames, time_info, status):  # noqa: ARG002
        if status:
            print(f"[audio] stream status: {status}")
        self._frames.append(indata.copy())
        if self._on_level is not None:
            try:
                self._on_level(rms_level(indata.reshape(-1)))
            except Exception:
                pass  # never let a viz hiccup disrupt capture

    def start(self) -> None:
        if self._stream is not None:
            return
        self._frames = []
        try:
            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
        except Exception as e:  # device may reject the rate; surface, don't crash the loop
            self._stream = None
            print(f"[audio] could not open input stream: {type(e).__name__}: {e}")

    def stop(self) -> np.ndarray:
        if self._stream is None:
            return np.zeros(0, dtype="float32")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        if not self._frames:
            return np.zeros(0, dtype="float32")
        audio = np.concatenate(self._frames, axis=0).reshape(-1)
        self._frames = []
        return audio

    @property
    def is_recording(self) -> bool:
        return self._stream is not None
