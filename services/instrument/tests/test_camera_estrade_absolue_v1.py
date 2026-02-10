from instrument.app.contrats import EtatMondeCanonique
from instrument.app.instruments.camera_estrade_absolue_v1 import CameraEstradeAbsolueV1


def test_invariance_par_rotation_sur_direction(etat_simple) -> None:
    inst = CameraEstradeAbsolueV1(niveau_bruit=0, seed_bruit=0)

    dirs = ["haut", "droite", "bas", "gauche"]
    pixels_ref = None

    for d in dirs:
        etat = EtatMondeCanonique(
            largeur=etat_simple.largeur,
            hauteur=etat_simple.hauteur,
            serpent=etat_simple.serpent,
            nourritures=etat_simple.nourritures,
            porte=etat_simple.porte,
            porte_ouverte=etat_simple.porte_ouverte,
            direction=d,
            palette=etat_simple.palette,
        )
        obs = inst.observer(etat)

        if pixels_ref is None:
            pixels_ref = obs.pixels
        else:
            assert obs.pixels == pixels_ref
