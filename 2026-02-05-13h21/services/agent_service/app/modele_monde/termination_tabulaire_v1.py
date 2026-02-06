# services/agent_service/app/modele_monde/termination_tabulaire_v1.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import DefaultDict, Tuple
from collections import defaultdict


CleTerminaison = Tuple[int, str, int]  # (etat, action, etat_suivant)


@dataclass(frozen=True)
class PredictionTerminaison:
    # probabilité empirique de terminer sur cette transition
    proba_termine: float
    # nombre d'observations apprises pour cette clé
    support: int


@dataclass
class ModeleTerminaisonTabulaireV1:
    # (etat, action, etat_suivant) -> (termine_bool -> compteur)
    _compteurs: DefaultDict[CleTerminaison, DefaultDict[bool, int]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int))
    )

    _nb_obs: int = 0

    def apprendre(self, etat: int, action: str, etat_suivant: int, termine: bool) -> None:
        cle = (int(etat), str(action), int(etat_suivant))
        self._compteurs[cle][bool(termine)] += 1
        self._nb_obs += 1

    def predire(self, etat: int, action: str, etat_suivant: int) -> PredictionTerminaison:
        cle = (int(etat), str(action), int(etat_suivant))
        counts = self._compteurs.get(cle)
        if not counts:
            return PredictionTerminaison(proba_termine=0.0, support=0)

        total = int(sum(counts.values()))
        termine_cnt = int(counts.get(True, 0))
        proba = (termine_cnt / total) if total else 0.0
        return PredictionTerminaison(proba_termine=float(proba), support=int(total))

    def stats(self) -> dict:
        nb_cles = len(self._compteurs)
        support_total = 0
        max_support = 0
        for dist in self._compteurs.values():
            s = int(sum(dist.values()))
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

