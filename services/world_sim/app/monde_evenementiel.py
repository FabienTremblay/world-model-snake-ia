from __future__ import annotations

from typing import List, Protocol

from .evenements import Evenement


class MondeEvenementiel(Protocol):
    """Interface minimale pour brancher le runner événementiel.

    Règle v1 :
    - le runner NE filtre PAS.
    - le monde reçoit la liste complète des événements d'un tick.
    """

    def appliquer_evenements(self, evenements: List[Evenement]) -> None:
        ...

    def tick(self) -> None:
        ...
