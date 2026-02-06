from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

from agent_service.app.preparation_agent.contrats import (
    CatalogueDeTetes,
    SpecTete,
    RefTronc,
    PlanPreparationAgent,
)
from agent_service.app.preparation_agent.pipeline import preparer_agent_personne
from agent_service.app.preparation_agent.assembleur import assembler_agent_personne
from agent_service.app.preparation_agent.stockage import (
    sauvegarder_agent_personne,
    sauvegarder_catalogue,
    sauvegarder_plan,
    sauvegarder_rapport,
)


def _racine_projet() -> Path:
    # services/ui_cli/app/preparation_agent/cli_preparer_agent.py -> parents[4] = racine
    return Path(__file__).resolve().parents[4]


def _assurer_dirs_preparation(bas: BacASableV1) -> dict[str, Path]:
    """répertoires canoniques ajoutés pour sai-a107."""
    base = bas.paths.artefacts_dir
    d = {
        "catalogues": (base / "catalogues").resolve(),
        "agent_personne": (base / "agent_personne").resolve(),
        "runs_preparation": (base / "runs_preparation").resolve(),
        "rapports_preparation": (base / "rapports_preparation").resolve(),
        "plans_preparation": (base / "plans_preparation").resolve(),
    }
    for p in d.values():
        p.mkdir(parents=True, exist_ok=True)
    return d


def _chemins_defaut(bas: BacASableV1, dirs: dict[str, Path], agent_personne_id: str) -> dict[str, str]:
    """résout les chemins d'artefacts par défaut."""
    return {
        "catalogue_tetes": str((dirs["catalogues"] / "catalogue_tetes.json").resolve()),
        "plan_preparation": str((dirs["plans_preparation"] / f"{agent_personne_id}.plan.json").resolve()),
        "agent_personne_dir": str((dirs["agent_personne"] / agent_personne_id).resolve()),
        "agent_personne_assemble": str((dirs["agent_personne"] / agent_personne_id / "agent_personne_assemble.json").resolve()),
        "agent_personne_final": str((dirs["agent_personne"] / agent_personne_id / "agent_personne.json").resolve()),
        "rapport_entrainement": str((dirs["rapports_preparation"] / f"{agent_personne_id}.rapport.json").resolve()),
        "runs_preparation_dir": str((dirs["runs_preparation"] / agent_personne_id).resolve()),
    }


def _lire_catalogue_si_existe(path: str) -> CatalogueDeTetes | None:
    p = Path(path)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    # reconstruction minimale
    tetes = [SpecTete(**t) for t in (d.get("tetes") or [])]
    return CatalogueDeTetes(
        version=str(d.get("version") or "v1"),
        genere_ts_ns=int(d.get("genere_ts_ns") or 0),
        run_id=str(d.get("run_id") or ""),
        arene_id=d.get("arene_id"),
        sources=dict(d.get("sources") or {}),
        tetes=tetes,
    )


# ---------------------------------------------------------------------
# sous-commandes

def cmd_editer_tete(args: argparse.Namespace) -> None:
    racine = _racine_projet()
    bas = BacASableV1.charger_depuis_id(racine, args.experience)
    bas.assurer_structure()
    dirs = _assurer_dirs_preparation(bas)
    chemins = _chemins_defaut(bas, dirs, agent_personne_id="__tmp__")

    fp_catalogue = args.catalogue or chemins["catalogue_tetes"]

    catalogue = _lire_catalogue_si_existe(fp_catalogue)
    if catalogue is None:
        catalogue = CatalogueDeTetes(
            version="v1",
            genere_ts_ns=time.time_ns(),
            run_id="",
            arene_id=None,
            sources={},
            tetes=[],
        )

    classes = []
    if args.classes:
        classes = [c.strip() for c in args.classes.split(",") if c.strip()]

    tete = SpecTete(
        id=args.tete_id,
        nom=args.nom,
        type_sortie=args.type,
        role=args.role,
        classes=classes,
        supervision={},
        influence={},
        meta={},
    )

    # upsert
    tetes = [t for t in catalogue.tetes if t.id != tete.id] + [tete]
    catalogue2 = CatalogueDeTetes(
        version=catalogue.version,
        genere_ts_ns=time.time_ns(),
        run_id=str(time.time_ns()),
        arene_id=catalogue.arene_id,
        sources=catalogue.sources,
        tetes=sorted(tetes, key=lambda t: t.id),
    )

    sauvegarder_catalogue(fp_catalogue, catalogue2)

    print(json.dumps(
        {
            "event": "catalogue_tetes_ecrit",
            "experience": args.experience,
            "catalogue": fp_catalogue,
            "nb_tetes": len(catalogue2.tetes),
        },
        ensure_ascii=False,
    ))


