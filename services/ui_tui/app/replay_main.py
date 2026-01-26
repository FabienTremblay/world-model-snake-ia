# services/runner/ui_tui/app/replay_main.py
from __future__ import annotations

import os
import threading
from pathlib import Path

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from ui_tui.app.main import SnakeTui  # réutilise exactement le même TUI
from runner.app.replay import boucle_replay
from agent_service.app.main import lancer_spectateur


def main() -> None:
    bus = BusEtatMemoire()
    # replay: plus lent + démarre en pause
    controle = ControleExecution(delai_s=0.15, demarrer_en_pause=True, niveau_bruit=0)

    lancer_spectateur(bus)

    # par défaut: artefacts/episodes.jsonl à la racine projet
    racine_projet = Path(__file__).resolve().parents[3]
    journal_defaut = racine_projet / "artefacts" / "episodes.jsonl"
    journal_path = Path(os.getenv("SNAKE_JOURNAL_PATH", str(journal_defaut)))

    t = threading.Thread(
        target=boucle_replay,
        args=(bus, controle, journal_path, racine_projet),
        kwargs={"boucle_infinie": True},
        daemon=True,
    )
    t.start()

    app = SnakeTui(bus, controle)
    app.title = "SnakeTui — REPLAY"
    app.run()


if __name__ == "__main__":
    main()
