# services/agent_service/app/agents/contrats.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from commun.contrats import Pixel


@dataclass(frozen=True)
class ContextePerception:
    """Paramètres de perception (côté agent).

    Idée (Cours 4) : un signal "perçu" dépend des modalités et des limites
    de l'agent (vision, audition, etc.), pas seulement de l'évolution du monde.

    Ce contexte est volontairement minimal et extensible.
    """

    # conventions de départ (extensibles)
    champ_vision_deg: int = 180
    rayon_vision: int = 0  # 0 = "autour immédiat" (via capteurs), >0 = vision à distance
    voit: bool = True
    entend: bool = False
    ressent: bool = False


@dataclass(frozen=True)
class ContexteDecision:
    """Contexte minimal fourni à l'agent lors d'une décision."""

    run_id: str
    episode_id: int
    tick: int
    largeur: int
    hauteur: int

    # optionnel : perception propre à l'agent (Cours 4)
    perception: ContextePerception | None = None


class IAgent(Protocol):
    """Contrat minimal d'un agent.

    L'agent choisit une direction à partir des capteurs (observation).
    Il peut conserver un état interne (mémoire) s'il le souhaite.
    """

    def choisir_action(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> str:
        ...


# --- Extensions Cours 5 (non destructives) ---

class AgentEnArene(IAgent, Protocol):
    """Alias explicite : agent incarné, point de vue local, action directe."""
    pass


@dataclass(frozen=True)
class TraceDecision:
    """Trace minimale optionnelle pour expliquer une décision (cours 5).

    Un agent *peut* fournir une trace. L'orchestrateur (ui_cli) peut l'écrire dans
    le journal pour alimenter l'analyse et l'épistémique sans couplage fort.
    """

    action_choisie: str
    raisons: list[str] | None = None
    score_actions: dict[str, float] | None = None
