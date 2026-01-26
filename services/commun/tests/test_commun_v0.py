# services/commun/tests/test_commun_v0.py
from __future__ import annotations

import dataclasses
import threading
import time

import pytest

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from commun.contrats import Observation, Pixel


def _pixel_encode_decode_existe() -> bool:
    # on supporte quelques conventions possibles, sans imposer une API
    return any(
        hasattr(Pixel, nom)
        for nom in ("to_dict", "from_dict", "encode", "decode", "to_json", "from_json")
    )


def test_pixel_serialize_deserialize() -> None:
    """
    Si Pixel expose un encode/décode (to_dict/from_dict, encode/decode, etc.),
    on vérifie le round-trip.
    Sinon, on skip (pas une erreur : c'est simplement non implémenté).
    """
    if not _pixel_encode_decode_existe():
        pytest.skip("Pixel n'expose pas d'API encode/decode (to_dict/from_dict/encode/decode/...)")

    p = Pixel(teinte=123, intensite=200, motif=3, clignote=1)

    if hasattr(Pixel, "to_dict") and hasattr(Pixel, "from_dict"):
        d = p.to_dict()  # type: ignore[attr-defined]
        p2 = Pixel.from_dict(d)  # type: ignore[attr-defined]
        assert p2 == p
        return

    if hasattr(Pixel, "encode") and hasattr(Pixel, "decode"):
        b = p.encode()  # type: ignore[attr-defined]
        p2 = Pixel.decode(b)  # type: ignore[attr-defined]
        assert p2 == p
        return

    if hasattr(Pixel, "to_json") and hasattr(Pixel, "from_json"):
        s = p.to_json()  # type: ignore[attr-defined]
        p2 = Pixel.from_json(s)  # type: ignore[attr-defined]
        assert p2 == p
        return

    pytest.fail("API de sérialisation détectée mais non reconnue par le test.")


def test_observation_dataclass_invariants() -> None:
    assert dataclasses.is_dataclass(Pixel)
    assert dataclasses.is_dataclass(Observation)

    # dataclass frozen (immutabilité)
    assert getattr(Pixel, "__dataclass_params__").frozen is True
    assert getattr(Observation, "__dataclass_params__").frozen is True

    # champs attendus (ordre stable = bon signal de contrat)
    champs = [f.name for f in dataclasses.fields(Observation)]
    assert champs == [
        "run_id",
        "episode_id",
        "tick",
        "capteurs",
        "rendu_debug",
        "mesure_bruit",
        "score",
        "longueur",
        "termine",
        "raison_fin",
    ]

    # valeur par défaut
    champ_raison = next(f for f in dataclasses.fields(Observation) if f.name == "raison_fin")
    assert champ_raison.default is None

    # instance valide minimale
    obs = Observation(
        run_id="r1",
        episode_id=1,
        tick=0,
        capteurs=[[Pixel(0, 0, 0, 0)]],
        rendu_debug=["#"],
        mesure_bruit=None,
        score=0,
        longueur=1,
        termine=False,
        raison_fin=None,
    )
    assert obs.termine is False
    assert obs.raison_fin is None


def test_bus_pub_sub() -> None:
    bus = BusEtatMemoire(maxlen=10)

    assert bus.dernier() is None
    assert bus.derniere_observation() is None  # compat

    obs1 = Observation(
        run_id="r1",
        episode_id=1,
        tick=1,
        capteurs=[[Pixel(1, 2, 3, 0)]],
        rendu_debug=["."],
        mesure_bruit=None,
        score=0,
        longueur=3,
        termine=False,
        raison_fin=None,
    )
    bus.publier(obs1)

    assert bus.dernier() == obs1
    assert bus.derniere_observation() == obs1

    obs2 = dataclasses.replace(obs1, tick=2)
    bus.publier(obs2)

    assert bus.dernier() == obs2


def test_controle_execution_pause_run_step() -> None:
    controle = ControleExecution(delai_s=0.01, demarrer_en_pause=True, niveau_bruit=0)
    assert controle.est_en_pause() is True

    # 1) en pause: attendre_autorisation doit BLOQUER jusqu'à step
    fini = threading.Event()

    def _attendre():
        controle.attendre_autorisation()
        fini.set()

    t = threading.Thread(target=_attendre, daemon=True)
    t.start()

    # on lui laisse un petit temps pour s'endormir sur wait()
    time.sleep(0.02)
    assert fini.is_set() is False  # toujours bloqué

    controle.demander_step()
    t.join(timeout=0.2)
    assert fini.is_set() is True  # débloqué par step

    # 2) toujours en pause: un nouvel attendre_autorisation rebloque
    fini2 = threading.Event()
    t2 = threading.Thread(target=lambda: (controle.attendre_autorisation(), fini2.set()), daemon=True)
    t2.start()
    time.sleep(0.02)
    assert fini2.is_set() is False

    # 3) passer en run: attendre_autorisation doit retourner immédiatement
    controle.basculer_pause()
    assert controle.est_en_pause() is False
    # maintenant, on ne devrait pas avoir besoin de step pour se débloquer
    t2.join(timeout=0.2)
    assert fini2.is_set() is True
