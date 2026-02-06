from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

from .contrats import RegistreEpistemiqueV2, IndicesEpistemiques, HypotheseV2


def charger_registre(path: Path) -> RegistreEpistemiqueV2 | None:
    if not path.exists():
        return None
    d = json.loads(path.read_text(encoding="utf-8"))
    indices_d = d.get("indices")
    indices = None
    if indices_d:
        indices = IndicesEpistemiques(**indices_d)
    hypotheses = [HypotheseV2(**h) for h in d.get("hypotheses", [])]
    return RegistreEpistemiqueV2(
        version=str(d.get("version", "v2")),
        genere_ts_ns=int(d.get("genere_ts_ns", 0)),
        run_id=str(d.get("run_id", "")),
        arene_id=d.get("arene_id"),
        sources=dict(d.get("sources", {}) or {}),
        indices=indices,
        hypotheses=hypotheses,
    )


def sauver_registre(path: Path, registre: RegistreEpistemiqueV2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(registre), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def creer_registre(
    *,
    run_id: str,
    arene_id: str | None,
    sources: dict[str, str],
    indices: IndicesEpistemiques,
    hypotheses: list[HypotheseV2],
) -> RegistreEpistemiqueV2:
    return RegistreEpistemiqueV2(
        version="v2",
        genere_ts_ns=time.time_ns(),
        run_id=run_id,
        arene_id=arene_id,
        sources=sources,
        indices=indices,
        hypotheses=hypotheses,
    )
