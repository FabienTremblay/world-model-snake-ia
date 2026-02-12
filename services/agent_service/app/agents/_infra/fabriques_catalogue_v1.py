from __future__ import annotations

"""Fabriques canoniques (v1) pour les agents.

Pourquoi ?
- certains agents ont des constructeurs qui attendent des objets (ex. ParametresCuriosite),
  et ne peuvent pas être instanciés proprement via `Classe(**params)`.

Chaque fabrique reçoit un dict de params runtime et retourne une instance IAgentArene.
"""

from typing import Any

from agent_service.app.contrats_agents import IAgentArene


def fabriquer_aleatoire(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.agents.agent_aleatoire import AgentAleatoire

    return AgentAleatoire(
        seed=params.get("seed"),
        epsilon=float(params.get("epsilon", 0.0)),
    )


def fabriquer_curiosite_tabulaire(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.agents.agent_curiosite_tabulaire import AgentCuriositeTabulaire, ParametresCuriosite

    p = ParametresCuriosite(
        epsilon=float(params.get("epsilon", 0.0)),
        w_inconnu=float(params.get("w_inconnu", 1.0)),
        w_entropie=float(params.get("w_entropie", 1.0)),
        w_inconfiance=float(params.get("w_inconfiance", 1.0)),
    )
    return AgentCuriositeTabulaire(
        seed=params.get("seed"),
        params=p,
        mode_latent=str(params.get("mode_latent", "checksum")),
    )


def fabriquer_planif_mpc_tabulaire(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.agents.agent_planif_mpc_tabulaire import AgentPlanifMPCTabulaire

    return AgentPlanifMPCTabulaire(
        seed=params.get("seed"),
        mode_latent=str(params.get("mode_latent", "checksum")),
    )


def fabriquer_planif_mpc_observateur_tabulaire(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.agents.agent_planif_mpc_observateur_tabulaire import AgentPlanifMPCObservateurTabulaire

    return AgentPlanifMPCObservateurTabulaire(
        seed=params.get("seed"),
        mode_latent=str(params.get("mode_latent", "checksum")),
    )


def fabriquer_planif_1pas_temperament(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.agents.agent_planif_1pas_temperament_v1 import AgentPlanif1PasTemperamentV1

    return AgentPlanif1PasTemperamentV1(
        seed=params.get("seed"),
        mode_latent=str(params.get("mode_latent", "checksum")),
    )


def fabriquer_agent_personne(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.incarnations.agent_personne_v1 import AgentPersonneV1

    path = params.get("agent_personne_path")
    if not path:
        raise ValueError("agent_personne: fournir params['agent_personne_path']")
    return AgentPersonneV1(
        agent_personne_path=str(path),
        seed=params.get("seed"),
        mode_latent=str(params.get("mode_latent", "checksum")),
    )


def fabriquer_snake_collectif_v1_c1(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.agents.snake_collectif_v1.agent_c1 import AgentSnakeCollectifV1C1

    return AgentSnakeCollectifV1C1(seed=params.get("seed"))


def fabriquer_snake_collectif_v1_c2(params: dict[str, Any]) -> IAgentArene:
    from agent_service.app.agents.snake_collectif_v1.agent_c2 import AgentSnakeCollectifV1C2

    return AgentSnakeCollectifV1C2(seed=params.get("seed"))
