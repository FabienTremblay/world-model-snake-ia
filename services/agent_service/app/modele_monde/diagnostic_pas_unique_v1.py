# services/agent_service/app/modele_monde/diagnostic_pas_unique_v1.py
from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path
from typing import List, Tuple

from agent_service.app.modele_monde.entrainement_depuis_journal import iterer_transitions
from agent_service.app.modele_monde.simulateur_interne_v1 import (
    SimulateurInterneV1,
)


Transition = Tuple[dict, dict, int, int, str]


def _resume(nums: List[float]) -> dict:
    if not nums:
        return {"n": 0, "moy": 0.0, "med": 0.0, "min": 0.0, "max": 0.0}
    return {
        "n": len(nums),
        "moy": float(statistics.fmean(nums)),
        "med": float(statistics.median(nums)),
        "min": float(min(nums)),
        "max": float(max(nums)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Diagnostic du pas unique (one-step) pour vérifier si le world model tabulaire "
            "est utilisable comme simulateur interne."
        )
    )
    ap.add_argument("--journal", type=str, default="artefacts/episodes_latent_appris.jsonl")
    ap.add_argument(
        "--champ-latent",
        type=str,
        default="latent_id",
        help=(
            "Définition de l'état latent: 'checksum' calcule depuis capteurs_compact; "
            "sinon lit ce champ entier dans le journal (ex: latent_id)."
        ),
    )
    ap.add_argument(
        "--ratio-train",
        type=float,
        default=0.7,
        help="ratio de transitions utilisées pour entraîner (le reste sert au test)",
    )
    ap.add_argument(
        "--n-samples",
        type=int,
        default=20,
        help="nombre de tirages Monte-Carlo par transition (sampling hit-rate)",
    )
    ap.add_argument(
        "--topk",
        type=int,
        default=3,
        help="top-k pour la métrique de rang (k>=1)",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=123,
        help="seed RNG pour reproductibilité",
    )
    ap.add_argument(
        "--limite-test",
        type=int,
        default=0,
        help="si >0, limite le nombre de transitions test analysées",
    )
    args = ap.parse_args()

    journal_path = Path(args.journal)
    transitions: List[Transition] = list(iterer_transitions(journal_path, champ_latent=args.champ_latent))
    n = len(transitions)
    n_train = int(max(0, min(n, round(n * float(args.ratio_train)))))
    transitions_train = transitions[:n_train]
    transitions_test = transitions[n_train:]
    if args.limite_test and args.limite_test > 0:
        transitions_test = transitions_test[: int(args.limite_test)]

    # NOTE: entrainer_modele_tabulaire_v1 apprend sur tout le journal; ici on veut un split.
    # On entraîne donc explicitement sur transitions_train.
    from agent_service.app.modele_monde.tabulaire_v1 import ModeleMondeTabulaireV1

    modele_split = ModeleMondeTabulaireV1()
    for _prev, _evt, z, z1, action in transitions_train:
        modele_split.apprendre_transition(z, action, z1)

    sim = SimulateurInterneV1(modele_split, seed=args.seed)
    rng = random.Random(args.seed)

    total = 0
    couverts = 0
    inconnus = 0

    hits_sampling = 0
    hits_sampling_topk = 0
    ranks: List[float] = []
    confs: List[float] = []
    ents: List[float] = []
    supports: List[float] = []

    topk = max(1, int(args.topk))
    n_samples = max(1, int(args.n_samples))

    for _prev_evt, _evt, z, z1, action in transitions_test:
        total += 1
        pred = modele_split.predire(z, action)
        if pred.support <= 0 or not pred.distribution:
            inconnus += 1
            continue

        couverts += 1
        confs.append(float(pred.confiance))
        ents.append(float(pred.entropie))
        supports.append(float(pred.support))

        # Rang du vrai état (1 = meilleur), inf si absent
        items = sorted(pred.distribution.items(), key=lambda kv: kv[1], reverse=True)
        rang = None
        for i, (etat, _p) in enumerate(items, start=1):
            if int(etat) == int(z1):
                rang = i
                break
        if rang is None:
            rang = len(items) + 1
        ranks.append(float(rang))

        # Sampling hit-rate (tirages indépendants)
        # On utilise un RNG local pour éviter toute dépendance à l'état de sim.
        ok = 0
        ok_topk = 0
        for _ in range(n_samples):
            # sim.step() utilise son propre RNG; ici on veut un tirage brut contrôlé.
            # => on réutilise la logique via SimulateurInterneV1 en re-seedant par transition.
            sim.seed(rng.randint(0, 2**31 - 1))
            res = sim.step(z, action)
            if res.inconnu or res.etat_suivant is None:
                continue
            if int(res.etat_suivant) == int(z1):
                ok += 1
            # top-k sampling: vrai z1 fait-il partie des k premiers de la distribution ?
            # (mesure déterministe complémentaire)
            if any(int(etat) == int(z1) for etat, _p in items[:topk]):
                ok_topk = 1
        if ok > 0:
            hits_sampling += 1
        hits_sampling_topk += ok_topk

    couverture = (couverts / total) if total else 0.0
    hit_rate_sampling = (hits_sampling / couverts) if couverts else 0.0
    hit_rate_topk = (hits_sampling_topk / couverts) if couverts else 0.0

    rapport = {
        "journal_path": str(journal_path),
        "champ_latent": str(args.champ_latent),
        "ratio_train": float(args.ratio_train),
        "nb_transitions": int(n),
        "nb_train": int(n_train),
        "nb_test": int(len(transitions_test)),
        "limite_test": int(args.limite_test),
        "couverture_test": float(couverture),
        "inconnus_test": int(inconnus),
        "topk": int(topk),
        "n_samples": int(n_samples),
        "seed": int(args.seed),
        "hit_rate_sampling": float(hit_rate_sampling),
        "hit_rate_topk": float(hit_rate_topk),
        "rang_vrai_etat": _resume(ranks),
        "confiance": _resume(confs),
        "entropie": _resume(ents),
        "support": _resume(supports),
        "stats_modele": modele_split.stats(),
        "note": (
            "hit_rate_sampling = proportion de transitions test où au moins 1 tirage (sur n_samples) "
            "retombe sur le vrai etat suivant. hit_rate_topk = proportion de transitions test où le vrai "
            "etat suivant est dans le top-k de la distribution (déterministe)."
        ),
    }

    print(json.dumps(rapport, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

