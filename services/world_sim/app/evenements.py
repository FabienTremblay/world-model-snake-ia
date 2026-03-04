from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Evenement:
    """Événement du monde (message daté).

    Convention v1 :
    - Les *actions* (motrices/instrumentales/...) sont des événements.
    - L'inaction = absence d'événement d'action émis par une source à un tick.
    """
    type: str
    source_id: str
    tick: int
    payload: Dict[str, Any] = field(default_factory=dict)


class BusEvenements:
    """Bus minimal.

    - En mode F (push), les objets publient directement ici.
    - En mode E (pull), le bus sert d'agrégateur local pendant le tick.
    """

    def __init__(self) -> None:
        self._buffer: List[Evenement] = []

    def publier(self, evt: Evenement) -> None:
        self._buffer.append(evt)

    def publier_tick_annonce(self, tick: int) -> None:
        self.publier(Evenement(type="tick_annonce", source_id="horloge", tick=tick, payload={}))

    def publier_tick_survenu(self, tick: int) -> None:
        self.publier(Evenement(type="tick_survenu", source_id="horloge", tick=tick, payload={}))

    def drainer(self) -> List[Evenement]:
        out = self._buffer
        self._buffer = []
        return out
