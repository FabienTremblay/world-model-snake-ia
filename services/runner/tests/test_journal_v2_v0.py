from __future__ import annotations

import json
from pathlib import Path

from commun.contrats import Pixel

from instrument.app.contrats import EtatMondeCanonique, ObservationDonnees, ObservationPixels
from runner.app.journal_v2 import JournalV2Writer
from world_sim.app.arenes_yaml import PALETTE_DEFAUT


def _grille(w: int, h: int) -> list[list[Pixel]]:
    return [[PALETTE_DEFAUT.sol for _ in range(w)] for _ in range(h)]


def test_journal_v2_ecrit_meta_et_jsonl_et_payloads(tmp_path: Path) -> None:
    # Simule un "root" de projet
    racine = tmp_path
    run_id = "r_test"

    j = JournalV2Writer(
        racine,
        run_id=run_id,
        meta={"exemple": True},
    )

    etat = EtatMondeCanonique(
        largeur=7,
        hauteur=7,
        serpent=[(1, 1), (1, 2)],
        nourritures={(3, 3)},
        porte=None,
        porte_ouverte=False,
        direction="haut",
        palette=PALETTE_DEFAUT,
    )

    obs = {
        "camera": ObservationPixels(pixels=_grille(3, 3), meta={"rayon": 1}),
        "gps": ObservationDonnees(donnees={"x": 1, "y": 2}, meta={}),
    }

    j.ecrire_tick(
        episode_id=0,
        tick=0,
        arene_id="demo_v0",
        seed=123,
        agent_id="aleatoire",
        incarnation_id=None,
        action=None,
        niveau_bruit=0,
        etat=etat,
        score=0,
        longueur=2,
        termine=False,
        raison_fin=None,
        observations=obs,
    )
    j.fermer()

    run_dir = racine / "artefacts" / "runs" / run_id
    assert (run_dir / "meta.json").exists()
    assert (run_dir / "journal.jsonl").exists()

    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["version"] == "journal_v2"

    lignes = (run_dir / "journal.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lignes) == 1

    tick = json.loads(lignes[0])
    assert tick["version"] == "journal_v2"
    assert tick["perception"]["instruments"]["gps"]["type"] == "donnees"
    assert tick["perception"]["instruments"]["camera"]["type"] == "pixels_npz"

    rel = tick["perception"]["instruments"]["camera"]["payload_ref"]
    assert (run_dir / rel).exists()
