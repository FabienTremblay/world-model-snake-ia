from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import executer_pipeline_epistemique_v2
from .resolution_bac import resoudre_run_epistemique


def construire_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Épistémique v2 (cours 5) — estrade (bac-à-sable)")
    ap.add_argument("--experience", type=str, required=True, help="ID d'expérience (donnees/config/experiences/<id>)")
    ap.add_argument("--run-id", type=str, default="", help="Nom du répertoire de run (sinon: dernier run)")
    ap.add_argument("--latent", type=str, default="", help="Surcharge ponctuelle du mode latent (sinon: experience.yml)")
    return ap


def main() -> None:
    ap = construire_parser()
    args = ap.parse_args()

    res = resoudre_run_epistemique(
        experience_id=str(args.experience),
        run_id=(args.run_id.strip() or None),
        latent_cli=(args.latent.strip() or None),
        depuis=Path(__file__),
    )

    sources = {
        "experience": str((res.bac.experience_dir / "experience.yml").resolve()),
        "run": res.run_nom,
        "journal": str(res.journal_path.resolve()),
        "meta": str(res.meta_path.resolve()),
    }
    if res.metrics_path is not None:
        sources["metrics"] = str(res.metrics_path.resolve())

    executer_pipeline_epistemique_v2(
        path_journal=res.journal_path,
        path_sortie_registre=res.registre_path,
        sources=sources,
        mode_latent=res.mode_latent,
    )

    print(f"[epistemique_v2] expérience={res.bac.experience_id} run={res.run_nom}")
    print(f"[epistemique_v2] registre écrit: {res.registre_path}")


if __name__ == "__main__":
    main()
