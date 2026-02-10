from __future__ import annotations

from instrument.app.instruments import InstrumentGPSV1


def test_gps_v1_retourne_position_tete(etat_simple) -> None:
    gps = InstrumentGPSV1()
    obs = gps.observer(etat_simple)

    assert obs.donnees["tete"] == (2, 4)
    assert obs.meta["instrument_id"] == "gps_v1"
    assert obs.meta["type"] == "donnees"
