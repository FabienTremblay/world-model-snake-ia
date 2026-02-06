# -*- coding: utf-8 -*-
"""
CLI - recoder_delta_score_pos_v1

But:
- lire un journal episodes.jsonl (events)
- calculer delta_score_pos par épisode (run_id, episode_id) à partir du champ `score`
  en regardant la différence entre tick courant et tick précédent
- écrire un nouveau jsonl où chaque événement reçoit: `delta_score_pos`

Convention:
- tick 0 (ou premier event d'un épisode) => delta_score_pos = None
- sinon:
    delta_score_pos = 1 si score(t) > score(t-1)
    delta_score_pos = 0 sinon
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, Any

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--journal", required=True, help="Path vers episodes.jsonl")
    p.add_argument("--out", required=False, help="Sortie episodes_delta_score_pos.jsonl (optionnel si --experience)")
    p.add_argument("--experience", required=False, help="Id d'expérience (pour résoudre les chemins + défauts de sortie)")
     p.add_argument(
    p.add_argument(
        "--champ",
        default="delta_score_pos",
        help="Nom du champ écrit (défaut: delta_score_pos)",
    )
    p.add_argument(
        "--tick0-none",
        action="store_true",
        help="Si présent: tick==0 => None (défaut). Sinon tick==0 => 0.",
    )
    p.add_argument("--limite", type=int, default=None, help="Limiter le nombre d'événements écrits")
    return p


def main() -> int:
    args = _parser().parse_args()
    racine = Path(__file__).resolve().parents[4]

    bac = None
    if args.experience:
        bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
        bac.assurer_structure()

    # entrée
    journal_path = Path(args.journal)
    if bac is not None and not journal_path.is_absolute():
        journal_path = bac.resoudre_chemin(journal_path)

    # sortie
    if args.out:
        out_path = Path(args.out)
        if bac is not None and not out_path.is_absolute():
            out_path = bac.resoudre_chemin(out_path)
    else:
        if bac is None:
            raise SystemExit("Il faut fournir --out, ou bien fournir --experience pour calculer une sortie par défaut.")
        out_path = bac.paths.datasets_dir / f"{journal_path.stem}_delta_score_pos.jsonl"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    nb_in = 0
    nb_out = 0
    nb_skip = 0

    # mémoire minimale: score précédent par épisode (run_id, episode_id)
    prev_score: Dict[Tuple[str, int], int] = {}

    with open(journal_path, "r", encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
        for line in f:
            line = line.strip()
            if not line:
                continue
            nb_in += 1
            try:
                evt = json.loads(line)

                run_id = str(evt.get("run_id", ""))
                episode_id = int(evt.get("episode_id", 0))
                tick = int(evt.get("tick", 0))

                # score doit être numérique
                score = evt.get("score", None)
                if score is None:
                    raise ValueError("score manquant")
                score_i = int(score)

                key = (run_id, episode_id)

                if tick == 0 or key not in prev_score:
                    # premier event => None par défaut (ou 0 si on choisit)
                    delta = None if args.tick0_none or True else 0  # keep default None
                    prev_score[key] = score_i
                else:
                    delta = 1 if score_i > prev_score[key] else 0
                    prev_score[key] = score_i

                evt2 = dict(evt)
                evt2[args.champ] = delta
            except Exception:
                nb_skip += 1
                continue

            out.write(json.dumps(evt2, ensure_ascii=False) + "\n")
            nb_out += 1

            if args.limite is not None and nb_out >= int(args.limite):
                break

    print(f"[ok] lu: {nb_in} ; écrit: {nb_out} ; ignorés: {nb_skip}")
    print(f"[ok] sortie: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

