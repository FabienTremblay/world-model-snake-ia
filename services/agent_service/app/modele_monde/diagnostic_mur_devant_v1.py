# services/agent_service/app/modele_monde/diagnostic_mur_devant_v1.py
"""Diagnostic ciblé: mur dans la direction de l'action.

Ce script lit un journal episodes.jsonl et calcule, sur les transitions observées:
- la proportion de transitions où l'action pointe vers un mur (motif==3)
- parmi ces transitions, la proportion de terminaisons observées au tick suivant

Il fournit aussi un tableau par action (haut/bas/gauche/droite).

Note: on reconstruit les motifs via les capteurs_compact; aucun champ additionnel n'est requis.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from runner.app.replay import decoder_capteurs_b64

from agent_service.app.modele_monde.latent_v1 import extraire_signaux_percus_voisinage_v1


MOTIF_MUR = 3
ACTIONS = {"haut", "bas", "gauche", "droite"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--journal", required=True, help="Path vers episodes.jsonl")
    p.add_argument("--limite", type=int, default=None, help="Limiter le nombre d'événements")
    return p


def _mur_dans_direction(extras: dict, action: str) -> bool:
    if action == "haut":
        return int(extras["motif_haut"]) == MOTIF_MUR
    if action == "bas":
        return int(extras["motif_bas"]) == MOTIF_MUR
    if action == "gauche":
        return int(extras["motif_gauche"]) == MOTIF_MUR
    if action == "droite":
        return int(extras["motif_droite"]) == MOTIF_MUR
    return False


def main() -> int:
    args = _parser().parse_args()
    path = Path(args.journal)

    # Regrouper par episode_id pour reconstruire les transitions tick->tick+1
    episodes: dict[int, list[dict]] = defaultdict(list)

    nb_evt = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            evt = json.loads(line)
            episodes[int(evt["episode_id"])].append(evt)
            nb_evt += 1
            if args.limite is not None and nb_evt >= int(args.limite):
                break

    total_transitions = 0
    total_mur_action = 0
    total_mur_action_termine = 0

    par_action = Counter()
    par_action_mur = Counter()
    par_action_mur_termine = Counter()

    # Analyse par episode
    for _, evts in episodes.items():
        evts.sort(key=lambda e: int(e.get("tick", 0)))
        for i in range(len(evts) - 1):
            e0 = evts[i]
            e1 = evts[i + 1]

            # transition valide: ticks consécutifs
            if int(e1.get("tick", -999)) != int(e0.get("tick", -999)) + 1:
                continue

            # Convention du journal:
            # - l'état observé est celui du tick t  (capteurs de e0)
            # - l'action appliquée pour passer à t+1 est enregistrée sur l'événement t+1 (e1.action)
            #   (ex.: tick=0 action=null, tick=1 action='haut')
            # - la terminaison causée par l'action est constatée sur e1.termine
            action = e1.get("action")
            if action not in ACTIONS:
                continue

            w = int(e0["largeur"])
            h = int(e0["hauteur"])
            capteurs = decoder_capteurs_b64(e0["capteurs_compact"], largeur=w, hauteur=h)
            extras = extraire_signaux_percus_voisinage_v1(capteurs)
            if extras is None:
                continue

            total_transitions += 1
            par_action[action] += 1

            vers_mur = _mur_dans_direction(extras, action)
            if vers_mur:
                total_mur_action += 1
                par_action_mur[action] += 1

                termine_next = bool(e1.get("termine", False))
                if termine_next:
                    total_mur_action_termine += 1
                    par_action_mur_termine[action] += 1

    def ratio(a: int, b: int) -> float:
        return float(a) / float(b) if b else 0.0

    out = {
        "journal": str(path),
        "nb_evenements": nb_evt,
        "nb_transitions": total_transitions,
        "nb_action_vers_mur": total_mur_action,
        "ratio_action_vers_mur": ratio(total_mur_action, total_transitions),
        "nb_termine_si_action_vers_mur": total_mur_action_termine,
        "ratio_termine_si_action_vers_mur": ratio(total_mur_action_termine, total_mur_action),
        "par_action": {
            a: {
                "nb_transitions": int(par_action[a]),
                "nb_action_vers_mur": int(par_action_mur[a]),
                "ratio_action_vers_mur": ratio(int(par_action_mur[a]), int(par_action[a])),
                "nb_termine_si_action_vers_mur": int(par_action_mur_termine[a]),
                "ratio_termine_si_action_vers_mur": ratio(
                    int(par_action_mur_termine[a]), int(par_action_mur[a])
                ),
            }
            for a in sorted(ACTIONS)
        },
        "note": "motif==3 est interprété comme mur (voir latent_v1._motif_cellule).",
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
