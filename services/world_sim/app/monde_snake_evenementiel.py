from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .evenements import Evenement
from .monde_evenementiel import MondeEvenementiel
from .monde_snake import MondeSnake


@dataclass
class MondeSnakeEvenementiel(MondeEvenementiel):
    """Adaptateur : MondeSnake -> MondeEvenementiel.

    Règle v1 :
    - le runner transmet *tous* les événements d'un tick.
    - le monde décide comment interpréter (et éventuellement ignorer) les événements.
    - l'inaction n'est pas un événement : absence d'ActionMotrice => on conserve la dynamique par défaut du monde.

    Interprétation minimale v1 :
    - `type == "action_motrice"` avec payload {"direction": <str|None>} :
        - si direction est None : on laisse `MondeSnake.step(None)` (contrat historique : avance "avant")
        - sinon : `MondeSnake.step(direction)`
    - `tick_annonce` / `tick_survenu` : ignorés par la dynamique (serviront aux instruments/abonnés).
    """

    monde: MondeSnake
    _buffer: List[Evenement] = field(default_factory=list)

    def appliquer_evenements(self, evenements: List[Evenement]) -> None:
        self._buffer.extend(evenements)

    def tick(self) -> None:
        # Choix v1 (simple et explicite) :
        # - si plusieurs actions motrices sont émises, on garde la dernière reçue
        #   (pas une "réduction" du runner : décision locale du monde).
        direction: Optional[str] = None
        for evt in self._buffer:
            if evt.type == "action_motrice":
                direction = evt.payload.get("direction")  # peut être None

        self._buffer = []

        # Délègue au monde snake.
        self.monde.step(direction)
