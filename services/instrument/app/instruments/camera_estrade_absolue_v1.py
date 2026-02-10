from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from instrument.app.contrats import EtatMondeCanonique, ObservationPixels
from instrument.app.projection_capteurs import projeter_capteurs, rendre_debug_ascii, appliquer_bruit
import random


@dataclass(frozen=True)
class CameraEstradeAbsolueV1:
    """
    Caméra d'estrade (repère absolu, invariant par rotation).

    - ne tient PAS compte de la direction du serpent
    - projette l'état canonique en grille HxW
    """

    instrument_id: str = "camera_estrade_absolue_v1"
    niveau_bruit: int = 0
    seed_bruit: int = 0

    def observer(self, etat: EtatMondeCanonique) -> ObservationPixels:
        pixels_canon = projeter_capteurs(
            largeur=etat.largeur,
            hauteur=etat.hauteur,
            serpent=etat.serpent,
            nourritures=etat.nourritures,
            porte=etat.porte,
            porte_ouverte=etat.porte_ouverte,
            palette=etat.palette,
        )

        rng = random.Random(self.seed_bruit)
        pixels = appliquer_bruit(pixels_canon, rng=rng, niveau_bruit=self.niveau_bruit)

        meta: Dict[str, Any] = {
            "instrument_id": self.instrument_id,
            "repere": "absolu",
            "niveau_bruit": self.niveau_bruit,
            "seed_bruit": self.seed_bruit,
            # debug utile (sans être la vérité de l'instrument)
            "debug_ascii": rendre_debug_ascii(pixels_canon),
        }
        return ObservationPixels(pixels=pixels, meta=meta)
