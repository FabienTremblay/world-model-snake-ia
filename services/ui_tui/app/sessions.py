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
from commun.contrats import Observation, Pixel
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
    - action inconnue: "⚠ hors_norme:<action>" (tolérant, mais visible)
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
    return f"⚠ hors_norme:{a}"


def _inferer_version_evt(evt: dict) -> str:
    """Infère la version de journal à partir des clés présentes.

    Objectif: être tolérant (pas de champ version obligatoire), mais fournir un diagnostic.
    """
    if not isinstance(evt, dict):
        return "inconnu"
    # v2: structure canonique
    if isinstance(evt.get("monde_canonique"), dict) or isinstance(evt.get("decision"), dict) or isinstance(evt.get("perception"), dict):
        return "v2"
    # v1: capteurs b64 + dimensions
    if "capteurs_compact" in evt or "capteurs_b64" in evt or "format_capteurs" in evt or "largeur" in evt or "hauteur" in evt:
        return "v1"
    return "inconnu"


def _extraire_action_evt(evt: dict) -> Any:
    """Extrait l'action du tick, compat v1/v2.

    v1: evt["action"]
    v2: evt["decision"]["action"] (si présent)
    """
    if not isinstance(evt, dict):
        return None
    if "action" in evt:
        return evt.get("action")
    dec = evt.get("decision")
    if isinstance(dec, dict) and "action" in dec:
        return dec.get("action")
    return None

# --- Décodage journal v2 (Option A) -------------------------------------------

def _decoder_capteurs_npz(path_npz: Path) -> list[list[Pixel]]:
    """Charge un NPZ (teinte/intensite/motif/clignote) en grille de Pixel."""
    import numpy as np  # import local: dépendance déjà présente ailleurs (journal_v2)

    data = np.load(path_npz)
    teinte = data["teinte"]
    intensite = data["intensite"]
    motif = data["motif"]
    clignote = data["clignote"]

    h, w = int(teinte.shape[0]), int(teinte.shape[1])
    capteurs: list[list[Pixel]] = []
    for y in range(h):
        row: list[Pixel] = []
        for x in range(w):
            row.append(
                Pixel(
                    teinte=int(teinte[y, x]) % 360,
                    intensite=int(intensite[y, x]),
                    motif=int(motif[y, x]),
                    clignote=int(clignote[y, x]),
                )
            )
        capteurs.append(row)
    return capteurs


