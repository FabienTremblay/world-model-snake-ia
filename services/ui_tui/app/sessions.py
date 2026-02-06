from __future__ import annotations

import os
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from agent_service.app.main import lancer_spectateur
from runner.app.main import boucle_episodes
from runner.app.replay import boucle_replay

from ui_tui.app.contrats import SourceEpisode

@dataclass
class SessionConfig:
    delai_s: float = 0.05
    demarrer_en_pause: bool = False
    niveau_bruit: int = 0
    boucle_infinie: bool = True

class SourceLive:
    def __init__(self, bus: BusEtatMemoire, controle: ControleExecution) -> None:
        self.bus = bus
        self.controle = controle
        self._thread: Optional[threading.Thread] = None
        self._erreur: Optional[str] = None

    def start(self) -> None:
        lancer_spectateur(self.bus)
        def _run() -> None:
            try:
                boucle_episodes(self.bus, self.controle)
            except Exception:
                self._erreur = traceback.format_exc()

                # 1) écrire dans /tmp (toujours dispo)
                try:
                    Path("/tmp/ui_tui_runner_error.txt").write_text(self._erreur, encoding="utf-8")
                except Exception:
                    pass

                # 2) écrire dans le run dir si on le connaît via le journal
                try:
                    jp = os.getenv("SNAKE_JOURNAL_PATH")
                    if jp:
                        run_dir = Path(jp).resolve().parent
                        (run_dir / "runner_error.txt").write_text(self._erreur, encoding="utf-8")
                except Exception:
                    pass
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def etat_courant(self) -> Any:
        return self.bus.dernier()

    def peut_avancer(self) -> bool:
        return True

    def avancer(self, action: Optional[Any] = None) -> None:
        # Le monde avance via le runner; l'action (humaine) passe par ControleExecution.
        return

    def journal_recent(self, n: int = 8) -> list[Any]:
        return []

    def erreur(self) -> Optional[str]:
        return self._erreur

    def stop(self) -> None:
        return

class SourceReplay:
    def __init__(self, bus: BusEtatMemoire, controle: ControleExecution, journal_path: Path, racine_projet: Path) -> None:
        self.bus = bus
        self.controle = controle
        self.journal_path = journal_path
        self.racine_projet = racine_projet
        self._thread: Optional[threading.Thread] = None
        self._erreur: Optional[str] = None

    def start(self) -> None:
        lancer_spectateur(self.bus)

        def _run() -> None:
            try:
                boucle_replay(
                    self.bus,
                    self.controle,
                    self.journal_path,
                    self.racine_projet,
                    boucle_infinie=True,
                )
            except Exception:
                self._erreur = traceback.format_exc()

                # 1) écrire dans /tmp (toujours dispo)
                try:
                    Path("/tmp/ui_tui_runner_error.txt").write_text(self._erreur, encoding="utf-8")
                except Exception:
                    pass

                # 2) écrire dans le run dir si on le connaît via le journal
                try:
                    jp = os.getenv("SNAKE_JOURNAL_PATH")
                    if jp:
                        run_dir = Path(jp).resolve().parent
                        (run_dir / "runner_error.txt").write_text(self._erreur, encoding="utf-8")
                except Exception:
                    pass

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()


    def etat_courant(self) -> Any:
        return self.bus.dernier()

    def peut_avancer(self) -> bool:
        return True

    def avancer(self, action: Optional[Any] = None) -> None:
        return

    def journal_recent(self, n: int = 8) -> list[Any]:
        return []

    def stop(self) -> None:
        return

    def erreur(self) -> Optional[str]:
        return self._erreur

def construire_source(mode: str, journal_path: Optional[Path] = None) -> tuple[SourceEpisode, BusEtatMemoire, ControleExecution]:
    bus = BusEtatMemoire()

    if mode == "replay":
        controle = ControleExecution(delai_s=0.15, demarrer_en_pause=True, niveau_bruit=0)
        racine_projet = Path(__file__).resolve().parents[3]
        if journal_path is None:
            j_env = os.getenv("SNAKE_JOURNAL_PATH", "").strip()
            if j_env:
                journal_path = Path(j_env)
            else:
                journal_path = racine_projet / "artefacts" / "episodes.jsonl"
        src = SourceReplay(bus, controle, journal_path=journal_path, racine_projet=racine_projet)
        src.start()
        return src, bus, controle

    controle = ControleExecution(delai_s=float(os.getenv("SNAKE_TUI_DELai", "0.05")))
    src = SourceLive(bus, controle)
    src.start()
    return src, bus, controle
