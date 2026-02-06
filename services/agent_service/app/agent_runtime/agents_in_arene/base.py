from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contrats import ContexteDecision
from commun.contrats import Pixel


@runtime_checkable
class IAgentEnArene(Protocol):
    """Contrat minimal d'un agent en arène (point de vue incarné)."""

    def choisir_action(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> str:
        ...

    # optionnel : certains agents voudront exposer une trace explicable
    def trace_derniere_decision(self):
        ...
