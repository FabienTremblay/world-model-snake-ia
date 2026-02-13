from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

from agent_service.app.modele_monde.latent_v1 import encoder_latent

from .contrats import EvenementTick, IndicesEpistemiques
from .lecteur_metrics import EvenementMetric


def _entropie_shannon(compte: Counter[str]) -> float:
    """Entropie (nats) sur une distribution discrète."""
    total = sum(compte.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in compte.values():
        p = c / total
        if p > 0:
            h -= p * math.log(p)
    return h


def calculer_indices(
    ticks: Iterable[EvenementTick],
    *,
    mode_latent: str | None = None,
    metrics: Iterable[EvenementMetric] | None = None,
) -> IndicesEpistemiques:
    """Calcule des indices épistémiques agrégés.

    Sources :
    - journal.jsonl : faits (actions, fins, pixels) -> indices "diagnostic"
    - metrics.jsonl : transitions instrumentées (checksum avant/après) -> indices "conceptuels"
    """
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

    # --- métriques (optionnelles) : checksum avant/après ---
    metrics_present = metrics is not None
    transitions = None
    etats_uniques = None
    ratio_revisite = None
    ratio_stationnaire = None
    entropie_actions = None
    actions_nulles_top = None
    transitions_top = None

    if metrics is not None:
        c_actions_m = Counter()
        c_etats = Counter()
        c_stationnaire = 0
        c_transitions = Counter()

        nb = 0
        for m in metrics:
            if m.checksum is None or m.checksum_avant is None:
                continue
            nb += 1
            c_etats[str(m.checksum)] += 1
            if m.action is not None:
                c_actions_m[str(m.action)] += 1

            # action nulle / stationnaire
            if m.checksum == m.checksum_avant:
                c_stationnaire += 1
                cle = f"{m.checksum}|{m.action}"
                c_transitions[cle] += 1  # même format, mais on le réutilise aussi en "actions_nulles_top"
            else:
                cle = f"{m.checksum_avant}|{m.action}|{m.checksum}"
                c_transitions[cle] += 1

        transitions = nb
        etats_uniques = len(c_etats)

        if nb > 0:
            ratio_stationnaire = c_stationnaire / nb
            # revisite = 1 - (#uniques / #transitions) (proxy)
            ratio_revisite = 1.0 - (etats_uniques / nb)

        entropie_actions = _entropie_shannon(c_actions_m) if c_actions_m else 0.0

        # top actions nulles : filtrer les clés "etat|action"
        c_nulles = Counter({k: v for k, v in c_transitions.items() if k.count("|") == 1})
        actions_nulles_top = c_nulles.most_common(20) if c_nulles else []

        c_tr = Counter({k: v for k, v in c_transitions.items() if k.count("|") == 2})
        transitions_top = c_tr.most_common(20) if c_tr else []

    return IndicesEpistemiques(
        run_id=run_id,
        arene_id=arene_id,
        episodes=len(episodes),
        ticks=nb_ticks,
        raisons_fin=dict(c_raisons),
        actions=dict(c_actions),
        latents_distincts=(len(c_latent) if mode_latent else None),
        latent_top=(c_latent.most_common(10) if mode_latent else None),
        metrics_present=metrics_present,
        transitions=transitions,
        etats_uniques=etats_uniques,
        ratio_revisite_etats=ratio_revisite,
        ratio_stationnaire=ratio_stationnaire,
        entropie_actions=entropie_actions,
        actions_nulles_top=actions_nulles_top,
        transitions_top=transitions_top,
    )
