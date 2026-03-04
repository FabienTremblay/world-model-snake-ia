from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from services.world_sim.app.evenements import BusEvenements, Evenement
from services.world_sim.app.objets_du_monde import ContexteTick


@dataclass
class AgentIndividuStubV1:
    """Stub d'individu en arène comme objet du monde.

    - Actif (peut émettre des événements).
    - V1 : émet une action motrice déterministe (ou aucune) pour valider l'infrastructure.
    """

    objet_id: str = "ia_stub_0001"
    est_actif: bool = True
    direction: Optional[str] = "avant"  # valeur de démonstration

    def emettre_evenements(self, ctx: ContexteTick, bus: BusEvenements) -> None:
        # Inaction = ne rien publier.
        if self.direction is None:
            return

        bus.publier(
            Evenement(
                type="action_motrice",
                source_id=self.objet_id,
                tick=ctx.tick,
                payload={"direction": self.direction},
            )
        )
