"""Lecture des artefacts pour SAI-A105 (catalogue diagnostics).

Objectifs:
- CLI robuste: --run peut pointer soit vers un run, soit vers une racine de runs.
- ContexteRun contient les artefacts *chargés* (dict/list), comme attendu par les diagnostics.
- Résolution config_epreuve.json robuste (plan_pipeline.json + fallbacks).

Artefacts requis (dans epreuve/):
- journal_agent.jsonl
- registre_epistemique.json

Artefact requis (par résolution):
- config_epreuve.json (souvent référencé via plan_pipeline.json)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .types import ContexteRun


PathLike = Union[str, Path]


@dataclass(frozen=True)
class ResolutionChemins:
    run_dir: Path
    epreuve_dir: Path
    journal_agent: Path
    registre_epistemique: Path
    config_epreuve: Path
    plan_pipeline: Optional[Path] = None


def _lire_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _lire_jsonl(p: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _est_run_valide(run_dir: Path) -> bool:
    epreuve_dir = run_dir / "epreuve"
    return epreuve_dir.is_dir() and (epreuve_dir / "journal_agent.jsonl").is_file() and (epreuve_dir / "registre_epistemique.json").is_file()


def resoudre_run_dir(entree: PathLike) -> Path:
    """Résout un run_dir valide.

    - Si `entree` est un run: on renvoie `entree`.
    - Si `entree` est une racine contenant des runs: on choisit le plus récent (mtime).
    """
    p = Path(entree).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"run_dir introuvable: {p}")
    if p.is_dir() and _est_run_valide(p):
        return p

    if p.is_dir():
        candidats: List[Tuple[float, Path]] = []
        for child in p.iterdir():
            if child.is_dir() and _est_run_valide(child):
                try:
                    mtime = child.stat().st_mtime
                except OSError:
                    mtime = 0.0
                candidats.append((mtime, child))
        if candidats:
            candidats.sort(key=lambda x: x[0], reverse=True)
            return candidats[0][1]

    raise FileNotFoundError(
        "Le chemin --run ne pointe pas vers un run valide et aucun sous-dossier run valide n'a été trouvé. "
        f"Chemin fourni: {p}"
    )


def _essais_config_epreuve(run_dir: Path) -> Tuple[Optional[Path], List[str], Optional[Path]]:
    """Trouve config_epreuve.json et retourne (path, essais, plan_pipeline)."""
    essais: List[Path] = []
    plan: Optional[Path] = None

    # 1) via plan_pipeline.json (path relatif ou absolu)
    cand_plan = run_dir / "plan_pipeline.json"
    if cand_plan.is_file():
        plan = cand_plan
        try:
            plan_obj = _lire_json(cand_plan)
            path_cfg = plan_obj.get("configs", {}).get("config_epreuve", {}).get("path")
            if isinstance(path_cfg, str) and path_cfg:
                raw = Path(path_cfg)
                essais.append(raw)
                if raw.is_absolute() and raw.is_file():
                    return raw, [str(e) for e in essais], plan
                # relatif au run
                rel = (run_dir / raw).resolve()
                essais.append(rel)
                if rel.is_file():
                    return rel, [str(e) for e in essais], plan
        except Exception:
            pass

    # 2) local dans le run
    essais.append(run_dir / "epreuve" / "config_epreuve.json")
    essais.append(run_dir / "config_epreuve.json")

    # 3) heuristique: remonter vers donnees/config/experiences/<id>/epreuve/config_epreuve.json
    parts = list(run_dir.parts)
    if "artefacts" in parts and "runs" in parts:
        try:
            idx_runs = parts.index("runs")
            racine_exp = Path(*parts[: idx_runs - 1])  # retire 'artefacts'
            essais.append(racine_exp / "epreuve" / "config_epreuve.json")
        except Exception:
            pass

    for e in essais:
        if e.is_file():
            return e, [str(x) for x in essais], plan

    return None, [str(x) for x in essais], plan


def resoudre_chemins_run(run_dir: PathLike) -> ResolutionChemins:
    run_dir = resoudre_run_dir(run_dir)
    epreuve_dir = run_dir / "epreuve"

    journal_agent = epreuve_dir / "journal_agent.jsonl"
    registre = epreuve_dir / "registre_epistemique.json"

    if not journal_agent.is_file():
        raise FileNotFoundError(f"journal_agent.jsonl introuvable: {journal_agent}")
    if not registre.is_file():
        raise FileNotFoundError(f"registre_epistemique.json introuvable: {registre}")

    cfg, essais, plan = _essais_config_epreuve(run_dir)
    if cfg is None:
        msg = "config_epreuve.json introuvable. Chemins essayés:\n" + "\n".join(f"- {e}" for e in essais)
        raise FileNotFoundError(msg)

    return ResolutionChemins(
        run_dir=run_dir,
        epreuve_dir=epreuve_dir,
        journal_agent=journal_agent,
        registre_epistemique=registre,
        config_epreuve=cfg,
        plan_pipeline=plan,
    )


def _deduire_experience_id(run_dir: Path) -> Optional[str]:
    parts = list(run_dir.parts)
    try:
        i = parts.index("experiences")
        if i + 1 < len(parts):
            return parts[i + 1]
    except ValueError:
        pass
    return None


def charger_contexte_run(run_dir: PathLike) -> ContexteRun:
    chemins = resoudre_chemins_run(run_dir)

    experience_id: Optional[str] = None
    run_id: Optional[str] = None
    if chemins.plan_pipeline and chemins.plan_pipeline.is_file():
        try:
            plan_obj = _lire_json(chemins.plan_pipeline)
            experience_id = plan_obj.get("experience_id") or plan_obj.get("experience")
            run_id = plan_obj.get("run_id") or plan_obj.get("run")
        except Exception:
            pass

    # Fallbacks
    if experience_id is None:
        experience_id = _deduire_experience_id(chemins.run_dir)
    if run_id is None:
        run_id = chemins.run_dir.name

    ctx = ContexteRun(
        run_dir=chemins.run_dir,
        epreuve_dir=chemins.epreuve_dir,
        experience_id=experience_id,
        run_id=run_id,
        config_epreuve=_lire_json(chemins.config_epreuve),
        registre_epistemique=_lire_json(chemins.registre_epistemique),
        journal_agent=_lire_jsonl(chemins.journal_agent),
        chemins={
            "journal_agent": str(chemins.journal_agent),
            "registre_epistemique": str(chemins.registre_epistemique),
            "config_epreuve": str(chemins.config_epreuve),
            "plan_pipeline": str(chemins.plan_pipeline) if chemins.plan_pipeline else "",
            "run_dir": str(chemins.run_dir),
            "epreuve_dir": str(chemins.epreuve_dir),
        },
    )
    return ctx
