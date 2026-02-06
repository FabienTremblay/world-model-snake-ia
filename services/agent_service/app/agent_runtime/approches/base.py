from __future__ import annotations

from typing import Protocol

from commun.contrats import Pixel
from agent_service.app.agent_runtime.agents_in_arene.contrats import ContexteDecision


class ApprocheDecision(Protocol):
    """Plug-in de décision (cours 5).

    Une approche choisit une action à partir des capteurs et d'un contexte.
    L'agent peut ensuite appliquer son tempérament (si pertinent).
    """

    def choisir_action(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> str:
        ...
