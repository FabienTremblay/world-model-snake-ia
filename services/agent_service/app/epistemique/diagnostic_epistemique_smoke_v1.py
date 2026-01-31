# services/agent_service/app/epistemique/diagnostic_epistemique_smoke_v1.py
"""Diagnostic minimal (smoke) de la couche épistémique.

But pédagogique:
- construire 2-3 hypothèses candidates à partir d'un journal de ticks;
- les évaluer grossièrement (support/confirmations/contradictions);
- montrer que la sémantique (les noms) est produite par l'APK.

Usage:
  PYTHONPATH=services python -m agent_service.app.epistemique.diagnostic_epistemique_smoke_v1 \
    --journal artefacts/episodes.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .contrats import EvaluationHypotheseV1, HypotheseEpistemiqueV1
from .registre_epistemique_v1 import RegistreEpistemiqueV1


def _lire_journal_ticks(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _evaluer_hypothese_ratio(
    *,
    id_hypothese: str,
    support: int,
    confirmations: int,
    contradictions: int,
    note: str | None = None,
) -> EvaluationHypotheseV1:
    # confiance = confirmations / support, conservatrice si contradictions existent
    if support <= 0:
        confiance = 0.0
    else:
        confiance = confirmations / float(support)
        if contradictions > 0:
            confiance *= 1.0 / (1.0 + contradictions)
    return EvaluationHypotheseV1(
        id_hypothese=id_hypothese,
        support=int(support),
        confirmations=int(confirmations),
        contradictions=int(contradictions),
        confiance=float(confiance),
        note=note,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--journal", required=True, type=Path)
    args = p.parse_args()

    journal = args.journal

    # registre + hypothèses "nommées" dans la langue de l'APK
    reg = RegistreEpistemiqueV1()

    # H1: collision_mur -> fin_irreversible
    h1 = HypotheseEpistemiqueV1(
        id_hypothese="H1",
        etiquette="collision_mur -> fin_irreversible",
        antecedents=["collision_mur"],
        consequences=["fin_irreversible"],
        metadonnees={"langue": "fr"},
    )
    reg.ajouter_hypothese(h1)

    # H2: croissance (delta_longueur>0) -> nourriture_consomme
    h2 = HypotheseEpistemiqueV1(
        id_hypothese="H2",
        etiquette="croissance -> nourriture_consomme",
        antecedents=["croissance"],
        consequences=["nourriture_consomme"],
        metadonnees={"langue": "fr"},
    )
    reg.ajouter_hypothese(h2)

    # Statistiques de base depuis le journal
    prev = {}
    support_h1 = conf_h1 = cont_h1 = 0
    support_h2 = conf_h2 = cont_h2 = 0

    compte_raisons_fin = Counter()
    nb_ticks = 0

    for e in _lire_journal_ticks(journal):
        nb_ticks += 1
        key = (e.get("run_id"), e.get("episode_id"))
        tick = int(e.get("tick", 0))
        termine = bool(e.get("termine", False))
        raison_fin = e.get("raison_fin")

        if termine and raison_fin:
            compte_raisons_fin[str(raison_fin)] += 1

        # H1: on "confirme" quand la fin est collision_mur
        if termine:
            support_h1 += 1
            if raison_fin == "collision_mur":
                conf_h1 += 1
            else:
                # contradiction: l'épisode se termine autrement
                cont_h1 += 1

        # H2: on observe les deltas de longueur
        if tick == 0:
            prev[key] = e
            continue
        if key not in prev:
            prev[key] = e
            continue

        e0 = prev[key]
        prev[key] = e

        l0 = int(e0.get("longueur", 0))
        l1 = int(e.get("longueur", 0))
        if l1 != l0:
            support_h2 += 1
            if l1 > l0:
                conf_h2 += 1
            else:
                # décroissance (si jamais) contredit notre lecture naïve
                cont_h2 += 1

    reg.enregistrer_evaluation(
        _evaluer_hypothese_ratio(
            id_hypothese="H1",
            support=support_h1,
            confirmations=conf_h1,
            contradictions=cont_h1,
            note="support=nb_episodes_termines (proxy)",
        )
    )
    reg.enregistrer_evaluation(
        _evaluer_hypothese_ratio(
            id_hypothese="H2",
            support=support_h2,
            confirmations=conf_h2,
            contradictions=cont_h2,
            note="support=nb_ticks_avec_delta_longueur (proxy)",
        )
    )

    out = {
        "journal": str(journal),
        "nb_lignes": nb_ticks,
        "raisons_fin": dict(compte_raisons_fin),
        "registre": reg.resumer(),
        "evaluations": {
            hid: {
                "support": ev.support,
                "confirmations": ev.confirmations,
                "contradictions": ev.contradictions,
                "confiance": ev.confiance,
                "note": ev.note,
            }
            for hid, ev in reg.evaluations.items()
        },
        "note": "smoke v1: hypothèses naïves, destinées à évoluer",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
