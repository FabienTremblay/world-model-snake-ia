#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Agrégation — snake_collectif_v1 (exp-local)

Entrée (centralisée par scripts/run_demo_c1_vs_c2.sh):
  artefacts/experiences/snake_collectif_v1/C1/seed_0/train.jsonl
  ...

Sorties (dans l'expérience, pas à la racine du repo):
  donnees/config/experiences/snake_collectif_v1/artefacts/analyses/resume_par_run.csv
  donnees/config/experiences/snake_collectif_v1/artefacts/analyses/resume_global.csv

Note:
- Les runs actuels semblent se terminer par *timeout max-ticks* (termine=false, raison_fin=null).
  Donc les colonnes de raisons fin seront vides tant que le moteur ne journalise pas la cause.
"""

from __future__ import annotations

import csv, json, re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

CLES_SCORE = ("score", "score_episode", "score_total", "recompense", "reward")
CLES_TICK = ("tick", "t", "pas", "step")
CLES_EPISODE = ("episode_id", "episode", "episodeId", "ep")
CLES_RAISONS = ("raison_fin", "cause_fin", "fin", "termination", "cause", "motif_fin")
CLES_TERMINE = ("termine", "done", "terminal", "fini")

def _premiere_valeur(obj: Dict[str, Any], cles: Tuple[str, ...]) -> Optional[Any]:
    for k in cles:
        if k in obj:
            return obj[k]
    return None

def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None or isinstance(x, bool):
            return None
        return float(x)
    except Exception:
        return None

def _as_int(x: Any) -> Optional[int]:
    try:
        if x is None or isinstance(x, bool):
            return None
        return int(x)
    except Exception:
        return None

def _as_str(x: Any) -> Optional[str]:
    if x is None or isinstance(x, (dict, list)):
        return None
    s = str(x).strip()
    return s or None

def _charger_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def _resumer_fichier(path: Path) -> Dict[str, Any]:
    # Résumé par episode_id (présent dans tes lignes)
    stats: Dict[int, Dict[str, Any]] = {}
    for obj in _charger_jsonl(path):
        ep = _as_int(_premiere_valeur(obj, CLES_EPISODE))
        if ep is None:
            continue
        st = stats.setdefault(ep, {"score": None, "tick_max": None, "raison_fin": None, "termine_true": False})
        tick = _as_int(_premiere_valeur(obj, CLES_TICK))
        if tick is not None:
            st["tick_max"] = tick if st["tick_max"] is None else max(st["tick_max"], tick)

        score = _as_float(_premiere_valeur(obj, CLES_SCORE))
        if score is not None:
            st["score"] = score

        rf = _as_str(_premiere_valeur(obj, CLES_RAISONS))
        if rf is not None:
            st["raison_fin"] = rf

        term = _premiere_valeur(obj, CLES_TERMINE)
        if term is True:
            st["termine_true"] = True

    episodes = sorted(stats.keys())
    scores = [stats[e]["score"] for e in episodes if stats[e]["score"] is not None]
    ticks = [stats[e]["tick_max"] for e in episodes if stats[e]["tick_max"] is not None]

    # tick_max est un index -> ticks_survecus = tick_max + 1
    ticks_survecus = [(t + 1) for t in ticks] if ticks else []

    # Causes fin (si le moteur les remplit)
    raisons = [stats[e]["raison_fin"] for e in episodes if stats[e]["raison_fin"]]
    nb_termine_true = sum(1 for e in episodes if stats[e]["termine_true"])

    return {
        "episodes_detectes": len(episodes),
        "score_moyen": (sum(scores)/len(scores)) if scores else "",
        "ticks_moyen": (sum(ticks_survecus)/len(ticks_survecus)) if ticks_survecus else "",
        "nb_episode_termine_true": nb_termine_true,
        "nb_raisons_fin": len(raisons),
    }

def main() -> int:
    # Racine "campagne" centralisée
    racine = Path("artefacts/experiences/snake_collectif_v1")
    if not racine.exists():
        print(f"[ERREUR] Racine campagne introuvable: {racine}")
        return 2

    out_dir = Path("donnees/config/experiences/snake_collectif_v1/artefacts/analyses")
    out_dir.mkdir(parents=True, exist_ok=True)

    runs: List[Dict[str, Any]] = []
    for condition in ("C1", "C2"):
        for seed_dir in sorted((racine / condition).glob("seed_*")):
            m = re.search(r"seed_(\d+)", seed_dir.name)
            if not m:
                continue
            seed = int(m.group(1))
            for phase in ("train", "eval"):
                f = seed_dir / f"{phase}.jsonl"
                if not f.exists():
                    continue
                res = _resumer_fichier(f)
                runs.append({
                    "condition": condition,
                    "seed": seed,
                    "phase": phase,
                    "fichier": str(f),
                    **res,
                })

    if not runs:
        print("[ERREUR] Aucun fichier train/eval.jsonl trouvé sous artefacts/experiences/snake_collectif_v1/")
        return 3

    out1 = out_dir / "resume_par_run.csv"
    champs = list(runs[0].keys())
    with out1.open("w", encoding="utf-8", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=champs)
        w.writeheader()
        for r in runs:
            w.writerow(r)

    # global
    def _f(x):
        try:
            return float(x)
        except Exception:
            return None

    global_rows = []
    for condition in ("C1", "C2"):
        for phase in ("train", "eval"):
            sub = [r for r in runs if r["condition"] == condition and r["phase"] == phase]
            if not sub:
                continue
            scores = [ _f(r["score_moyen"]) for r in sub ]
            scores = [s for s in scores if s is not None]
            ticks = [ _f(r["ticks_moyen"]) for r in sub ]
            ticks = [t for t in ticks if t is not None]
            term_true = [ int(r["nb_episode_termine_true"]) for r in sub ]
            raisons = [ int(r["nb_raisons_fin"]) for r in sub ]

            global_rows.append({
                "condition": condition,
                "phase": phase,
                "runs": len(sub),
                "score_moyen_moyenne_seeds": (sum(scores)/len(scores)) if scores else "",
                "ticks_moyen_moyenne_seeds": (sum(ticks)/len(ticks)) if ticks else "",
                "nb_episode_termine_true_total": sum(term_true),
                "nb_raisons_fin_total": sum(raisons),
            })

    out2 = out_dir / "resume_global.csv"
    champs2 = list(global_rows[0].keys())
    with out2.open("w", encoding="utf-8", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=champs2)
        w.writeheader()
        for r in global_rows:
            w.writerow(r)

    print(f"[OK] écrit: {out1}")
    print(f"[OK] écrit: {out2}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
