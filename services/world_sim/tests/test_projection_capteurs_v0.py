# services/world_sim/tests/test_projection_capteurs_v0.py
from __future__ import annotations

from commun.contrats import Pixel
from world_sim.app.arenes_yaml import PALETTE_DEFAUT
from world_sim.app.projection_capteurs import projeter_capteurs


def test_projection_bordure_murs() -> None:
    largeur, hauteur = 7, 5
    serpent = [(3, 2)]  # tête seule au centre
    nourritures: set[tuple[int, int]] = set()

    capteurs = projeter_capteurs(
        largeur=largeur,
        hauteur=hauteur,
        serpent=serpent,
        nourritures=nourritures,
        palette=PALETTE_DEFAUT,
        porte=None,
        porte_ouverte=False,
    )

    assert len(capteurs) == hauteur
    assert all(len(ligne) == largeur for ligne in capteurs)

    mur = PALETTE_DEFAUT.mur

    # bordures haut/bas
    for x in range(largeur):
        assert capteurs[0][x] == mur
        assert capteurs[hauteur - 1][x] == mur

    # bordures gauche/droite
    for y in range(hauteur):
        assert capteurs[y][0] == mur
        assert capteurs[y][largeur - 1] == mur

    # et une case intérieure de contrôle (sol attendu, sauf serpent)
    assert capteurs[1][1] in (PALETTE_DEFAUT.sol, PALETTE_DEFAUT.serpent_corps, PALETTE_DEFAUT.serpent_tete)


def test_projection_porte_ouverte_fermee() -> None:
    largeur, hauteur = 9, 6
    serpent = [(4, 3)]
    nourritures: set[tuple[int, int]] = set()
    porte = (2, 2)

    capteurs_fermee = projeter_capteurs(
        largeur=largeur,
        hauteur=hauteur,
        serpent=serpent,
        nourritures=nourritures,
        palette=PALETTE_DEFAUT,
        porte=porte,
        porte_ouverte=False,
    )
    capteurs_ouverte = projeter_capteurs(
        largeur=largeur,
        hauteur=hauteur,
        serpent=serpent,
        nourritures=nourritures,
        palette=PALETTE_DEFAUT,
        porte=porte,
        porte_ouverte=True,
    )

    x, y = porte
    px_fermee: Pixel = capteurs_fermee[y][x]
    px_ouverte: Pixel = capteurs_ouverte[y][x]

    assert px_fermee == PALETTE_DEFAUT.porte_fermee
    assert px_ouverte == PALETTE_DEFAUT.porte_ouverte
    assert px_fermee != px_ouverte
