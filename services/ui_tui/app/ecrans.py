from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, OptionList, Static, DataTable
from textual.screen import ModalScreen
from textual import on

from rich.markup import escape as rich_escape

from ui_tui.app.catalogues import (
    racine_projet,
    lister_arenes_ids,
    lister_experiences_ids,
    preparer_bac_a_sable,
    lister_journaux_replay,
)
from ui_tui.app.sessions import demarrer_session
from ui_tui.app.rendu_oriente import rendu_oriente_tete

from runner.app.replay_index import StatEpisode

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1


def _horodatage_compact() -> str:
    """Horodatage compact pour noms de fichiers (ex: 2026-02-06_08h54)."""
    t = time.localtime()
    return f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}_{t.tm_hour:02d}h{t.tm_min:02d}"


# -----------------------------------------------------------------------------
# Modèles UI


@dataclass
class ChoixSituation:
    mode: str  # "manual" | "replay"
    experience_id: Optional[str]
    arene_id: Optional[str]
    journal_path: Optional[Path]


# -----------------------------------------------------------------------------
# Écran menu / wizard


class EcranMenu(Screen[None]):
    """Wizard minimal.

    Objectif: préparer *tout* ce qu'il faut pour E542 (gestion d'épisode),
    en appliquant la règle: si bac à sable choisi -> priorité à son contenu.
    """

    BINDINGS = [
        ("escape", "retour", "Retour"),
        ("q", "quitter", "Quitter"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._racine = racine_projet()
        self._etape = 0

        self._mode: Optional[str] = None
        self._experience_id: Optional[str] = None
        self._arene_id: Optional[str] = None
        self._journal_path: Optional[Path] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="menu_root"):
            yield Static("SnakeAI — TUI", id="titre")
            yield Static("", id="etat")
            yield OptionList(id="menu_options")
            yield Static("Entrée=valider | esc=retour | q=quit", id="hint")
        yield Footer()

    def on_mount(self) -> None:
        self._afficher_etape_0()

    def action_quitter(self) -> None:
        self.app.exit()

    def action_retour(self) -> None:
        if self._etape <= 0:
            self.app.exit()
            return
        self._etape -= 1
        if self._etape == 0:
            self._afficher_etape_0()
        elif self._etape == 1:
            self._afficher_etape_1()
        elif self._etape == 2:
            self._afficher_etape_2()

    def _etat(self, txt: str) -> None:
        self.query_one("#etat", Static).update(txt)

    def _options(self) -> OptionList:
        return self.query_one("#menu_options", OptionList)

    def _afficher_etape_0(self) -> None:
        self._etape = 0
        self._etat("Étape 1 : choisir le mode")
        ol = self._options()
        ol.clear_options()
        ol.add_option("live — commande manuelle")
        ol.add_option("replay — relire un journal")

    def _afficher_etape_1(self) -> None:
        self._etape = 1
        self._etat("Étape 2 : choisir un bac à sable (optionnel) — priorité à l'expérience")
        ol = self._options()
        ol.clear_options()
        ol.add_option("(aucun bac à sable)")
        for exp in lister_experiences_ids(self._racine):
            ol.add_option(f"bac:{exp}")

    def _afficher_etape_2(self) -> None:
        self._etape = 2
        # Règle: si bac choisi -> arène imposée par le bac (et journal/artefacts aussi)
        if self._experience_id:
            self._etat("Étape 3 : bac choisi — arène imposée (prêt à lancer)")
            ol = self._options()
            ol.clear_options()
            ol.add_option("lancer")
            return

        self._etat("Étape 3 : choisir une arène")
        ol = self._options()
        ol.clear_options()
        for a in lister_arenes_ids(self._racine):
            ol.add_option(a)

    def _afficher_etape_3_replay(self) -> None:
        self._etape = 3
        self._etat("Étape 4 : choisir un journal replay")
        ol = self._options()
        ol.clear_options()
        journaux = lister_journaux_replay(self._racine, self._experience_id)
        if not journaux:
            ol.add_option("(aucun journal trouvé)")
        else:
            for p in journaux:
                ol.add_option(str(p))

    def _lancer(self) -> None:
        choix = ChoixSituation(
            mode=self._mode or "manual",
            experience_id=self._experience_id,
            arene_id=self._arene_id,
            journal_path=self._journal_path,
        )
        self.app.push_screen(EcranSession(choix))

    @on(OptionList.OptionSelected)
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        lib = event.option.prompt

        if self._etape == 0:
            self._mode = "manual" if lib.startswith("live") else "replay"
            self._afficher_etape_1()
            return

        if self._etape == 1:
            if lib.startswith("(aucun"):
                self._experience_id = None
            else:
                self._experience_id = lib.split("bac:", 1)[1]

            # si replay: on choisit ensuite le journal ; sinon on choisit l'arène (ou on lance si bac)
            if self._mode == "replay":
                self._afficher_etape_3_replay()
            else:
                self._afficher_etape_2()
            return

        if self._etape == 2:
            if self._experience_id:
                # bac choisi: bouton "lancer"
                self._lancer()
                return
            self._arene_id = lib
            self._lancer()
            return

        if self._etape == 3:
            if lib.startswith("(aucun"):
                return
            self._journal_path = Path(lib)
            self._lancer()
            return


# -----------------------------------------------------------------------------
# Écran session (E542) : live/replay + stats + sélection épisode


def _resume_observation(obs: Any) -> str:
    """Résumé compact, sans markup Textual."""
    try:
        lignes = []
        lignes.append(f"run={getattr(obs,'run_id', '?')}  ep={getattr(obs,'episode_id','?')}  tick={getattr(obs,'tick','?')}")
        lignes.append(
            f"score={getattr(obs,'score','?')}  longueur={getattr(obs,'longueur','?')}  termine={getattr(obs,'termine','?')}  fin={getattr(obs,'raison_fin',None)}"
        )
        rendu = getattr(obs, "rendu_debug", None)
        if rendu:
            lignes.append("")
            # limiter hauteur
            for ln in rendu[:12]:
                lignes.append(str(ln))
        return "\n".join(lignes)

    except Exception:
        # Ne jamais faire planter l'UI sur un rendu/objet inattendu.
        try:
            return str(obs)
        except Exception:
            return "(observation illisible)"




# --- Contrat journal: formatage action ----------------------------------------

_ACTIONS_SUPPORTEES_TUI = {
    "avant",
    "observer_gauche",
    "observer_droite",
}

def _formatter_action_pour_tui(*, tick: int, action: Any) -> str:
    """Affichage robuste de l'action (tick/action)."""
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

class DialogueAllerEpisode(ModalScreen[int | None]):
    """Petit dialogue pour saisir un numéro d'épisode (mode replay)."""

    BINDINGS = [("escape", "annuler", "Annuler"), ("enter", "valider", "Valider")]

    def __init__(self, max_episode: int, courant: int) -> None:
        super().__init__()
        self._max = max_episode
        self._courant = courant

    def compose(self) -> ComposeResult:
        msg = f"Aller à l'épisode (0..{self._max}) — courant: {self._courant}" \
            if self._max is not None else "Aller à l'épisode"
        yield Static(msg)
        yield Input(value=str(self._courant), placeholder="numéro d'épisode", id="ep_input")

    def on_mount(self) -> None:
        self.query_one("#ep_input", Input).focus()

    @on(Input.Submitted)
    def _submitted(self, event: Input.Submitted) -> None:
        self.action_valider()

    def action_annuler(self) -> None:
        self.dismiss(None)

    def action_valider(self) -> None:
        txt = self.query_one("#ep_input", Input).value.strip()
        try:
            n = int(txt)
        except Exception:
            self.dismiss(None)
            return
        if n < 0:
            n = 0
        if self._max is not None and n > self._max:
            n = self._max
        self.dismiss(n)


def _stats_episode_depuis_source(source: Any) -> dict[int, StatEpisode]:
    """Index des épisodes depuis la source REPLAY.

    Invariant: aucun écran TUI ne lit le journal brut. La lecture/indexation
    est centralisée dans `SourceReplay` (ui_tui.app.sessions).
    """
    if source is None:
        return {}
    rs = getattr(source, "replay_session", None)
    if rs is None:
        return {}
    try:
        return dict(getattr(rs, "stats_episodes", {}) or {})
    except Exception:
        return {}


class DialogueListeEpisodes(ModalScreen[int | None]):
    """Liste des épisodes (mode replay) + sélection.

    Retourne l'episode_id sélectionné (int) ou None si annulé.
    """

    BINDINGS = [
        ("escape", "annuler", "Annuler"),
        ("enter", "valider", "Valider"),
    ]

    def __init__(self, stats: dict[int, StatEpisode], courant: int) -> None:
        super().__init__()
        self._stats = stats
        self._courant = int(courant)
        self._episodes = sorted(stats.keys())

    def compose(self) -> ComposeResult:
        yield Static(f"Choisir un épisode (total: {len(self._episodes)}) — courant: {self._courant}")
        yield OptionList(id="liste_episodes")

    def on_mount(self) -> None:
        ol = self.query_one("#liste_episodes", OptionList)
        ol.clear_options()

        for eid in self._episodes:
            st = self._stats.get(eid)
            if st is None:
                lib = f"{eid}"
            else:
                lib = (
                    f"ep {eid:4d} | ticks={st.ticks:4d} | score={st.score_final:4d} | "
                    f"longueur={st.longueur_final:3d} | termine={str(st.termine)}"
                )
            ol.add_option(lib)

        # essayer de positionner la sélection sur l'épisode courant
        try:
            idx = self._episodes.index(self._courant)
            # Textual 0.5x: selected/index varie; on tente plusieurs API.
            if hasattr(ol, "index"):
                ol.index = idx  # type: ignore[attr-defined]
            elif hasattr(ol, "highlighted"):
                ol.highlighted = idx  # type: ignore[attr-defined]
        except Exception:
            pass

        ol.focus()

    @on(OptionList.OptionSelected)
    def _selected(self, event: OptionList.OptionSelected) -> None:
        # Double-clic / Enter sur l'option.
        self.action_valider()

    def action_annuler(self) -> None:
        self.dismiss(None)

    def action_valider(self) -> None:
        ol = self.query_one("#liste_episodes", OptionList)
        try:
            # Textual expose parfois selected/ highlighted / index.
            idx = getattr(ol, "index", None)
            if idx is None:
                idx = getattr(ol, "highlighted", None)
            if idx is None:
                idx = 0
            idx = int(idx)
        except Exception:
            idx = 0
        if not self._episodes:
            self.dismiss(None)
            return
        idx = max(0, min(idx, len(self._episodes) - 1))
        self.dismiss(int(self._episodes[idx]))


# -----------------------------------------------------------------------------
# Vue journal (ticks) d'un épisode en replay


class EcranJournalEpisode(Screen[tuple[int, int] | None]):
    """Affiche le journal d'un épisode (liste des ticks) en mode replay.

    - navigation: flèches, PgUp/PgDn, Home/End
    - Enter: choisir le tick (retourne (episode_id, tick))
    """

    BINDINGS = [
        ("escape", "retour", "Retour"),
        ("enter", "choisir", "Aller"),
        ("pageup", "saut_haut", "PgUp"),
        ("pagedown", "saut_bas", "PgDn"),
        ("home", "debut", "Début"),
        ("end", "fin", "Fin"),
    ]

    def __init__(self, *, replay_session: Any, episode_id: int, tick_courant: int = 0) -> None:
        super().__init__()
        self.replay_session = replay_session
        self.episode_id = int(episode_id)
        self.tick_courant = max(0, int(tick_courant))
        self._ticks: list[int] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="journal_root"):
            yield Static("", id="journal_titre")
            table = DataTable(id="journal_table")
            table.zebra_stripes = True
            yield table
            yield Static("↑/↓ sélectionner · PgUp/PgDn sauter · Home/End · Enter=aller · Esc=retour", id="journal_hint")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#journal_titre", Static).update(f"Journal — épisode {self.episode_id}")
        table = self.query_one("#journal_table", DataTable)

        table.add_column("tick", width=6)
        table.add_column("action", width=20)
        table.add_column("score", width=6)
        table.add_column("long", width=6)
        table.add_column("term", width=6)
        table.add_column("fin", width=18)

        rep = None
        try:
            rep = self.replay_session.nouveau_replay_ui()
            rep.charger_episode(self.episode_id)
        except Exception:
            rep = None

        if rep is None:
            table.add_row("-", "(replay)", "-", "-", "-", "session indisponible")
            return

        for evt in rep.ticks():
            try:
                tick = int(evt.get("tick", 0) or 0)
            except Exception:
                continue
            self._ticks.append(tick)
            table.add_row(
                str(tick),
                _formatter_action_pour_tui(tick=tick, action=evt.get("action"))[:10],
                str(evt.get("score", 0)),
                str(evt.get("longueur", 0)),
                str(bool(evt.get("termine", False))),
                str(evt.get("raison_fin") or "")[:18],
            )

        # positionner le curseur au tick courant si possible
        try:
            if self._ticks:
                idx = 0
                if self.tick_courant in self._ticks:
                    idx = self._ticks.index(self.tick_courant)
                idx = max(0, min(idx, len(self._ticks) - 1))
                table.move_cursor(row=idx, column=0)
                table.focus()
        except Exception:
            pass

    def on_key(self, event) -> None:  # Textual: Key
        """Assurer que Enter fonctionne même quand le focus est dans la DataTable.

        Certaines versions de Textual interceptent Enter au niveau DataTable.
        On force donc l'action "choisir" ici.
        """
        try:
            if getattr(event, "key", None) == "enter":
                event.stop()
                self.action_choisir()
        except Exception:
            pass

    @on(DataTable.RowSelected)
    def _row_selected(self, _event: DataTable.RowSelected) -> None:
        # Double-clic / Enter sur une ligne.
        self.action_choisir()

    def _row_count(self) -> int:
        return len(self._ticks)

    def _set_row(self, row: int) -> None:
        table = self.query_one("#journal_table", DataTable)
        if self._row_count() <= 0:
            return
        row = max(0, min(int(row), self._row_count() - 1))
        table.move_cursor(row=row, column=0)

    def action_retour(self) -> None:
        self.dismiss(None)

    def action_choisir(self) -> None:
        if not self._ticks:
            self.dismiss(None)
            return
        table = self.query_one("#journal_table", DataTable)
        try:
            row = int(table.cursor_coordinate.row)
        except Exception:
            row = 0
        row = max(0, min(row, len(self._ticks) - 1))
        self.dismiss((self.episode_id, int(self._ticks[row])))

    def action_saut_haut(self) -> None:
        table = self.query_one("#journal_table", DataTable)
        try:
            row = int(table.cursor_coordinate.row)
        except Exception:
            row = 0
        self._set_row(row - 10)

    def action_saut_bas(self) -> None:
        table = self.query_one("#journal_table", DataTable)
        try:
            row = int(table.cursor_coordinate.row)
        except Exception:
            row = 0
        self._set_row(row + 10)

    def action_debut(self) -> None:
        self._set_row(0)

    def action_fin(self) -> None:
        self._set_row(max(0, self._row_count() - 1))


