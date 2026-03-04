from __future__ import annotations

from agent_service.app.individu.charger_individu_v1 import calculer_hash_individu


def test_hash_individu_stable_sur_meme_dict():
    individu = {
        "schema": "individu_agent_arene_v1",
        "individu_id": "ia_x",
        "famille_id": "fa_x",
        "version": 1,
        "politique": {"direction": "avant"},
        "memoire_courte": {"compteur_runs": 0},
        "provenance": {"parent_hash": None},
    }

    h1 = calculer_hash_individu(individu)
    h2 = calculer_hash_individu(individu)
    assert h1 == h2
    assert len(h1) == 64
