from __future__ import annotations

import pytest

from instrument.app.contrats import EtatMondeCanonique
from instrument.app.instruments import CameraEstradeAbsolueV1, CameraEgocentreeV1, InstrumentGPSV1
from world_sim.app.arenes_yaml import PALETTE_DEFAUT


@pytest.fixture()
def etat_simple() -> EtatMondeCanonique:
    # Monde minimal 5x5, serpent vertical, une nourriture. Murs implicites.
    return EtatMondeCanonique(
        largeur=5,
        hauteur=5,
        serpent=[(2, 2), (2, 3), (2, 4)],  # dernier = tête
        direction="haut",
        nourritures={(3, 2)},
        porte=None,
        porte_ouverte=False,
        palette=PALETTE_DEFAUT,
    )


@pytest.fixture()
def instruments_core():
    # Tous les instruments doivent respecter le CORE (forme, déterminisme sans bruit si applicable).
    return [
        CameraEstradeAbsolueV1(niveau_bruit=0, seed_bruit=1),
        CameraEgocentreeV1(rayon=2, niveau_bruit=0, seed_bruit=1),
        InstrumentGPSV1(),
    ]
