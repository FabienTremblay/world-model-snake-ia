	from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Type, TypeVar

from .contrats import AgentPersonne, CatalogueDeTetes, RapportEntrainement, PlanPreparationAgent


T = TypeVar("T")


def _ecrire_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _lire_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sauvegarder_catalogue(path: str, catalogue: CatalogueDeTetes) -> None:
    _ecrire_json(Path(path), asdict(catalogue))


def charger_catalogue(path: str) -> CatalogueDeTetes:
    d = _lire_json(Path(path))
    # chargement naïf : on reconstruit progressivement quand on en aura besoin.
    # pour le squelette, on laisse la responsabilité au pipeline d'instancier correctement.
    return CatalogueDeTetes(**d)


def sauvegarder_plan(path: str, plan: PlanPreparationAgent) -> None:
    _ecrire_json(Path(path), asdict(plan))


def charger_plan(path: str) -> PlanPreparationAgent:
    d = _lire_json(Path(path))
    return PlanPreparationAgent(**d)


def sauvegarder_agent_personne(path: str, agent: AgentPersonne) -> None:
    _ecrire_json(Path(path), asdict(agent))


def charger_agent_personne(path: str) -> AgentPersonne:
    d = _lire_json(Path(path))
    return AgentPersonne(**d)


def sauvegarder_rapport(path: str, rapport: RapportEntrainement) -> None:
    _ecrire_json(Path(path), asdict(rapport))

