# services/agent_service/app/modele_monde/diagnostic_termination_binning_v1.py
from __future__ import annotations

"""Diagnostic - binning de P(termine) et support0_ratio.

Motivation (Cours 4):
- quand le latent est trop précis (ex: checksum), la plupart des clés (z,a,z1)
  ont support=0 => p_fin "None" => MPC/observateur ne généralise pas.
- quand le latent regroupe par signaux perçus, les clés se répètent => support>0
  et p_fin peut "s'allumer" sur les transitions dangereuses.

Ce script:
- entraîne (modele_monde, modele_t, modele_u) depuis un journal
- évalue sur le même journal (diagnostic simple) la distribution de p_fin
  et le ratio de transitions inconnues (support=0).

Usage:
  PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_termination_binning_v1 \
    --journal artefacts/episodes_signaux_hash.jsonl \
    --champ-latent signaux_hash
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

from agent_service.app.modele_monde.entrainement_depuis_journal import (
    entrainer_utilite_observateur_tabulaire_v1,
    iterer_transitions,
)


def _bin_p(p: float) -> float:
    # bins grossiers (pédagogiques)
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    # arrondi au dixième pour avoir peu de catégories
    return round(float(p), 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--experience", required=False, help="Id d'expérience (pour résoudre les chemins + sortie défaut)")
    ap.add_argument("--out", required=False, help="Fichier JSON de sortie (optionnel; défaut: artefacts/diagnostics)")
    ap.add_argument(
        "--champ-latent",
        default="checksum",
        help='"checksum" calcule depuis capteurs_compact; sinon lit ce champ dans le jsonl',
    )
    ap.add_argument(
        "--ratio-train",
        type=float,
        default=0.7,
        help="ratio transitions utilisées pour entraîner (le reste sert au test)",
    )
    ap.add_argument("--limite", type=int, default=0, help="si >0, limite nb transitions évaluées")
    args = ap.parse_args()

    racine = Path(__file__).resolve().parents[4]
    bac = None
    if args.experience:
        bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
        bac.assurer_structure()

    journal_path = Path(args.journal)
    if bac is not None and not journal_path.is_absolute():
        journal_path = bac.resoudre_chemin(journal_path)

    out_path = None
    if args.out:
        out_path = Path(args.out)
        if bac is not None and not out_path.is_absolute():
            out_path = bac.resoudre_chemin(out_path)
    elif bac is not None:
        out_path = bac.paths.diagnostics_dir / f"{Path(__file__).stem}__{journal_path.stem}.json"

    champ_latent = str(args.champ_latent)

    transitions = list(iterer_transitions(journal_path, champ_latent=champ_latent))
    n = len(transitions)
    n_train = int(max(0, min(n, round(n * float(args.ratio_train)))))
    transitions_train = transitions[:n_train]
    transitions_test = transitions[n_train:]

    # entraînement terminaison sur le split train
    from agent_service.app.modele_monde.termination_tabulaire_v1 import ModeleTerminaisonTabulaireV1
    modele_t = ModeleTerminaisonTabulaireV1()
    nb_obs = 0
    for _prev_evt, evt, z, z1, action in transitions_train:
        modele_t.apprendre(z, action, z1, bool(evt.get("termine", False)))
        nb_obs += 1

    stats = {
        "journal_path": str(journal_path),
        "nb_obs": int(nb_obs),
        "stats_modele_termination": modele_t.stats(),
        "ratio_train": float(args.ratio_train),
        "nb_transitions": int(n),
        "nb_train": int(n_train),
        "nb_test": int(len(transitions_test)),
    }

    total = 0
    inconnus = 0
    bins = Counter()
    pairs = Counter()

    for _prev_evt, evt, z, z1, action in transitions_test:
        total += 1
        pt = modele_t.predire(z, action, z1)
        if pt.support <= 0:
            inconnus += 1
            bins["None"] += 1
            continue
        p = float(pt.proba_termine)
        b = _bin_p(p)
        bins[b] += 1
        pairs[(b, int(evt.get("termine", False)))] += 1
        if args.limite and total >= int(args.limite):
            break

    rapport = {
        "journal": str(journal_path),
        "champ_latent": champ_latent,
        "nb_transitions_eval": int(total),
        "support0_ratio": float(inconnus / total) if total else 0.0,
        "bins_p_fin": dict(bins),
        "bins_(p_fin,termine)": {str(k): int(v) for k, v in pairs.items()},
        "stats_entrainement": stats,
    }
    texte = json.dumps(rapport, ensure_ascii=False, indent=2)
    print(texte)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(texte + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
