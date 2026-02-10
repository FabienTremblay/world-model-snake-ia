from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from instrument.app.contrats import EtatMondeCanonique, ObservationDonnees


@dataclass(frozen=True)
class InstrumentGPSV1:
    """Instrument GPS (v1) : retourne la position de la tête en (x,y).

    C'est volontairement "absolu" (repère arène).
    """

    instrument_id: str = "gps_v1"

    def observer(self, etat: EtatMondeCanonique) -> ObservationDonnees:
        if not etat.serpent:
            raise ValueError("etat.serpent vide (tête introuvable)")

        x, y = etat.serpent[-1]
        meta: Dict[str, Any] = {
            "instrument_id": self.instrument_id,
            "repere": "absolu",
            "type": "donnees",
        }
        return ObservationDonnees(donnees={"tete": (x, y)}, meta=meta)
