from __future__ import annotations

from pathlib import Path

from agent_service.app.individu.charger_individu_v1 import calculer_hash_individu, appliquer_evolution_post_run


def test_evolution_post_run_cree_provenance_et_incremente_version(tmp_path: Path):
    entree = {
        "schema": "individu_agent_arene_v1",
        "individu_id": "ia_demo",
        "famille_id": "fa_demo",
        "version": 1,
        "politique": {"direction": "avant"},
        "memoire_courte": {"compteur_runs": 0},
        "provenance": {"parent_hash": None, "run_id": None},
    }

    parent_hash = calculer_hash_individu(entree)
    sortie = appliquer_evolution_post_run(entree, run_id="r1", run_dir=str(tmp_path), ticks=50)

    assert sortie["version"] == 2
    assert sortie["provenance"]["parent_hash"] == parent_hash
    assert sortie["memoire_courte"]["compteur_runs"] == 1
