from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import Iterable, Optional

from agent_service.app.modele_monde.latent_v1 import encoder_latent

from .contrats import EvenementTick, IndicesEpistemiques


def calculer_indices(
    ticks: Iterable[EvenementTick],
    *,
    mode_latent: str | None = None,
) -> IndicesEpistemiques:
    """Calcule des indices épistémiques simples à partir des ticks."""
    c_raisons = Counter()
    c_actions = Counter()
    c_latent = Counter()

    run_id = None
    arene_id = None
    episodes = set()
    nb_ticks = 0

    for t in ticks:
        if run_id is None:
            run_id = t.run_id
        if arene_id is None:
            arene_id = t.arene_id
        episodes.add(t.episode_id)
        nb_ticks += 1

        if t.action is not None:
            c_actions[str(t.action)] += 1

        if t.termine and t.raison_fin:
            c_raisons[str(t.raison_fin)] += 1

        if mode_latent:
            z = encoder_latent(t.capteurs, mode_latent)
            c_latent[str(z)] += 1

    if run_id is None:
        run_id = ""
    idx = IndicesEpistemiques(
        run_id=run_id,
        arene_id=arene_id,
        episodes=len(episodes),
        ticks=nb_ticks,
        raisons_fin=dict(c_raisons),
        actions=dict(c_actions),
        latents_distincts=(len(c_latent) if mode_latent else None),
        latent_top=(c_latent.most_common(10) if mode_latent else None),
    )
    return idx
