from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1


def trouver_racine_projet(depuis: Path) -> Path:
    """Remonte l'arborescence jusqu'à trouver (services/ + donnees/)."""
    p = depuis.resolve()
    for parent in [p] + list(p.parents):
        if (parent / "services").exists() and (parent / "donnees").exists():
            return parent
    # fallback: 5 niveaux au-dessus (compatible structure repo)
    return p.parents[5]


@dataclass(frozen=True)
class ResolutionRunEpistemique:
    racine_projet: Path
    bac: BacASableV1
    run_nom: str
    run_dir: Path
    journal_path: Path
    meta_path: Path
    metrics_path: Path | None
    registre_path: Path
    mode_latent: str | None


def _lire_latent_depuis_experience(cfg: dict[str, Any]) -> str | None:
    # Priorités YAML (sans surcharger le CLI) :
    # - latent (top-level)
    # - modele_monde.latent_cli (si présent)
    latent = cfg.get("latent")
    if isinstance(latent, str) and latent.strip():
        return latent.strip()

    mm = cfg.get("modele_monde")
    if isinstance(mm, dict):
        latent_cli = mm.get("latent_cli")
        if isinstance(latent_cli, str) and latent_cli.strip():
            return latent_cli.strip()

    return None


def resoudre_run_epistemique(
    *,
    experience_id: str,
    run_id: str | None,
    latent_cli: str | None,
    depuis: Path,
) -> ResolutionRunEpistemique:
    racine = trouver_racine_projet(depuis)
    bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=experience_id)
    bac.assurer_structure()

    run_dir, journal_path, stdout_path, meta_path = bac.resoudre_run_existant(run_id=run_id)
    # metrics (optionnel)
    metrics_path = run_dir / "metrics.jsonl"
    if not metrics_path.exists():
        metrics_path = None

    # mode latent (CLI > YAML)
    mode_latent = latent_cli.strip() if isinstance(latent_cli, str) and latent_cli.strip() else _lire_latent_depuis_experience(bac.cfg)

    registre_path = run_dir / "registre_epistemique_v2.json"

    return ResolutionRunEpistemique(
        racine_projet=racine,
        bac=bac,
        run_nom=run_dir.name,
        run_dir=run_dir,
        journal_path=journal_path,
        meta_path=meta_path,
        metrics_path=metrics_path,
        registre_path=registre_path,
        mode_latent=mode_latent,
    )
