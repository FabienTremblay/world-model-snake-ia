from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Protocol, Optional, Dict, Any

from commun.contrats import Pixel
from world_sim.app.arenes_yaml import PalettePixels, PALETTE_DEFAUT

Position = Tuple[int, int]


@dataclass(frozen=True)
class EtatMondeCanonique:
    """Snapshot minimal du monde, suffisant pour projeter une observation."""

    largeur: int
    hauteur: int
    serpent: List[Position]          # ordre: corps ... tête (tête = dernier)
    nourritures: set[Position]
    porte: Optional[Position] = None
    porte_ouverte: bool = False
    direction: Optional[str] = None  # utile pour instruments égocentrés (pas utilisé par la caméra estrade)
    palette: PalettePixels = PALETTE_DEFAUT


@dataclass(frozen=True)
class ObservationPixels:
    """Observation sous forme de grille de pixels + meta."""

    pixels: List[List[Pixel]]
    meta: Dict[str, Any]


class IInstrument(Protocol):
    instrument_id: str

    def observer(self, etat: EtatMondeCanonique) -> ObservationPixels: ...
