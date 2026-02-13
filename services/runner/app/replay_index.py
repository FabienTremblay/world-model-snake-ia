# services/runner/app/replay_index.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Any, Optional


@dataclass(frozen=True)
class StatEpisode:
    episode_id: int
    debut_ligne: int
    fin_ligne: int
    ticks: int
    score_final: int
    longueur_final: int
    termine: bool


def _extraire_score_longueur_termine(evt: dict[str, Any]) -> tuple[int, int, bool]:
    """Compat v1/v2.

    v1:
      - score, longueur, termine au niveau racine

    v2 (journal_v2):
      - monde_canonique.score / longueur / termine
    """
    monde = evt.get("monde_canonique")
    if isinstance(monde, dict):
        score = monde.get("score", 0)
        longueur = monde.get("longueur", 0)
        termine = monde.get("termine", False)
        try:
            return int(score or 0), int(longueur or 0), bool(termine)
        except Exception:
            return 0, 0, bool(termine)

    # fallback v1
    try:
        return int(evt.get("score", 0) or 0), int(evt.get("longueur", 0) or 0), bool(evt.get("termine", False))
    except Exception:
        return 0, 0, bool(evt.get("termine", False))


def indexer_episodes(lignes: Iterable[dict[str, Any]], run_id: Optional[str] = None) -> Dict[int, StatEpisode]:
    """
    Indexe un fichier d'épisodes (jsonl déjà décodé en dicts).

    - regroupe par episode_id
    - calcule bornes (debut/fin) en numéros de ligne 0-based
    - calcule quelques stats de fin
    - filtre optionnellement par run_id

    Compat:
      - journal v1 (legacy)
      - journal v2 (journal_v2)
    """
    stats: Dict[int, StatEpisode] = {}
    courant: Dict[int, dict[str, Any]] = {}

    for i, evt in enumerate(lignes):
        if run_id is not None and str(evt.get("run_id", "")) != str(run_id):
            continue
        try:
            eid = int(evt.get("episode_id", 0))
        except Exception:
            continue

        score, longueur, termine = _extraire_score_longueur_termine(evt)

        if eid not in courant:
            courant[eid] = {
                "debut": i,
                "fin": i,
                "ticks": 0,
                "score_final": score,
                "longueur_final": longueur,
                "termine": termine,
            }
        c = courant[eid]
        c["fin"] = i
        c["ticks"] += 1
        c["score_final"] = score
        c["longueur_final"] = longueur
        c["termine"] = termine

    for eid, c in courant.items():
        stats[eid] = StatEpisode(
            episode_id=eid,
            debut_ligne=int(c["debut"]),
            fin_ligne=int(c["fin"]),
            ticks=int(c["ticks"]),
            score_final=int(c["score_final"]),
            longueur_final=int(c["longueur_final"]),
            termine=bool(c["termine"]),
        )
    return stats
