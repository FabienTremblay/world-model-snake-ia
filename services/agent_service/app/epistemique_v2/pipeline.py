from __future__ import annotations

from pathlib import Path

from .lecteur_journal import lire_journal_ticks
from .indices import calculer_indices
from .inference import inferer_hypotheses
from .registre import creer_registre, sauver_registre


def executer_pipeline_epistemique_v2(
    *,
    path_journal: Path,
    path_sortie_registre: Path,
    sources: dict[str, str],
    mode_latent: str | None = None,
) -> None:
    ticks = list(lire_journal_ticks(path_journal))
    indices = calculer_indices(ticks, mode_latent=mode_latent)
    hypotheses = inferer_hypotheses(indices)
    registre = creer_registre(
        run_id=indices.run_id,
        arene_id=indices.arene_id,
        sources=sources,
        indices=indices,
        hypotheses=hypotheses,
    )
    sauver_registre(path_sortie_registre, registre)
