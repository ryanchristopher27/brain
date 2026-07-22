"""Local TTS via macOS `say`. Zero-dependency baseline.

Speaks synchronously (blocks until playback finishes) but tracks the process so a future
barge-in / interrupt can stop it. B4 will call speak() per sentence as Claude streams.
"""
from __future__ import annotations

import subprocess

from .base import TTS


class SayTTS(TTS):
    def __init__(self, voice: str = "Samantha", rate: int | None = None, **_):
        self.voice = voice
        self.rate = rate
        self._proc: subprocess.Popen | None = None

    def speak(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        cmd = ["say", "-v", self.voice]
        if self.rate:
            cmd += ["-r", str(self.rate)]
        cmd.append(text)
        self._proc = subprocess.Popen(cmd)
        try:
            self._proc.wait()
        finally:
            self._proc = None

    def stop(self) -> None:
        """Interrupt current playback (for future barge-in support)."""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None