class EcranSession(Screen[None]):
    BINDINGS = [
        ("escape", "retour_menu", "Menu"),
        ("p", "pause", "Play/Pause"),
        ("s", "step", "Step"),
        ("r", "reset", "Reset"),
        ("j", "journal_episode", "Journal"),
        ("J", "toggle_journal", "Mini"),
        ("t", "toggle_stats", "Stats"),
        ("[", "episode_prec", "Épisode -"),
        ("]", "episode_suiv", "Épisode +"),
        ("g", "episode_aller", "Aller"),
        ("l", "episode_liste", "Liste"),
        ("e", "terminer_episode", "Fin ép."),
        ("i", "infos_bac", "Bac"),
        ("q", "quitter", "Quitter"),
    ]

    def __init__(self, choix: ChoixSituation | None = None, *, mode: str | None = None, journal: Path | None = None) -> None:
        super().__init__()
        # compat: anciens appels (main.py)
        if choix is None:
            choix = ChoixSituation(mode=mode or "manual", experience_id=None, arene_id=None, journal_path=journal)
        self.choix = choix

        self.source = None
        self.bus = None
        self.controle = None

        self._journal_visible = False
        self._stats_visible = True
        self._stats_index: Optional[dict[int, StatEpisode]] = None

        self._episode_id_affiche = 0
        self._episode_id_attendu: Optional[int] = None
        self._runner_err: Optional[str] = None

        # navigation (journal): aller à un tick précis par steps
        self._tick_cible: Optional[int] = None
        self._tick_cible_attend_reset: bool = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="situation_root"):
            # Zone principale: statut + arène (rendu_debug) en grand.
            with Vertical(id="main"):
                yield Static("", id="sit_texte")
                yield Static("", id="arene", markup=False)
            with Vertical(id="side"):
                yield Static("", id="journal", markup=False)
                yield Static("", id="stats", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        # appliquer bac à sable si choisi (prioritaire)
        if self.choix.experience_id:
            bac, journal_path, _run_dir = preparer_bac_a_sable(racine_projet(), self.choix.experience_id)
            # si replay sans journal explicite: forcer celui du bac
            if self.choix.mode == "replay" and self.choix.journal_path is None:
                self.choix.journal_path = journal_path
            # si live: arène imposée (par env déjà appliqué par preparer_bac_a_sable)
        else:
            # pas de bac: arène du wizard
            if self.choix.arene_id:
                os.environ["SNAKE_ARENE"] = self.choix.arene_id

        # démarrer session
        src, bus, ctrl = demarrer_session(mode=self.choix.mode, journal_path=self.choix.journal_path)
        self.source, self.bus, self.controle = src, bus, ctrl

        # init UI
        self._journal_visible = False
        self._stats_visible = True
        self._set_side_visibility()
        self._afficher_situation()

        # tick UI
        self.set_interval(0.05, self._tick)

    def action_quitter(self) -> None:
        self.app.exit()

    def action_retour_menu(self) -> None:
        try:
            if self.source:
                self.source.stop()
        finally:
            self.app.pop_screen()

    def _afficher_situation(self) -> None:
        extra = []
        if self.choix.experience_id:
            extra.append(f"bac:{self.choix.experience_id}")
        if self.choix.arene_id and not self.choix.experience_id:
            extra.append(f"arène:{self.choix.arene_id}")
        if self.choix.mode == "replay" and self.choix.journal_path:
            extra.append(f"journal:{self.choix.journal_path.name}")
        # Afficher l'épisode courant pour rendre visible toute bascule.
        extra2 = [f"ép:{self._episode_id_affiche}"] + extra
        msg = f"{self.choix.mode.upper()} — gérer un épisode" + (" | " + " ".join(extra2) if extra2 else "")
        self.query_one("#sit_texte", Static).update(msg)

    def _set_side_visibility(self) -> None:
        jw = self.query_one("#journal", Static)
        sw = self.query_one("#stats", Static)
        jw.display = self._journal_visible
        sw.display = self._stats_visible

    def _tick(self) -> None:
        # journal
        if self._journal_visible and self.source:
            items = self.source.journal_recent(10)
            txt = "\n".join(str(x) for x in items) if items else "(journal) en attente…"
            self.query_one("#journal", Static).update(txt)

        # arène + stats
        txt = "(stats) en attente…"
        if self.bus:
            dernier = self.bus.dernier()
            if dernier is None:
                # Rien reçu pour l'instant. Si on est en changement d'épisode,
                # on laisse le message "chargement…" posé par _demander_episode().
                if self._episode_id_attendu is None:
                    self.query_one("#arene", Static).update("(arène) en attente…")
            else:
                ep_obs = int(getattr(dernier, "episode_id", self._episode_id_affiche))
                if self._episode_id_attendu is not None and ep_obs != self._episode_id_attendu:
                    # Dernier événement du bus = ancien épisode : ignorer tant qu'on n'a pas
                    # reçu un événement du nouvel épisode.
                    txt = "(stats) chargement…"
                else:
                    if self._episode_id_attendu is not None and ep_obs == self._episode_id_attendu:
                        self._episode_id_attendu = None
                    self._episode_id_affiche = ep_obs

                    # Direction courante (si disponible) pour orienter visuellement la tête.
                    tick_obs = 0
                    try:
                        tick_obs = int(getattr(dernier, "tick", 0) or 0)
                    except Exception:
                        tick_obs = 0
                    direction = getattr(dernier, "direction", None)
                    if direction is None and self.source is not None:
                        # REPLAY: demander à la source (lecture du journal) si elle peut fournir une direction.
                        try:
                            fn = getattr(self.source, "direction_pour", None)
                            if callable(fn):
                                direction = fn(episode_id=ep_obs, tick=tick_obs)
                        except Exception:
                            direction = None

                    rendu = getattr(dernier, "rendu_debug", None)
                    if rendu:
                        try:
                            rendu_aff = rendu_oriente_tete([str(x) for x in rendu], direction)
                            self.query_one("#arene", Static).update("\n".join(rendu_aff))
                        except Exception:
                            self.query_one("#arene", Static).update("(arène) rendu illisible")
                    else:
                        self.query_one("#arene", Static).update("(arène) …")

                    # garder la ligne de statut à jour (affiche ép:)
                    self._afficher_situation()
                    txt = _resume_observation(dernier)

                    # si on est en train d'aller à un tick précis (depuis la vue Journal)
                    if self._tick_cible is not None and self.controle and self.choix.mode == "replay":
                        tick_obs = int(getattr(dernier, "tick", 0) or 0)
                        ep_obs2 = int(getattr(dernier, "episode_id", self._episode_id_affiche) or 0)
                        if self._episode_id_attendu is None and ep_obs2 == self._episode_id_affiche:
                            # Phase 1: attendre de constater le reset (tick=0) avant de "marcher".
                            if self._tick_cible_attend_reset:
                                if tick_obs == 0:
                                    self._tick_cible_attend_reset = False
                                    if int(self._tick_cible) == 0:
                                        self._tick_cible = None
                                # tant que le reset n'est pas visible, ne pas annuler la cible
                            else:
                                if tick_obs < int(self._tick_cible):
                                    # On avance 1 pas à la fois (runner est en pause en replay).
                                    self.controle.demander_step()
                                else:
                                    self._tick_cible = None

        if self._stats_visible and self.bus:
            dernier = self.bus.dernier()
            if dernier is None:
                txt = "(stats) chargement…" if self._episode_id_attendu is not None else "(stats) en attente…"

            # en replay, ajouter un résumé par épisode depuis l'index Replay (source de vérité)
            if self.choix.mode == "replay":
                if self._stats_index is None:
                    self._stats_index = _stats_episode_depuis_source(self.source)
                st = self._stats_index.get(self._episode_id_affiche)
                if st:
                    txt += "\n\n" + (
                        f"Épisode {self._episode_id_affiche} | ticks={st.ticks} | score_final={st.score_final} | longueur_final={st.longueur_final} | termine={st.termine}"
                    )
            self.query_one("#stats", Static).update(txt)

    # --- contrôles

    def action_pause(self) -> None:
        if self.controle:
            self.controle.basculer_pause()

    def action_step(self) -> None:
        if self.controle:
            self.controle.demander_step()

    def action_reset(self) -> None:
        if self.controle:
            self.controle.demander_reset()

    def action_toggle_journal(self) -> None:
        self._journal_visible = not self._journal_visible
        self._set_side_visibility()
        if self._journal_visible:
            self.query_one("#journal", Static).update("(journal) …")

    def _demander_tick(self, tick: int) -> None:
        """Aller à un tick précis (replay), en restant pause/step.

        Invariant: aucun accès au journal brut; on pilote le runner via ControleExecution.
        """
        if self.choix.mode != "replay" or not self.controle:
            return

        tick = max(0, int(tick))
        # Assurer le mode pause pour que demander_step() fonctionne.
        try:
            if not self.controle.est_en_pause():
                self.controle.basculer_pause()
        except Exception:
            pass

        self._tick_cible = tick
        self._tick_cible_attend_reset = True
        self.controle.demander_reset()

        # Feedback immédiat (évite l'impression que Enter "ne fait rien").
        try:
            self.query_one("#arene", Static).update("(arène) positionnement au tick…")
        except Exception:
            pass
        self._afficher_situation()

    def action_journal_episode(self) -> None:
        """Vue journal (par épisode) en mode replay.

        `j` ouvre une vue navigable des ticks de l'épisode courant. Enter sur un tick
        synchronise l'arène sur ce tick.
        """
        if self.choix.mode != "replay" or not self.controle:
            return
        # besoin d'une ReplaySession (source de vérité)
        rep_sess = getattr(self.source, "replay_session", None)
        if rep_sess is None:
            return

        # tick courant (si disponible)
        tick_courant = 0
        try:
            dernier = self.bus.dernier() if self.bus else None
            if dernier is not None:
                tick_courant = int(getattr(dernier, "tick", 0) or 0)
        except Exception:
            tick_courant = 0

        def _appliquer(sel: tuple[int, int] | None) -> None:
            if not sel or not isinstance(sel, tuple) or len(sel) != 2:
                return
            ep, tick = int(sel[0]), int(sel[1])
            if ep != self._episode_id_affiche:
                self._demander_episode(ep)
            self._demander_tick(tick)

        self.app.push_screen(
            EcranJournalEpisode(replay_session=rep_sess, episode_id=self._episode_id_affiche, tick_courant=tick_courant),
            callback=_appliquer,
        )

    def action_toggle_stats(self) -> None:
        self._stats_visible = not self._stats_visible
        self._set_side_visibility()
        if self._stats_visible:
            self.query_one("#stats", Static).update("(stats) …")

    # --- navigation épisode (replay)

    def _max_episode(self) -> int:
        if self._stats_index is None:
            self._stats_index = _stats_episode_depuis_source(self.source)
        if not self._stats_index:
            return 0
        return max(self._stats_index.keys())


    def _demander_episode(self, n: int) -> None:
        """Demande un changement d'épisode avec feedback immédiat.

        Important: tant que le runner n'a pas émis une observation du nouvel épisode,
        on évite d'écraser l'affichage avec l'ancien épisode (dernier événement bus).
        """
        if self.choix.mode != "replay" or not self.controle:
            return
        n = int(n)
        self._episode_id_attendu = n
        self._episode_id_affiche = n
        self._afficher_situation()
        # Afficher un état transitoire visible.
        try:
            self.query_one("#arene", Static).update("(arène) chargement…")
        except Exception:
            pass
        try:
            self.query_one("#stats", Static).update("(stats) chargement…")
        except Exception:
            pass
        # Appliquer côté runner.
        self.controle.demander_episode(n)
        self.controle.demander_reset()

    def action_episode_liste(self) -> None:
        """Ouvre la liste des épisodes (mode replay) et bascule sur celui choisi."""
        if self.choix.mode != "replay" or not self.controle:
            return

        if self._stats_index is None:
            self._stats_index = _stats_episode_depuis_source(self.source)

        def _appliquer(n: int | None) -> None:
            if not isinstance(n, int):
                return
            self._demander_episode(int(n))

        self.app.push_screen(DialogueListeEpisodes(stats=self._stats_index, courant=self._episode_id_affiche), callback=_appliquer)

    def action_episode_prec(self) -> None:
        if self.choix.mode != "replay" or not self.controle:
            return
        cible = max(0, self._episode_id_affiche - 1)
        self._demander_episode(cible)

    def action_episode_suiv(self) -> None:
        if self.choix.mode != "replay" or not self.controle:
            return
        max_ep = self._max_episode()
        cible = min(max_ep, self._episode_id_affiche + 1)
        self._demander_episode(cible)

    def action_episode_aller(self) -> None:
        """Aller à un épisode précis (mode replay).

        Raccourci volontairement simple côté utilisateur : on ouvre un petit
        dialogue qui accepte un entier.
        """
        if self.choix.mode != "replay" or not self.controle:
            return
        max_ep = self._max_episode()
        self.app.push_screen(
            DialogueAllerEpisode(max_episode=max_ep, courant=self._episode_id_affiche),
            callback=lambda n: self._demander_episode(n) if isinstance(n, int) else None,
        )

    def action_terminer_episode(self) -> None:
        """Terminer/recommencer l'épisode courant.

        En live, ça sert à "couper" un épisode en cours (commande manuelle) sans
        attendre la fin naturelle.

        En replay, on réinitialise aussi (utile pour revenir au début) mais la
        navigation principale reste [ ] / g.
        """
        if not self.controle:
            return
        self.controle.demander_reset()

    # --- infos bac à sable

    def action_infos_bac(self) -> None:
        """Affiche une page d'information sur le bac à sable (README, notes, runs).

        Disponible seulement si une expérience est sélectionnée.
        """
        if not self.choix.experience_id:
            return
        self.app.push_screen(EcranBac(experience_id=self.choix.experience_id))


# -----------------------------------------------------------------------------
# Écran bac à sable (README + notes)


class EcranBac(Screen[None]):
    BINDINGS = [
        ("escape", "retour", "Retour"),
        ("n", "nouvelle_note", "Note"),
        ("r", "recharger", "Recharger"),
        ("q", "quitter", "Quitter"),
    ]

    def __init__(self, experience_id: str) -> None:
        super().__init__()
        self.experience_id = str(experience_id)
        self._racine = racine_projet()
        self._bac: Optional[BacASableV1] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        # NOTE: on veut pouvoir naviguer (flèches / pgup / pgdn) dans le README.
        # Un Static seul ne scrolle pas; on place tout dans un VerticalScroll.
        with Vertical(id="bac_root"):
            with VerticalScroll(id="bac_scroll"):
                yield Static("", id="bac_titre")
                yield Static("", id="bac_info", markup=False)
                yield Static("", id="bac_readme", markup=False)
                yield Static("", id="bac_notes", markup=False)
            yield Static("n=nouvelle note | r=recharger | esc=retour", id="bac_hint")
        yield Footer()

    def on_mount(self) -> None:
        self._charger_et_afficher()
        # Par défaut, mettre le focus sur la zone scrollable.
        try:
            self.query_one("#bac_scroll").focus()
        except Exception:
            pass

    def action_quitter(self) -> None:
        self.app.exit()

    def action_retour(self) -> None:
        self.app.pop_screen()

    def action_recharger(self) -> None:
        self._charger_et_afficher()

    def _charger_et_afficher(self) -> None:
        self._bac = BacASableV1.charger_depuis_id(self._racine, self.experience_id)
        rapport = self._bac.assurer_structure()

        titre = f"BAC — {self.experience_id}"
        self.query_one("#bac_titre", Static).update(titre)

        readme = self._bac.experience_dir / "README.md"
        readme_txt = ""
        if readme.exists():
            readme_txt = readme.read_text(encoding="utf-8", errors="replace")
        else:
            readme_txt = "(README.md absent)"

        # notes
        notes_dir = self._bac.paths.notes_dir
        notes = []
        if notes_dir.exists():
            notes = sorted([p for p in notes_dir.glob("*.md") if p.is_file()], key=lambda p: p.name, reverse=True)

        infos = [
            f"experience_dir: {self._bac.experience_dir}",
            f"runs_dir     : {self._bac.paths.runs_dir}",
            f"notes_dir    : {self._bac.paths.notes_dir}",
        ]
        if rapport.get("creations"):
            infos.append("")
            infos.append("créé:")
            for c in rapport["creations"][:12]:
                infos.append(f"  - {c}")
            if len(rapport["creations"]) > 12:
                infos.append(f"  … +{len(rapport['creations'])-12}")

        self.query_one("#bac_info", Static).update("\n".join(infos))
        # éviter les erreurs de markup même si le README contient des crochets
        self.query_one("#bac_readme", Static).update(rich_escape(readme_txt))

        bloc_notes = ["notes (récentes):"]
        if not notes:
            bloc_notes.append("  (aucune)")
        else:
            for p in notes[:10]:
                bloc_notes.append(f"  - {p.name}")
            if len(notes) > 10:
                bloc_notes.append(f"  … +{len(notes)-10}")
        self.query_one("#bac_notes", Static).update("\n".join(bloc_notes))

    def action_nouvelle_note(self) -> None:
        if not self._bac:
            return
        notes_dir = self._bac.paths.notes_dir
        notes_dir.mkdir(parents=True, exist_ok=True)
        ts = _horodatage_compact()
        fp = notes_dir / f"note_{ts}.md"
        if not fp.exists():
            fp.write_text(
                f"# note — {ts}\n\n"
                f"expérience: {self.experience_id}\n\n"
                "## contexte\n\n"
                "- ...\n\n"
                "## observations\n\n"
                "- ...\n\n"
                "## suite\n\n"
                "- ...\n",
                encoding="utf-8",
            )
        # Indice utilisateur minimal (sinon on a l'impression que "n" ne fait rien).
        try:
            self.query_one("#bac_hint", Static).update(
                f"note créée: {fp.name} | n=nouvelle note | r=recharger | esc=retour"
            )
        except Exception:
            pass
        self._charger_et_afficher()
