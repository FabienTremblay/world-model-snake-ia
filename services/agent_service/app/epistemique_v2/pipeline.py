from __future__ import annotations

from pathlib import Path

from .lecteur_journal import lire_journal_ticks
from .lecteur_metrics import lire_metrics
from .indices import calculer_indices
from .inference import inferer_hypotheses
from .concepts import produire_concepts_candidates
from .registre import creer_registre, sauver_registre


def executer_pipeline_epistemique_v2(
    *,
    path_journal: Path,
    path_sortie_registre: Path,
    sources: dict[str, str],
    mode_latent: str | None = None,
    path_metrics: Path | None = None,
) -> None:
    ticks = list(lire_journal_ticks(path_journal))

    metrics = None
    if path_metrics is not None and path_metrics.exists():
        metrics = list(lire_metrics(path_metrics))

    indices = calculer_indices(ticks, mode_latent=mode_latent, metrics=metrics)
    hypotheses = inferer_hypotheses(indices)
    concepts = produire_concepts_candidates(indices)

    registre = creer_registre(
        run_id=indices.run_id,
        arene_id=indices.arene_id,
        sources=sources,
        indices=indices,
        hypotheses=hypotheses,
        concepts_candidates=concepts,
    )
    sauver_registre(path_sortie_registre, registre)
