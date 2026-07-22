"""Push-to-talk mic capture (sounddevice / PortAudio).

Recorder.start() opens a mono input stream and buffers frames on the PortAudio callback
thread; stop() closes it and returns the captured audio as a flat float32 numpy array,
ready for the STT backend in B2.
"""
from __future__ import annotations

import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, samplerate: int = 16000, channels: int = 1):
        self.samplerate = samplerate
        self.channels = channels
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []

    # PortAudio thread — keep it minimal, just buffer.
    def _callback(self, indata, frames, time_info, status):  # noqa: ARG002
        if status:
            print(f"[audio] stream status: {status}")
        self._frames.append(indata.copy())

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
