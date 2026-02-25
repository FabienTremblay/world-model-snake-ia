from __future__ import annotations

import argparse

from ui_cli.app.pipeline.pipeline_runner import executer_pipeline


def construire_parser_pipeline() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ui_cli pipeline",
        description="Orchestre un pipeline d'expérience (collecte → enrichissement → dataset → entrainement → epreuve).",
    )

    sp = ap.add_subparsers(dest="cmd", required=True)

    run = sp.add_parser("run", help="Exécuter une phase (ou toutes) du pipeline.")
    run.add_argument("--experience", required=True, help="Id d'expérience (ex: JEPA-1, JEPA-2).")
    run.add_argument(
        "--phase",
        required=True,
        choices=["collecte", "enrichissement", "dataset", "entrainement", "epreuve", "all"],
        help="Phase à exécuter.",
    )
    run.add_argument(
        "--run-tag",
        default=None,
        help="Tag optionnel du run (si absent, lu depuis experience.yml → pipeline.run_tag_collecte).",
    )
    run.add_argument(
        "--force",
        action="store_true",
        help="Si activé, écrase les artefacts stabilisés (datasets/*, agents/*, poids/*, journaux/*).",
    )
    run.add_argument(
        "--run-id",
        default=None,
        help="Optionnel: forcer un run_id (sinon auto). Utilisé surtout pour debug/replay.",
    )

    return ap


def main_pipeline(argv: list[str] | None = None) -> None:
    args = construire_parser_pipeline().parse_args(argv)
    if args.cmd == "run":
        executer_pipeline(
            experience_id=str(args.experience),
            phase=str(args.phase),
            run_tag=str(args.run_tag) if args.run_tag else None,
            force=bool(args.force),
            run_id=str(args.run_id) if args.run_id else None,
        )
        return

    raise SystemExit(f"Commande inconnue: {args.cmd}")
