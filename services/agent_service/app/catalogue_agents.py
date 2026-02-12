from __future__ import annotations

"""Catalogue canon des agents (SAI-A***).

Norme v1 (plug-ins) :
  - les agents sont définis par des fichiers YAML (agent*.yml) découverts sur disque
  - le catalogue est construit au démarrage par indexation de ces définitions
  - l'API `creer_agent(id_agent, params, instruments)` est STRICTE (pas de kwargs)

Multi-sources (priorités, dernier gagne) :
  1) built-in (dans `services/agent_service/app/agents/**/agent*.yml`)
  2) global config (`donnees/config/agents/**/*.yml`)
  3) expérience (`donnees/config/experiences/<id>/agents/**/*.yml`)
  4) override (`SNAKE_AGENTS_PATH=/chemin1:/chemin2`)

Garde-fous :
  - import strings restreints à des préfixes autorisés
  - YAML validé "fail fast"
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import importlib
import os

import yaml

from instrument.app.instruments import CameraEgocentreeV1, CameraEstradeAbsolueV1, InstrumentGPSV1
from agent_service.app.contrats_agents import IAgentArene


# -----------------------------
# Specs canoniques
# -----------------------------

@dataclass(frozen=True)
class SpecInstrument:
    instrument_id: str
    params: dict[str, Any] | None = None


@dataclass(frozen=True)
class SpecAgent:
    id_agent: str
    fabrique: Callable[[dict[str, Any]], IAgentArene]
    description: str
    instruments_defaut: list[SpecInstrument]
    source: str | None = None  # pour debug (chemin du yaml)


# -----------------------------
# Instruments (canon)
# -----------------------------

def _fabriquer_instrument(spec: SpecInstrument):
    p = spec.params or {}
    iid = spec.instrument_id
    if iid == "camera_egocentree_v1":
        return CameraEgocentreeV1(
            rayon=int(p.get("rayon", 2)),
            niveau_bruit=int(p.get("niveau_bruit", 0)),
            seed_bruit=int(p.get("seed_bruit", 1)),
        )
    if iid == "camera_estrade_absolue_v1":
        return CameraEstradeAbsolueV1(
            niveau_bruit=int(p.get("niveau_bruit", 0)),
            seed_bruit=int(p.get("seed_bruit", 1)),
        )
    if iid == "gps_v1":
        return InstrumentGPSV1()
    raise ValueError(f"instrument inconnu: {iid!r}")


def creer_instruments(specs: list[SpecInstrument] | None) -> list[Any]:
    return [_fabriquer_instrument(s) for s in (specs or [])]


# -----------------------------
# Plug-ins (agent.yml)
# -----------------------------

_PREFIXES_IMPORT_AUTORISES: tuple[str, ...] = (
    "agent_service.app.agents.",
    "agent_service.app.incarnations.",
)

def _verifier_import_string(import_str: str) -> None:
    if not any(import_str.startswith(p) for p in _PREFIXES_IMPORT_AUTORISES):
        raise ValueError(
            "import non autorisé (garde-fou). "
            f"Reçu={import_str!r}, préfixes={_PREFIXES_IMPORT_AUTORISES}"
        )


def _importer_callable(import_str: str) -> Callable[..., Any]:
    """Importe `module:objet` (fonction ou classe)."""
    if ":" not in import_str:
        raise ValueError(f"import string invalide (attendu module:objet): {import_str!r}")
    module_name, obj_name = import_str.split(":", 1)
    _verifier_import_string(module_name + ".")  # check prefix on module
    module = importlib.import_module(module_name)
    try:
        obj = getattr(module, obj_name)
    except AttributeError as e:
        raise ValueError(f"objet introuvable: {import_str!r}") from e
    return obj


def _specs_instruments_depuis_yaml(raw: Any, source: str) -> list[SpecInstrument]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"instruments_defaut doit être une liste ({source})")
    specs: list[SpecInstrument] = []
    for it in raw:
        if isinstance(it, str):
            specs.append(SpecInstrument(it, {}))
        elif isinstance(it, dict):
            iid = it.get("instrument_id") or it.get("id") or it.get("instrument")
            if not iid or not isinstance(iid, str):
                raise ValueError(f"instrument sans id ({source}): {it!r}")
            params = it.get("params") or {}
            if params is None:
                params = {}
            if not isinstance(params, dict):
                raise ValueError(f"params instrument doit être dict ({source})")
            specs.append(SpecInstrument(iid, params))
        else:
            raise ValueError(f"entrée instrument invalide ({source}): {it!r}")
    return specs


def _charger_agent_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"agent.yml invalide (dict attendu): {path}")
    return data


def _spec_agent_depuis_yaml(data: dict[str, Any], source_path: Path) -> SpecAgent:
    source = str(source_path)
    version = data.get("version", 1)
    if version != 1:
        raise ValueError(f"version agent.yml non supportée ({version}) : {source}")
    id_agent = data.get("id")
    if not isinstance(id_agent, str) or not id_agent.strip():
        raise ValueError(f"id manquant/invalid: {source}")
    id_agent = id_agent.strip()

    description = data.get("description") or data.get("desc") or ""
    if not isinstance(description, str):
        raise ValueError(f"description invalide: {source}")
    description = description.strip() or id_agent

    # fabrique (préférée) ou classe (simple)
    fabrique_str = data.get("fabrique")
    classe_str = data.get("classe")

    if fabrique_str and not isinstance(fabrique_str, str):
        raise ValueError(f"fabrique invalide (str attendu): {source}")
    if classe_str and not isinstance(classe_str, str):
        raise ValueError(f"classe invalide (str attendu): {source}")

    if not fabrique_str and not classe_str:
        raise ValueError(f"fabrique/classe manquant: {source}")

    if fabrique_str:
        fab = _importer_callable(fabrique_str)
        if not callable(fab):
            raise ValueError(f"fabrique non-callable: {fabrique_str!r} ({source})")

        def _fabrique(params: dict[str, Any]) -> IAgentArene:
            return fab(params)  # type: ignore[misc]

    else:
        cls = _importer_callable(classe_str)  # type: ignore[arg-type]
        if not callable(cls):
            raise ValueError(f"classe non-callable: {classe_str!r} ({source})")

        def _fabrique(params: dict[str, Any]) -> IAgentArene:
            # convention : les constructeurs d'agents acceptent (seed, mode_latent, etc.)
            return cls(**params)  # type: ignore[misc]

    instruments_defaut = _specs_instruments_depuis_yaml(data.get("instruments_defaut"), source)
    return SpecAgent(
        id_agent=id_agent.lower(),
        fabrique=_fabrique,
        description=description,
        instruments_defaut=instruments_defaut,
        source=source,
    )


def _trouver_racine_repo() -> Path | None:
    """Trouve la racine du repo en remontant depuis ce fichier."""
    ici = Path(__file__).resolve()
    for p in ici.parents:
        if (p / "donnees").exists() and (p / "services").exists():
            return p
    return None


def _collecter_ymls_depuis_dir(base: Path, patterns: list[str]) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    for pat in patterns:
        out.extend(sorted(base.glob(pat)))
    # dédoublonnage conservant ordre
    vus: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        s = str(p.resolve())
        if s in vus:
            continue
        vus.add(s)
        uniq.append(p)
    return uniq


def _sources_plugins() -> list[list[Path]]:
    """Retourne les sources dans l'ordre de priorité (dernier gagne)."""
    patterns = ["**/agent*.yml", "**/agent*.yaml"]

    # 1) built-in : sous services/agent_service/app/agents
    built_in_dir = Path(__file__).resolve().parent / "agents"
    built_in = _collecter_ymls_depuis_dir(built_in_dir, patterns)

    # 2) global config : donnees/config/agents
    root = _trouver_racine_repo()
    global_dir = (root / "donnees" / "config" / "agents") if root else Path("donnees/config/agents")
    global_ymls = _collecter_ymls_depuis_dir(global_dir, ["**/*.yml", "**/*.yaml"])

    # 3) expérience
    exp_id = (os.getenv("SNAKE_EXPERIENCE") or os.getenv("SNAKE_EXPERIENCE_ID") or "").strip()
    exp_ymls: list[Path] = []
    if exp_id:
        exp_dir = (root / "donnees" / "config" / "experiences" / exp_id) if root else Path(f"donnees/config/experiences/{exp_id}")
        exp_ymls = _collecter_ymls_depuis_dir(exp_dir / "agents", ["**/*.yml", "**/*.yaml"])

    # 4) overrides env
    override_env = (os.getenv("SNAKE_AGENTS_PATH") or "").strip()
    override_ymls: list[Path] = []
    if override_env:
        for part in override_env.split(os.pathsep):
            part = part.strip()
            if not part:
                continue
            p = Path(part)
            if p.is_file():
                override_ymls.append(p)
            elif p.is_dir():
                override_ymls.extend(_collecter_ymls_depuis_dir(p, ["**/*.yml", "**/*.yaml"]))

    return [built_in, global_ymls, exp_ymls, override_ymls]


