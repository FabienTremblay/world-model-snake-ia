# services/agent_service/app/epistemique/contrats.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class HypotheseEpistemiqueV1:
    """Hypothèse testable exprimée dans la terminologie de l'APK.

    Remarque: on ne suppose pas de "vérité" ontologique. Une hypothèse est un
    artefact révisable, évalué à partir d'observations.
    """

    id_hypothese: str
    etiquette: str
    antecedents: List[str] = field(default_factory=list)  # ex. ["collision_mur"]
    consequences: List[str] = field(default_factory=list)  # ex. ["fin_irreversible"]
    metadonnees: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RegleInferenceV1:
    """Règle: transforme des informations (noms) en d'autres informations."""

    id_regle: str
    etiquette: str
    premisses: List[str]
    conclusion: str
    metadonnees: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationHypotheseV1:
    """Évaluation empirique d'une hypothèse."""

    id_hypothese: str
    support: int
    confirmations: int
    contradictions: int
    confiance: float
    note: Optional[str] = None
