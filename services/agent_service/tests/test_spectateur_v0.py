# services/agent_service/tests/test_spectateur_v0.py
from __future__ import annotations

import json
from pathlib import Path

from commun.contrats import Observation, Pixel
from agent_service.app.spectateur import Spectateur, _checksum_rapide, _stats_intensite


def _obs(
    *,
    racine: Path,
    run_id: str = "r1",
    episode_id: int = 1,
    tick: int = 0,
    capteurs: list[list[Pixel]],
    score: int = 0,
    longueur: int = 3,
    termine: bool = False,
    raison_fin: str | None = None,
    note: str | None = None,
) -> Observation:
    # Observation contract v1 (commun/contrats.py)
    return Observation(
        run_id=run_id,
        episode_id=episode_id,
        tick=tick,
        capteurs=capteurs,
        rendu_debug=["dev-only"],
        mesure_bruit=note,
        score=score,
        longueur=longueur,
        termine=termine,
        raison_fin=raison_fin,
    )


def _lire_jsonl(path: Path) -> list[dict]:
    lignes: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        lignes.append(json.loads(line))
    return lignes


def test_spectateur_calcule_stats() -> None:
    # grille 2x2, intensités : 10, 30, 50, 70 => mu=40
    # variance (population) = mean(x^2) - mu^2
    # mean(x^2)=(100+900+2500+4900)/4=2100
    # var=2100-1600=500
    # nonvide: motif!=0 -> on en met 2/4 => 0.5
    capteurs = [
        [Pixel(0, 10, 0, 0), Pixel(0, 30, 1, 0)],
        [Pixel(0, 50, 0, 0), Pixel(0, 70, 2, 1)],
    ]

    mu, var, prop = _stats_intensite(capteurs)

    assert mu == 40.0
    assert var == 500.0
    assert prop == 0.5


def test_spectateur_checksum_stable() -> None:
    capteurs1 = [
        [Pixel(10, 20, 0, 0), Pixel(11, 21, 1, 0)],
        [Pixel(12, 22, 0, 0), Pixel(13, 23, 2, 1)],
    ]
    capteurs2 = [
        [Pixel(10, 20, 0, 0), Pixel(11, 21, 1, 0)],
        [Pixel(12, 22, 0, 0), Pixel(13, 23, 2, 1)],
    ]
    capteurs3 = [
        [Pixel(10, 20, 0, 0), Pixel(11, 21, 1, 0)],
        [Pixel(12, 22, 0, 0), Pixel(99, 23, 2, 1)],  # teinte change => checksum change
    ]

    chk1 = _checksum_rapide(capteurs1)
    chk2 = _checksum_rapide(capteurs2)
    chk3 = _checksum_rapide(capteurs3)

    assert chk1 == chk2
    assert chk1 != chk3


def test_prediction_checksum_pred() -> None:
    # Baseline v0: prédire "checksum identique au précédent" (si pas rupture)
    capteurs_a = [[Pixel(10, 20, 1, 0)]]
    capteurs_b = [[Pixel(10, 21, 1, 0)]]  # change => checksum différent

    chk_a = _checksum_rapide(capteurs_a)
    chk_b = _checksum_rapide(capteurs_b)
    assert chk_a != chk_b

    # On passe par Spectateur.traiter() et on lit le JSONL (plus fidèle)
    # (tmp_path géré côté test ci-dessous)
    # Ici on valide la logique: tick 0 => pred=None ; tick 1 => pred=tick0
    # et err_pred = 0 si égal, 1 sinon.


def test_ecrit_spectateur_jsonl(tmp_path) -> None:
    spect = Spectateur(tmp_path)

    capteurs_a = [[Pixel(10, 20, 1, 0)]]
    capteurs_b = [[Pixel(10, 21, 1, 0)]]

    obs0 = _obs(
        racine=tmp_path,
        run_id="runX",
        episode_id=1,
        tick=0,
        capteurs=capteurs_a,
        score=0,
        longueur=3,
        termine=False,
        note="bruit: Δteinte≈0.0, Δint≈0.0",
    )
    obs1 = _obs(
        racine=tmp_path,
        run_id="runX",
        episode_id=1,
        tick=1,
        capteurs=capteurs_a,  # identique => err_pred attendu 0
        score=0,
        longueur=3,
        termine=False,
        note="bruit: Δteinte≈0.0, Δint≈0.0",
    )
    obs2 = _obs(
        racine=tmp_path,
        run_id="runX",
        episode_id=1,
        tick=2,
        capteurs=capteurs_b,  # différent => err_pred attendu 1
        score=1,
        longueur=4,
        termine=True,
        raison_fin="porte_fin",
        note="REPLAY tiny_v0",
    )

    spect.traiter(obs0)
    spect.traiter(obs1)
    spect.traiter(obs2)
    spect.fermer()

    path = tmp_path / "artefacts" / "spectateur.jsonl"
    assert path.exists()

    lignes = _lire_jsonl(path)
    assert len(lignes) == 3

    requis = {
        "ts_ns",
        "run_id",
        "episode_id",
        "tick",
        "score",
        "longueur",
        "termine",
        "raison_fin",
        "mu_int",
        "var_int",
        "prop_nonvide",
        "checksum",
        "checksum_pred",
        "err_pred",
        "rupture",
        "note",
    }
    for evt in lignes:
        assert requis.issubset(evt.keys())

    # tick0: pas de checksum_pred / err_pred
    assert lignes[0]["tick"] == 0
    assert lignes[0]["checksum_pred"] is None
    assert lignes[0]["err_pred"] is None
    assert lignes[0]["rupture"] is False

    # tick1: capteurs identiques => err_pred=0
    assert lignes[1]["tick"] == 1
    assert lignes[1]["checksum_pred"] == lignes[0]["checksum"]
    assert lignes[1]["err_pred"] == 0
    assert lignes[1]["rupture"] is False

    # tick2: capteurs changent => err_pred=1
    assert lignes[2]["tick"] == 2
    assert lignes[2]["checksum_pred"] == lignes[1]["checksum"]
    assert lignes[2]["err_pred"] == 1
    assert lignes[2]["termine"] is True
    assert lignes[2]["raison_fin"] == "porte_fin"
    assert isinstance(lignes[2]["note"], str)
