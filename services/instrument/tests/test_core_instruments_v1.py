from instrument.app.instruments.camera_estrade_absolue_v1 import CameraEstradeAbsolueV1


def test_core_observer_retourne_pixels_et_meta(etat_simple) -> None:
    inst = CameraEstradeAbsolueV1(niveau_bruit=0, seed_bruit=1)
    obs = inst.observer(etat_simple)

    assert obs.pixels is not None
    assert len(obs.pixels) == etat_simple.hauteur
    assert len(obs.pixels[0]) == etat_simple.largeur

    assert obs.meta["instrument_id"] == inst.instrument_id
    assert obs.meta["repere"] == "absolu"


def test_core_determinisme_si_pas_de_bruit(etat_simple) -> None:
    inst1 = CameraEstradeAbsolueV1(niveau_bruit=0, seed_bruit=999)
    inst2 = CameraEstradeAbsolueV1(niveau_bruit=0, seed_bruit=123)

    obs1 = inst1.observer(etat_simple)
    obs2 = inst2.observer(etat_simple)

    # même état + bruit=0 => pixels identiques
    assert obs1.pixels == obs2.pixels
