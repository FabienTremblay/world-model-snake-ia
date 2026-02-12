from __future__ import annotations

import random
from typing import Any

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene


class AgentSnakeCollectifV1C1(IAgentArene):
    """Agent démo C1 (incarné seul) — conforme au contrat IAgentArene.

    Politique volontairement simple : mouvement aléatoire.
    """

    id_agent = "snake_collectif_v1_c1"

    def __init__(self, seed: int | None = None, instruments: list[object] | None = None) -> None:
        self.rng = random.Random(seed)
        self._instruments = list(instruments or [])

    def definir_instruments(self, instruments: list[object]) -> None:
        self._instruments = list(instruments)

    def instruments(self) -> list[Any]:
        return list(self._instruments)

    def choisir_action(self, contexte: ContexteDecision) -> str:
        return self.rng.choice(["N", "E", "S", "W"])
