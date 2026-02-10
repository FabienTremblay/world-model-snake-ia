from __future__ import annotations

"""Catalogue canon des agents (SAI-A***).

Rupture assumée : le runner et les UI ne doivent plus instancier les agents
par des `if/elif` dispersés. Tout passe ici.
"""

from dataclasses import dataclass
from typing import Any, Callable

from instrument.app.instruments import CameraEgocentreeV1, CameraEstradeAbsolueV1, InstrumentGPSV1

from agent_service.app.contrats_agents import IAgentArene


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


def charger_catalogue() -> dict[str, SpecAgent]:
    """Catalogue code-first v1.

    On migrera ensuite vers YAML si désiré.
    """

    def _aleatoire(params: dict[str, Any]) -> IAgentArene:
        from agent_service.app.agents.agent_aleatoire import AgentAleatoire

        return AgentAleatoire(seed=params.get("seed"), epsilon=float(params.get("epsilon", 0.0)))

    def _curiosite(params: dict[str, Any]) -> IAgentArene:
        from agent_service.app.agents.agent_curiosite_tabulaire import AgentCuriositeTabulaire, ParametresCuriosite

        p = ParametresCuriosite(
            epsilon=float(params.get("epsilon", 0.0)),
            w_inconnu=float(params.get("w_inconnu", 1.0)),
            w_entropie=float(params.get("w_entropie", 1.0)),
            w_inconfiance=float(params.get("w_inconfiance", 1.0)),
        )
        return AgentCuriositeTabulaire(seed=params.get("seed"), params=p, mode_latent=str(params.get("mode_latent", "checksum")))

    def _mpc(params: dict[str, Any]) -> IAgentArene:
        from agent_service.app.agents.agent_planif_mpc_tabulaire import AgentPlanifMPCTabulaire

        return AgentPlanifMPCTabulaire(seed=params.get("seed"), mode_latent=str(params.get("mode_latent", "checksum")))

    def _mpc_obs(params: dict[str, Any]) -> IAgentArene:
        from agent_service.app.agents.agent_planif_mpc_observateur_tabulaire import AgentPlanifMPCObservateurTabulaire

        return AgentPlanifMPCObservateurTabulaire(seed=params.get("seed"), mode_latent=str(params.get("mode_latent", "checksum")))

    def _temperament(params: dict[str, Any]) -> IAgentArene:
        from agent_service.app.agents.agent_planif_1pas_temperament_v1 import AgentPlanif1PasTemperamentV1

        return AgentPlanif1PasTemperamentV1(seed=params.get("seed"), mode_latent=str(params.get("mode_latent", "checksum")))

    def _agent_personne(params: dict[str, Any]) -> IAgentArene:
        from agent_service.app.incarnations.agent_personne_v1 import AgentPersonneV1

        path = params.get("agent_personne_path")
        if not path:
            raise ValueError("agent_personne: fournir params['agent_personne_path']")
        return AgentPersonneV1(agent_personne_path=str(path), seed=params.get("seed"), mode_latent=str(params.get("mode_latent", "checksum")))

    instruments_defaut = [
        SpecInstrument("camera_egocentree_v1", {"rayon": 2, "niveau_bruit": 0, "seed_bruit": 1}),
        SpecInstrument("gps_v1", {}),
    ]

    return {
        "aleatoire": SpecAgent("aleatoire", _aleatoire, "Agent aléatoire", instruments_defaut),
        "curiosite_tabulaire": SpecAgent("curiosite_tabulaire", _curiosite, "Curiosité tabulaire", instruments_defaut),
        "planif_mpc_tabulaire": SpecAgent("planif_mpc_tabulaire", _mpc, "Planification MPC tabulaire", instruments_defaut),
        "planif_mpc_observateur_tabulaire": SpecAgent(
            "planif_mpc_observateur_tabulaire", _mpc_obs, "Planification MPC + observateur", instruments_defaut
        ),
        "planif_1pas_temperament": SpecAgent("planif_1pas_temperament", _temperament, "1 pas + tempérament", instruments_defaut),
        "agent_personne": SpecAgent("agent_personne", _agent_personne, "Incarnation d'un agent-personne préparé", instruments_defaut),
    }


def creer_agent(
    id_agent: str,
    params: dict[str, Any] | None = None,
    instruments: list[SpecInstrument] | None = None,
) -> IAgentArene:
    cat = charger_catalogue()
    key = (id_agent or "").strip().lower()
    if key not in cat:
        raise ValueError(f"agent inconnu: {id_agent!r} (connus: {', '.join(sorted(cat.keys()))})")
    spec = cat[key]
    agent = spec.fabrique(params or {})
    # injection instruments (canon) : si l'agent expose `definir_instruments`, sinon attribut.
    insts = creer_instruments(instruments or spec.instruments_defaut)
    if hasattr(agent, "definir_instruments") and callable(getattr(agent, "definir_instruments")):
        agent.definir_instruments(insts)  # type: ignore[attr-defined]
    else:
        setattr(agent, "_instruments", insts)
    return agent
