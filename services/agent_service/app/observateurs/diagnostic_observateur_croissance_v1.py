# services/agent_service/app/observateurs/diagnostic_observateur_croissance_v1.py
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from agent_service.app.contrats_agents import ContexteDecision, ContextePerception
from agent_service.app.signaux.signaux_percus_v1 import extraire_signaux_percus_v1
from agent_service.app.observateurs.observateur_croissance_v1 import ObservateurCroissanceV1


def _lire_lignes(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="diagnostic_observateur_croissance_v1",
        description="Calcule des stats de signaux perçus et d'utilité (observateur croissance) depuis un journal jsonl.",
    )
    ap.add_argument("--journal", type=str, required=True)
    ap.add_argument("--poids-croissance", type=float, default=1.0)
    ap.add_argument("--penalite-collision-mur", type=float, default=1.0)
    args = ap.parse_args(argv)

    journal_path = Path(args.journal)
    obs = ObservateurCroissanceV1(
        poids_croissance=float(args.poids_croissance),
        penalite_collision_mur=float(args.penalite_collision_mur),
    )

    # regrouper par épisode pour garantir l'ordre tick
    par_episode: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for e in _lire_lignes(journal_path):
        par_episode[(str(e.get("run_id")), int(e.get("episode_id", 0)))].append(e)

    utilites = []
    compte_signaux = Counter()
    nb_transitions = 0

    for (run_id, episode_id), evts in par_episode.items():
        evts.sort(key=lambda x: int(x.get("tick", 0)))
        if len(evts) < 2:
            continue

        ctx = ContexteDecision(
            run_id=run_id,
            episode_id=episode_id,
            tick=0,
            observations={},
            info={"largeur": int(evts[0].get("largeur", 0) or 0), "hauteur": int(evts[0].get("hauteur", 0) or 0)},
        )

        for i in range(1, len(evts)):
            prev_evt = evts[i - 1]
            curr_evt = evts[i]
            ctx = ContexteDecision(
                run_id=run_id,
                episode_id=episode_id,
                tick=int(curr_evt.get("tick", 0) or 0),
                observations={},
                info=ctx.info,
            )

            signaux = extraire_signaux_percus_v1(
                prev_evt=prev_evt,
                curr_evt=curr_evt,
                capteurs_t=None,
                capteurs_t1=None,
                contexte=ctx,
            )
            nb_transitions += 1

            dl = int(signaux.get("delta_longueur", 0) or 0)
            ds = int(signaux.get("delta_score", 0) or 0)
            if dl > 0:
                compte_signaux["croissance"] += 1
            if ds > 0:
                compte_signaux["delta_score_pos"] += 1
            if bool(signaux.get("termine", False)):
                compte_signaux["termine"] += 1
            if bool(signaux.get("collision_mur", False)):
                compte_signaux["collision_mur"] += 1

            u = obs.utilite(signaux)
            utilites.append(u)

    resume = {
        "journal": str(journal_path),
        "nb_episodes": len(par_episode),
        "nb_transitions": nb_transitions,
        "compte_signaux": dict(compte_signaux),
        "ratio_croissance": (compte_signaux["croissance"] / nb_transitions) if nb_transitions else 0.0,
        "utilite_moy": (sum(utilites) / len(utilites)) if utilites else 0.0,
        "utilite_min": min(utilites) if utilites else 0.0,
        "utilite_max": max(utilites) if utilites else 0.0,
        "note": "v1 utilise signaux_percus (mode estrade) mais la signature est prête pour perception partielle.",
    }

    print(json.dumps(resume, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

