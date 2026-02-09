
from typing import Iterable, Dict, Any, Iterator
from .replay_index import indexer_episodes

class Replay:
    def __init__(self, journal_lignes: Iterable[dict]):
        self._lignes = list(journal_lignes)
        self._index = indexer_episodes(self._lignes)
        self._episode_id = None
        self._cursor = 0

    def episodes(self) -> Dict[int, dict]:
        return self._index

    def charger_episode(self, episode_id: int) -> None:
        if episode_id not in self._index:
            raise KeyError(f"episode {episode_id} absent")
        self._episode_id = episode_id
        self._cursor = 0

    def ticks(self) -> Iterator[dict]:
        if self._episode_id is None:
            raise RuntimeError("episode non chargé")
        for row in self._lignes:
            if int(row.get("episode_id", -1)) == self._episode_id:
                yield row
