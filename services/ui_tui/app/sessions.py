from __future__ import annotations

import os
import time
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from commun.contrats import Observation
from agent_service.app.main import lancer_spectateur
from runner.app.main import boucle_episodes
from runner.app.replay_api import Replay
from runner.app.replay import decoder_capteurs_b64, _rendre_debug_depuis_capteurs, _lire_jsonl
from runner.app.replay_index import StatEpisode

from ui_tui.app.contrats import SourceEpisode


@dataclass
class ReplaySession:
    """Source de vérité unique pour le replay côté TUI.

    Invariant: le TUI ne lit jamais le journal brut ailleurs que dans `SourceReplay`.
    """

    journal_path: Path
    run_id_filtre: Optional[str]
    replay: Replay
    stats_episodes: dict[int, StatEpisode]

    def nouveau_replay_ui(self) -> Replay:
        """Retourne une instance Replay indépendante (UI).

        `Replay` garde un état interne (episode_id courant). Le thread de replay
        (runner) utilise aussi une instance `Replay`. Pour éviter les races,
        l'UI utilise une instance distincte qui pointe sur les mêmes lignes.
        """
        return Replay(self.replay.lignes, run_id=self.run_id_filtre)

    @property
    def episodes_ids(self) -> list[int]:
        return sorted(self.stats_episodes.keys())



# --- Formatage actions (contrat) ------------------------------------------------

_ACTIONS_SUPPORTEES_TUI = {
    "avant",
    "observer_gauche",
    "observer_droite",
}