def _capteurs_synthetiques_depuis_monde_canonique(monde: dict) -> list[list[Pixel]]:
    """Fallback si aucune caméra n'est présente dans le journal v2.

    On reconstruit un 'capteur' minimal depuis monde_canonique.
    Hypothèse snake-centric:
      - murs = bordure
      - nourriture / serpent / porte projetés en motifs compatibles avec _rendre_debug_depuis_capteurs()
    """
    try:
        largeur = int(monde.get("largeur", 0) or 0)
        hauteur = int(monde.get("hauteur", 0) or 0)
    except Exception:
        largeur, hauteur = 0, 0

    if largeur <= 0 or hauteur <= 0:
        return []

    # helpers motifs (doivent matcher runner.app.replay._rendre_debug_depuis_capteurs)
    def px_vide():
        return Pixel(teinte=0, intensite=0, motif=0, clignote=0)

    grille = [[px_vide() for _ in range(largeur)] for _ in range(hauteur)]

    # bordure = mur
    for x in range(largeur):
        grille[0][x] = Pixel(teinte=0, intensite=255, motif=3, clignote=0)
        grille[hauteur - 1][x] = Pixel(teinte=0, intensite=255, motif=3, clignote=0)
    for y in range(hauteur):
        grille[y][0] = Pixel(teinte=0, intensite=255, motif=3, clignote=0)
        grille[y][largeur - 1] = Pixel(teinte=0, intensite=255, motif=3, clignote=0)

    # nourritures
    nourritures = monde.get("nourritures")
    if isinstance(nourritures, list):
        for pos in nourritures:
            if isinstance(pos, (list, tuple)) and len(pos) == 2:
                x, y = int(pos[0]), int(pos[1])
                if 0 <= x < largeur and 0 <= y < hauteur:
                    grille[y][x] = Pixel(teinte=120, intensite=255, motif=6, clignote=1)

    # serpent (corps ... tête)
    serpent = monde.get("serpent")
    if isinstance(serpent, list) and serpent:
        for i, pos in enumerate(serpent):
            if isinstance(pos, (list, tuple)) and len(pos) == 2:
                x, y = int(pos[0]), int(pos[1])
                if 0 <= x < largeur and 0 <= y < hauteur:
                    is_tete = (i == len(serpent) - 1)
                    grille[y][x] = Pixel(teinte=30 if is_tete else 20, intensite=255, motif=5 if is_tete else 2, clignote=0)

    # porte (optionnelle)
    porte = monde.get("porte")
    if isinstance(porte, (list, tuple)) and len(porte) == 2:
        x, y = int(porte[0]), int(porte[1])
        if 0 <= x < largeur and 0 <= y < hauteur:
            ouverte = bool(monde.get("porte_ouverte", False))
            grille[y][x] = Pixel(teinte=200, intensite=255, motif=1, clignote=1 if ouverte else 0)

    return grille


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
        """LIVE: pas de reconstruction de direction depuis journal."""
        return None

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
        self._diag_fichier_multi_run: Optional[str] = None


        # Charger/indexer le journal UNE SEULE FOIS, ici.
        # L'UI s'appuie ensuite sur `replay_session.stats_episodes`.
        try:
            if self.journal_path.exists():
                lignes = list(_lire_jsonl(self.journal_path))
                run_id = os.getenv("SNAKE_RUN_ID", "").strip() or None

                # --- auto-filtrage si fichier multi-run ---
                if run_id is None and lignes:
                    from collections import Counter

                    runs = [
                        str(e.get("run_id"))
                        for e in lignes
                        if e.get("run_id") is not None
                    ]

                    if runs:
                        c = Counter(runs)
                        if len(c) > 1:
                            run_id = c.most_common(1)[0][0]
                            self._diag_fichier_multi_run = (
                                f"⚠ fichier multi-run ({len(c)} runs). run_id auto={run_id}"
                            )

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
# Diagnostics: actions hors norme + version détectée (par épisode)
                self._diagnostic_actions_hors_norme: dict[int, dict[str, int]] = {}
                self._version_detectee_par_episode: dict[int, str] = {}
                for eid, tick_map in self._tick_map_par_episode.items():
                    c = {}
                    version_ep = "inconnu"
                    for _tk, e in (tick_map or {}).items():
                        version_ep = version_ep if version_ep != "inconnu" else _inferer_version_evt(e)
                        a = _extraire_action_evt(e)
                        txt = _formatter_action_pour_tui(tick=int(_tk), action=a)
                        if txt.startswith("⚠ hors_norme:"):
                            key = txt.split(":", 1)[1] if ":" in txt else str(a)
                            c[key] = int(c.get(key, 0)) + 1
                    if c:
                        self._diagnostic_actions_hors_norme[int(eid)] = c
                    self._version_detectee_par_episode[int(eid)] = version_ep

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
            action = str(_extraire_action_evt(evt) or "").strip()
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
        """Direction reconstruite pour le rendu orienté (REPLAY).

        Source: cache _direction_map_par_episode (calculée une fois au chargement).
        Convention: tick=0 => direction initiale "droite".
        """
        try:
            eid = int(episode_id)
            tk = int(tick)
        except Exception:
            return None

        m = self._direction_map_par_episode.get(eid)
        if not m:
            return "droite" if tk == 0 else None
        return m.get(tk) if tk in m else ("droite" if tk == 0 else None)

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
                        # --- compat replay v1/v2 -------------------------------------------------
                        version = str(evt.get("version") or "").strip()
                        est_v2 = (version == "journal_v2") or (_inferer_version_evt(evt) == "v2")

                        if est_v2:
                            monde = evt.get("monde_canonique") if isinstance(evt.get("monde_canonique"), dict) else {}
                            largeur = int(monde.get("largeur", 0) or 0)
                            hauteur = int(monde.get("hauteur", 0) or 0)

                            # action (nested)
                            action = _extraire_action_evt(evt)

                            # capteurs: préférer caméra égocentrée si présente
                            capteurs = []
                            insts = {}
                            perc = evt.get("perception")
                            if isinstance(perc, dict):
                                insts = perc.get("instruments") or {}
                            if isinstance(insts, dict):
                                # ordre de préférence
                                for inst_id in ["camera_egocentree_v1", "camera_estrade_absolue_v1"]:
                                    o = insts.get(inst_id)
                                    if isinstance(o, dict) and o.get("type") == "pixels_npz" and o.get("payload_ref"):
                                        path_npz = (self.journal_path.parent / str(o["payload_ref"])).resolve()
                                        if path_npz.exists():
                                            capteurs = _decoder_capteurs_npz(path_npz)
                                            break
                                # sinon: première caméra pixels_npz
                                if not capteurs:
                                    for o in insts.values():
                                        if isinstance(o, dict) and o.get("type") == "pixels_npz" and o.get("payload_ref"):
                                            path_npz = (self.journal_path.parent / str(o["payload_ref"])).resolve()
                                            if path_npz.exists():
                                                capteurs = _decoder_capteurs_npz(path_npz)
                                                break

                            # fallback: reconstruire depuis monde_canonique
                            if not capteurs:
                                capteurs = _capteurs_synthetiques_depuis_monde_canonique(monde)

                            rendu_debug = _rendre_debug_depuis_capteurs(capteurs) if capteurs else []

                            obs = Observation(
                                run_id=str(evt.get("run_id") or f"replay:{self.journal_path.name}"),
                                episode_id=int(evt.get("episode_id", episode_courant)),
                                tick=int(evt.get("tick", idx_frame)),
                                capteurs=capteurs,
                                rendu_debug=rendu_debug,
                                mesure_bruit=f"REPLAY(v2) file={self.journal_path.name} episode={episode_courant} frame={idx_frame} action={_formatter_action_pour_tui(tick=evt.get('tick', idx_frame), action=action)}",
                                score=int(monde.get("score", 0) or 0),
                                longueur=int(monde.get("longueur", 0) or 0),
                                termine=bool(monde.get("termine", False)),
                                raison_fin=monde.get("raison_fin"),
                            )
                        else:
                            # legacy v1
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
                                mesure_bruit=f"REPLAY file={self.journal_path.name} episode={episode_courant} frame={idx_frame} action={_formatter_action_pour_tui(tick=evt.get('tick', idx_frame), action=_extraire_action_evt(evt))}",
                                score=int(evt.get("score", 0)),
                                longueur=int(evt.get("longueur", 0)),
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

        # Diagnostic: fichier multi-run (si auto-filtré)
        if getattr(self, "_diag_fichier_multi_run", None):
            lignes.append(str(self._diag_fichier_multi_run))

        # Diagnostics: actions hors norme (tolérant, mais visible)
        hors = getattr(self, "_diagnostic_actions_hors_norme", {}).get(int(eid), {})
        if hors:
            details = ", ".join(f"{k}×{v}" for k, v in sorted(hors.items(), key=lambda kv: (-kv[1], kv[0]))[:6])
            lignes.append(f"⚠ actions hors norme (ép {eid}): {details}")

        # Diagnostic: version détectée (heuristique)
        ver = getattr(self, "_version_detectee_par_episode", {}).get(int(eid), "inconnu")
        if ver != "inconnu":
            lignes.append(f"(journal {ver})")
        for tk in fenetre:
            e = tick_map.get(tk) or {}
            action_txt = _formatter_action_pour_tui(tick=int(tk), action=_extraire_action_evt(e))
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


    # TUI LIVE: si aucune expérience n'est active, on force le mode manuel
    # (évite de rejouer un ancien SNAKE_AGENT restant dans l'env).
    if not (os.getenv("SNAKE_EXPERIENCE") or os.getenv("SNAKE_EXPERIENCE_ID")):
        os.environ.pop("SNAKE_AGENT", None)

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
