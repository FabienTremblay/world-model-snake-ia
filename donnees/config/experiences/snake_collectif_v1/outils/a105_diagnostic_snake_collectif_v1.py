#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SAI-A105 — analyser résultats (diagnostic) pour snake_collectif_v1.

Ce diagnostic est volontairement "sans hypothèses" :
- il décrit ce qui s'est passé dans les runs, à partir de metrics.jsonl et journal.jsonl
- il produit des artefacts d'analyse exp-local

Entrée:
  donnees/config/experiences/snake_collectif_v1/artefacts/runs/*/metrics.jsonl
  donnees/config/experiences/snake_collectif_v1/artefacts/runs/*/journal.jsonl

Sorties:
  donnees/config/experiences/snake_collectif_v1/artefacts/analyses/a105_diagnostic_par_run.csv
  donnees/config/experiences/snake_collectif_v1/artefacts/analyses/a105_diagnostic_global.csv

Métriques principales:
- episodes: nombre d'épisodes observés
- ticks_moyen: longueur moyenne (nb de ticks par épisode)
- etats_uniques_moyen: nb moyen de checksums distincts par épisode (proxy exploration)
- ratio_revisite_etats: 1 - uniques / total_transitions
- ratio_stationnaire: checksum == checksum_avant (action "inutile" ou bloquée)
- entropie_actions: diversité des actions
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _charger_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _entropie(counter: Counter) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counter.values():
        p = c / total
        if p > 0:
            h -= p * math.log(p, 2)
    return h


@dataclass
class StatsEpisode:
    ticks: int = 0
    transitions: int = 0
    checksums_uniques: int = 0
    stationnaires: int = 0
    actions: Counter = None

    def __post_init__(self):
        if self.actions is None:
            self.actions = Counter()


def analyser_run(metrics_path: Path) -> Dict[str, Any]:
    episodes: Dict[int, StatsEpisode] = {}
    checksums_par_ep: Dict[int, set] = defaultdict(set)

    for obj in _charger_jsonl(metrics_path):
        ep = int(obj.get("episode_id", 0))
        tick = int(obj.get("tick", 0))
        action = obj.get("action", None)
        ch_av = obj.get("checksum_avant", None)
        ch = obj.get("checksum", None)

        st = episodes.setdefault(ep, StatsEpisode())
        st.ticks = max(st.ticks, tick)
        st.transitions += 1
        if action is not None:
            st.actions[action] += 1
        if ch is not None:
            checksums_par_ep[ep].add(ch)
        if ch is not None and ch_av is not None and ch == ch_av:
            st.stationnaires += 1

    eps = sorted(episodes.keys())
    if not eps:
        return {"episodes": 0}

    # ticks sont indexés à partir de 1 dans metrics.jsonl (dans ton exemple), on garde (max tick)
    ticks = []
    trans = []
    uniques = []
    station = []
    entropies = []
    for ep in eps:
        st = episodes[ep]
        ticks.append(st.ticks)
        trans.append(st.transitions)
        uniques.append(len(checksums_par_ep.get(ep, set())))
        station.append(st.stationnaires)
        entropies.append(_entropie(st.actions))

    total_trans = sum(trans)
    total_uniques = sum(uniques)
    total_station = sum(station)

    return {
        "episodes": len(eps),
        "ticks_moyen": sum(ticks) / len(ticks),
        "transitions_moyen": sum(trans) / len(trans),
        "etats_uniques_moyen": sum(uniques) / len(uniques),
        "ratio_revisite_etats": (1.0 - (total_uniques / total_trans)) if total_trans else 0.0,
        "ratio_stationnaire": (total_station / total_trans) if total_trans else 0.0,
        "entropie_actions_moyenne": sum(entropies) / len(entropies),
    }


def main() -> int:
    exp_dir = Path("donnees/config/experiences/snake_collectif_v1")
    runs_dir = exp_dir / "artefacts" / "runs"
    if not runs_dir.exists():
        print(f"[ERREUR] runs introuvable: {runs_dir}")
        return 2

    out_dir = exp_dir / "artefacts" / "analyses"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for d in sorted(runs_dir.glob("*")):
        if not d.is_dir():
            continue
        m = d / "metrics.jsonl"
        if not m.exists():
            continue
        stats = analyser_run(m)
        row = {"run_dir": str(d), "metrics": str(m), **stats}
        rows.append(row)

    if not rows:
        print("[ERREUR] Aucun metrics.jsonl trouvé sous runs/")
        return 3

    out1 = out_dir / "a105_diagnostic_par_run.csv"
    with out1.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # global: moyenne simple
    def _mean(key: str) -> float:
        vals = [float(r.get(key, 0.0) or 0.0) for r in rows if r.get(key) not in ("", None)]
        return sum(vals) / max(1, len(vals))

    global_row = {
        "runs": len(rows),
        "episodes_moyen": _mean("episodes"),
        "ticks_moyen": _mean("ticks_moyen"),
        "etats_uniques_moyen": _mean("etats_uniques_moyen"),
        "ratio_revisite_etats": _mean("ratio_revisite_etats"),
        "ratio_stationnaire": _mean("ratio_stationnaire"),
        "entropie_actions_moyenne": _mean("entropie_actions_moyenne"),
    }

    out2 = out_dir / "a105_diagnostic_global.csv"
    with out2.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(global_row.keys()))
        w.writeheader()
        w.writerow(global_row)

    print(f"[OK] écrit: {out1}")
    print(f"[OK] écrit: {out2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
