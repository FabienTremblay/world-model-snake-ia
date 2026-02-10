# services/commun/controle.py
from __future__ import annotations

import threading
from typing import Optional


class ControleExecution:
    """
    Contrôle simple pour runner:
    - pause/reprise
    - step manuel (quand en pause)
    - vitesse (delai en secondes)
    """

    def __init__(self, delai_s: float = 0.05, demarrer_en_pause: bool = False, niveau_bruit: int = 0) -> None:
        self._pause = threading.Event()
        if demarrer_en_pause:
            self._pause.set()
        else:
            self._pause.clear()  # non en pause
        self._step = threading.Event()
        self._lock = threading.Lock()
        self._delai_s = delai_s
        self._reset = threading.Event()
        self._bruit_lock = threading.Lock()
        self._niveau_bruit = max(0, min(40, int(niveau_bruit)))
        self._replay_lock = threading.Lock()
        self._replay_slot: Optional[int] = None
        self._direction_lock = threading.Lock()
        self._direction: Optional[str] = None  # "haut"|"bas"|"gauche"|"droite"
        self._episode_lock = threading.Lock()
        self._episode_demande: Optional[int] = None  # episode_id demandé (replay)

    def est_en_pause(self) -> bool:
        return self._pause.is_set()

    def basculer_pause(self) -> None:
        if self._pause.is_set():
            self._pause.clear()
            # En sortie de pause, libère immédiatement tout thread bloqué
            # dans attendre_autorisation() (qui attend sur _step).
            # Sans ça, l'UI peut "unpause" mais le runner reste bloqué
            # jusqu'à un step explicite.
            self._step.set()
        else:
            self._pause.set()

    def demander_step(self) -> None:
        # Step n'a un sens que si en pause.
        if self._pause.is_set():
            self._step.set()

    def attendre_autorisation(self) -> None:
        """
        Bloque si en pause jusqu'à un step.
        Si pas en pause, ne bloque pas.
        """
        if not self._pause.is_set():
            return
        self._step.wait()
        self._step.clear()

    def delai_s(self) -> float:
        with self._lock:
            return self._delai_s

    def ajuster_delai(self, delta_s: float) -> None:
        with self._lock:
            self._delai_s = max(0.0, min(1.0, self._delai_s + delta_s))

    def demander_reset(self) -> None:
        # Le runner peut être bloqué dans attendre_autorisation() (pause).
        # On réveille donc l'attente de step afin que le reset soit appliqué
        # immédiatement (sinon l'UI donne l'impression que 'r' ne fonctionne
        # qu'"plus tard").
        self._reset.set()
        self._step.set()

    def consommer_reset(self) -> bool:
        """
        Retourne True si un reset a été demandé (et le consomme).
        """
        if self._reset.is_set():
            self._reset.clear()
            return True
        return False

    def niveau_bruit(self) -> int:
        with self._bruit_lock:
            return self._niveau_bruit

    def ajuster_bruit(self, delta: int) -> None:
        with self._bruit_lock:
            self._niveau_bruit = max(0, min(40, self._niveau_bruit + int(delta)))

    def demander_replay_slot(self, slot: int) -> None:
        """
        Demande de charger un autre replay (slot 10,20,...).
        Consommé par la boucle replay.
        """
        with self._replay_lock:
            self._replay_slot = int(slot)

    def consommer_replay_slot(self) -> Optional[int]:
        with self._replay_lock:
            slot = self._replay_slot
            self._replay_slot = None
            return slot

    def definir_direction(self, direction: str) -> None:
        """
        Dépose une direction (mode assisté).
        La direction sera consommée une fois par le runner (au prochain tick).
        """
        if direction not in {"haut", "bas", "gauche", "droite"}:
            return
        with self._direction_lock:
            self._direction = direction

    def consommer_direction(self) -> Optional[str]:
        """Retourne la dernière direction déposée et la vide (1-shot)."""
        with self._direction_lock:
            d = self._direction
            self._direction = None
            return d

    def demander_episode(self, episode_id: int) -> None:
        """Demande de basculer le replay vers un épisode (episode_id)."""
        with self._episode_lock:
            self._episode_demande = int(episode_id)
        # Même logique que demander_reset(): si le runner est bloqué en pause
        # en attendant un step, on doit le réveiller pour qu'il consomme la
        # demande d'épisode sans délai.
        self._step.set()

    def consommer_episode(self) -> Optional[int]:
        """Retourne l'episode_id demandé et le consomme."""
        with self._episode_lock:
            eid = self._episode_demande
            self._episode_demande = None
            return eid

 
