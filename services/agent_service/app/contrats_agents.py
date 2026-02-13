from __future__ import annotations

"""Contrats canoniques pour les agents (SAI-A***).

Nouvelle version (rupture assumée) :
  - un agent en arène choisit une action à partir d'OBSERVATIONS (instruments)
  - la perception est instrumentée (camera, gps, radio, etc.)
  - le runner orchestre l'exécution des instruments, mais la liste vient de l'agent.

Ces contrats sont volontairement minimaux et stables :
ils sont appelés à être étendus proprement (ex. décisions expliquées,
instruments composites, connaissances, etc.).
"""

from dataclasses import dataclass
from typing import Any, Protocol, Dict

from instrument.app.contrats import ObservationInstrument

# NOTE: La norme d'actions Snake est définie dans `services/commun/actions_snake.py`
# et documentée dans `docs/contrats/CONTRAT_ACTIONS_SNAKE.md`.

from commun.actions_snake import ActionSnake as Action


@dataclass(frozen=True)
class ContexteDecision:
    """Contexte minimal fourni à l'agent lors d'une décision."""

    run_id: str
    episode_id: int
    tick: int

    # observations produites par les instruments (caméra, gps, radio, etc.)
    # forme : dict instrument_id -> ObservationInstrument
    observations: dict[str, ObservationInstrument]

    # informations additionnelles non-structurantes (debug / compat transitoire)
    info: dict[str, Any] | None = None


@dataclass(frozen=True)
class ContextePerception:
    """Contexte de perception "brut" (avant décision).

    Utilisé par des composants pédagogiques (signaux, diagnostics, entraînement).
    """

    run_id: str | None
    episode_id: int | None
    tick: int
    observations: Dict[str, ObservationInstrument]
    info: dict[str, Any] | None = None


class IAgentArene(Protocol):
    """Contrat minimal d'un agent incarné en arène."""

    id_agent: str

    def instruments(self) -> list[Any]:
        """Liste d'instruments 'portés' par l'agent.

        Chaque instrument doit exposer :
          - instrument_id: str
          - observer(etat_canonique) -> ObservationInstrument
        """

    def choisir_action(self, contexte: ContexteDecision) -> Action:
        """Choisit une action discrète."""