def cmd_assembler(args: argparse.Namespace) -> None:
    racine = _racine_projet()
    bas = BacASableV1.charger_depuis_id(racine, args.experience)
    bas.assurer_structure()
    dirs = _assurer_dirs_preparation(bas)

    chemins = _chemins_defaut(bas, dirs, agent_personne_id=args.agent_personne_id)
    Path(chemins["agent_personne_dir"]).mkdir(parents=True, exist_ok=True)

    fp_catalogue = args.catalogue or chemins["catalogue_tetes"]
    catalogue = _lire_catalogue_si_existe(fp_catalogue)
    if catalogue is None:
        raise SystemExit(
            f"catalogue introuvable: {fp_catalogue}. "
            "crée-le d'abord avec: preparer-agent editer-tete ..."
        )

    tronc = RefTronc(
        id=args.tronc_id,
        type_tronc=args.type_tronc,
        chemin_poids=args.tronc_poids,
        meta={},
    )

    plan = PlanPreparationAgent(
        experience=args.experience,
        arene_id=args.arene_id,
        agent_personne_id=args.agent_personne_id,
        tronc=tronc,
        tetes_selectionnees=[t.strip() for t in (args.tetes or "").split(",") if t.strip()],
        intentions={},
        entrainement={},
        chemins={
            "runs_preparation_dir": chemins["runs_preparation_dir"],
        },
    )

    agent_assemble = assembler_agent_personne(plan=plan, catalogue=catalogue)

    sauvegarder_plan(chemins["plan_preparation"], plan)
    sauvegarder_agent_personne(chemins["agent_personne_assemble"], agent_assemble)

    print(json.dumps(
        {
            "event": "agent_personne_assemble",
            "experience": args.experience,
            "agent_personne_id": args.agent_personne_id,
            "plan": chemins["plan_preparation"],
            "agent_personne_assemble": chemins["agent_personne_assemble"],
            "catalogue": fp_catalogue,
        },
        ensure_ascii=False,
    ))


