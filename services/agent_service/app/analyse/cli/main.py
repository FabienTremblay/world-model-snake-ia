"""CLI — SAI-A105 diagnostics (v3.6)

Correctifs:
1) JSON sérialisation robuste (Path -> str, set/tuple -> list, autres -> str fallback)
2) Préservation des sorties précédentes: si le fichier de sortie existe, on le renomme en .bak_<UTC> avant d'écrire.

Usage:
  PYTHONPATH=services python -m agent_service.app.analyse.cli.main --run <path_run|runs_root> --set jepa5_v1
"""

from __future__ import annotations

import argparse
import inspect
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from agent_service.app.analyse.catalogue.catalogue import (
    get_diagnostic,
    get_set,
    liste_diagnostics,
    liste_sets,
)
from agent_service.app.analyse.noyau.lecture_artefacts import charger_contexte_run, resoudre_run_dir

import agent_service.app.analyse.noyau.gabarits_rapport as gr


def _trouver_fonction_rendu():
    noms = ("rendre_rapport_diagnostics", "rendre_rapport", "generer_rapport_diagnostics", "rendre_rapport_md")
    for nom in noms:
        if hasattr(gr, nom):
            return getattr(gr, nom), nom
    raise ImportError(
        "Impossible de trouver une fonction de rendu dans noyau/gabarits_rapport.py. "
        "Attendu un des noms: " + ", ".join(noms)
    )


_RENDRE, _RENDRE_NOM = _trouver_fonction_rendu()


def _rendre_rapport(ctx, resultats) -> str:
    sig = inspect.signature(_RENDRE)
    params = sig.parameters

    if len(params) == 2:
        return _RENDRE(ctx, resultats)

    if "sections_extra" in params:
        return _RENDRE(ctx, resultats, sections_extra=[])

    kwargs = {}
    if "contexte" in params:
        kwargs["contexte"] = ctx
    if "ctx" in params:
        kwargs["ctx"] = ctx
    if "resultats" in params:
        kwargs["resultats"] = resultats
    if "diagnostics" in params:
        kwargs["diagnostics"] = resultats
    if "sections_extra" in params:
        kwargs["sections_extra"] = []

    try:
        return _RENDRE(**kwargs)
    except TypeError as e:
        raise TypeError(
            f"Signature de rendu non supportée pour {_RENDRE_NOM}: {sig}. "
            "Attendu (ctx, resultats) ou (ctx, resultats, sections_extra)."
        ) from e


def _json_default(o: Any):
    # Pathlib
    if isinstance(o, Path):
        return str(o)
    # Sets / tuples
    if isinstance(o, (set, tuple)):
        return list(o)
    # Datetime
    if hasattr(o, "isoformat"):
        try:
            return o.isoformat()
        except Exception:
            pass
    # Fallback: string representation
    return str(o)


def _backup_if_exists(path: Path) -> None:
    if path.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bak = path.with_name(path.name + f".bak_{ts}")
        path.rename(bak)


SCHEMA_VERSION = "sai-a105.diagnostics.v1"


def executer(
    run_dir: str,
    diagnostics: Optional[List[str]],
    out_md: str,
    out_json: str,
    set_nom: Optional[str] = None,
) -> dict:
    run_path = Path(run_dir)
    run_path_resolu = resoudre_run_dir(run_path)

    ctx = charger_contexte_run(str(run_path_resolu))

    if set_nom:
        diag_ids = get_set(set_nom)
    else:
        diag_ids = diagnostics or liste_diagnostics()

    resultats = []
    for diag_id in diag_ids:
        diag = get_diagnostic(diag_id)
        res = diag.executer(ctx)
        resultats.append(res)

    sortie_dir = Path(getattr(ctx, "epreuve_dir", None) or str(run_path_resolu))
    sortie_dir.mkdir(parents=True, exist_ok=True)

    # Rapport MD
    rapport_md_path = sortie_dir / out_md
    _backup_if_exists(rapport_md_path)
    rapport_md = _rendre_rapport(ctx, resultats)
    rapport_md_path.write_text(rapport_md, encoding="utf-8")

    # JSON
    sortie_json_path = sortie_dir / out_json
    _backup_if_exists(sortie_json_path)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "experience_id": getattr(ctx, "experience_id", None),
        "run_id": getattr(ctx, "run_id", None),
        "run_dir": str(run_path_resolu),
        "run_dir_entree": str(run_path),
        "run_dir_resolu": str(run_path_resolu),
        "epreuve_dir": getattr(ctx, "epreuve_dir", None),
        "date_utc": getattr(ctx, "date_utc", None),
        "diagnostics": [asdict(r) for r in resultats],
        "renderer": _RENDRE_NOM,
        "renderer_signature": str(inspect.signature(_RENDRE)),
    }
    sortie_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")

    return {
        "sortie_dir": str(sortie_dir),
        "rapport_md": str(rapport_md_path),
        "sortie_json": str(sortie_json_path),
        "diagnostics": diag_ids,
        "set": set_nom,
        "run_dir_entree": str(run_path),
        "run_dir_resolu": str(run_path_resolu),
        "renderer": _RENDRE_NOM,
        "renderer_signature": str(inspect.signature(_RENDRE)),
    }


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Exécute des diagnostics SAI-A105 sur un run.")
    p.add_argument("--run", required=True, help="Chemin vers un run (ou une racine contenant plusieurs runs).")
    p.add_argument("--diagnostics", nargs="*", default=None, help="Liste d'IDs diagnostics à exécuter (sinon: tous).")
    p.add_argument("--set", default=None, help="Nom d'un set de diagnostics (ex: jepa5_v1).")
    p.add_argument("--out-md", default="rapport_diagnostics.md", help="Nom du fichier rapport Markdown.")
    p.add_argument("--out-json", default="diagnostics.json", help="Nom du fichier JSON machine.")
    p.add_argument("--list", action="store_true", help="Liste les diagnostics disponibles et quitte.")
    p.add_argument("--list-sets", action="store_true", help="Liste les sets disponibles et quitte.")
    return p


def main() -> None:
    p = _build_parser()
    args = p.parse_args()

    if args.list:
        for d in liste_diagnostics():
            print(d)
        return

    if args.list_sets:
        for s in liste_sets():
            print(s)
        return

    if args.set and args.diagnostics:
        raise SystemExit("Erreur: utiliser soit --set, soit --diagnostics, pas les deux.")

    res = executer(args.run, args.diagnostics, args.out_md, args.out_json, set_nom=args.set)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
