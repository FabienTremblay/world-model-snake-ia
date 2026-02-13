#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Observateur O1 — Surprise de transition (v1)

Détecte les "bris" au sens:
- on apprend P(etat_suivant | etat, action) sur les transitions observées
- puis on marque comme surprise une transition dont etat_suivant != transition la plus probable

Important:
- Si l'état (checksum) est très complet et l'environnement déterministe, la surprise peut être 0.
  Dans ce cas, tu peux choisir une abstraction plus grossière via --prefix-bits (ex: 16)
  pour regrouper plusieurs états en une même classe.

Entrée
- --run-dir: dossier du run (doit contenir metrics.jsonl)

Sortie
- JSONL de propositions type "surprise_transition"
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, Tuple

# ---------------------------------------------------------------------------
# Bootstrap import: l'expérience vit hors du package Python.
# On veut pouvoir exécuter:
#   python donnees/config/experiences/.../o1_observateur_surprise_v1.py
# sans exiger PYTHONPATH=services.
# ---------------------------------------------------------------------------
try:
    from commun.actions_snake import est_action_snake  # type: ignore
except Exception:
    _ici = Path(__file__).resolve()
    # .../donnees/config/experiences/snake_collectif_v1/outils/o1_....py
    # remonter au root du repo ia-snake
    _repo_root = _ici.parents[5]
    _services = _repo_root / "services"
    if str(_services) not in sys.path:
        sys.path.insert(0, str(_services))
    from commun.actions_snake import est_action_snake  # type: ignore


def _etat_cle(checksum: int, prefix_bits: int) -> int:
    if prefix_bits >= 32:
        return int(checksum) & 0xFFFFFFFF
    shift = 32 - prefix_bits
    return (int(checksum) & 0xFFFFFFFF) >> shift


def lire_metrics(metrics_path: Path):
    for line in metrics_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True, help="Dossier du run (contient metrics.jsonl)")
    p.add_argument("--sortie", required=True, help="Fichier JSONL de sortie")
    p.add_argument("--prefix-bits", type=int, default=32,
                   help="Abstraction de l'état: nombre de bits conservés sur checksum (32=aucune)")
    p.add_argument("--min-support", type=int, default=10, help="Support minimal pour émettre une proposition")
    args = p.parse_args()

    run_dir = Path(args.run_dir)
    metrics_path = run_dir / "metrics.jsonl"
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.jsonl introuvable: {metrics_path}")

    # 1) apprendre distribution P(suivant | (etat, action))
    dist: Dict[Tuple[int, str], Counter] = defaultdict(Counter)
    total = 0
    actions_inconnues = 0
    for m in lire_metrics(metrics_path):
        chk_avant = m.get("checksum_avant")
        chk = m.get("checksum")
        action = m.get("action")
        if chk_avant is None or chk is None or action is None:
            continue
        # Contrat actions snake: valider les actions canoniques.
        # Si une action non canonique apparaît, on la compte et on la saute.
        if not est_action_snake(str(action)):
            actions_inconnues += 1
            continue
        ea = (_etat_cle(chk_avant, args.prefix_bits), str(action))
        es = _etat_cle(chk, args.prefix_bits)
        dist[ea][es] += 1
        total += 1

    # 2) produire surprises: transitions != argmax
    propositions = []
    surprises = 0
    for (etat, action), counts in dist.items():
        support = sum(counts.values())
        if support < args.min_support:
            continue
        etat_mode, c_mode = counts.most_common(1)[0]
        # proportion surprise = 1 - p(mode)
        p_mode = c_mode / support
        if len(counts) <= 1:
            # déterministe à cette abstraction, pas de surprise locale
            continue
        # on produit une proposition "surprise_transition" au niveau (etat, action) en indiquant dispersion
        entropie = 0.0
        for c in counts.values():
            p_ = c / support
            entropie -= p_ * math.log(p_ + 1e-12)
        propositions.append({
            "type": "surprise_transition",
            "cible": {"etat": etat, "action": action},
            "hypothese": {"etat_mode": etat_mode},
            "preuve": {
                "support": support,
                "p_mode": p_mode,
                "nb_suivants_distincts": len(counts),
                "entropie": entropie,
                "suivants_top": counts.most_common(5),
                "prefix_bits": args.prefix_bits,
            },
            "support": support,
            "confiance": 1.0 - p_mode,
            "source": {"observateur": "O1", "run_dir": str(run_dir)},
        })
        surprises += 1

    sortie = Path(args.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with sortie.open("w", encoding="utf-8") as f:
        for prop in propositions:
            f.write(json.dumps(prop, ensure_ascii=False) + "\n")

    print(f"[OK] écrit: {sortie} ({len(propositions)} propositions)")
    if actions_inconnues:
        print(f"[INFO] actions ignorées (non canoniques ActionSnake): {actions_inconnues}")
    if len(propositions) == 0:
        print("[INFO] 0 surprise détectée. Causes fréquentes:")
        print("       - état trop complet + environnement déterministe (normal)")
        print("       - min-support trop élevé")
        print("       Astuce: réessaie avec --prefix-bits 16 ou 20.")


if __name__ == "__main__":
    main()
