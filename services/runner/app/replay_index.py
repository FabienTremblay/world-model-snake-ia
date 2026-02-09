
from typing import Dict, Iterable, Any

def indexer_episodes(journal_lignes: Iterable[dict]) -> Dict[int, dict]:
    episodes: Dict[int, dict] = {}
    for row in journal_lignes:
        ep = int(row.get("episode_id", 0))
        tick = int(row.get("tick", 0))
        if ep not in episodes:
            episodes[ep] = {
                "tick_min": tick,
                "tick_max": tick,
                "score_final": row.get("score"),
                "raison_fin": row.get("raison_fin"),
            }
        else:
            episodes[ep]["tick_min"] = min(episodes[ep]["tick_min"], tick)
            episodes[ep]["tick_max"] = max(episodes[ep]["tick_max"], tick)
            if row.get("termine"):
                episodes[ep]["score_final"] = row.get("score")
                episodes[ep]["raison_fin"] = row.get("raison_fin")
    return episodes
