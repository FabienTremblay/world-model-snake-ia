# services/agent_service/app/epistemique/agent_producteur_connaissances_v1.py
"""Agent producteur de connaissances (apk) — v1.

But (Cours 4) :
- partir d’un journal de ticks (offline) ;
- produire une terminologie (noms) + quelques artefacts (hypothèses, règles) ;
- évaluer grossièrement ces hypothèses (support/confirmations/contradictions).

Important :
- le monde n’impose aucune sémantique ;
- les “noms” ci-dessous sont ceux de l’apk (révisables).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Optional, Tuple
 
from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

from agent_service.app.signaux.signaux_monde_v1 import extraire_signaux_monde_v1

from .contrats import EvaluationHypotheseV1, HypotheseEpistemiqueV1, RegleInferenceV1
from .registre_epistemique_v1 import RegistreEpistemiqueV1


def _evaluer_hypothese_ratio(
    id_hypothese: str,
    support: int,
    confirmations: int,
    contradictions: int,
    note: str | None = None,
) -> EvaluationHypotheseV1:
    """Confiance naïve = confirmations / support (si support>0)."""
    conf = (confirmations / support) if support > 0 else 0.0
    return EvaluationHypotheseV1(
        id_hypothese=id_hypothese,
        support=int(support),
        confirmations=int(confirmations),
        contradictions=int(contradictions),
        confiance=float(conf),
        note=note,
    )


def produire_registre_depuis_journal_v1(journal: Path) -> Tuple[RegistreEpistemiqueV1, Dict]:
    """Construit un registre épistémique minimal à partir d’un journal.

    v1 (volontairement simple) :
    - Hypothèse H1 : collision_mur -> fin_irreversible
    - Hypothèse H2 : croissance + delta_score_pos -> nourriture_consomme
    - Règle R1 : delta_longueur_pos -> croissance
    - Règle R2 : delta_score_pos -> gain_score

    Évaluation :
    - H1 support = nb transitions où collision_mur est vrai
      confirmation = collision_mur implique termine (devrait être vrai)
    - H2 support = nb transitions où delta_longueur > 0 (croissance)
      confirmation = delta_score > 0 (proxy “nourriture”)
      contradiction = delta_score <= 0
    """

    reg = RegistreEpistemiqueV1()
def produire_registre_depuis_journal_v1(
    journal: Path,
    registre_initial: Optional[RegistreEpistemiqueV1] = None,
) -> Tuple[RegistreEpistemiqueV1, Dict]:
    """Construit/actualise un registre épistémique minimal à partir d’un journal."""

    reg = registre_initial or RegistreEpistemiqueV1()

    # --- terminologie (langue de l’apk) ---
    # (On garde ça explicite : ce sont des noms, pas des vérités du monde.)
    concepts = {
        "collision_mur",
        "fin_irreversible",
        "delta_longueur_pos",
        "croissance",
        "delta_score_pos",
        "gain_score",
        "nourriture_consomme",
    }

    # --- hypothèses candidates ---
    # On (ré)injecte les artefacts de base si absents (APK v1 = “seed” de terminologie)
    if "H1" not in reg.hypotheses:
        reg.ajouter_hypothese(
        HypotheseEpistemiqueV1(
            id_hypothese="H1",
            etiquette="collision_mur -> fin_irreversible",
            antecedents=["collision_mur"],
            consequences=["fin_irreversible"],
            metadonnees={"version": "v1", "type": "danger"},
        )
        )
    if "H2" not in reg.hypotheses:
        reg.ajouter_hypothese(
        HypotheseEpistemiqueV1(
            id_hypothese="H2",
            etiquette="croissance + delta_score_pos -> nourriture_consomme",
            antecedents=["croissance", "delta_score_pos"],
            consequences=["nourriture_consomme"],
            metadonnees={"version": "v1", "type": "benefice"},
        )
        )

    # --- règles d’inférence (transformations info -> info) ---
    if "R1" not in reg.regles:
        reg.ajouter_regle(
        RegleInferenceV1(
            id_regle="R1",
            etiquette="delta_longueur_pos => croissance",
            premisses=["delta_longueur_pos"],
            conclusion="croissance",
            metadonnees={"version": "v1"},
        )
        )
    if "R2" not in reg.regles:
        reg.ajouter_regle(
        RegleInferenceV1(
            id_regle="R2",
            etiquette="delta_score_pos => gain_score",
            premisses=["delta_score_pos"],
            conclusion="gain_score",
            metadonnees={"version": "v1"},
        )
        )

    # --- extraction + stats ---
    nb_lignes = 0
    nb_transitions = 0
    compte_raisons_fin = Counter()

    support_h1 = conf_h1 = cont_h1 = 0
    support_h2 = conf_h2 = cont_h2 = 0

    prev_par_episode = {}

    with open(journal, "r", encoding="utf-8") as f:
        for line in f:
            nb_lignes += 1
            e = json.loads(line)

            key = (e.get("run_id"), e.get("episode_id"))
            tick = int(e.get("tick", 0))

            # tick 0: initialisation
            if tick == 0:
                prev_par_episode[key] = e
                continue

            if key not in prev_par_episode:
                prev_par_episode[key] = e
                continue

            e0 = prev_par_episode[key]
            prev_par_episode[key] = e
            nb_transitions += 1

            signaux = extraire_signaux_monde_v1(e0, e)

            # raisons fin (au tick terminal)
            if signaux.get("termine"):
                compte_raisons_fin[str(signaux.get("raison_fin"))] += 1

            # H1 : collision_mur -> fin_irreversible
            if bool(signaux.get("collision_mur")):
                support_h1 += 1
                if bool(signaux.get("termine")):
                    conf_h1 += 1
                else:
                    cont_h1 += 1

            # H2 : croissance + delta_score_pos -> nourriture_consomme
            dl = int(signaux.get("delta_longueur", 0))
            ds = int(signaux.get("delta_score", 0))

            if dl > 0:
                support_h2 += 1
                if ds > 0:
                    conf_h2 += 1
                else:
                    cont_h2 += 1

    ev_h1 = _evaluer_hypothese_ratio(
            id_hypothese="H1",
            support=support_h1,
            confirmations=conf_h1,
            contradictions=cont_h1,
            note="support=nb transitions collision_mur ; confirmation=termine==True",
    )
    ev_h2 = _evaluer_hypothese_ratio(
            id_hypothese="H2",
            support=support_h2,
            confirmations=conf_h2,
            contradictions=cont_h2,
            note="support=nb transitions delta_longueur>0 ; confirmation=delta_score>0 (proxy nourriture)",
    )

    # Mise à jour incrémentale : on additionne support/confirm/contrad puis on recalcule confiance.
    old1 = reg.evaluation("H1")
    if old1 is not None:
        ev_h1 = _evaluer_hypothese_ratio(
            id_hypothese="H1",
            support=old1.support + ev_h1.support,
            confirmations=old1.confirmations + ev_h1.confirmations,
            contradictions=old1.contradictions + ev_h1.contradictions,
            note=ev_h1.note,
        )
    old2 = reg.evaluation("H2")
    if old2 is not None:
        ev_h2 = _evaluer_hypothese_ratio(
            id_hypothese="H2",
            support=old2.support + ev_h2.support,
            confirmations=old2.confirmations + ev_h2.confirmations,
            contradictions=old2.contradictions + ev_h2.contradictions,
            note=ev_h2.note,
        )

    reg.enregistrer_evaluation(ev_h1)
    reg.enregistrer_evaluation(ev_h2)

    out = {
        "journal": str(journal),
        "nb_lignes": nb_lignes,
        "nb_transitions": nb_transitions,
        "raisons_fin": dict(compte_raisons_fin),
        "terminologie_apk": sorted(concepts),
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
        "note": "apk v1: hypothèses/règles minimales, destinées à être révisées",
    }
    return reg, out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True, help="Chemin vers un journal .jsonl (ticks)")
    ap.add_argument("--in-registre", default=None, help="Chemin vers un registre JSON existant (optionnel)")
    ap.add_argument("--out-registre", default=None, help="Chemin où sauvegarder le registre JSON (optionnel)")
    ap.add_argument("--experience", required=False, help="Id d'expérience (pour résoudre chemins + défauts de sortie)")
    args = ap.parse_args()

    racine = Path(__file__).resolve().parents[4]
    bac = None
    if args.experience:
        bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
        bac.assurer_structure()

    journal_path = Path(args.journal)
    if bac is not None and not journal_path.is_absolute():
        journal_path = bac.resoudre_chemin(journal_path)

    in_registre_path = None
    if args.in_registre:
        in_registre_path = Path(args.in_registre)
        if bac is not None and not in_registre_path.is_absolute():
            in_registre_path = bac.resoudre_chemin(in_registre_path)

    out_registre_path = None
    if args.out_registre:
        out_registre_path = Path(args.out_registre)
        if bac is not None and not out_registre_path.is_absolute():
            out_registre_path = bac.resoudre_chemin(out_registre_path)
    elif bac is not None:
        out_registre_path = bac.paths.registres_dir / f"{Path(__file__).stem}__{journal_path.stem}.json"

    registre_initial = None
    if in_registre_path:
        registre_initial = RegistreEpistemiqueV1.charger_json(in_registre_path)
    reg, out = produire_registre_depuis_journal_v1(
        journal_path,
        registre_initial=registre_initial,
    )

    if out_registre_path:
        out_registre_path.parent.mkdir(parents=True, exist_ok=True)
        reg.sauvegarder_json(out_registre_path)
        out["registre_out"] = str(out_registre_path)
        out["registre_out_resume"] = reg.resumer()

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

