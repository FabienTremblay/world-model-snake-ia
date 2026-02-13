from __future__ import annotations

import random

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene
from commun.actions_snake import (
    ACTION_AVANT,
    ACTION_OBSERVER_DROITE,
    ACTION_OBSERVER_GAUCHE,
    ActionSnake,
)


class AgentSnakeCollectifV1C1(IAgentArene):
    """Agent C1 — baseline.

    - respecte strictement le langage canonique ActionSnake (voir commun/actions_snake.py)
    - comportement : exploreur naïf (choix uniforme)
    """

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def choisir_action(self, ctx: ContexteDecision) -> ActionSnake:
        # Choix uniforme parmi les 3 actions canoniques.
        return self.rng.choice(
            [ACTION_AVANT, ACTION_OBSERVER_GAUCHE, ACTION_OBSERVER_DROITE]
        )
