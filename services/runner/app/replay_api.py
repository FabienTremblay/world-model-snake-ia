# services/runner/app/replay_api.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Optional

from runner.app.replay_index import StatEpisode, indexer_episodes


@dataclass
class Replay:
    """
    API de lecture d'un journal jsonl d'épisodes.

    Entrée: itérable de dicts (événements), typiquement issu d'un jsonl.
    Usage:
        rep = Replay(lignes)
        episodes = rep.episodes()
        rep.charger_episode(episode_id)
        for evt in rep.ticks():
            ...
    """

    lignes: list[dict[str, Any]]
    run_id: Optional[str] = None

    def __post_init__(self) -> None:
        self._index: Optional[Dict[int, StatEpisode]] = None
        self._episode_id: Optional[int] = None

    def episodes(self) -> Dict[int, StatEpisode]:
        if self._index is None:
            self._index = indexer_episodes(self.lignes, run_id=self.run_id)
        return self._index

    def max_episode(self) -> int:
        eps = self.episodes()
        return max(eps.keys()) if eps else 0

    def charger_episode(self, episode_id: int) -> None:
        self._episode_id = int(episode_id)

    def ticks(self) -> Iterator[dict[str, Any]]:
        if self._episode_id is None:
            # défaut: premier épisode
            eps = self.episodes()
            self._episode_id = sorted(eps.keys())[0] if eps else 0

        eid = int(self._episode_id)
        for evt in self.lignes:
            try:
                if int(evt.get("episode_id", 0)) != eid:
                    continue
            except Exception:
                continue
            if self.run_id is not None and str(evt.get("run_id", "")) != str(self.run_id):
                continue
            yield evt
