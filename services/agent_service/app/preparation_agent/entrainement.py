from __future__ import annotations

import time
from dataclasses import replace

from .contrats import AgentPersonne, PlanPreparationAgent, RapportEntrainement


def entrainer_agent_personne(
    plan: PlanPreparationAgent,
    agent: AgentPersonne,
) -> tuple[AgentPersonne, RapportEntrainement]:
    """
    squelette d'entraînement.

    pour l'instant :
    - ne fait pas de ml
    - produit un rapport et simule l'écriture de chemins de poids
    """
    # à remplacer par la vraie boucle d'entraînement (torch, etc.)
    chemins_poids = {
        "tronc": agent.tronc.chemin_poids or "",
        "tetes": "a_definir",
        "policy": "a_definir",
    }

    agent_entraine = replace(
        agent,
        poids=chemins_poids,
        meta={**agent.meta, "entrainement": plan.entrainement},
    )

    rapport = RapportEntrainement(
        genere_ts_ns=time.time_ns(),
        experience=plan.experience,
        arene_id=plan.arene_id,
        agent_personne_id=plan.agent_personne_id,
        succes=True,
        mesures={
            "etat": "squelette",
            "commentaire": "aucun apprentissage réel dans ce prototype",
        },
        chemins={
            "poids": "a_definir",
            "logs": plan.chemins.get("runs_preparation_dir", ""),
        },
        notes=[
            "prototype : entrainement non implémenté",
        ],
    )
    return agent_entraine, rapport
