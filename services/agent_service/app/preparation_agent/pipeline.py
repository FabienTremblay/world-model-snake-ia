from __future__ import annotations

from dataclasses import replace

from .assembleur import assembler_agent_personne
from .contrats import ArtefactAgentPersonne, CatalogueDeTetes, PlanPreparationAgent, RapportEntrainement
from .entrainement import entrainer_agent_personne


def preparer_agent_personne(
    plan: PlanPreparationAgent,
    catalogue: CatalogueDeTetes,
) -> tuple[ArtefactAgentPersonne, RapportEntrainement]:
    """
    pipeline haut niveau sai-a107 :
    1) assembler (tronc + têtes)
    2) entraîner (prototype)
    3) retourner (agent_personne, rapport)
    """
    agent = assembler_agent_personne(plan=plan, catalogue=catalogue)
    agent_entraine, rapport = entrainer_agent_personne(plan=plan, agent=agent)
    return agent_entraine, rapport
