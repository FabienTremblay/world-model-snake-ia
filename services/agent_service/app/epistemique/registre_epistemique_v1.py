# services/agent_service/app/epistemique/registre_epistemique_v1.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .contrats import EvaluationHypotheseV1, HypotheseEpistemiqueV1, RegleInferenceV1


@dataclass
class RegistreEpistemiqueV1:
    """Registre en mémoire des artefacts épistémiques.

    Objectif pédagogique: offrir un point de stockage simple pour ce que l'APK
    produit (terminologie, hypothèses, règles), sans dépendre du monde.
    """

    hypotheses: Dict[str, HypotheseEpistemiqueV1] = field(default_factory=dict)
    regles: Dict[str, RegleInferenceV1] = field(default_factory=dict)
    evaluations: Dict[str, EvaluationHypotheseV1] = field(default_factory=dict)

    # index simples pour la navigation
    index_par_etiquette: Dict[str, List[str]] = field(default_factory=dict)

    def ajouter_hypothese(self, h: HypotheseEpistemiqueV1) -> None:
        self.hypotheses[h.id_hypothese] = h
        self.index_par_etiquette.setdefault(h.etiquette, []).append(h.id_hypothese)

    def ajouter_regle(self, r: RegleInferenceV1) -> None:
        self.regles[r.id_regle] = r
        self.index_par_etiquette.setdefault(r.etiquette, []).append(r.id_regle)

    def enregistrer_evaluation(self, e: EvaluationHypotheseV1) -> None:
        self.evaluations[e.id_hypothese] = e

    def evaluation(self, id_hypothese: str) -> Optional[EvaluationHypotheseV1]:
        return self.evaluations.get(id_hypothese)

    def lister_hypotheses(self) -> List[HypotheseEpistemiqueV1]:
        return list(self.hypotheses.values())

    def lister_regles(self) -> List[RegleInferenceV1]:
        return list(self.regles.values())

    def resumer(self) -> Dict[str, int]:
        return {
            "hypotheses": len(self.hypotheses),
            "regles": len(self.regles),
            "evaluations": len(self.evaluations),
        }
