# services/agent_service/app/observateurs/observateur_croissance_v1.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservateurCroissanceV1:
    """Observateur minimal : s'intéresse à la croissance.

    Interprétation volontairement minimale :
    - on ne nomme pas "nourriture"
    - on observe seulement qu'une transition a produit delta_longueur > 0

    L'étape suivante (Cours 4) consistera à relier cette régularité à des
    causes potentielles (enquête / expédition).
    """

    poids_croissance: float = 1.0
    penalite_collision_mur: float = 1.0

    def utilite(self, signaux_percus: dict) -> float:
        dl = float(signaux_percus.get("delta_longueur", 0.0))
        collision_mur = bool(signaux_percus.get("collision_mur", False))

        u = 0.0
        if dl > 0:
            u += self.poids_croissance
        if collision_mur:
            u -= self.penalite_collision_mur
        return float(u)

