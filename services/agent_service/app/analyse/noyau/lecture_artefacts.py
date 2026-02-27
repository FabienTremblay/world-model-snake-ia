"""Lecture des artefacts pour SAI-A105.

On vise un CLI robuste aux runs "copiés" ou "in situ".

Artefacts requis :
- journal_agent.jsonl
- registre_epistemique.json
- config_epreuve.json (souvent référencé via plan_pipeline.json)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .types import ContexteRun


@dataclass(frozen=True)
class ResolutionChemins:
    run_dir: Path
    epreuve_dir: Path
    journal_agent: Path
    registre_epistemique: Path
    config_epreuve: Path


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


def _essais_config_epreuve(run_dir: Path) -> Tuple[Optional[Path], List[str]]:
    essais: List[Path] = []

    # 1) via plan_pipeline.json
    plan = run_dir / "plan_pipeline.json"
    if plan.exists():
        try:
            plan_obj = _lire_json(plan)
            path_cfg = (
                plan_obj.get("configs", {})
                .get("config_epreuve", {})
                .get("path")
            )
            if isinstance(path_cfg, str) and path_cfg:
                p = Path(path_cfg)
                essais.append(p)
                if p.exists():
                    return p, [str(e) for e in essais]
        except Exception:
            # si plan corrompu, on continue les essais
            pass

    # 2) local dans le run
    essais.append(run_dir / "epreuve" / "config_epreuve.json")
    essais.append(run_dir / "config_epreuve.json")

    # 3) heuristique: remonter vers donnees/config/experiences/<id>/epreuve/config_epreuve.json
    # Ex: .../donnees/config/experiences/JEPA-5/artefacts/runs/<run_id>
    parts = list(run_dir.parts)
    if "artefacts" in parts and "runs" in parts:
        try:
            idx_runs = parts.index("runs")
            # .../<experience>/artefacts/runs/<run_id>
            # => .../<experience>/epreuve/config_epreuve.json
            racine_exp = Path(*parts[: idx_runs - 1])  # retire 'artefacts'
            essais.append(racine_exp / "epreuve" / "config_epreuve.json")
        except Exception:
            pass

    for e in essais:
        if e.exists():
            return e, [str(x) for x in essais]

    return None, [str(x) for x in essais]


def resoudre_chemins_run(run_dir: Path) -> ResolutionChemins:
    run_dir = run_dir.expanduser().resolve()
    # epreuve_dir = run_dir/epreuve si existe sinon run_dir
    epreuve_dir = (run_dir / "epreuve") if (run_dir / "epreuve").exists() else run_dir

    journal_agent = epreuve_dir / "journal_agent.jsonl"
    registre = epreuve_dir / "registre_epistemique.json"

    if not journal_agent.exists():
        raise FileNotFoundError(f"journal_agent.jsonl introuvable: {journal_agent}")
    if not registre.exists():
        raise FileNotFoundError(f"registre_epistemique.json introuvable: {registre}")

    cfg, essais = _essais_config_epreuve(run_dir)
    if cfg is None:
        msg = "config_epreuve.json introuvable. Chemins essayés:\n" + "\n".join(f"- {e}" for e in essais)
        raise FileNotFoundError(msg)

    return ResolutionChemins(
        run_dir=run_dir,
        epreuve_dir=epreuve_dir,
        journal_agent=journal_agent,
        registre_epistemique=registre,
        config_epreuve=cfg,
    )


def charger_contexte_run(run_dir: Path) -> ContexteRun:
    chemins = resoudre_chemins_run(run_dir)

    plan = chemins.run_dir / "plan_pipeline.json"
    experience_id: Optional[str] = None
    run_id: Optional[str] = None
    if plan.exists():
        try:
            plan_obj = _lire_json(plan)
            experience_id = plan_obj.get("experience_id")
            run_id = plan_obj.get("run_id")
        except Exception:
            pass

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
            "run_dir": str(chemins.run_dir),
            "epreuve_dir": str(chemins.epreuve_dir),
        },
    )
    return ctx
