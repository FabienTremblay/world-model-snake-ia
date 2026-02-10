from __future__ import annotations

import time
from dataclasses import replace

from .contrats import ArtefactAgentPersonne, CatalogueDeTetes, PlanPreparationAgent, SpecTete


def assembler_agent_personne(
    plan: PlanPreparationAgent,
    catalogue: CatalogueDeTetes,
) -> ArtefactAgentPersonne:
    """
    assemble un agent-personne :
    - sélectionne les têtes
    - installe la gouvernance initiale
    - produit un artefact agent-personne (sans entraîner encore)
    """
    index = {t.id: t for t in catalogue.tetes}
    tetes: list[SpecTete] = []
    inconnues: list[str] = []
    for tid in plan.tetes_selectionnees:
        t = index.get(tid)
        if t is None:
            inconnues.append(tid)
        else:
            tetes.append(t)

    gouvernance = {
        "intentions": plan.intentions,
        "influences": {t.id: t.influence for t in tetes},
        "notes": [],
    }
    if inconnues:
        gouvernance["notes"].append(f"têtes inconnues ignorées: {inconnues}")

    agent = ArtefactAgentPersonne(
        genere_ts_ns=time.time_ns(),
        experience=plan.experience,
        arene_id=plan.arene_id,
        agent_personne_id=plan.agent_personne_id,
        tronc=plan.tronc,
        tetes=tetes,
        gouvernance=gouvernance,
        poids={},
        etat_initial={},
        meta={"catalogue_version": catalogue.version},
    )
    return agent
