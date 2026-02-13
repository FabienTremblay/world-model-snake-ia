from __future__ import annotations

import random

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene
from commun.actions_snake import (
    ACTION_AVANT,
    ACTION_OBSERVER_DROITE,
    ACTION_OBSERVER_GAUCHE,
    ActionSnake,
)


class AgentSnakeCollectifV1C2(IAgentArene):
    """Agent C2 — 'fourmi' minimaliste.

    Idée :
      - fait plus d'observation que C1 (caméra egocentrée) pour générer des traces exploitables
        par les observateurs (SAI-A106/A107), sans coder dur des concepts métier.

    Stratégie :
      - forte proba d'observer (gauche/droite)
      - sinon avance
    """

    def __init__(self, seed: int | None = None, p_observer: float = 0.7):
        self.rng = random.Random(seed)
        self.p_observer = float(p_observer)

    def choisir_action(self, ctx: ContexteDecision) -> ActionSnake:
        if self.rng.random() < self.p_observer:
            return self.rng.choice([ACTION_OBSERVER_GAUCHE, ACTION_OBSERVER_DROITE])
        return ACTION_AVANT
