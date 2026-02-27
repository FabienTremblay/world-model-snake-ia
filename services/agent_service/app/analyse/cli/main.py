"""Point d'entrée CLI pour SAI-A105 (analyse diagnostics).

Usage:
  PYTHONPATH=services python -m agent_service.app.analyse.cli.main --run <path_run>

Le CLI:
- charge les artefacts
- exécute une liste de diagnostics (par défaut: set_minimum_v1)
- écrit un rapport Markdown et un JSON machine dans le dossier du run
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ..noyau.lecture_artefacts import charger_contexte_run
from ..noyau.gabarits_rapport import rendre_rapport_md
from ..noyau.types import ResultatDiagnostic, SectionRapport
from ..catalogue.catalogue import get_diagnostic, liste_diagnostics, set_minimum_v1


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="agent_service.analyse", description="SAI-A105 — analyser résultats (diagnostics)")
    p.add_argument("--run", required=True, help="Chemin vers un run (dossier).")
    p.add_argument(
        "--diagnostics",
        nargs="*",
        default=None,
        help="Liste d'ids diagnostics. Par défaut: set_minimum_v1.",
    )
    p.add_argument("--out-md", default="rapport_diagnostics.md", help="Nom du rapport Markdown.")
    p.add_argument("--out-json", default="diagnostics.json", help="Nom du fichier JSON de sortie.")
    return p.parse_args()


def _choisir_dir_sortie(run_dir: Path) -> Path:
    # si sous-dossier epreuve existe, on écrit là
    epreuve = run_dir / "epreuve"
    return epreuve if epreuve.exists() else run_dir


def executer(run_path: str, diagnostics: List[str] | None = None, out_md: str = "rapport_diagnostics.md", out_json: str = "diagnostics.json") -> Dict[str, Any]:
    run_dir = Path(run_path).expanduser().resolve()
    ctx = charger_contexte_run(run_dir)

    diag_ids = diagnostics if diagnostics is not None and len(diagnostics) > 0 else set_minimum_v1()

    resultats: List[ResultatDiagnostic] = []
    sections_extra: List[SectionRapport] = []

    for did in diag_ids:
        diag = get_diagnostic(did)
        res = diag.executer(ctx)
        resultats.append(res)
        try:
            sections_extra.extend(diag.sections_rapport(res, ctx))
        except Exception:
            # sections optionnelles: on ne fait pas tomber l'ensemble
            pass

    sortie_dir = _choisir_dir_sortie(ctx.run_dir)

    md = rendre_rapport_md(ctx, resultats, sections_extra)
    (sortie_dir / out_md).write_text(md, encoding="utf-8")

    payload = {
        "experience_id": ctx.experience_id,
        "run_id": ctx.run_id or ctx.run_dir.name,
        "run_dir": str(ctx.run_dir),
        "epreuve_dir": str(ctx.epreuve_dir),
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "diagnostics": [r.vers_json() for r in resultats],
    }

    (sortie_dir / out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "sortie_dir": str(sortie_dir),
        "rapport_md": str(sortie_dir / out_md),
        "sortie_json": str(sortie_dir / out_json),
        "diagnostics": diag_ids,
    }


def main() -> None:
    args = _parse_args()
    if args.diagnostics:
        inconnus = [d for d in args.diagnostics if d not in liste_diagnostics()]
        if inconnus:
            raise SystemExit(f"Diagnostics inconnus: {inconnus}. Disponibles: {liste_diagnostics()}")

    res = executer(args.run, args.diagnostics, args.out_md, args.out_json)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
