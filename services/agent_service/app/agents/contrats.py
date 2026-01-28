from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from commun.contrats import Pixel


@dataclass(frozen=True)
class ContexteDecision:
    """Contexte minimal fourni à l'agent lors d'une décision."""

    run_id: str
    episode_id: int
    tick: int
    largeur: int
    hauteur: int


class IAgent(Protocol):
    """Contrat minimal d'un agent.

    L'agent choisit une direction à partir des capteurs (observation).
    Il peut conserver un état interne (mémoire) s'il le souhaite.
    """

    def choisir_action(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> str:
        ...
