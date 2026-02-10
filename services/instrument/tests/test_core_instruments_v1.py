from __future__ import annotations

from instrument.app.contrats import ObservationPixels, ObservationDonnees


def test_core_observer_retourne_payload_et_meta(instruments_core, etat_simple) -> None:
    for inst in instruments_core:
        obs = inst.observer(etat_simple)

        assert hasattr(obs, "meta")
        assert obs.meta["instrument_id"] == inst.instrument_id

        # nature du payload
        if isinstance(obs, ObservationPixels):
            assert obs.pixels is not None
            assert len(obs.pixels) > 0
            assert len(obs.pixels[0]) > 0
        elif isinstance(obs, ObservationDonnees):
            assert obs.donnees is not None
            assert isinstance(obs.donnees, dict)
        else:
            raise AssertionError(f"Type d'observation inattendu: {type(obs)!r}")


def test_core_determinisme_si_pas_de_bruit(instruments_core, etat_simple) -> None:
    """Même état + instruments déterministes => même observation.

    Note: pour les caméras, le bruit doit être à 0 (fixture instruments_core).
    """
    for inst in instruments_core:
        obs1 = inst.observer(etat_simple)
        obs2 = inst.observer(etat_simple)

        if isinstance(obs1, ObservationPixels):
            assert obs1.pixels == obs2.pixels
        else:
            assert obs1.donnees == obs2.donnees
