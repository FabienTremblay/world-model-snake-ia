from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1


def racine_projet() -> Path:
    # services/ui_tui/app/catalogues.py -> parents[3] = racine projet
    return Path(__file__).resolve().parents[3]


def lister_arenes_ids(racine: Optional[Path] = None) -> list[str]:
    r = racine or racine_projet()
    d = r / "donnees" / "config" / "arenes"
    if not d.exists():
        return []
    return sorted([p.stem for p in d.glob("*.yml")])


def lister_experiences_ids(racine: Optional[Path] = None) -> list[str]:
    r = racine or racine_projet()
    d = r / "donnees" / "config" / "experiences"
    if not d.exists():
        return []
    ids: list[str] = []
    for p in d.iterdir():
        if p.is_dir() and not p.name.startswith("_"):
            # présence de experience.yml = heuristique simple
            if (p / "experience.yml").exists():
                ids.append(p.name)
            else:
                ids.append(p.name)
    return sorted(ids)


def _yaml_top_level_get(path: Path, cle: str) -> Optional[str]:
    """Extraction minimaliste (top-level 'cle: valeur').
    On évite de dépendre d'un parseur YAML ici.
    """
    if not path.exists():
        return None
    pat = re.compile(rf"^\s*{re.escape(cle)}\s*:\s*(.+?)\s*$")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.match(line)
        if m:
            val = m.group(1).strip().strip("'\"")
            if val and val.lower() not in {"null", "none", "~"}:
                return val
    return None


def _appliquer_env_depuis_experience(experience_dir: Path) -> None:
    """Applique au minimum les paramètres 'forts' définis par le bac à sable.

    Règle : si une expérience est choisie, **elle a priorité** sur les choix TUI.
    """
    exp_yml = experience_dir / "experience.yml"

    # arène
    arene = _yaml_top_level_get(exp_yml, "arene") or _yaml_top_level_get(exp_yml, "arene_id")
    if arene:
        os.environ["SNAKE_ARENE"] = arene

    # agent / latent / seed / epsilon (noms probables)
    agent = _yaml_top_level_get(exp_yml, "agent") or _yaml_top_level_get(exp_yml, "agent_id")
    if agent:
        os.environ["SNAKE_AGENT"] = agent

    latent = _yaml_top_level_get(exp_yml, "latent") or _yaml_top_level_get(exp_yml, "latent_id") or _yaml_top_level_get(exp_yml, "champ_latent")
    if latent:
        os.environ["SNAKE_AGENT_LATENT"] = latent

    seed = _yaml_top_level_get(exp_yml, "seed")
    if seed:
        os.environ["SNAKE_AGENT_SEED"] = seed

    epsilon = _yaml_top_level_get(exp_yml, "epsilon")
    if epsilon:
        os.environ["SNAKE_AGENT_EPSILON"] = epsilon


def preparer_bac_a_sable(racine: Path, experience_id: str) -> tuple[BacASableV1, Path, Path]:
    """Prépare un run et exporte les variables d'env utiles (journal, monde, etc.).

    Important : quand un bac à sable est choisi, **il devient la source de vérité** :
    l'arène (et autres paramètres) viennent de l'expérience, pas du menu TUI.
    """
    exp_dir = racine / "donnees" / "config" / "experiences" / experience_id

    # 1) charger bac + lire la cfg YAML (source de vérité)
    bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=experience_id)
    # appliquer env depuis la cfg YAML complète (arène, agent, etc.)
    if isinstance(getattr(bac, 'cfg', None), dict):
        _appliquer_env_depuis_cfg(bac.cfg)
    bac.assurer_structure()
    run_dir, journal_path, _stdout, _meta = bac.preparer_run(run_tag="tui", run_id=str(os.getpid()))

    # 3) journal prioritaire au run
    os.environ["SNAKE_JOURNAL_PATH"] = str(journal_path)

    # 4) variables env liées au modèle monde (si l'expérience en contient)
    bac.appliquer_env_modele_monde()

    return bac, journal_path, run_dir


def lister_journaux_replay(racine: Path, experience_id: Optional[str]) -> list[Path]:
    """Liste des journaux jsonl candidats au replay, du plus récent au plus ancien."""
    candidats: list[Path] = []

    if experience_id:
        exp_dir = racine / "donnees" / "config" / "experiences" / experience_id
        runs_dir = exp_dir / "artefacts" / "runs"
        if runs_dir.exists():
            for run in sorted(runs_dir.iterdir(), reverse=True):
                if not run.is_dir():
                    continue
                for fp in sorted(run.glob("*.jsonl"), reverse=True):
                    candidats.append(fp)

    fp_global = racine / "artefacts" / "episodes.jsonl"
    if fp_global.exists():
        candidats.append(fp_global)

    uniq: list[Path] = []
    seen = set()
    for p in candidats:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq

# NOTE: parsing YAML volontairement minimal (top-level key: value)

def _appliquer_env_depuis_cfg(cfg: dict) -> None:
    # Applique les paramètres de l'expérience (source de vérité)
    # Aucun docstring multilignes ici volontairement

    def _get(d: dict, *path):
        cur = d
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur

    arene_id = _get(cfg, "arene", "id") or cfg.get("arene_id") or cfg.get("arene")
    if isinstance(arene_id, str) and arene_id.strip():
        os.environ["SNAKE_ARENE"] = arene_id.strip()

    agent_id = _get(cfg, "agent", "id") or cfg.get("agent_id") or cfg.get("agent")
    if isinstance(agent_id, str) and agent_id.strip():
        os.environ["SNAKE_AGENT"] = agent_id.strip()

    latent = (
        cfg.get("latent")
        or cfg.get("latent_id")
        or _get(cfg, "modele_monde", "latent_cli")
    )
    if isinstance(latent, str) and latent.strip():
        os.environ["SNAKE_AGENT_LATENT"] = latent.strip()

    seed = _get(cfg, "generation", "seed") or cfg.get("seed")
    if seed is not None:
        os.environ["SNAKE_AGENT_SEED"] = str(seed)

    epsilon = cfg.get("epsilon")
    if epsilon is not None:
        os.environ["SNAKE_AGENT_EPSILON"] = str(epsilon)



# NOTE: helper corrigé

def _appliquer_env_depuis_cfg(cfg: dict) -> None:
    """Applique les paramètres de l'expérience (source de vérité).

    Supporte les structures imbriquées usuelles :
      - arene: { id: ... }
      - agent: { id: ... }
      - generation: { seed: ... }
    """

    def _get(d: dict, *path):
        cur = d
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur

    arene_id = _get(cfg, "arene", "id") or cfg.get("arene_id") or cfg.get("arene")
    if isinstance(arene_id, str) and arene_id.strip():
        os.environ["SNAKE_ARENE"] = arene_id.strip()

    agent_id = _get(cfg, "agent", "id") or cfg.get("agent_id") or cfg.get("agent")
    if isinstance(agent_id, str) and agent_id.strip():
        os.environ["SNAKE_AGENT"] = agent_id.strip()

    latent = cfg.get("latent") or cfg.get("latent_id") or _get(cfg, "modele_monde", "latent_cli")
    if isinstance(latent, str) and latent.strip():
        os.environ["SNAKE_AGENT_LATENT"] = latent.strip()

    seed = _get(cfg, "generation", "seed") or cfg.get("seed")
    if seed is not None:
        os.environ["SNAKE_AGENT_SEED"] = str(seed)

    epsilon = cfg.get("epsilon")
    if epsilon is not None:
        os.environ["SNAKE_AGENT_EPSILON"] = str(epsilon)
