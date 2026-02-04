# services/agent_service/app/epistemique/apk_regles_dangers_v1.py
"""APK minimal: dériver et enregistrer des règles de danger à partir d'un journal.

Objectif cours 4:
- Produire des artefacts épistémiques lisibles (hypothèses + règles + évaluations)
  à partir de régularités empiriques simples:
    (mur devant) & (action vers mur) -> termine
    (corps devant) & (action vers corps) -> termine (collision_soi)

Ce script:
- lit un journal episodes.jsonl
- calcule support/confirmations/contradictions pour chaque règle
- écrit/merge dans un registre épistémique JSON (RegistreEpistemiqueV1)

Convention du journal: action appliquée est e1.action pour la transition e0->e1.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

from runner.app.replay import decoder_capteurs_b64

from agent_service.app.modele_monde.latent_v1 import extraire_signaux_percus_voisinage_v1
from agent_service.app.epistemique.contrats import EvaluationHypotheseV1, HypotheseEpistemiqueV1, RegleInferenceV1
from agent_service.app.epistemique.registre_epistemique_v1 import RegistreEpistemiqueV1


ACTIONS = {"haut", "bas", "gauche", "droite"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--journal", required=True, help="Path vers episodes.jsonl")
    p.add_argument("--out-registre", required=False, help="Path vers registre JSON (créé/merge) (optionnel si --experience)")
    p.add_argument("--experience", required=False, help="Id d'expérience (pour résoudre chemins + défauts de sortie)")
    p.add_argument("--etiquette", default="dangers_v1", help="Etiquette pour les artefacts")
    p.add_argument("--motif-mur", type=int, default=3, help="Motif interprété comme mur (défaut 3)")
    p.add_argument("--motif-corps", type=int, default=1, help="Motif interprété comme corps (défaut 1)")
    p.add_argument("--raison-collision-soi", default="collision_soi", help="raison_fin attendue pour collision corps")
    p.add_argument("--limite", type=int, default=None, help="Limiter le nombre d'événements")
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


def _charger_episodes(path: Path, limite: int | None) -> tuple[int, dict[int, list[dict]]]:
    episodes: dict[int, list[dict]] = defaultdict(list)
    nb_evt = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            evt = json.loads(line)
            episodes[int(evt["episode_id"])].append(evt)
            nb_evt += 1
            if limite is not None and nb_evt >= int(limite):
                break
    return nb_evt, episodes


def _evaluer_regle(episodes: dict[int, list[dict]], motif_cible: int, raison_fin_attendue: str | None = None) -> dict:
    support = 0
    confirmations = 0
    contradictions = 0
    confirmations_raison = 0

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

            motif_dir = _motif_dans_direction(extras, action)
            if motif_dir != int(motif_cible):
                continue

            support += 1
            termine_next = bool(e1.get("termine", False))
            if termine_next:
                confirmations += 1
                if raison_fin_attendue is not None and str(e1.get("raison_fin") or "") == raison_fin_attendue:
                    confirmations_raison += 1
            else:
                contradictions += 1

    confiance = float(confirmations) / float(support) if support else 0.0
    return {
        "support": support,
        "confirmations": confirmations,
        "contradictions": contradictions,
        "confiance": confiance,
        "confirmations_raison": confirmations_raison,
    }


def main() -> int:
    args = _parser().parse_args()
    racine = Path(__file__).resolve().parents[4]
    bac = None
    if args.experience:
        bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
        bac.assurer_structure()

    journal = Path(args.journal)
    if bac is not None and not journal.is_absolute():
        journal = bac.resoudre_chemin(journal)

    if args.out_registre:
        out_registre = Path(args.out_registre)
        if bac is not None and not out_registre.is_absolute():
            out_registre = bac.resoudre_chemin(out_registre)
    else:
        if bac is None:
            raise SystemExit("Il faut fournir --out-registre, ou bien fournir --experience pour calculer une sortie par défaut.")
        out_registre = bac.paths.registres_dir / f"{Path(__file__).stem}__{journal.stem}.json"

    etiquette = str(args.etiquette)

    nb_evt, episodes = _charger_episodes(journal, args.limite)

    mur = _evaluer_regle(episodes, motif_cible=int(args.motif_mur), raison_fin_attendue="collision_mur")
    corps = _evaluer_regle(
        episodes, motif_cible=int(args.motif_corps), raison_fin_attendue=str(args.raison_collision_soi)
    )

    # Charger/Créer registre
    if out_registre.exists():
        reg = RegistreEpistemiqueV1.charger_json(out_registre)
    else:
        reg = RegistreEpistemiqueV1()

    # Hypothèses
    h_mur_id = "h.danger_mur_v1"
    h_corps_id = "h.danger_corps_v1"

    reg.ajouter_hypothese(
        HypotheseEpistemiqueV1(
            id_hypothese=h_mur_id,
            etiquette=etiquette,
            antecedents=["mur_devant", "action_vers_mur"],
            consequences=["termine"],
            metadonnees={"motif_mur": str(args.motif_mur), "journal": str(journal), "nb_evenements": str(nb_evt)},
        )
    )
    reg.ajouter_hypothese(
        HypotheseEpistemiqueV1(
            id_hypothese=h_corps_id,
            etiquette=etiquette,
            antecedents=["corps_devant", "action_vers_corps"],
            consequences=["termine"],
            metadonnees={
                "motif_corps": str(args.motif_corps),
                "raison_collision_soi": str(args.raison_collision_soi),
                "journal": str(journal),
                "nb_evenements": str(nb_evt),
            },
        )
    )

    # Règles (inférence)
    reg.ajouter_regle(
        RegleInferenceV1(
            id_regle="r.eviter_mur_v1",
            etiquette=etiquette,
            premisses=["mur_devant", "action_vers_mur"],
            conclusion="action_interdite",
            metadonnees={"note": "dérivée empiriquement (cours 4)"},
        )
    )
    reg.ajouter_regle(
        RegleInferenceV1(
            id_regle="r.eviter_corps_v1",
            etiquette=etiquette,
            premisses=["corps_devant", "action_vers_corps"],
            conclusion="action_interdite",
            metadonnees={"note": "dérivée empiriquement (cours 4)"},
        )
    )

    # Évaluations
    reg.enregistrer_evaluation(
        EvaluationHypotheseV1(
            id_hypothese=h_mur_id,
            support=int(mur["support"]),
            confirmations=int(mur["confirmations"]),
            contradictions=int(mur["contradictions"]),
            confiance=float(mur["confiance"]),
            note="confirmations_raison=%d" % int(mur["confirmations_raison"]),
        )
    )
    reg.enregistrer_evaluation(
        EvaluationHypotheseV1(
            id_hypothese=h_corps_id,
            support=int(corps["support"]),
            confirmations=int(corps["confirmations"]),
            contradictions=int(corps["contradictions"]),
            confiance=float(corps["confiance"]),
            note="confirmations_raison=%d" % int(corps["confirmations_raison"]),
        )
    )

    reg.sauvegarder_json(out_registre)

    out = {
        "journal": str(journal),
        "out_registre": str(out_registre),
        "etiquette": etiquette,
        "mur": mur,
        "corps": corps,
        "resume_registre": reg.resumer(),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
