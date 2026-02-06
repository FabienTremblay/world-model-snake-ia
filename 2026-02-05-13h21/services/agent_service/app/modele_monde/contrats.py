# services/agent_service/app/modele_monde/contrats.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol


@dataclass(frozen=True)
class Prediction:
    # meilleur candidat
    etat_suivant: Optional[int]
    # 0..1, probabilité empirique du meilleur candidat
    confiance: float
    # nombre d'observations apprises pour cette clé (etat, action)
    support: int
    # entropie (bits) sur la distribution empirique des successeurs
    entropie: float
    # distribution complète (état -> prob), utile pour audit/pédagogie
    distribution: Dict[int, float]


class IModeleMonde(Protocol):
    def predire(self, etat: int, action: str) -> Prediction: ...

    def apprendre_transition(self, etat: int, action: str, etat_suivant: int) -> None: ...

    def stats(self) -> dict: ...
