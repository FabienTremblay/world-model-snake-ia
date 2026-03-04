from __future__ import annotations

import json
import hashlib
from pathlib import Path

import yaml


def _racine_catalogue_individus(racine_projet: Path) -> Path:
    return racine_projet / "donnees" / "catalogues" / "individus"


def charger_individu_v1(*, racine_projet: Path, individu_id: str, valider_schema: bool = True) -> dict:
    """Charge un individu depuis le catalogue.

    Convention:
      donnees/catalogues/individus/<individu_id>/individu.yml
    """
    p = _racine_catalogue_individus(racine_projet) / individu_id / "individu.yml"
    if not p.exists():
        raise FileNotFoundError(f"individu introuvable: {p}")

    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("individu.yml doit contenir un mapping YAML (dict)")

    if valider_schema:
        for champ in ("schema", "individu_id", "famille_id", "version", "politique"):
            if champ not in cfg:
                raise ValueError(f"champ obligatoire manquant dans individu.yml: {champ}")
        if str(cfg.get("schema")) != "individu_agent_arene_v1":
            raise ValueError("schema d'individu non supporté (attendu: individu_agent_arene_v1)")

    return cfg


def calculer_hash_individu(individu_cfg: dict) -> str:
    """Hash canonique d'un individu (sha256) pour l'immutabilité et la traçabilité."""
    payload = json.dumps(individu_cfg, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def appliquer_evolution_post_run(individu_entree: dict, *, run_id: str, run_dir: str, ticks: int) -> dict:
    """Évolution minimale (v1) appliquée *après* run, uniquement en entraînement.

    - Pas d'apprentissage de réseau ici (pour l'instant).
    - Mise à jour mémoire courte + provenance + version.
    """
    # deep copy simple et stable
    sortie = json.loads(json.dumps(individu_entree, ensure_ascii=False))

    mem = sortie.get("memoire_courte")
    if not isinstance(mem, dict):
        mem = {}
        sortie["memoire_courte"] = mem

    mem["compteur_runs"] = int(mem.get("compteur_runs") or 0) + 1
    mem["derniere_duree_ticks"] = int(ticks)
    mem["dernier_run_id"] = str(run_id)
    mem["dernier_run_dir"] = str(run_dir)

    prov = sortie.get("provenance")
    if not isinstance(prov, dict):
        prov = {}
        sortie["provenance"] = prov

    prov["parent_hash"] = calculer_hash_individu(individu_entree)
    prov["parent_run_id"] = None
    prov["run_id"] = str(run_id)

    try:
        sortie["version"] = int(sortie.get("version") or 0) + 1
    except Exception:
        sortie["version"] = 1

    return sortie
