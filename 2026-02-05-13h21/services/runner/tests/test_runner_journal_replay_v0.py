# services/runner/tests/test_runner_journal_replay_v0.py
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from commun.contrats import Pixel
from runner.app.journal import JournalEpisodes, encoder_capteurs_b64
from runner.app.replay import boucle_replay, decoder_capteurs_b64
from runner.app.replay_catalogue import CatalogueReplays


def _capteurs_exemple(w: int = 4, h: int = 3) -> list[list[Pixel]]:
    # teinte dans 0..359, motif 0..7, clignote 0/1 (compat v1)
    capteurs: list[list[Pixel]] = []
    for y in range(h):
        row: list[Pixel] = []
        for x in range(w):
            row.append(Pixel(teinte=(10 + x + y) % 360, intensite=50 + x, motif=(x % 7), clignote=(y % 2)))
        capteurs.append(row)
    return capteurs


def _lire_jsonl(path: Path) -> list[dict]:
    lignes: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        lignes.append(json.loads(line))
    return lignes


def test_journal_ecrit_jsonl(tmp_path, monkeypatch) -> None:
    # écrire dans tmp_path, pas dans artefacts/
    journal_path = tmp_path / "episodes.jsonl"
    monkeypatch.setenv("SNAKE_JOURNAL", "1")
    monkeypatch.setenv("SNAKE_JOURNAL_PATH", str(journal_path))

    j = JournalEpisodes(racine_projet=tmp_path)

    capteurs = _capteurs_exemple(5, 4)

    for tick in range(3):
        j.ecrire_tick(
            run_id="run-test",
            episode_id=1,
            tick=tick,
            arene_id="tiny_v0",
            seed=7,
            action_direction="droite",
            niveau_bruit=0,
            score=tick,
            longueur=3 + tick,
            termine=(tick == 2),
            raison_fin=("porte_fin" if tick == 2 else None),
            capteurs=capteurs,
        )

    j.fermer()

    assert journal_path.exists()
    lignes = _lire_jsonl(journal_path)
    assert len(lignes) == 3

    requis = {
        "ts_ns",
        "run_id",
        "episode_id",
        "tick",
        "action",
        "niveau_bruit",
        "score",
        "longueur",
        "termine",
        "raison_fin",
        "largeur",
        "hauteur",
        "format_capteurs",
        "capteurs_compact",
        # additifs attendus si fournis :
        "arene_id",
        "seed",
    }

    for i, evt in enumerate(lignes):
        assert requis.issubset(evt.keys())
        assert evt["run_id"] == "run-test"
        assert evt["episode_id"] == 1
        assert evt["tick"] == i
        assert evt["arene_id"] == "tiny_v0"
        assert evt["seed"] == 7
        assert evt["largeur"] == 5
        assert evt["hauteur"] == 4
        assert isinstance(evt["capteurs_compact"], str)
        assert "capteurs_b64_v1" in str(evt["format_capteurs"])

    assert lignes[-1]["termine"] is True
    assert lignes[-1]["raison_fin"] == "porte_fin"


def test_capteurs_compact_roundtrip() -> None:
    capteurs = _capteurs_exemple(6, 2)

    b64, w, h, fmt = encoder_capteurs_b64(capteurs)
    assert w == 6 and h == 2
    assert "capteurs_b64_v1" in fmt

    capteurs2 = decoder_capteurs_b64(b64, largeur=w, hauteur=h)
    assert capteurs2 == capteurs


def test_replay_lit_journal(tmp_path, monkeypatch) -> None:
    # produire un mini journal dans tmp
    journal_path = tmp_path / "episodes.jsonl"
    monkeypatch.setenv("SNAKE_JOURNAL", "1")
    monkeypatch.setenv("SNAKE_JOURNAL_PATH", str(journal_path))

    j = JournalEpisodes(racine_projet=tmp_path)
    capteurs = _capteurs_exemple(4, 3)

    for tick in range(3):
        j.ecrire_tick(
            run_id="run-replay",
            episode_id=1,
            tick=tick,
            arene_id="tiny_v0",
            seed=7,
            action_direction="droite",
            niveau_bruit=0,
            score=tick,
            longueur=3 + tick,
            termine=(tick == 2),
            raison_fin=("porte_fin" if tick == 2 else None),
            capteurs=capteurs,
        )
    j.fermer()

    bus = BusEtatMemoire(maxlen=100)
    controle = ControleExecution(delai_s=0.0, demarrer_en_pause=False, niveau_bruit=0)

    # Important: boucle_infinie=False pour terminer en fin de fichier
    boucle_replay(bus, controle, journal_path=journal_path, racine_projet=tmp_path, boucle_infinie=False)

    # On inspecte la file interne (bus utilitaire)
    toutes = list(bus._q)  # test-only
    assert len(toutes) >= 3

    # ticks cohérents et croissants
    ticks = [o.tick for o in toutes]
    assert ticks == sorted(ticks)
    assert ticks[0] == 0
    assert ticks[-1] == 2

    assert toutes[-1].termine is True
    assert toutes[-1].raison_fin == "porte_fin"
    assert toutes[-1].run_id == "run-replay"


def test_replay_catalogue_liste_archives(tmp_path) -> None:
    # On simule un root projet dans tmp_path
    racine = tmp_path
    cat = CatalogueReplays(racine)

    # Créer des faux journaux
    j10 = racine / "artefacts" / "replays" / "replay-0010.jsonl"
    j20 = racine / "artefacts" / "replays" / "replay-0020.jsonl"
    j10.parent.mkdir(parents=True, exist_ok=True)
    j10.write_text("{}", encoding="utf-8")
    j20.write_text("{}", encoding="utf-8")

    cat.enregistrer_slot(20, j20)
    cat.enregistrer_slot(10, j10)

    # resoudre fonctionne
    p10 = cat.resoudre(10)
    p20 = cat.resoudre(20)
    assert p10 is not None and p10.exists()
    assert p20 is not None and p20.exists()

    # manifest écrit, et les slots sont présents
    assert cat.manifest.exists()
    data = json.loads(cat.manifest.read_text(encoding="utf-8"))
    assert "slots" in data
    assert set(data["slots"].keys()) >= {"10", "20"}

    # "listing trié" (au sens: tri numérique stable des slots présents)
    slots_tries = sorted((int(k) for k in data["slots"].keys()))
    assert slots_tries[:2] == [10, 20]
