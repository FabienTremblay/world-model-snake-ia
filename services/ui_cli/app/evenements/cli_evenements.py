from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

from world_sim.app.arenes_yaml import charger_arene_v0
from world_sim.app.monde_snake import ConfigMonde, MondeSnake

from services.world_sim.app.monde_snake_evenementiel import MondeSnakeEvenementiel
from services.runner_service.app.runner_evenements_v2 import RunnerEvenementsV2, ConfigRunnerEvenementsV2
from services.agent_service.app.individu_objet_du_monde_v1 import AgentIndividuStubV1


def _racine_projet() -> Path:
    # services/ui_cli/app/evenements/cli_evenements.py -> parents[4] = racine projet
    return Path(__file__).resolve().parents[4]


def _resoudre_path_arene(racine_projet: Path, arene: str) -> Path:
    """Résout un id d'arène ou un chemin vers un fichier .yml.

    Convention repo (prioritaire) :
      - donnees/config/arenes/<id>.yml
    Fallback historique :
      - donnees/arenes/<id>.yml
    """
    p = Path(arene)

    # Chemin explicite
    if p.suffix == ".yml" and p.exists():
        return p

    # Id d'arène
    candidats = [
        racine_projet / "donnees" / "config" / "arenes" / f"{arene}.yml",
        racine_projet / "donnees" / "arenes" / f"{arene}.yml",
    ]
    for c in candidats:
        if c.exists():
            return c

    # On retourne le chemin "canonique" pour un message d'erreur utile
    return candidats[0]


def construire_parser_evenements() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ui_cli evenements",
        description="Exécute un run via RunnerEvenementsV2 (E/F) et journalise evenements.jsonl.",
    )
    ap.add_argument(
        "--experience",
        required=True,
        help="Id de l'expérience (bac à sable) sous donnees/config/experiences/<id>/",
    )
    ap.add_argument("--run-tag", help="Tag libre pour nommer le run (optionnel).")
    ap.add_argument(
        "--mode",
        default="entrainement",
        choices=["entrainement", "epreuve"],
        help="Mode: entrainement (E/pull) ou epreuve (F/push).",
    )
    ap.add_argument("--ticks", type=int, default=200, help="Nombre de ticks.")
    ap.add_argument(
        "--publier-ticks",
        action="store_true",
        help="Publie tick_annonce/tick_survenu dans le flux d'événements.",
    )
    ap.add_argument(
        "--arene",
        default="demo_v0",
        help="Chemin vers une arène .yml, ou id d'arène (ex: demo_v0).",
    )
    ap.add_argument("--seed", type=int, default=None, help="Seed monde (override).")

    ap.add_argument(
        "--direction",
        default="avant",
        choices=["avant", "gauche", "droite", "arriere"],
        help="Direction du stub d'individu. Use --direction none pour inaction.",
    )
    ap.add_argument(
        "--inaction",
        action="store_true",
        help="Force l'inaction (aucun événement action_motrice). Override --direction.",
    )
    return ap


