# services/ui_tui/tests/test_orientation_tete.py
from __future__ import annotations

from ui_tui.app.rendu_oriente import rendu_oriente_tete
from ui_tui.app.sessions import SourceReplay
from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution


def test_oriente_premier_O_selon_direction_fr() -> None:
    rendu = [
        ".....",
        "..O..",
        "..o..",
    ]
    assert rendu_oriente_tete(rendu, "haut")[1] == "..↑.."
    assert rendu_oriente_tete(rendu, "droite")[1] == "..→.."
    assert rendu_oriente_tete(rendu, "bas")[1] == "..↓.."
    assert rendu_oriente_tete(rendu, "gauche")[1] == "..←.."


def test_conserve_O_si_direction_absente_ou_inconnue() -> None:
    rendu = ["..O.."]
    assert rendu_oriente_tete(rendu, None) == rendu
    assert rendu_oriente_tete(rendu, "?") == rendu


def test_ne_remplace_que_le_premier_O() -> None:
    rendu = [
        "O...O",
        "..O..",
    ]
    out = rendu_oriente_tete(rendu, "droite")
    assert out[0] == "→...O"
    assert out[1] == "..O.."


def test_source_replay_direction_pour_depuis_action(tmp_path) -> None:
    # Journal minimal: actions du contrat (avant/observer_*), direction reconstruite.
    journal = tmp_path / "episodes.jsonl"
    journal.write_text(
        "\n".join(
            [
                # tick0 snapshot: direction initiale = "droite"
                '{"run_id":"r1","episode_id":0,"tick":0,"action":null,"largeur":1,"hauteur":1,"capteurs_compact":"AAAA"}',
                # tick1: avant => direction inchangée ("droite")
                '{"run_id":"r1","episode_id":0,"tick":1,"action":"avant","largeur":1,"hauteur":1,"capteurs_compact":"AAAA"}',
                # tick2: observer_gauche => tourne ("haut")
                '{"run_id":"r1","episode_id":0,"tick":2,"action":"observer_gauche","largeur":1,"hauteur":1,"capteurs_compact":"AAAA"}',
                # tick3: observer_droite => revient ("droite")
                '{"run_id":"r1","episode_id":0,"tick":3,"action":"observer_droite","largeur":1,"hauteur":1,"capteurs_compact":"AAAA"}',
                "",
            ]
        ),
        encoding="utf-8",
    )

    src = SourceReplay(BusEtatMemoire(), ControleExecution(), journal_path=journal, racine_projet=tmp_path)
    assert src.direction_pour(episode_id=0, tick=0) == "droite"
    assert src.direction_pour(episode_id=0, tick=1) == "droite"
    assert src.direction_pour(episode_id=0, tick=2) == "haut"
    assert src.direction_pour(episode_id=0, tick=3) == "droite"

