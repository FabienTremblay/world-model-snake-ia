from __future__ import annotations

from typing import Any

# Adapte les imports à tes chemins exacts (je garde volontairement simple)
from agent_service.app.agents.agent_personne_v1 import AgentPersonneV1  # <-- à ajuster si différent


def fabriquer_agent_personne(params: dict[str, Any]) -> AgentPersonneV1:
    """
    Fabrique canonique pour l'incarnation "agent_personne".

    params requis:
      - agent_personne_path: str  (chemin vers l'artefact JSON)
    """
    if params is None:
        params = {}

    chemin = params.get("agent_personne_path")
    if not chemin or not isinstance(chemin, str):
        raise ValueError(
            "agent_personne: params['agent_personne_path'] est requis (str). "
            "ex: params={'agent_personne_path': '.../agent_personne.json'}"
        )

    # Ajoute ici d'autres params si AgentPersonneV1 en attend
    return AgentPersonneV1(agent_personne_path=chemin)
