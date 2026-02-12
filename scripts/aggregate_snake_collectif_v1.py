#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agrégation robuste des journaux JSONL de la campagne snake_collectif_v1.

Entrée (créée par scripts/run_demo_c1_vs_c2.sh):
  artefacts/experiences/snake_collectif_v1/C1/seed_0/train.jsonl
  artefacts/experiences/snake_collectif_v1/C1/seed_0/eval.jsonl
  ... idem C2

Sorties:
  artefacts/experiences/snake_collectif_v1/resume_par_run.csv
  artefacts/experiences/snake_collectif_v1/resume_global.csv

Le format exact des events peut évoluer (tick-level, episode-level, etc.).
Ce script applique des heuristiques:
- groupage par 'episode' si présent, sinon détection par reset de 'tick'
  (tick qui revient à 0) ou par events de début d'épisode.
- score = dernière valeur numérique rencontrée parmi des clés candidates
- raison_fin = dernière valeur texte rencontrée parmi des clés candidates
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --- Heuristiques de clés ---
CLES_SCORE = ("score", "score_episode", "score_total", "recompense", "reward")
CLES_TICK = ("tick", "t", "pas", "step")
CLES_EPISODE = ("episode", "episode_id", "id_episode", "ep")
CLES_RAISONS = ("raison_fin", "cause_fin", "fin", "termination", "cause", "motif_fin")
CLES_LONGUEUR = ("longueur", "taille", "length", "snake_len", "snake_length")
CLES_EVENT = ("event", "type", "evt")

EVENTS_DEBUT = {"episode_debut", "debut_episode", "episode_start", "start_episode"}
EVENTS_FIN = {"episode_fin", "fin_episode", "episode_end", "end_episode", "termine", "episode_termine"}

RX_MUR = re.compile(r"(mur|wall)", re.IGNORECASE)
RX_CORPS = re.compile(r"(corps|body|self)", re.IGNORECASE)
RX_FAMINE = re.compile(r"(famine|starv)", re.IGNORECASE)

@dataclass
class ResumeEpisode:
    episode: int
    score: Optional[float] = None
    ticks: Optional[int] = None
    raison_fin: Optional[str] = None
    longueur_finale: Optional[int] = None

def _premiere_valeur(obj: Dict[str, Any], cles: Tuple[str, ...]) -> Optional[Any]:
    for k in cles:
        if k in obj:
            return obj[k]
    return None

def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return None
        return float(x)
    except Exception:
        return None

def _as_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return None
        return int(x)
    except Exception:
        return None

def _as_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return None
    s = str(x).strip()
    return s or None

def _detecter_episode_par_event(obj: Dict[str, Any]) -> Tuple[bool, bool]:
    ev = _premiere_valeur(obj, CLES_EVENT)
    evs = _as_str(ev)
    if not evs:
        return (False, False)
    evs = evs.strip()
    return (evs in EVENTS_DEBUT, evs in EVENTS_FIN)

def _charger_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                # ligne non JSON : on ignore (robuste)
                continue

def _resumer_fichier(path: Path) -> List[ResumeEpisode]:
    episodes: List[ResumeEpisode] = []

    episode_courant = 0
    dernier_tick: Optional[int] = None
    courant = ResumeEpisode(episode=episode_courant)

    def pousser():
        nonlocal courant
        episodes.append(courant)
        courant = ResumeEpisode(episode=episode_courant)

    for obj in _charger_jsonl(path):
        # Si l'episode est explicitement fourni : on switch directement
        ep_val = _premiere_valeur(obj, CLES_EPISODE)
        ep_int = _as_int(ep_val)
        if ep_int is not None:
            if ep_int != episode_courant:
                # pousser l'ancien épisode si on a déjà des données
                if courant.score is not None or courant.ticks is not None or courant.raison_fin is not None:
                    episodes.append(courant)
                episode_courant = ep_int
                courant = ResumeEpisode(episode=episode_courant)
                dernier_tick = None

        # Détection par event
        debut, fin = _detecter_episode_par_event(obj)
        if debut and (courant.score is not None or courant.ticks is not None or courant.raison_fin is not None):
            # nouveau départ => on clôt l'épisode courant
            episodes.append(courant)
            episode_courant += 1
            courant = ResumeEpisode(episode=episode_courant)
            dernier_tick = None

        # Détection par tick reset
        tick_val = _premiere_valeur(obj, CLES_TICK)
        tick_int = _as_int(tick_val)
        if tick_int is not None:
            if dernier_tick is not None and tick_int == 0 and dernier_tick > 0:
                # nouveau épisode
                episodes.append(courant)
                episode_courant += 1
                courant = ResumeEpisode(episode=episode_courant)
            dernier_tick = tick_int
            # ticks: on garde le max observé
            if courant.ticks is None or tick_int > courant.ticks:
                courant.ticks = tick_int

        # Score (dernière valeur rencontrée)
        score_val = _premiere_valeur(obj, CLES_SCORE)
        score_f = _as_float(score_val)
        if score_f is not None:
            courant.score = score_f

        # Longueur
        long_val = _premiere_valeur(obj, CLES_LONGUEUR)
        long_i = _as_int(long_val)
        if long_i is not None:
            courant.longueur_finale = long_i

        # Raison fin
        rf_val = _premiere_valeur(obj, CLES_RAISONS)
        rf_s = _as_str(rf_val)
        if rf_s is not None:
            courant.raison_fin = rf_s

        if fin:
            # fin d'épisode explicite
            episodes.append(courant)
            episode_courant += 1
            courant = ResumeEpisode(episode=episode_courant)
            dernier_tick = None

    # pousser le dernier si non vide
    if courant.score is not None or courant.ticks is not None or courant.raison_fin is not None:
        episodes.append(courant)

    # Normaliser ticks : si tick est 0..N, alors ticks_survecus = N+1
    for ep in episodes:
        if ep.ticks is not None:
            ep.ticks = ep.ticks + 1

    return episodes

