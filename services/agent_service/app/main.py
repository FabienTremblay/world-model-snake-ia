# services/agent_service/app/main.py
from __future__ import annotations

import threading
import time
from pathlib import Path

from commun.bus import BusEtatMemoire
from agent_service.app.spectateur import Spectateur


def _boucle_spectateur(bus: BusEtatMemoire, spectateur: Spectateur) -> None:
    """
    Boucle passive: on lit la dernière Observation du bus et on journalise.
    Déduplication basique par (episode_id, tick).
    """
    dernier_cle = None
    while True:
        obs = bus.dernier()
        if obs is not None:
            cle = (obs.run_id, obs.episode_id, obs.tick)
            if cle != dernier_cle:
                spectateur.traiter(obs)
                dernier_cle = cle
        time.sleep(0.01)


def lancer_spectateur(bus: BusEtatMemoire) -> None:
    racine_projet = Path(__file__).resolve().parents[3]
    spectateur = Spectateur(racine_projet)
    t = threading.Thread(target=_boucle_spectateur, args=(bus, spectateur), daemon=True)
    t.start()


def main() -> None:
    # IMPORTANT:
    # Ici, on ne crée pas le monde. On suppose que le process courant a déjà un bus en mémoire.
    # Ce main est surtout utile si tu l'intègres dans un même process (voir hook runner/ui).
    print("agent_service: spectateur prêt (à intégrer dans le process TUI/runner).")


if __name__ == "__main__":
    main()

