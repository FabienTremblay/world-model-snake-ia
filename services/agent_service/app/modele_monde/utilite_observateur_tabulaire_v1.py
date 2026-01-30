# services/agent_service/app/modele_monde/utilite_observateur_tabulaire_v1.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Tuple
from collections import defaultdict


CleUtilite = Tuple[int, str, int]  # (etat, action, etat_suivant)


@dataclass(frozen=True)
class PredictionUtilite:
    esperance: float
    support: int
    distribution: Dict[int, float]  # utilite_entière -> proba


@dataclass
class ModeleUtiliteObservateurTabulaireV1:
    _compteurs: DefaultDict[CleUtilite, DefaultDict[int, int]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int))
    )
    _nb_obs: int = 0

    def apprendre(self, etat: int, action: str, etat_suivant: int, utilite: int) -> None:
        cle = (int(etat), str(action), int(etat_suivant))
        self._compteurs[cle][int(utilite)] += 1
        self._nb_obs += 1

    def predire(self, etat: int, action: str, etat_suivant: int) -> PredictionUtilite:
        cle = (int(etat), str(action), int(etat_suivant))
        dist_counts = self._compteurs.get(cle)
        if not dist_counts:
            return PredictionUtilite(esperance=0.0, support=0, distribution={})

        total = sum(dist_counts.values())
        distribution: Dict[int, float] = {k: v / total for k, v in dist_counts.items()}

        esperance = 0.0
        for u, p in distribution.items():
            esperance += float(u) * float(p)

        return PredictionUtilite(
            esperance=float(esperance),
            support=int(total),
            distribution=distribution,
        )

    def stats(self) -> dict:
        nb_cles = len(self._compteurs)
        support_total = 0
        max_support = 0
        for dist in self._compteurs.values():
            s = sum(dist.values())
            support_total += s
            if s > max_support:
                max_support = s
        support_moyen = (support_total / nb_cles) if nb_cles else 0.0
        return {
            "nb_cles": int(nb_cles),
            "nb_obs": int(self._nb_obs),
            "support_total": int(support_total),
            "support_moyen": float(support_moyen),
            "support_max": int(max_support),
        }

