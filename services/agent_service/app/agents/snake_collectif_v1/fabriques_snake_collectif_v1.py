from __future__ import annotations

"""Fabriques d'agents — campagne snake_collectif_v1.

On garde les fabriques exp-locales dans ce package pour éviter de polluer
la couche _infra (catalogue global).
"""

from typing import Any, Dict

from agent_service.app.agents.snake_collectif_v1.agent_fourmi import AgentSnakeCollectifV1Fourmi, ParamsFourmi


def fabriquer_snake_collectif_v1_fourmi(params: Dict[str, Any]) -> object:
    """Fabrique catalogue v1.

    Params supportés (tous optionnels):
      - seed: int
      - poids_nouveaute: float
      - bonus_nourriture: float
      - penalite_demi_tour: float
      - epsilon: float
      - instruments: list[object]  (rare, plutôt géré par instruments_defaut)
    """
    seed = params.get("seed", None)

    pf = ParamsFourmi(
        poids_nouveaute=float(params.get("poids_nouveaute", 1.0)),
        bonus_nourriture=float(params.get("bonus_nourriture", 5.0)),
        penalite_demi_tour=float(params.get("penalite_demi_tour", 0.25)),
        epsilon=float(params.get("epsilon", 0.02)),
    )

    instruments = params.get("instruments", None)
    return AgentSnakeCollectifV1Fourmi(seed=seed, instruments=instruments, params=pf)
