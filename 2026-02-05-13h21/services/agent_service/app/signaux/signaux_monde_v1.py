# services/agent_service/app/signaux/signaux_monde_v1.py
"""Signaux du monde (v1).

Un *signal du monde* est une variation mesurable entre deux événements
consécutifs du journal. Il est :

- amoral (ni bon ni mauvais),
- non sémantique (pas d'ontologie),
- indépendant de la perception d'un agent.
"""


def extraire_signaux_monde_v1(prev_evt: dict, curr_evt: dict) -> dict:
    """Extrait des signaux *objectifs* (monde) entre deux événements consécutifs."""

    delta_longueur = curr_evt.get("longueur", 0) - prev_evt.get("longueur", 0)
    delta_score = curr_evt.get("score", 0) - prev_evt.get("score", 0)
    raison_fin = curr_evt.get("raison_fin")

    return {
        "delta_longueur": delta_longueur,
        "delta_score": delta_score,
        "termine": bool(curr_evt.get("termine", False)),
        "raison_fin": raison_fin,
        "collision_mur": raison_fin == "collision_mur",
        "tick": curr_evt.get("tick"),
        "episode_id": curr_evt.get("episode_id"),
    }

