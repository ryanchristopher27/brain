"""TTS interface. All backends implement speak()."""
from __future__ import annotations

from abc import ABC, abstractmethod


class TTS(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Speak `text` aloud, blocking until playback finishes."""
        raise NotImplementedError
