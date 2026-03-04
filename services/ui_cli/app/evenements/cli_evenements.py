from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional

import yaml

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1
from world_sim.app.arenes_yaml import charger_arene_v0
from world_sim.app.monde_snake import ConfigMonde, MondeSnake
from world_sim.app.monde_snake_evenementiel import MondeSnakeEvenementiel

from runner_service.app.runner_evenements_v2 import ConfigRunnerEvenementsV2, RunnerEvenementsV2

from agent_service.app.individu.charger_individu_v1 import (
    appliquer_evolution_post_run,
    calculer_hash_individu,
    charger_individu_v1,
)
from agent_service.app.individu.individu_objet_du_monde_v2 import IndividuAgentAreneV1ObjetDuMonde
from agent_service.app.individu_objet_du_monde_v1 import AgentIndividuStubV1


def _racine_projet() -> Path:
    # services/ui_cli/app/evenements/cli_evenements.py -> racine projet
    return Path(__file__).resolve().parents[4]


def _resoudre_path_arene(racine_projet: Path, arene: str) -> Path:
    """Résout un id d'arène ou un chemin vers un fichier .yml.

    Convention repo (prioritaire):
      - donnees/config/arenes/<id>.yml
    Fallback historique:
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

    # Retourner le chemin "canonique" pour aider le message d'erreur
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
        "--individu",
        default=None,
        help="Id d'individu (catalogue) sous donnees/catalogues/individus/<id>/. "
        "Override experience.yml: evenements.individu_id.",
    )
    ap.add_argument(
        "--promouvoir",
        action="store_true",
        help="En mode entrainement, promeut individu_sortie.yml vers le catalogue individus/<id>/individu.yml et archive historique.",
    )
    # Fallback stub (utile pour smoke)
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

    Règle: uniquement si l'utilisateur n'a pas surchargé via CLI.
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

    # individu_id (default CLI = None)
    individu_id = ev.get("individu_id")
    if isinstance(individu_id, str) and individu_id.strip() and args.individu is None:
        args.individu = individu_id.strip()

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

    # --- Individu (catalogue) ou stub
    individu_entree_cfg: dict | None = None
    individu_entree_hash: str | None = None
    individu_sortie_hash: str | None = None
    famille_id: str | None = None

    if args.individu:
        individu_entree_cfg = charger_individu_v1(
            racine_projet=racine,
            individu_id=str(args.individu),
            valider_schema=True,
        )
        individu_entree_hash = calculer_hash_individu(individu_entree_cfg)
        famille_id = str(individu_entree_cfg.get("famille_id") or "")

        (run_dir / "individu_entree.yml").write_text(
            yaml.safe_dump(individu_entree_cfg, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        individu_obj = IndividuAgentAreneV1ObjetDuMonde(individu_cfg=individu_entree_cfg)
        objets = [individu_obj]
    else:
        direction = None if args.inaction or args.direction == "none" else str(args.direction)
        objets = [AgentIndividuStubV1(direction=direction)]

    cfg_runner = ConfigRunnerEvenementsV2(
        mode=str(args.mode),
        ticks=int(args.ticks),
        publier_ticks=bool(args.publier_ticks),
    )
    runner = RunnerEvenementsV2(monde=monde_evt, objets=objets, config=cfg_runner)
    journal = runner.run()

    evenements_path.write_text(
        "".join(json.dumps(getattr(e, "__dict__", e), ensure_ascii=False) + "\n" for e in journal),
        encoding="utf-8",
    )

    # --- Traçabilité individu (runs)
    if args.individu and individu_entree_cfg is not None and individu_entree_hash is not None:
        if str(args.mode) == "entrainement":
            individu_sortie_cfg = appliquer_evolution_post_run(
                individu_entree_cfg,
                run_id=run_id,
                run_dir=str(run_dir),
                ticks=int(args.ticks),
            )
            individu_sortie_hash = calculer_hash_individu(individu_sortie_cfg)

            (run_dir / "individu_sortie.yml").write_text(
                yaml.safe_dump(individu_sortie_cfg, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            (run_dir / "lineage.json").write_text(
                json.dumps(
                    {
                        "schema": "individu_agent_arene_v1",
                        "individu_id": str(args.individu),
                        "famille_id": famille_id,
                        "parent": {"hash": individu_entree_hash, "run_id": None},
                        "enfant": {"hash": individu_sortie_hash, "run_id": run_id},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            # --- Promotion contrôlée vers catalogue
            promotion_effectuee = False

            if args.promouvoir:
                cat_dir = racine / "donnees" / "catalogues" / "individus" / str(args.individu)
                cat_dir.mkdir(parents=True, exist_ok=True)

                hist_dir = cat_dir / "historique"
                hist_dir.mkdir(parents=True, exist_ok=True)

                # archive immuable
                (hist_dir / f"{individu_sortie_hash}.yml").write_text(
                    yaml.safe_dump(individu_sortie_cfg, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )

                # état courant
                (cat_dir / "individu.yml").write_text(
                    yaml.safe_dump(individu_sortie_cfg, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )

                promotion_effectuee = True
        else:
            if args.promouvoir:
                raise SystemExit("promotion interdite en mode=epreuve")
            (run_dir / "lineage.json").write_text(
                json.dumps(
                    {
                        "schema": "individu_agent_arene_v1",
                        "individu_id": str(args.individu),
                        "famille_id": famille_id,
                        "parent": {"hash": individu_entree_hash, "run_id": None},
                        "enfant": None,
                        "note": "mode=epreuve: pas d'evolution/promotion",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
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
            "individu_id": str(args.individu) if args.individu else None,
            "famille_id": famille_id,
            "individu_entree_hash": individu_entree_hash,
            "individu_sortie_hash": individu_sortie_hash,
            "promotion_effectuee": locals().get("promotion_effectuee", False),
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {"event": "run_termine", "run_dir": str(run_dir), "evenements": str(evenements_path)},
            ensure_ascii=False,
        )
    )