def charger_catalogue() -> dict[str, SpecAgent]:
    """Construit le catalogue en indexant les plug-ins YAML."""
    catalogue: dict[str, SpecAgent] = {}
    # on garde trace de la source ayant créé l'entrée (utile pour collisions)
    provenance: dict[str, str] = {}

    for source_list in _sources_plugins():
        for yml_path in source_list:
            data = _charger_agent_yaml(yml_path)
            spec = _spec_agent_depuis_yaml(data, yml_path)
            key = spec.id_agent
            if key in catalogue:
                # override (priorité supérieure)
                provenance[key] = str(yml_path)
            else:
                provenance[key] = str(yml_path)
            catalogue[key] = spec

    if not catalogue:
        raise RuntimeError("Aucun agent découvert via plug-ins (agent*.yml). Vérifier l'installation.")

    return catalogue


def creer_agent(
    id_agent: str,
    params: dict[str, Any] | None = None,
    instruments: list[SpecInstrument] | None = None,
) -> IAgentArene:
    cat = charger_catalogue()
    key = (id_agent or "").strip().lower()
    if key not in cat:
        connus = ", ".join(sorted(cat.keys()))
        raise ValueError(f"agent inconnu: {id_agent!r} (connus: {connus})")
    spec = cat[key]
    agent = spec.fabrique(params or {})
    # injection instruments (canon) : si l'agent expose `definir_instruments`, sinon attribut.
    insts = creer_instruments(instruments or spec.instruments_defaut)
    if hasattr(agent, "definir_instruments") and callable(getattr(agent, "definir_instruments")):
        agent.definir_instruments(insts)  # type: ignore[attr-defined]
    else:
        setattr(agent, "_instruments", insts)
    return agent