def _appliquer_defaults_evenements(args: argparse.Namespace, cfg: dict) -> None:
    """Applique les defaults de experience.yml pour la sous-commande `evenements`.

    Règle : uniquement si l'utilisateur n'a pas surchargé via CLI.
    """
    if not isinstance(cfg, dict):
        return
    ev = cfg.get("evenements")
    if not isinstance(ev, dict):
        return

    # mode (default CLI = entrainement)
    mode = ev.get("mode")
    if isinstance(mode, str) and mode.strip() and args.mode == "entrainement":
        args.mode = mode.strip()

    # ticks (default CLI = 200)
    ticks = ev.get("ticks")
    if ticks is not None and args.ticks == 200:
        try:
            args.ticks = int(ticks)
        except Exception:
            pass

    # publier_ticks (default CLI = False)
    publier = ev.get("publier_ticks")
    if isinstance(publier, bool) and publier and args.publier_ticks is False:
        args.publier_ticks = True

    # arene (default CLI = demo_v0)
    arene = ev.get("arene")
    if isinstance(arene, str) and arene.strip() and args.arene == "demo_v0":
        args.arene = arene.strip()

    # seed (default CLI = None)
    seed = ev.get("seed")
    if seed is not None and args.seed is None:
        try:
            args.seed = int(seed)
        except Exception:
            pass

    # run_tag (default CLI = None)
    run_tag = ev.get("run_tag")
    if isinstance(run_tag, str) and run_tag.strip() and args.run_tag is None:
        args.run_tag = run_tag.strip()

    # stub (direction/inaction)
    stub = ev.get("stub")
    if isinstance(stub, dict):
        direction = stub.get("direction")
        if isinstance(direction, str) and direction.strip():
            if args.direction == "avant" and not args.inaction:
                args.direction = direction.strip()
        inaction = stub.get("inaction")
        if isinstance(inaction, bool) and inaction:
            args.inaction = True


def main_evenements(argv: Optional[list[str]] = None) -> None:
    args = construire_parser_evenements().parse_args(argv)

    racine = _racine_projet()
    run_id = str(time.time_ns())

    bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
    _appliquer_defaults_evenements(args, getattr(bac, "cfg", {}))

    rapport = bac.assurer_structure()
    if rapport.get("creations"):
        print(
            json.dumps(
                {"event": "bac_a_sable_cree", "experience": str(args.experience), "creations": rapport["creations"]},
                ensure_ascii=False,
            )
        )

    run_dir, _journal_path, _stdout_path, meta_path = bac.preparer_run(
        run_tag=str(args.run_tag) if args.run_tag else None,
        run_id=run_id,
    )

    evenements_path = run_dir / "evenements.jsonl"

    # --- Monde snake (via arène)
    path_arene = _resoudre_path_arene(racine, str(args.arene))
    ar = charger_arene_v0(path_arene)

    base_seed = int(args.seed) if args.seed is not None else int(ar.seed)
    cfg_base = ConfigMonde(
        largeur=ar.largeur,
        hauteur=ar.hauteur,
        seed=base_seed,
        nb_nourriture=ar.nb_nourriture,
        niveau_bruit=int(ar.niveau_bruit_defaut),
        arene_id=ar.id,
        epsilon_par_pas=ar.epsilon_par_pas,
        bonus_fin=ar.bonus_fin,
        porte_position=ar.porte_position,
        porte_ouverte_initiale=(ar.porte_etat_initial == "ouverte"),
        regle_ouverture_porte=ar.regle_ouverture,
        palette=ar.palette,
    )

    monde_reel = MondeSnake(cfg_base)
    monde_evt = MondeSnakeEvenementiel(monde_reel)

    # --- Objet individu stub
    direction = None if args.inaction or args.direction == "none" else str(args.direction)
    individu = AgentIndividuStubV1(direction=direction)

    cfg_runner = ConfigRunnerEvenementsV2(
        mode=str(args.mode),
        ticks=int(args.ticks),
        publier_ticks=bool(args.publier_ticks),
    )
    runner = RunnerEvenementsV2(monde=monde_evt, objets=[individu], config=cfg_runner)
    journal = runner.run()

    evenements_path.write_text(
        "".join(json.dumps(e.__dict__, ensure_ascii=False) + "\n" for e in journal),
        encoding="utf-8",
    )

    if meta_path is not None:
        meta = {
            "run_id": run_id,
            "experience": str(args.experience),
            "run_tag": args.run_tag,
            "runner": "evenements_v2",
            "mode": str(args.mode),
            "ticks": int(args.ticks),
            "publier_ticks": bool(args.publier_ticks),
            "arene": str(args.arene),
            "arene_path": str(path_arene),
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {"event": "run_termine", "run_dir": str(run_dir), "evenements": str(evenements_path)},
            ensure_ascii=False,
        )
    )
