# services/runner/app/bus.py
from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from .contrats import Observation


class BusEtatMemoire:
    """Bus minimal: le runner pousse des observations, le TUI les lit."""

    def __init__(self, maxlen: int = 2000) -> None:
        self._q: Deque[Observation] = deque(maxlen=maxlen)

    def publier(self, obs: Observation) -> None:
        self._q.append(obs)

    def dernier(self) -> Optional[Observation]:
        return self._q[-1] if self._q else None
