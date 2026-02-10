from __future__ import annotations

from instrument.app.contrats import EtatMondeCanonique
from instrument.app.instruments import CameraEgocentreeV1
from world_sim.app.arenes_yaml import PALETTE_DEFAUT


def test_egocentree_depend_de_la_direction__doit_changer() -> None:
    """Test spécifique égocentré (RED).

    À état spatial identique, changer la direction de la tête doit changer
    la projection égocentrée (car 'avant'/'gauche'/'droite' changent).

    Tant que CameraEgocentreeV1 délègue à l'estrade, ce test doit ÉCHOUER.
    """

    cam = CameraEgocentreeV1(rayon=2, niveau_bruit=0, seed_bruit=1)

    base = EtatMondeCanonique(
        largeur=7,
        hauteur=7,
        serpent=[(3, 1), (3, 2), (3, 3)],  # tête=(3,3)
        direction="haut",
        nourritures={(4, 3)},  # à droite de la tête en repère absolu
        porte=None,
        porte_ouverte=False,
        palette=PALETTE_DEFAUT,
    )

    obs_haut = cam.observer(base)

    base_droite = EtatMondeCanonique(
        **{**base.__dict__, "direction": "droite"}
    )
    obs_droite = cam.observer(base_droite)

    assert obs_haut.pixels != obs_droite.pixels
