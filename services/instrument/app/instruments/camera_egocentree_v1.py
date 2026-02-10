from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from commun.contrats import Pixel
from instrument.app.contrats import EtatMondeCanonique, ObservationPixels
from .camera_estrade_absolue_v1 import CameraEstradeAbsolueV1


def _rotation_depuis_direction(direction: str | None) -> str:
    """
    Rotation pour aligner l'AVANT de l'agent vers le HAUT de la matrice retournée.

    Convention repère absolu:
      - x vers la droite, y vers le bas
      - direction: "haut", "droite", "bas", "gauche"
    """
    if direction is None or direction == "haut":
        return "r0"
    if direction == "droite":
        return "cw"     # +x (avant) devient -y (haut)
    if direction == "bas":
        return "r180"   # +y (avant) devient -y (haut)
    if direction == "gauche":
        return "ccw"    # -x (avant) devient -y (haut)
    raise ValueError(f"direction invalide: {direction!r}")


def _rotater(pixels: List[List[Pixel]], rotation: str) -> List[List[Pixel]]:
    """Rotation sur matrice carrée."""
    n = len(pixels)
    if n == 0:
        return pixels

    if rotation == "r0":
        return [list(row) for row in pixels]

    if rotation == "r180":
        return [list(reversed(row)) for row in reversed(pixels)]

    if rotation == "cw":
        # new[i][j] = old[n-1-j][i]
        return [[pixels[n - 1 - j][i] for j in range(n)] for i in range(n)]

    if rotation == "ccw":
        # new[i][j] = old[j][n-1-i]
        return [[pixels[j][n - 1 - i] for j in range(n)] for i in range(n)]

    raise ValueError(f"rotation invalide: {rotation!r}")


def _pixel_mur(etat: EtatMondeCanonique, fallback: Pixel) -> Pixel:
    mur = getattr(etat.palette, "mur", None)
    return mur if isinstance(mur, Pixel) else fallback


@dataclass(frozen=True)
class CameraEgocentreeV1:
    """Caméra égocentrée (v1) : patch local + rotation avant->haut."""

    instrument_id: str = "camera_egocentree_v1"
    rayon: int = 2
    niveau_bruit: int = 0
    seed_bruit: int = 0

    def observer(self, etat: EtatMondeCanonique) -> ObservationPixels:
        # 1) Projection estrade (utile pour murs/palette/bruit de mesure)
        cam_estrade = CameraEstradeAbsolueV1(
            niveau_bruit=self.niveau_bruit,
            seed_bruit=self.seed_bruit,
        )
        obs_estrade = cam_estrade.observer(etat)
        grille = obs_estrade.pixels  # [y][x]
        hauteur = len(grille)
        largeur = len(grille[0]) if hauteur > 0 else 0

        if not etat.serpent:
            raise ValueError("etat.serpent vide (tête introuvable)")

        tete_x, tete_y = etat.serpent[-1]
        r = self.rayon

        mur_px = _pixel_mur(
            etat,
            grille[0][0] if (hauteur > 0 and largeur > 0) else Pixel(0, 0, 0, 0),
        )

        def get_px(x: int, y: int) -> Pixel:
            if 0 <= y < hauteur and 0 <= x < largeur:
                return grille[y][x]
            return mur_px

        # 2) Patch local en repère absolu (avant rotation)
        patch: List[List[Pixel]] = []
        for dy in range(-r, r + 1):
            row: List[Pixel] = []
            for dx in range(-r, r + 1):
                row.append(get_px(tete_x + dx, tete_y + dy))
            patch.append(row)

        # 3) Rotation pour repère égocentré (avant = haut)
        rotation = _rotation_depuis_direction(etat.direction)
        patch_rot = _rotater(patch, rotation)

        meta: Dict[str, Any] = dict(obs_estrade.meta)
        meta.update(
            {
                "instrument_id": self.instrument_id,
                "repere": "egocentre",
                "rayon": self.rayon,
                "niveau_bruit": self.niveau_bruit,
                "seed_bruit": self.seed_bruit,
                "rotation": rotation,
            }
        )
        return ObservationPixels(pixels=patch_rot, meta=meta)

