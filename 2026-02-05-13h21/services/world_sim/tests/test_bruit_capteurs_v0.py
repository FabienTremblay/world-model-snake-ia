# services/world_sim/tests/test_bruit_capteurs_v0.py
from __future__ import annotations

import random

from world_sim.app.arenes_yaml import PALETTE_DEFAUT
from world_sim.app.projection_capteurs import appliquer_bruit, projeter_capteurs


def _grille_base() -> list[list]:
    largeur, hauteur = 9, 6
    serpent = [(4, 3)]
    nourritures = {(6, 2)}
    porte = (2, 2)

    return projeter_capteurs(
        largeur=largeur,
        hauteur=hauteur,
        serpent=serpent,
        nourritures=nourritures,
        palette=PALETTE_DEFAUT,
        porte=porte,
        porte_ouverte=False,
    )


def test_appliquer_bruit_niveau_0_pas_de_changement() -> None:
    capteurs = _grille_base()
    rng = random.Random(12345)

    capteurs_bruit = appliquer_bruit(capteurs, niveau_bruit=0, rng=rng)
    assert capteurs_bruit == capteurs


def test_appliquer_bruit_niveau_n_change_pixels_mais_reste_dans_domaines() -> None:
    capteurs = _grille_base()

    a_change = False

    for niveau in (1, 2, 3):
        # RNG injecté => test déterministe
        rng = random.Random(12345 + niveau)
        capteurs_bruit = appliquer_bruit(capteurs, niveau_bruit=niveau, rng=rng)

        if capteurs_bruit != capteurs:
            a_change = True

        for ligne in capteurs_bruit:
            for px in ligne:
                # bornes conservatrices (selon Pixel: teinte/intensité en int)
                assert 0 <= px.teinte <= 65535
                assert 0 <= px.intensite <= 255
                assert 0 <= px.motif <= 255
                assert 0 <= px.clignote <= 255

    assert a_change, "avec bruit 1..3, on s'attend à ce qu'au moins un pixel change"

