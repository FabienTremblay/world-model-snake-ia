# services/agent_service/app/signaux/signaux_transition_v1.py
"""
Extraction des signaux de transition (v1).

Un signal est une variation mesurable émise par l’environnement
entre deux états consécutifs, sans interprétation ni valeur.
NOTE (Cours 4) :
- on distingue désormais 2 niveaux : signaux du monde vs signaux perçus
- ce module est conservé pour compatibilité ; il correspond aux signaux du monde
 """
 
from .signaux_monde_v1 import extraire_signaux_monde_v1


def extraire_signaux_transition(prev_evt: dict, curr_evt: dict) -> dict:
    """
    Extrait les signaux de transition bruts entre deux événements consécutifs.

    Paramètres
    ----------
    prev_evt : dict
        Événement au tick t
    curr_evt : dict
        Événement au tick t+1

    Retour
    ------
    dict
        Dictionnaire de signaux de transition
    """

    delta_longueur = (
        curr_evt.get("longueur", 0) - prev_evt.get("longueur", 0)
    )

    delta_score = (
        curr_evt.get("score", 0) - prev_evt.get("score", 0)
    )

    raison_fin = curr_evt.get("raison_fin")

    # alias "monde"
    return extraire_signaux_monde_v1(prev_evt, {**curr_evt, "raison_fin": raison_fin})

