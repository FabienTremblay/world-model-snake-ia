from __future__ import annotations

from typing import Any

from commun.contrats import Pixel
from instrument.app.contrats import ObservationPixels

from agent_service.app.contrats_agents import ContexteDecision


def pixels_depuis_contexte(contexte: ContexteDecision, instrument_id: str | None = None) -> list[list[Pixel]]:
    """Retourne une grille de pixels depuis le contexte.

    Convention :
      - si `instrument_id` est fourni, on le cherche d'abord.
      - sinon, on retourne la première ObservationPixels trouvée.

    Rupture assumée : l'agent consomme des observations produites par des instruments.
    """

    obs = contexte.observations
    if instrument_id:
        o = obs.get(instrument_id)
        if isinstance(o, ObservationPixels):
            return o.pixels

    for o in obs.values():
        if isinstance(o, ObservationPixels):
            return o.pixels

    # fallback transitoire : certains parcours peuvent encore passer un "capteurs" legacy dans info.
    info: dict[str, Any] = contexte.info or {}
    capteurs = info.get("capteurs")
    if capteurs is not None:
        return capteurs

    raise KeyError("Aucune ObservationPixels trouvée dans contexte.observations")
