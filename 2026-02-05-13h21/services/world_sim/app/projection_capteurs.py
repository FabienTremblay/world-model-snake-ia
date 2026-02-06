# services/world_sim/app/projection_capteurs.py
from __future__ import annotations

from typing import List, Tuple
import random

from commun.contrats import Pixel
from .arenes_yaml import PalettePixels, PALETTE_DEFAUT

Position = Tuple[int, int]


def projeter_capteurs(
    largeur: int,
    hauteur: int,
    serpent: List[Position],
    nourritures: set[Position],
    porte: Position | None = None,
    porte_ouverte: bool = False,
    palette: PalettePixels = PALETTE_DEFAUT,
) -> List[List[Pixel]]:
    """
    Transforme l'état interne en grille de capteurs (signal).
    Important: aucune étiquette sémantique n'est exposée.
    """
    capteurs: List[List[Pixel]] = [[palette.sol for _ in range(largeur)] for _ in range(hauteur)]

    # murs (bordures)
    for x in range(largeur):
        capteurs[0][x] = palette.mur
        capteurs[hauteur - 1][x] = palette.mur
    for y in range(hauteur):
        capteurs[y][0] = palette.mur
        capteurs[y][largeur - 1] = palette.mur

    # nourriture
    for (x, y) in nourritures:
        capteurs[y][x] = palette.nourriture

    if porte is not None:
        px = palette.porte_ouverte if porte_ouverte else palette.porte_fermee
        x, y = porte
        capteurs[y][x] = px

    # serpent
    for (x, y) in serpent[:-1]:
        capteurs[y][x] = palette.serpent_corps
    hx, hy = serpent[-1]
    capteurs[hy][hx] = palette.serpent_tete

    return capteurs


def rendre_debug_ascii(capteurs: List[List[Pixel]]) -> List[str]:
    """
    Rendu ASCII strictement pour debug (TUI).
    Le mapping ci-dessous est DEV ONLY.
    """
    lignes: List[str] = []
    for row in capteurs:
        chars = []
        for px in row:
            if px == PALETTE_DEFAUT.mur:
                chars.append("#")
            elif px == PALETTE_DEFAUT.nourriture:
                chars.append("*")
            elif px == PALETTE_DEFAUT.serpent_tete:
                chars.append("O")
            elif px == PALETTE_DEFAUT.serpent_corps:
                chars.append("o")
            elif px == PALETTE_DEFAUT.porte_fermee:
                chars.append("D")
            elif px == PALETTE_DEFAUT.porte_ouverte:
                chars.append("d")
            else:
                chars.append(".")
        lignes.append("".join(chars))
    return lignes




def _clamp(v: int, vmin: int, vmax: int) -> int:
    return vmin if v < vmin else vmax if v > vmax else v


def appliquer_bruit(
    capteurs_canon: List[List[Pixel]],
    rng: random.Random,
    niveau_bruit: int,
) -> List[List[Pixel]]:
    """
    Applique un bruit léger aux capteurs (signal) sans modifier le rendu debug.

    - teinte: jitter +-niveau_bruit (mod 360)
    - intensite: jitter +- (niveau_bruit*4) (clamp 0..255)
    - motif/clignote restent stables (v1)
    """
    if niveau_bruit <= 0:
        return capteurs_canon

    bruit_teinte = niveau_bruit
    bruit_int = niveau_bruit * 4

    capteurs: List[List[Pixel]] = []
    for row in capteurs_canon:
        row_out: List[Pixel] = []
        for px in row:
            teinte = (px.teinte + rng.randint(-bruit_teinte, bruit_teinte)) % 360
            intensite = _clamp(px.intensite + rng.randint(-bruit_int, bruit_int), 0, 255)
            row_out.append(
                Pixel(
                    teinte=teinte,
                    intensite=intensite,
                    motif=px.motif,
                    clignote=px.clignote,
                )
            )
        capteurs.append(row_out)
    return capteurs
