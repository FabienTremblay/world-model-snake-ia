from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Protocol, Optional, Dict, Any, Union

from commun.contrats import Pixel
from world_sim.app.arenes_yaml import PalettePixels, PALETTE_DEFAUT

Position = Tuple[int, int]


@dataclass(frozen=True)
class EtatMondeCanonique:
    """Snapshot minimal du monde, suffisant pour projeter une observation.

    Convention :
      - positions en (x, y)
      - serpent : corps ... tête (tête = dernier élément)
    """

    largeur: int
    hauteur: int
    serpent: List[Position]
    nourritures: set[Position]
    porte: Optional[Position] = None
    porte_ouverte: bool = False
    direction: Optional[str] = None  # utile pour instruments égocentrés
    palette: PalettePixels = PALETTE_DEFAUT


@dataclass(frozen=True)
class ObservationPixels:
    """Observation sous forme de grille de pixels + meta."""

    pixels: List[List[Pixel]]
    meta: Dict[str, Any]


@dataclass(frozen=True)
class ObservationDonnees:
    """Observation sous forme de données structurées + meta.

    Exemples :
      - gps : position (x,y)
      - boussole : direction
      - thermomètre : température
      - radio : messages reçus
      - livre : connaissances (plus tard)
    """

    donnees: Dict[str, Any]
    meta: Dict[str, Any]


ObservationInstrument = Union[ObservationPixels, ObservationDonnees]


class IInstrument(Protocol):
    instrument_id: str

    def observer(self, etat: EtatMondeCanonique) -> ObservationInstrument: ...
