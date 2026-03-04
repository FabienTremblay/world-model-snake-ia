from __future__ import annotations

from dataclasses import dataclass

from services.world_sim.app.evenements import BusEvenements, Evenement
from services.world_sim.app.objets_du_monde import ContexteTick, ObjetDuMonde


@dataclass
class IndividuAgentAreneV1ObjetDuMonde:
    """Individu (agent en arène) transportable — v1 (minimal).

    Contrat runner_evenements_v2 :
      - emettre_evenements(ctx, bus) -> None
      - l'objet publie sur le bus.
    """
    individu_cfg: dict

    def id_objet(self) -> str:
        return str(self.individu_cfg.get("individu_id") or "individu")

    def est_actif(self) -> bool:
        return True

    def emettre_evenements(self, ctx: ContexteTick, bus: BusEvenements) -> None:
        pol = self.individu_cfg.get("politique") or {}
        if not isinstance(pol, dict):
            pol = {}

        direction = pol.get("direction")
        if direction in (None, "", "none"):
            # inaction = aucun événement publié
            return

        bus.publier(
            Evenement(
                type="action_motrice",
                source_id=self.id_objet(),
                tick=int(ctx.tick),
                payload={"direction": str(direction)},
            )
        )
