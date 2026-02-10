from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


TypeSortieTete = Literal[
    "classification_binaire",
    "classification_multiclasse",
    "multi_label",
    "score",
    "regression",
    "policy_actions",
    "gate",
]

RoleTete = Literal[
    "categorie_contenu",
    "categorie_controle",
    "policy",
    "gouvernance",
    "journalisation",
]


@dataclass(frozen=True)
class SpecTete:
    """
    spécification déclarative d'une tête spécialisée.

    une tête est un "slot instanciable" : on la décrit avant de l'entraîner.
    """

    id: str
    nom: str
    type_sortie: TypeSortieTete
    role: RoleTete

    # pour la classification
    classes: list[str] = field(default_factory=list)

    # source de supervision (labels, pseudo-labels, auto-supervision, etc.)
    supervision: dict[str, Any] = field(default_factory=dict)

    # influence sur la décision (ex. moduler la policy, favoriser observer, etc.)
    influence: dict[str, Any] = field(default_factory=dict)

    # métadonnées libres (lien vers hypothèse id, notes expérimentateur, etc.)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CatalogueDeTetes:
    """ensemble versionné de têtes candidates / sélectionnées."""

    version: str = "v1"
    genere_ts_ns: int = 0
    run_id: str = ""
    arene_id: str | None = None
    sources: dict[str, str] = field(default_factory=dict)  # ex. registre épistémique, dataset, etc.
    tetes: list[SpecTete] = field(default_factory=list)


@dataclass(frozen=True)
class RefTronc:
    """
    référence à un tronc.

    au début, ça peut être juste une référence de type + un chemin vers des poids.
    plus tard, tu peux enrichir avec des hyperparamètres, versionnage, etc.
    """

    id: str
    type_tronc: str  # ex. "tabulaire_v1", "cnn_gru_v1"
    chemin_poids: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanPreparationAgent:
    """
    plan d'assemblage/entraînement pour sai-a107.

    c'est l'équivalent de "ce que l'expérimentateur décide".
    """

    experience: str
    arene_id: str
    agent_personne_id: str

    tronc: RefTronc
    tetes_selectionnees: list[str] = field(default_factory=list)  # ids de SpecTete
    intentions: dict[str, Any] = field(default_factory=dict)  # ex. préférer exploration, mission, etc.

    # paramètres d'entraînement
    entrainement: dict[str, Any] = field(default_factory=dict)

    # chemins d'artefacts (résolus par le bac-à-sable)
    chemins: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtefactAgentPersonne:
    """
    artefact produit par sai-a107.

    c'est la "personne" : mémoire + structure interne disponible + références aux poids.
    """

    version: str = "v1"
    genere_ts_ns: int = 0
    experience: str = ""
    arene_id: str = ""
    agent_personne_id: str = ""

    tronc: RefTronc | None = None
    tetes: list[SpecTete] = field(default_factory=list)

    # règles de gouvernance (comment les catégories influencent la policy, seuils, etc.)
    gouvernance: dict[str, Any] = field(default_factory=dict)

    # pointeurs vers artefacts de poids (tronc/têtes/policy, etc.)
    poids: dict[str, str] = field(default_factory=dict)

    # mémoire initiale éventuelle / état initial
    etat_initial: dict[str, Any] = field(default_factory=dict)

    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RapportEntrainement:
    """rapport minimal produit par sai-a107 (pour décision 'satisfait ?')."""

    genere_ts_ns: int
    experience: str
    arene_id: str
    agent_personne_id: str

    succes: bool
    mesures: dict[str, Any] = field(default_factory=dict)
    chemins: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
