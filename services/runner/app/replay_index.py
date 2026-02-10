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


def indexer_episodes(lignes: Iterable[dict[str, Any]], run_id: Optional[str] = None) -> Dict[int, StatEpisode]:
    """
    Indexe un fichier d'épisodes (jsonl déjà décodé en dicts).

    - regroupe par episode_id
    - calcule bornes (debut/fin) en numéros de ligne 0-based
    - calcule quelques stats de fin
    - filtre optionnellement par run_id

    Le but est de permettre:
      * sélectionner un épisode parmi des centaines
      * relire rapidement un épisode précis
      * afficher des stats par épisode
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

        if eid not in courant:
            courant[eid] = {
                "debut": i,
                "fin": i,
                "ticks": 0,
                "score_final": int(evt.get("score", 0) or 0),
                "longueur_final": int(evt.get("longueur", 0) or 0),
                "termine": bool(evt.get("termine", False)),
            }
        c = courant[eid]
        c["fin"] = i
        c["ticks"] += 1
        c["score_final"] = int(evt.get("score", c["score_final"]) or 0)
        c["longueur_final"] = int(evt.get("longueur", c["longueur_final"]) or 0)
        c["termine"] = bool(evt.get("termine", c["termine"]))

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