def _formatter_action_pour_tui(*, tick: int, action: Any) -> str:
    """Rend l'action conforme au contrat de journalisation.

    - tick 0: snapshot initial -> (snapshot) si action absente/null
    - action inconnue: "non supportée:<action>"
    """
    try:
        tick_i = int(tick)
    except Exception:
        tick_i = 0

    if tick_i == 0 and (action is None or str(action).strip() == ""):
        return "(snapshot)"

    if action is None:
        return ""

    a = str(action).strip()
    if not a:
        return ""

    if a in _ACTIONS_SUPPORTEES_TUI:
        return a

    return f"non supportée:{a}"

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


    # --- API UI: orientation -------------------------------------------------

    def direction_pour(self, *, episode_id: int, tick: int) -> Optional[str]:
        """Retourne une direction exploitable pour le rendu orienté (REPLAY).

        On ne touche pas aux capteurs. En mode replay, la seule source stable
        et non-heuristique est l'événement du journal pour (episode_id, tick).

        Convention: si `action` vaut une direction cardinale (haut/bas/gauche/droite),
        on peut l'utiliser comme direction courante pour l'affichage.

        Si la direction est absente/inconnue, retourne None.
        """
        try:
            eid = int(episode_id)
            tk = int(tick)
        except Exception:
            return None

        tick_map = self._tick_map_par_episode.get(eid) or {}
        evt = tick_map.get(tk) or {}
        d = (evt.get("action") or "").strip()
        if d in {"haut", "bas", "gauche", "droite"}:
            return d
        return None

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
        self._replay_session: Optional[ReplaySession] = None

        # Cache UI (mini-journal) : événements par épisode pour accès rapide.
        self._evenements_par_episode: dict[int, list[dict]] = {}
        self._tick_map_par_episode: dict[int, dict[int, dict]] = {}
        self._direction_map_par_episode: dict[int, dict[int, str]] = {}


        # Charger/indexer le journal UNE SEULE FOIS, ici.
        # L'UI s'appuie ensuite sur `replay_session.stats_episodes`.
        try:
            if self.journal_path.exists():
                lignes = list(_lire_jsonl(self.journal_path))
                run_id = os.getenv("SNAKE_RUN_ID", "").strip() or None
                rep = Replay(lignes, run_id=run_id)
                stats = rep.episodes() or {}
                self._replay_session = ReplaySession(
                    journal_path=self.journal_path,
                    run_id_filtre=run_id,
                    replay=rep,
                    stats_episodes=stats,
                )
        except Exception:
            # On laisse start() écrire le détail si nécessaire.
            self._replay_session = None

        # Construire les caches si on a pu charger le replay (même filtré par run_id).
        try:
            if self._replay_session is not None:
                run_id_filtre = self._replay_session.run_id_filtre
                for evt in self._replay_session.replay.lignes:
                    try:
                        eid = int(evt.get("episode_id", 0))
                    except Exception:
                        continue
                    if run_id_filtre is not None and str(evt.get("run_id", "")) != str(run_id_filtre):
                        continue
                    self._evenements_par_episode.setdefault(eid, []).append(evt)
                for eid, evts in self._evenements_par_episode.items():
                    m: dict[int, dict] = {}
                    for e in evts:
                        try:
                            tk = int(e.get("tick", 0) or 0)
                        except Exception:
                            continue
                        m[tk] = e
                    self._tick_map_par_episode[eid] = m
                # Calcul direction (UI) : déterministe, basé sur les actions, sans capteurs.
                for eid in self._tick_map_par_episode.keys():
                    self._direction_map_par_episode[eid] = self._calculer_directions_episode(eid)
        except Exception:
            # Cache non critique: ignorer
            pass

    def _calculer_directions_episode(self, episode_id: int) -> dict[int, str]:
        """Reconstruit direction(tick) à partir des actions du journal.

        - Purement UI (rendu orienté), sans toucher aux capteurs.
        - Déterministe, sans heuristique fragile.
        - Convention alignée sur MondeSnake:
            - direction initiale = "droite"
            - "observer_gauche"/"observer_droite" => tourne relatif sans avancer
            - "avant" => ne change pas la direction
            - "haut/bas/gauche/droite" => direction absolue (pas de demi-tour), puis avance
        """
        ordre = ["haut", "droite", "bas", "gauche"]

        def opposée(d1: str, d2: str) -> bool:
            return (d1 == "haut" and d2 == "bas") or (d1 == "bas" and d2 == "haut") or (d1 == "gauche" and d2 == "droite") or (d1 == "droite" and d2 == "gauche")

        def tourner_rel(dir_courante: str, sens: str) -> str:
            if dir_courante not in ordre:
                return dir_courante
            i = ordre.index(dir_courante)
            if sens == "gauche":
                return ordre[(i - 1) % 4]
            if sens == "droite":
                return ordre[(i + 1) % 4]
            return dir_courante

        ticks = sorted((self._tick_map_par_episode.get(int(episode_id)) or {}).keys())
        direction = "droite"
        out: dict[int, str] = {}
        for tk in ticks:
            evt = (self._tick_map_par_episode.get(int(episode_id)) or {}).get(tk) or {}
            action = (evt.get("action") or "").strip()
            if tk == 0:
                out[tk] = direction
                continue
            if action in {"observer_gauche", "observer_droite", "tourner_gauche", "tourner_droite"}:
                sens = "gauche" if action.endswith("gauche") else "droite"
                direction = tourner_rel(direction, sens)
            elif action in {"gauche", "droite"}:
                # legacy: tourner + avancer => tourne relatif
                direction = tourner_rel(direction, action)
            elif action in {"haut", "bas", "gauche", "droite"}:
                # absolu, pas de demi-tour
                if not opposée(action, direction):
                    direction = action
            # "avant" ou inconnue => direction inchangée
            out[tk] = direction
        return out

    @property
    def replay_session(self) -> Optional[ReplaySession]:
        return self._replay_session

    def direction_pour(self, *, episode_id: int, tick: int) -> Optional[str]:
        """Direction reconstruite pour le rendu orienté (REPLAY)."""
        try:
            eid = int(episode_id)
            tk = int(tick)
        except Exception:
            return None
        m = self._direction_map_par_episode.get(eid)
        if not m:
            return None
        return m.get(tk)

    def direction_pour(self, *, episode_id: int, tick: int) -> Optional[str]:
        """Retourne une direction exploitable pour le rendu orienté (REPLAY).

        Purement pour l'UI: on ne touche pas aux capteurs, et on n'infère rien.
        Source: événement du journal indexé (episode_id, tick).

        Convention minimale: si `action` vaut une direction cardinale (haut/bas/gauche/droite),
        on la considère comme direction courante affichable.
        Sinon -> None.
        """
        try:
            eid = int(episode_id)
            tk = int(tick)
        except Exception:
            return None

        tick_map = self._tick_map_par_episode.get(eid) or {}
        evt = tick_map.get(tk) or {}
        action = (evt.get("action") or "").strip()

        if action in {"haut", "bas", "gauche", "droite"}:
            return action
        return None

    def start(self) -> None:
        lancer_spectateur(self.bus)

        def _run() -> None:
            try:
                if self._replay_session is None:
                    raise RuntimeError(f"ReplaySession absente (journal={self.journal_path})")

                rep = self._replay_session.replay
                episodes = self._replay_session.stats_episodes or {}

                # épisode initial: env SNAKE_EPISODE ou 1er épisode disponible
                env_ep = os.getenv("SNAKE_EPISODE", "").strip()
                if env_ep.isdigit():
                    episode_courant = int(env_ep)
                else:
                    episode_courant = sorted(episodes.keys())[0] if episodes else 0

                while True:
                    # bascule d'épisode demandée par l'UI ?
                    demande = self.controle.consommer_episode()
                    if demande is not None:
                        episode_courant = int(demande)

                    rep.charger_episode(episode_courant)
                    idx_frame = 0

                    # Si on casse la boucle des ticks (reset / changement d'épisode),
                    # on doit redémarrer immédiatement le replay. Sinon on tombe
                    # dans la boucle "attendre reset" et l'UI paraît figée.
                    redemarrer = False

                    for evt in rep.ticks():
                        # reset ou changement d'épisode ?
                        if self.controle.consommer_reset():
                            redemarrer = True
                            break
                        demande = self.controle.consommer_episode()
                        if demande is not None:
                            episode_courant = int(demande)
                            redemarrer = True
                            break

                        # Publier 1re frame immédiatement, puis obéir au contrôle (pause/step).
                        if idx_frame > 0:
                            self.controle.attendre_autorisation()
                            if self.controle.consommer_reset():
                                redemarrer = True
                                break
                            demande = self.controle.consommer_episode()
                            if demande is not None:
                                episode_courant = int(demande)
                                redemarrer = True
                                break

                        largeur = int(evt.get("largeur", 0) or 0)
                        hauteur = int(evt.get("hauteur", 0) or 0)
                        capteurs_b64 = evt.get("capteurs_compact") or evt.get("capteurs_b64") or evt.get("capteurs")
                        capteurs = decoder_capteurs_b64(capteurs_b64, largeur=largeur, hauteur=hauteur)
                        rendu_debug = _rendre_debug_depuis_capteurs(capteurs)

                        obs = Observation(
                            run_id=str(evt.get("run_id") or f"replay:{self.journal_path.name}"),
                            episode_id=int(evt.get("episode_id", episode_courant)),
                            tick=int(evt.get("tick", idx_frame)),
                            capteurs=capteurs,
                            rendu_debug=rendu_debug,
                            mesure_bruit=f"REPLAY file={self.journal_path.name} episode={episode_courant} frame={idx_frame} action={evt.get('action')}",
                            score=int(evt.get("score", 0) or 0),
                            longueur=int(evt.get("longueur", 0) or 0),
                            termine=bool(evt.get("termine", False)),
                            raison_fin=evt.get("raison_fin"),
                        )
                        self.bus.publier(obs)
                        idx_frame += 1

                        if not self.controle.est_en_pause():
                            time.sleep(self.controle.delai_s())

                    # Si on a demandé un reset ou un changement d'épisode,
                    # on relance immédiatement (recharger épisode + publier frame 0).
                    if redemarrer:
                        continue

                    # fin d'épisode/fichier: attendre reset / changement épisode
                    while True:
                        if self.controle.consommer_reset():
                            break
                        demande = self.controle.consommer_episode()
                        if demande is not None:
                            episode_courant = int(demande)
                            break
                        time.sleep(0.05)

            except Exception:
                self._erreur = traceback.format_exc()

                try:
                    Path("/tmp/ui_tui_runner_error.txt").write_text(self._erreur, encoding="utf-8")
                except Exception:
                    pass

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
        """Mini-journal autour du tick courant (replay).

        Source de vérité: ReplaySession (lignes déjà chargées) + caches locaux.
        """
        if self._replay_session is None:
            return ["(journal) indisponible"]

        dernier = None
        try:
            dernier = self.bus.dernier()
        except Exception:
            dernier = None

        if dernier is None:
            return ["(journal) en attente…"]

        try:
            eid = int(getattr(dernier, "episode_id", 0) or 0)
        except Exception:
            eid = 0
        try:
            tk_courant = int(getattr(dernier, "tick", 0) or 0)
        except Exception:
            tk_courant = 0

        evts = self._evenements_par_episode.get(eid) or []
        tick_map = self._tick_map_par_episode.get(eid) or {}

        if not evts:
            return [f"(journal) épisode {eid} vide"]

        # Fenêtre centrée (tick-3..tick+3), bornée aux ticks existants.
        ticks_dispos = sorted(tick_map.keys())
        if not ticks_dispos:
            return [f"(journal) épisode {eid} sans ticks"]

        # Choisir la fenêtre par indices (évite de supposer des ticks continus).
        # Trouver l'index du tick courant (ou le plus proche inférieur).
        idx_c = 0
        for i, tk in enumerate(ticks_dispos):
            if tk <= tk_courant:
                idx_c = i
            else:
                break

        demi = max(1, int(n) // 2)
        debut = max(0, idx_c - demi)
        fin = min(len(ticks_dispos), idx_c + demi + 1)
        fenetre = ticks_dispos[debut:fin]

        lignes: list[str] = []
        for tk in fenetre:
            e = tick_map.get(tk) or {}
            action_txt = _formatter_action_pour_tui(tick=int(tk), action=e.get("action"))
            sel = "→" if int(tk) == int(tk_courant) else " "
            score = int(e.get("score", 0) or 0)
            longu = int(e.get("longueur", 0) or 0)
            term = bool(e.get("termine", False))
            lignes.append(f"{sel} t={int(tk):04d}  {action_txt:<20}  score={score:<3d} long={longu:<3d} term={str(term):<5}")

        return lignes

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


# --- Compat UI_TUI ---
def demarrer_session(mode: str, journal_path: Optional[Path] = None):
    """Démarre une session LIVE ou REPLAY.

    Compatibilité: certains écrans importent `demarrer_session`.
    """
    return construire_source(mode=mode, journal_path=journal_path)
