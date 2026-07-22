"""STT interface. All backends implement transcribe()."""
from __future__ import annotations

from abc import ABC, abstractmethod


class STT(ABC):
    @abstractmethod
    def transcribe(self, audio, sample_rate: int) -> str:
        """Turn a mono PCM audio buffer into text. `audio` is a numpy float32 array."""
        raise NotImplementedError
