# services/agent_service/app/modele_monde/diagnostic_utilite_v1.py
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import List, Tuple
from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

from agent_service.app.modele_monde.entrainement_depuis_journal import iterer_transitions
from agent_service.app.modele_monde.recompense_tabulaire_v1 import ModeleRecompenseTabulaireV1
from agent_service.app.modele_monde.termination_tabulaire_v1 import ModeleTerminaisonTabulaireV1


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
    ap = argparse.ArgumentParser(description="Diagnostic des modèles tabulaires de récompense et terminaison (cours 4).")
    ap.add_argument("--journal", type=str, default="artefacts/episodes_latent_appris.jsonl")
    ap.add_argument("--champ-latent", type=str, default="latent_id")
    ap.add_argument("--experience", required=False, help="Id d'expérience (pour résoudre les chemins + sortie défaut)")
    ap.add_argument("--out", required=False, help="Fichier JSON de sortie (optionnel; défaut: artefacts/diagnostics)")
    ap.add_argument("--ratio-train", type=float, default=0.7)
    ap.add_argument("--limite-test", type=int, default=0)
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

    transitions: List[Transition] = list(iterer_transitions(journal_path, champ_latent=args.champ_latent))
    n = len(transitions)
    n_train = int(max(0, min(n, round(n * float(args.ratio_train)))))
    transitions_train = transitions[:n_train]
    transitions_test = transitions[n_train:]
    if args.limite_test and args.limite_test > 0:
        transitions_test = transitions_test[: int(args.limite_test)]

    modele_r = ModeleRecompenseTabulaireV1()
    modele_t = ModeleTerminaisonTabulaireV1()

    for prev_evt, evt, z, z1, action in transitions_train:
        try:
            delta_score = int(evt.get("score", 0)) - int(prev_evt.get("score", 0))
            termine = bool(evt.get("termine", False))
        except Exception:
            continue
        modele_r.apprendre(z, action, z1, delta_score)
        modele_t.apprendre(z, action, z1, termine)

    total = 0
    couverts_r = 0
    couverts_t = 0

    mae_esperance: List[float] = []
    brier_term: List[float] = []
    proba_term: List[float] = []

    nb_gain = 0
    nb_termine = 0

    for prev_evt, evt, z, z1, action in transitions_test:
        total += 1
        delta_score = int(evt.get("score", 0)) - int(prev_evt.get("score", 0))
        termine = bool(evt.get("termine", False))
        if delta_score != 0:
            nb_gain += 1
        if termine:
            nb_termine += 1

        pr = modele_r.predire(z, action, z1)
        if pr.support > 0:
            couverts_r += 1
            mae_esperance.append(abs(float(delta_score) - float(pr.esperance)))

        pt = modele_t.predire(z, action, z1)
        if pt.support > 0:
            couverts_t += 1
            p = float(pt.proba_termine)
            proba_term.append(p)
            y = 1.0 if termine else 0.0
            brier_term.append((p - y) ** 2)

    rapport = {
        "journal_path": str(journal_path),
        "champ_latent": str(args.champ_latent),
        "ratio_train": float(args.ratio_train),
        "nb_transitions": int(n),
        "nb_train": int(n_train),
        "nb_test": int(len(transitions_test)),
        "limite_test": int(args.limite_test),
        "couverture_recompense_test": (couverts_r / total) if total else 0.0,
        "couverture_termination_test": (couverts_t / total) if total else 0.0,
        "gain_reel_ratio_test": (nb_gain / total) if total else 0.0,
        "termine_reel_ratio_test": (nb_termine / total) if total else 0.0,
        "mae_esperance_delta_score": _resume(mae_esperance),
        "brier_termination": _resume(brier_term),
        "proba_termine_pred": _resume(proba_term),
        "stats_modele_recompense": modele_r.stats(),
        "stats_modele_termination": modele_t.stats(),
        "note": (
            "MAE espérance: abs(delta_score - E[delta_score|z,a,z1]). "
            "Brier: (p_termine - y)^2 (plus petit = mieux)."
        ),
    }
    texte = json.dumps(rapport, ensure_ascii=False, indent=2)
    print(texte)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(texte + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

