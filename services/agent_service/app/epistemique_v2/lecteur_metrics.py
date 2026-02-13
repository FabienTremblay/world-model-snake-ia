from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class EvenementMetric:
    """Événement issu de metrics.jsonl (trace instrumentée).

    On se concentre sur les champs utiles à l'observateur épistémique :
    - checksum_avant / checksum : identifiants d'état (latent discret)
    - action : action tentée
    """

    ts_ns: int
    run_id: str
    episode_id: int
    tick: int
    action: str | None
    checksum_avant: int | None
    checksum: int | None


def lire_metrics(path_metrics: Path) -> Iterator[EvenementMetric]:
    """Lit metrics.jsonl en streaming."""
    with path_metrics.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            yield EvenementMetric(
                ts_ns=int(d.get("ts_ns", 0)),
                run_id=str(d.get("run_id", "")),
                episode_id=int(d.get("episode_id", 0)),
                tick=int(d.get("tick", 0)),
                action=(d.get("action") if d.get("action") is None else str(d.get("action"))),
                checksum_avant=(int(d["checksum_avant"]) if "checksum_avant" in d and d["checksum_avant"] is not None else None),
                checksum=(int(d["checksum"]) if "checksum" in d and d["checksum"] is not None else None),
            )