def _taux_raison(raisons: List[str], rx: re.Pattern) -> float:
    if not raisons:
        return 0.0
    nb = sum(1 for r in raisons if rx.search(r or ""))
    return nb / max(1, len(raisons))

def main() -> int:
    racine = Path("artefacts/experiences/snake_collectif_v1")
    if not racine.exists():
        print(f"[ERREUR] Racine introuvable: {racine} (lancer depuis la racine du repo)")
        return 2

    runs: List[Dict[str, Any]] = []
    for condition in ("C1", "C2"):
        for seed_dir in sorted((racine / condition).glob("seed_*")):
            seed_m = re.search(r"seed_(\d+)", seed_dir.name)
            if not seed_m:
                continue
            seed = int(seed_m.group(1))
            for phase in ("train", "eval"):
                f = seed_dir / f"{phase}.jsonl"
                if not f.exists():
                    continue
                eps = _resumer_fichier(f)
                scores = [e.score for e in eps if e.score is not None]
                ticks = [e.ticks for e in eps if e.ticks is not None]
                raisons = [e.raison_fin for e in eps if e.raison_fin is not None]

                row = {
                    "condition": condition,
                    "seed": seed,
                    "phase": phase,
                    "fichier": str(f),
                    "episodes_detectes": len(eps),
                    "score_moyen": (sum(scores)/len(scores)) if scores else "",
                    "ticks_moyen": (sum(ticks)/len(ticks)) if ticks else "",
                    "taux_mur": _taux_raison(raisons, RX_MUR) if raisons else "",
                    "taux_corps": _taux_raison(raisons, RX_CORPS) if raisons else "",
                    "taux_famine": _taux_raison(raisons, RX_FAMINE) if raisons else "",
                }
                runs.append(row)

    if not runs:
        print("[ERREUR] Aucun run trouvé. Vérifie que les fichiers train/eval.jsonl existent.")
        return 3

    out1 = racine / "resume_par_run.csv"
    champs = list(runs[0].keys())
    with out1.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for r in runs:
            w.writerow(r)

    # Agrégat global par condition/phase
    def _float_or_none(x):
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
            scores = [ _float_or_none(r["score_moyen"]) for r in sub ]
            scores = [s for s in scores if s is not None]
            ticks = [ _float_or_none(r["ticks_moyen"]) for r in sub ]
            ticks = [t for t in ticks if t is not None]
            taux_mur = [ _float_or_none(r["taux_mur"]) for r in sub ]
            taux_mur = [t for t in taux_mur if t is not None]
            taux_corps = [ _float_or_none(r["taux_corps"]) for r in sub ]
            taux_corps = [t for t in taux_corps if t is not None]
            taux_famine = [ _float_or_none(r["taux_famine"]) for r in sub ]
            taux_famine = [t for t in taux_famine if t is not None]

            global_rows.append({
                "condition": condition,
                "phase": phase,
                "runs": len(sub),
                "score_moyen_moyenne_seeds": (sum(scores)/len(scores)) if scores else "",
                "ticks_moyen_moyenne_seeds": (sum(ticks)/len(ticks)) if ticks else "",
                "taux_mur_moyenne_seeds": (sum(taux_mur)/len(taux_mur)) if taux_mur else "",
                "taux_corps_moyenne_seeds": (sum(taux_corps)/len(taux_corps)) if taux_corps else "",
                "taux_famine_moyenne_seeds": (sum(taux_famine)/len(taux_famine)) if taux_famine else "",
            })

    out2 = racine / "resume_global.csv"
    champs2 = list(global_rows[0].keys())
    with out2.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs2)
        w.writeheader()
        for r in global_rows:
            w.writerow(r)

    print(f"[OK] écrit: {out1}")
    print(f"[OK] écrit: {out2}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