def cmd_entrainer(args: argparse.Namespace) -> None:
    racine = _racine_projet()
    bas = BacASableV1.charger_depuis_id(racine, args.experience)
    bas.assurer_structure()
    dirs = _assurer_dirs_preparation(bas)

    chemins = _chemins_defaut(bas, dirs, agent_personne_id=args.agent_personne_id)
    Path(chemins["agent_personne_dir"]).mkdir(parents=True, exist_ok=True)
    Path(chemins["runs_preparation_dir"]).mkdir(parents=True, exist_ok=True)

    # charge plan
    fp_plan = args.plan or chemins["plan_preparation"]
    if not Path(fp_plan).exists():
        raise SystemExit(
            f"plan introuvable: {fp_plan}. "
            "crée-le d'abord avec: preparer-agent assembler ..."
        )
    dplan = json.loads(Path(fp_plan).read_text(encoding="utf-8"))

    # reconstruction minimale
    tronc = RefTronc(**dplan["tronc"])
    plan = PlanPreparationAgent(
        experience=dplan["experience"],
        arene_id=dplan["arene_id"],
        agent_personne_id=dplan["agent_personne_id"],
        tronc=tronc,
        tetes_selectionnees=list(dplan.get("tetes_selectionnees") or []),
        intentions=dict(dplan.get("intentions") or {}),
        entrainement=dict(dplan.get("entrainement") or {}),
        chemins=dict(dplan.get("chemins") or {}),
    )

    # charge catalogue
    fp_catalogue = args.catalogue or chemins["catalogue_tetes"]
    catalogue = _lire_catalogue_si_existe(fp_catalogue)
    if catalogue is None:
        raise SystemExit(f"catalogue introuvable: {fp_catalogue}")

    # exécute pipeline (prototype)
    agent_personne, rapport = preparer_agent_personne(plan=plan, catalogue=catalogue)

    sauvegarder_agent_personne(chemins["agent_personne_final"], agent_personne)
    sauvegarder_rapport(chemins["rapport_entrainement"], rapport)

    # log minimal dans runs_preparation (utile pour traçabilité)
    fp_logs = Path(chemins["runs_preparation_dir"]) / "logs.json"
    fp_logs.write_text(
        json.dumps(
            {
                "event": "preparation_agent_terminee",
                "ts_ns": time.time_ns(),
                "experience": args.experience,
                "agent_personne_id": args.agent_personne_id,
                "plan": fp_plan,
                "catalogue": fp_catalogue,
                "agent_personne": chemins["agent_personne_final"],
                "rapport": chemins["rapport_entrainement"],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(
        {
            "event": "agent_personne_entraine",
            "experience": args.experience,
            "agent_personne_id": args.agent_personne_id,
            "agent_personne": chemins["agent_personne_final"],
            "rapport": chemins["rapport_entrainement"],
            "plan": fp_plan,
            "catalogue": fp_catalogue,
        },
        ensure_ascii=False,
    ))


# ---------------------------------------------------------------------
# parsing / main

def construire_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ui_cli preparer-agent",
        description="pipeline sai-a107 : catalogue -> assembler -> entrainer",
    )
    sp = ap.add_subparsers(dest="cmd", required=True)

    # editer-tete
    p = sp.add_parser("editer-tete", help="crée / met à jour une tête dans le catalogue")
    p.add_argument("--experience", required=True)
    p.add_argument("--catalogue", default=None, help="chemin catalogue (sinon défaut dans artefacts/catalogues)")
    p.add_argument("--tete-id", required=True)
    p.add_argument("--nom", required=True)
    p.add_argument(
        "--type",
        required=True,
        choices=[
            "classification_binaire",
            "classification_multiclasse",
            "multi_label",
            "score",
            "regression",
            "policy_actions",
            "gate",
        ],
    )
    p.add_argument(
        "--role",
        required=True,
        choices=[
            "categorie_contenu",
            "categorie_controle",
            "policy",
            "gouvernance",
            "journalisation",
        ],
    )
    p.add_argument("--classes", default="", help="liste csv (si multiclasse/multi-label)")
    p.set_defaults(func=cmd_editer_tete)

    # assembler
    p = sp.add_parser("assembler", help="assemble un agent-personne à partir d'un tronc + têtes")
    p.add_argument("--experience", required=True)
    p.add_argument("--catalogue", default=None)
    p.add_argument("--arene-id", required=True)
    p.add_argument("--agent-personne-id", required=True)
    p.add_argument("--tronc-id", required=True)
    p.add_argument("--type-tronc", required=True)
    p.add_argument("--tronc-poids", default=None)
    p.add_argument("--tetes", default="", help="ids csv des têtes à instancier (ex: a,b,c)")
    p.set_defaults(func=cmd_assembler)

    # entrainer
    p = sp.add_parser("entrainer", help="entraîne (prototype) un agent-personne à partir du plan + catalogue")
    p.add_argument("--experience", required=True)
    p.add_argument("--agent-personne-id", required=True)
    p.add_argument("--plan", default=None, help="chemin du plan (sinon défaut dans artefacts/plans_preparation)")
    p.add_argument("--catalogue", default=None, help="chemin catalogue (sinon défaut)")
    p.set_defaults(func=cmd_entrainer)

    return ap


def main_preparer_agent(argv: list[str] | None = None) -> None:
    ap = construire_parser()
    args = ap.parse_args(argv)
    args.func(args)
