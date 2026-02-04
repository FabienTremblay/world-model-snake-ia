# services/agent_service/app/modele_monde/diagnostic_collision_soi_devant_v1.py
"""Diagnostic ciblé: collision avec le corps dans la direction de l'action.

Convention du journal:
- l'état observé est celui du tick t  (capteurs de e0)
- l'action appliquée pour passer à t+1 est enregistrée sur l'événement t+1 (e1.action)
  (ex.: tick=0 action=null, tick=1 action='haut')
- la terminaison causée par l'action est constatée sur e1.termine (et souvent e1.raison_fin)

Ce script lit un journal episodes.jsonl et calcule, sur les transitions observées:
- la proportion de transitions où l'action pointe vers une case occupée par le corps (motif_corps)
- parmi ces transitions, la proportion de terminaisons observées au tick suivant
- optionnel: la proportion de terminaisons avec raison_fin == collision_soi

Note: on reconstruit les motifs via capteurs_compact; aucun champ additionnel n'est requis.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from runner.app.replay import decoder_capteurs_b64

# On réutilise la même fonction de voisinage que le diagnostic mur.
from agent_service.app.modele_monde.latent_v1 import extraire_signaux_percus_voisinage_v1


ACTIONS = {"haut", "bas", "gauche", "droite"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--journal", required=True, help="Path vers episodes.jsonl")
    p.add_argument("--limite", type=int, default=None, help="Limiter le nombre d'événements")
    p.add_argument(
        "--motif-corps",
        type=int,
        default=1,
        help="Valeur de motif interprétée comme 'corps' (par défaut 1).",
    )
    p.add_argument(
        "--raison-fin",
        default="collision_soi",
        help="Valeur attendue de raison_fin (défaut: collision_soi).",
    )
    return p


def _motif_dans_direction(extras: dict, action: str) -> int | None:
    if action == "haut":
        return int(extras["motif_haut"])
    if action == "bas":
        return int(extras["motif_bas"])
    if action == "gauche":
        return int(extras["motif_gauche"])
    if action == "droite":
        return int(extras["motif_droite"])
    return None


def main() -> int:
    args = _parser().parse_args()
    path = Path(args.journal)
    motif_corps = int(args.motif_corps)
    raison_attendue = str(args.raison_fin)

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
    total_corps_action = 0
    total_corps_action_termine = 0
    total_corps_action_raison = 0

    par_action = Counter()
    par_action_corps = Counter()
    par_action_corps_termine = Counter()
    par_action_corps_raison = Counter()

    for _, evts in episodes.items():
        evts.sort(key=lambda e: int(e.get("tick", 0)))
        for i in range(len(evts) - 1):
            e0 = evts[i]
            e1 = evts[i + 1]

            if int(e1.get("tick", -999)) != int(e0.get("tick", -999)) + 1:
                continue

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

            motif_dir = _motif_dans_direction(extras, action)
            if motif_dir == motif_corps:
                total_corps_action += 1
                par_action_corps[action] += 1

                termine_next = bool(e1.get("termine", False))
                if termine_next:
                    total_corps_action_termine += 1
                    par_action_corps_termine[action] += 1

                    if str(e1.get("raison_fin") or "") == raison_attendue:
                        total_corps_action_raison += 1
                        par_action_corps_raison[action] += 1

    def ratio(a: int, b: int) -> float:
        return float(a) / float(b) if b else 0.0

    out = {
        "journal": str(path),
        "nb_evenements": nb_evt,
        "nb_transitions": total_transitions,
        "motif_corps": motif_corps,
        "raison_fin_attendue": raison_attendue,
        "nb_action_vers_corps": total_corps_action,
        "ratio_action_vers_corps": ratio(total_corps_action, total_transitions),
        "nb_termine_si_action_vers_corps": total_corps_action_termine,
        "ratio_termine_si_action_vers_corps": ratio(total_corps_action_termine, total_corps_action),
        "nb_raison_fin_attendue_si_action_vers_corps": total_corps_action_raison,
        "ratio_raison_fin_attendue_si_action_vers_corps": ratio(total_corps_action_raison, total_corps_action),
        "par_action": {
            a: {
                "nb_transitions": int(par_action[a]),
                "nb_action_vers_corps": int(par_action_corps[a]),
                "ratio_action_vers_corps": ratio(int(par_action_corps[a]), int(par_action[a])),
                "nb_termine_si_action_vers_corps": int(par_action_corps_termine[a]),
                "ratio_termine_si_action_vers_corps": ratio(
                    int(par_action_corps_termine[a]), int(par_action_corps[a])
                ),
                "nb_raison_fin_attendue_si_action_vers_corps": int(par_action_corps_raison[a]),
                "ratio_raison_fin_attendue_si_action_vers_corps": ratio(
                    int(par_action_corps_raison[a]), int(par_action_corps[a])
                ),
            }
            for a in sorted(ACTIONS)
        },
        "note": "motif_corps est paramétrable; motif==3 est le mur dans l'autre diagnostic.",
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
