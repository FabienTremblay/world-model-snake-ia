# services/agent_service/app/modele_monde/evaluer_tabulaire_v1.py
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from agent_service.app.modele_monde.tabulaire_v1 import ModeleMondeTabulaireV1
from agent_service.app.modele_monde.entrainement_depuis_journal import iterer_transitions


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


def _evaluer_sur_transitions(
    modele: ModeleMondeTabulaireV1,
    transitions: List[Transition],
    apprendre: bool,
    out_jsonl: Optional[Path],
) -> dict:
    total = 0
    couverts = 0
    corrects_couverts = 0

    confs: List[float] = []
    ents: List[float] = []
    supports: List[int] = []

    par_action: Dict[str, Dict[str, int]] = {}

    f = None
    if out_jsonl is not None:
        out_jsonl.parent.mkdir(parents=True, exist_ok=True)
        f = open(out_jsonl, "w", encoding="utf-8")

    try:
        for _prev_evt, evt, chk_prev, chk, action in transitions:
            total += 1
            pred = modele.predire(chk_prev, action)
            had = pred.support > 0

            ok: Optional[int]
            if had:
                couverts += 1
                ok = 1 if pred.etat_suivant == chk else 0
                corrects_couverts += ok
                confs.append(pred.confiance)
                ents.append(pred.entropie)
                supports.append(pred.support)
            else:
                ok = None

            d = par_action.setdefault(action, {"total": 0, "couverts": 0, "corrects": 0})
            d["total"] += 1
            if had:
                d["couverts"] += 1
                d["corrects"] += int(ok)

            if f is not None:
                ligne = {
                    "run_id": str(evt.get("run_id")),
                    "episode_id": int(evt.get("episode_id")),
                    "tick": int(evt.get("tick")),
                    "action": action,
                    "checksum_t": int(chk_prev),
                    "checksum_t1": int(chk),
                    "pred_checksum_t1": pred.etat_suivant,
                    "support": int(pred.support),
                    "confiance": float(pred.confiance),
                    "entropie": float(pred.entropie),
                    "ok": ok,
                }
                f.write(json.dumps(ligne, ensure_ascii=False) + "\n")

            if apprendre:
                modele.apprendre_transition(chk_prev, action, chk)
    finally:
        if f is not None:
            f.flush()
            f.close()

    exact_cond = (corrects_couverts / couverts) if couverts else 0.0
    couverture = (couverts / total) if total else 0.0

    par_action_calc = {}
    for a, d in sorted(par_action.items()):
        cov = (d["couverts"] / d["total"]) if d["total"] else 0.0
        acc = (d["corrects"] / d["couverts"]) if d["couverts"] else 0.0
        par_action_calc[a] = {
            "total": d["total"],
            "couverture": float(cov),
            "exactitude_cond": float(acc),
        }

    return {
        "total_transitions": int(total),
        "couverture": float(couverture),
        "exactitude_conditionnelle": float(exact_cond),
        "confiance": _resume(confs),
        "entropie": _resume(ents),
        "support": _resume([float(s) for s in supports]),
        "par_action": par_action_calc,
    }


def evaluer_en_ligne(journal_path: Path, out_jsonl: Optional[Path] = None) -> dict:
    """Évaluation online: prédire puis apprendre au fil du journal."""
    modele = ModeleMondeTabulaireV1()
    transitions = list(iterer_transitions(journal_path))
    bloc = _evaluer_sur_transitions(modele, transitions, apprendre=True, out_jsonl=out_jsonl)

    return {
        "mode": "online",
        "journal_path": str(journal_path),
        "modele_stats_fin": modele.stats(),
        **bloc,
        "out_jsonl": str(out_jsonl) if out_jsonl is not None else None,
    }


def evaluer_split_train_test(
    journal_path: Path,
    ratio_train: float = 0.7,
    apprendre_pendant_test: bool = False,
    out_jsonl: Optional[Path] = None,
) -> dict:
    """Évaluation train/test sur un seul journal.

    - on apprend sur les premières transitions (ratio_train)
    - on évalue sur le reste
    Par défaut, on n'apprend PAS pendant le test (mesure de généralisation).
    """
    transitions = list(iterer_transitions(journal_path))
    n = len(transitions)
    n_train = int(max(0, min(n, round(n * ratio_train))))

    modele = ModeleMondeTabulaireV1()
    # apprentissage
    for _prev_evt, _evt, chk_prev, chk, action in transitions[:n_train]:
        modele.apprendre_transition(chk_prev, action, chk)

    bloc_test = _evaluer_sur_transitions(
        modele,
        transitions[n_train:],
        apprendre=apprendre_pendant_test,
        out_jsonl=out_jsonl,
    )

    return {
        "mode": "split",
        "journal_path": str(journal_path),
        "ratio_train": float(ratio_train),
        "nb_train": int(n_train),
        "nb_test": int(n - n_train),
        "apprendre_pendant_test": bool(apprendre_pendant_test),
        "modele_stats_apres_train": modele.stats(),
        **bloc_test,
        "out_jsonl": str(out_jsonl) if out_jsonl is not None else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", type=str, default="artefacts/episodes.jsonl")
    ap.add_argument("--mode", choices=["online", "split"], default="split")
    ap.add_argument("--ratio-train", type=float, default=0.7)
    ap.add_argument("--apprendre-pendant-test", action="store_true")
    ap.add_argument("--out", type=str, default="artefacts/modele_monde_eval_tabulaire_v1.jsonl")
    ap.add_argument("--sans-out", action="store_true", help="ne pas écrire de jsonl de détails")
    args = ap.parse_args()

    journal_path = Path(args.journal)
    out = None if args.sans_out else Path(args.out)

    if args.mode == "online":
        rapport = evaluer_en_ligne(journal_path, out_jsonl=out)
    else:
        rapport = evaluer_split_train_test(
            journal_path,
            ratio_train=args.ratio_train,
            apprendre_pendant_test=args.apprendre_pendant_test,
            out_jsonl=out,
        )

    print(json.dumps(rapport, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
