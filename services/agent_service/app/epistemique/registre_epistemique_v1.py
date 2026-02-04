# services/agent_service/app/epistemique/registre_epistemique_v1.py
from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass, field
from pathlib import Path
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

    def to_dict(self) -> Dict:
        """Sérialisation simple (json-friendly) du registre."""
        return {
            "hypotheses": {k: asdict(v) for k, v in self.hypotheses.items()},
            "regles": {k: asdict(v) for k, v in self.regles.items()},
            "evaluations": {k: asdict(v) for k, v in self.evaluations.items()},
            "index_par_etiquette": dict(self.index_par_etiquette),
            "version": "registre_epistemique_v1",
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RegistreEpistemiqueV1":
        reg = cls()

        for _k, hv in (d.get("hypotheses") or {}).items():
            h = HypotheseEpistemiqueV1(**hv)
            reg.ajouter_hypothese(h)

        for _k, rv in (d.get("regles") or {}).items():
            r = RegleInferenceV1(**rv)
            reg.ajouter_regle(r)

        for _k, ev in (d.get("evaluations") or {}).items():
            e = EvaluationHypotheseV1(**ev)
            reg.enregistrer_evaluation(e)

        # l’index est reconstruit par ajouter_* mais on tolère sa présence
        if "index_par_etiquette" in d and isinstance(d["index_par_etiquette"], dict):
            reg.index_par_etiquette = {k: list(v) for k, v in d["index_par_etiquette"].items()}

        return reg

    @classmethod
    def charger_json(cls, path: Path) -> "RegistreEpistemiqueV1":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls.from_dict(d)

    def sauvegarder_json(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
