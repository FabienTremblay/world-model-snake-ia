# services/agent_service/tests/test_modele_monde_tabulaire_v1.py
from __future__ import annotations

from agent_service.app.modele_monde.tabulaire_v1 import ModeleMondeTabulaireV1


def test_tabulaire_apprend_et_predire() -> None:
    m = ModeleMondeTabulaireV1()
    # 3 exemples identiques + 1 différent
    for _ in range(3):
        m.apprendre_transition(10, "droite", 11)
    m.apprendre_transition(10, "droite", 12)

    pred = m.predire(10, "droite")
    assert pred.etat_suivant == 11
    assert pred.support == 4
    assert 0.74 < pred.confiance < 0.76  # 3/4
    assert pred.entropie > 0.0  # 2 successeurs possibles

def test_tabulaire_inconnu() -> None:
    m = ModeleMondeTabulaireV1()
    pred = m.predire(999, "haut")
    assert pred.etat_suivant is None
    assert pred.support == 0
    assert pred.confiance == 0.0
    assert pred.entropie == 0.0
