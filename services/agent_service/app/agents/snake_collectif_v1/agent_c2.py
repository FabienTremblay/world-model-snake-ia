from __future__ import annotations

import random
from typing import Any

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene


class AgentSnakeCollectifV1C2(IAgentArene):
    """Agent démo C2 — conforme au contrat IAgentArene.

    Politique simple (différente de C1 pour la démo) : biais vers l'Est.
    """

    id_agent = "snake_collectif_v1_c2"

    def __init__(self, seed: int | None = None, instruments: list[object] | None = None, proba_est: float = 0.55) -> None:
        self.rng = random.Random(seed)
        self.proba_est = float(proba_est)
        self._instruments = list(instruments or [])

    def definir_instruments(self, instruments: list[object]) -> None:
        self._instruments = list(instruments)

    def instruments(self) -> list[Any]:
        return list(self._instruments)

    def choisir_action(self, contexte: ContexteDecision) -> str:
        if self.rng.random() < self.proba_est:
            return "E"
        return self.rng.choice(["N", "S", "W"])
