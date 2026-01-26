# services/world_sim/app/projection_capteurs.py
from __future__ import annotations

from typing import List, Tuple
import random

from commun.contrats import Pixel

Position = Tuple[int, int]


# Attributs visuels (signal) — v1 (sans bruit)
# NB: ces attributs sont un choix de projection; ils ne doivent pas révéler la sémantique.
PIXEL_SOL = Pixel(teinte=200, intensite=40, motif=0, clignote=0)
PIXEL_MUR = Pixel(teinte=210, intensite=120, motif=3, clignote=0)
PIXEL_CORPS = Pixel(teinte=120, intensite=160, motif=2, clignote=0)
PIXEL_TETE = Pixel(teinte=120, intensite=230, motif=5, clignote=0)
PIXEL_NOURRITURE = Pixel(teinte=30, intensite=220, motif=6, clignote=1)


def projeter_capteurs(
    largeur: int,
    hauteur: int,
    serpent: List[Position],
    nourritures: set[Position],
) -> List[List[Pixel]]:
    """
    Transforme l'état interne en grille de capteurs (signal).
    Important: aucune étiquette sémantique n'est exposée.
    """
    capteurs: List[List[Pixel]] = [[PIXEL_SOL for _ in range(largeur)] for _ in range(hauteur)]

    # murs (bordures)
    for x in range(largeur):
        capteurs[0][x] = PIXEL_MUR
        capteurs[hauteur - 1][x] = PIXEL_MUR
    for y in range(hauteur):
        capteurs[y][0] = PIXEL_MUR
        capteurs[y][largeur - 1] = PIXEL_MUR

    # nourriture
    for (x, y) in nourritures:
        capteurs[y][x] = PIXEL_NOURRITURE

    # serpent
    for (x, y) in serpent[:-1]:
        capteurs[y][x] = PIXEL_CORPS
    hx, hy = serpent[-1]
    capteurs[hy][hx] = PIXEL_TETE

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
            if px == PIXEL_MUR:
                chars.append("#")
            elif px == PIXEL_NOURRITURE:
                chars.append("*")
            elif px == PIXEL_TETE:
                chars.append("O")
            elif px == PIXEL_CORPS:
                chars.append("o")
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
