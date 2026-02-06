# services/agent_service/app/modele_monde/tabulaire_v1.py
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Tuple
from collections import defaultdict

from agent_service.app.modele_monde.contrats import Prediction


Cle = Tuple[int, str]


@dataclass
class ModeleMondeTabulaireV1:
    # (etat, action) -> (etat_suivant -> compteur)
    _compteurs: DefaultDict[Cle, DefaultDict[int, int]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int))
    )

    _nb_transitions: int = 0

    def apprendre_transition(self, etat: int, action: str, etat_suivant: int) -> None:
        self._compteurs[(int(etat), str(action))][int(etat_suivant)] += 1
        self._nb_transitions += 1

    def predire(self, etat: int, action: str) -> Prediction:
        cle = (int(etat), str(action))
        dist_counts = self._compteurs.get(cle)
        if not dist_counts:
            return Prediction(
                etat_suivant=None,
                confiance=0.0,
                support=0,
                entropie=0.0,
                distribution={},
            )

        total = sum(dist_counts.values())
        # normalisation
        distribution: Dict[int, float] = {k: v / total for k, v in dist_counts.items()}

        # meilleur candidat
        etat_suiv, max_count = max(dist_counts.items(), key=lambda kv: kv[1])
        confiance = max_count / total if total else 0.0

        # entropie de shannon (bits)
        ent = 0.0
        for p in distribution.values():
            if p > 0.0:
                ent -= p * math.log2(p)

        return Prediction(
            etat_suivant=int(etat_suiv),
            confiance=float(confiance),
            support=int(total),
            entropie=float(ent),
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
            "nb_transitions": int(self._nb_transitions),
            "support_total": int(support_total),
            "support_moyen": float(support_moyen),
            "support_max": int(max_support),
        }
