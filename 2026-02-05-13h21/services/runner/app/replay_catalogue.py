# services/runner/app/replay_catalogue.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class EntreeReplay:
    slot: int
    path: str


class CatalogueReplays:
    """
    Catalogue minimal:
      artefacts/replays/manifest.json
    Format:
      { "slots": { "10": "artefacts/replays/replay-0010.jsonl", ... } }
    """

    def __init__(self, racine_projet: Path) -> None:
        self.racine = racine_projet
        self.dir_replays = self.racine / "artefacts" / "replays"
        self.manifest = self.dir_replays / "manifest.json"
        self.dir_replays.mkdir(parents=True, exist_ok=True)

    def _charger(self) -> Dict[str, Dict[str, str]]:
        if not self.manifest.exists():
            return {"slots": {}}
        return json.loads(self.manifest.read_text(encoding="utf-8"))

    def _sauver(self, data: Dict[str, Dict[str, str]]) -> None:
        self.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def enregistrer_slot(self, slot: int, journal_path: Path) -> None:
        data = self._charger()
        slots = data.setdefault("slots", {})
        slots[str(int(slot))] = str(journal_path)
        self._sauver(data)

    def resoudre(self, slot: int) -> Optional[Path]:
        data = self._charger()
        p = data.get("slots", {}).get(str(int(slot)))
        if not p:
            return None
        path = Path(p)
        return path if path.is_absolute() else (self.racine / path)

    def slot_existe(self, slot: int) -> bool:
        return self.resoudre(slot) is not None

