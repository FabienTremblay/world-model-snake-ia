from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from commun.contrats import Pixel


StatutHypothese = Literal["proposee", "validee", "refutee"]


@dataclass(frozen=True)
class EvenementTick:
    """Événement factuel (issu du journal JSONL)."""

    ts_ns: int
    run_id: str
    episode_id: int
    tick: int
    arene_id: str | None
    seed: int | None
    action: str | None
    niveau_bruit: int
    score: int
    longueur: int
    termine: bool
    raison_fin: str | None
    largeur: int
    hauteur: int
    capteurs: list[list[Pixel]]


@dataclass(frozen=True)
class IndicesEpistemiques:
    """Indices agrégés (v2)."""

    run_id: str
    arene_id: str | None
    episodes: int
    ticks: int
    raisons_fin: dict[str, int] = field(default_factory=dict)
    actions: dict[str, int] = field(default_factory=dict)
    latents_distincts: int | None = None
    latent_top: list[tuple[str, int]] | None = None

    # --- indices dérivés de metrics.jsonl (si disponible) ---
    metrics_present: bool = False
    transitions: int | None = None
    etats_uniques: int | None = None
    ratio_revisite_etats: float | None = None
    ratio_stationnaire: float | None = None
    entropie_actions: float | None = None
    actions_nulles_top: list[tuple[str, int]] | None = None  # clé = "etat|action"
    transitions_top: list[tuple[str, int]] | None = None     # clé = "etat|action|etat2"


@dataclass(frozen=True)
class HypotheseV2:
    """Hypothèse épistémique (v2)."""

    id: str
    titre: str
    description: str
    statut: StatutHypothese = "proposee"
    confiance: float = 0.5  # 0..1
    conditions: list[str] = field(default_factory=list)
    evidences: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RegistreEpistemiqueV2:
    """Registre épistémique versionné (v2)."""

    version: str = "v2"
    genere_ts_ns: int = 0
    run_id: str = ""
    arene_id: str | None = None
    sources: dict[str, str] = field(default_factory=dict)
    indices: Optional[IndicesEpistemiques] = None
    hypotheses: list[HypotheseV2] = field(default_factory=list)

    # Concepts candidats (instillables) produits par l'observateur à partir des traces.
    # Format volontairement simple (liste de dict) pour rester souple et évolutif.
    concepts_candidates: list[dict[str, Any]] = field(default_factory=list)
