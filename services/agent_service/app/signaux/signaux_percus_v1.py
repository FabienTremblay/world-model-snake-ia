# services/agent_service/app/signaux/signaux_percus_v1.py
"""Signaux perçus (v1).

Un *signal perçu* est un signal du monde filtré par :

- les modalités de perception d'un agent (voir, entendre, ressentir),
- ses limites (champ de vision, portée, obstacles),
- son état interne (mémoire, orientation),
- éventuellement le point de vue d'un observateur (ex. "estrade").

Ce module prépare le terrain : dans les premières itérations du Cours 4,
on peut utiliser une perception "omnisciente" (estrade) afin de rester
pédagogique. Ensuite, on remplace progressivement cette perception par
des perceptions partielles (vision 180°, agent sourd, etc.).
"""

from __future__ import annotations

from agent_service.app.contrats_agents import ContexteDecision

from .signaux_monde_v1 import extraire_signaux_monde_v1


def extraire_signaux_percus_v1(
    prev_evt: dict,
    curr_evt: dict,
    capteurs_t: object | None,
    capteurs_t1: object | None,
    contexte: ContexteDecision,
) -> dict:
    """Extrait les signaux *perçus* entre deux ticks.

    Paramètres
    ----------
    prev_evt, curr_evt:
        Événements du journal (monde) aux ticks t et t+1.

    capteurs_t, capteurs_t1:
        Observations (capteurs) côté agent aux ticks t et t+1.
        v1 : non utilisés (réservés aux versions perception-partielle).

    contexte:
        Contexte de décision incluant éventuellement `contexte.perception`.

    Retour
    ------
    dict
        Signaux perçus.

    Notes
    -----
    v1 se comporte comme un "observateur en estrade" : on retourne les signaux
    du monde. Les versions ultérieures exploiteront `capteurs_*` et
    `contexte.perception` pour filtrer.
    """

    _ = capteurs_t, capteurs_t1  # réservé aux versions ultérieures
    # v1 : perception omnisciente (signaux du monde). L'instrumentation est
    # gérée ailleurs; ici on conserve juste une trace de "mode".
    signaux = extraire_signaux_monde_v1(prev_evt, curr_evt)
    signaux["profil_perception"] = {
        "mode": "monde_v1",
    }
    return signaux

