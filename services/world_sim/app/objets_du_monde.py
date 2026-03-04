from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .evenements import BusEvenements


@dataclass(frozen=True)
class ContexteTick:
    tick: int


class ObjetDuMonde(Protocol):
    """Contrat v1.

    Un objet du monde est passif ou actif.
    - passif : n'émet rien
    - actif  : peut émettre 0..N événements (inaction = 0)
    """
    objet_id: str
    est_actif: bool

    def emettre_evenements(self, ctx: ContexteTick, bus: BusEvenements) -> None:
        ...
