from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static

from ui_tui.app.catalogues import (
    racine_projet,
    lister_arenes_ids,
    lister_experiences_ids,
    preparer_bac_a_sable,
    lister_journaux_replay,
)
from ui_tui.app.sessions import construire_source
from ui_tui.app.widgets import Grille, Bandeau, PanneauAide


class EcranMenu(Screen):
    """Menu multi-niveaux (wizard).

    Étapes :
      1) domaine : live / replay
      2) bac à sable : aucun / choisir expérience
      3) sélection spécifique :
          - live : arène (yaml)
          - replay : journal (jsonl)
      4) action : lancer la session (commande manuelle / replay)
    """

    BINDINGS = [("q", "app.quitter", "Quitter")]

    def __init__(self) -> None:
        super().__init__()
        self.etape = 1
        self.domaine: Optional[str] = None     # "manual" | "replay"
        self.experience_id: Optional[str] = None
        self.arene_id: Optional[str] = None
        self.journal_path: Optional[Path] = None

        self._racine = racine_projet()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="menu_root"):
            yield Static("SnakeAI — TUI", id="titre")
            yield Static("", id="breadcrumb")
            yield Static("", id="sous_titre")
            yield OptionList(id="menu_options")
            yield Static("Entrée=valider | esc=retour | q=quit", id="hint")
        yield Footer()

    def on_mount(self) -> None:
        self._rafraichir_options()

    def _breadcrumb(self) -> str:
        parts = []
        if self.domaine:
            parts.append("live" if self.domaine == "manual" else "replay")
        if self.experience_id:
            parts.append(f"bac:{self.experience_id}")
        if self.arene_id:
            parts.append(f"arène:{self.arene_id}")
        if self.journal_path:
            parts.append(f"journal:{self.journal_path.name}")
        return " > ".join(parts) if parts else "(non configuré)"

    def _rafraichir_options(self) -> None:
        self.query_one("#breadcrumb", Static).update(self._breadcrumb())
        sous_titre = self.query_one("#sous_titre", Static)
        menu = self.query_one("#menu_options", OptionList)
        menu.clear_options()

        if self.etape == 1:
            sous_titre.update("Étape 1 : choisir un domaine")
            menu.add_options(["Épisode (live)", "Replay"])
        elif self.etape == 2:
            sous_titre.update("Étape 2 : choisir un bac à sable (optionnel)")
            opts = ["Aucun bac à sable"]
            exps = lister_experiences_ids(self._racine)
            opts += [f"Expérience: {e}" for e in exps]
            menu.add_options(opts)
        elif self.etape == 3:
            if self.domaine == "manual":
                # Règle : si un bac à sable est choisi, l'arène définie par l'expérience a priorité.
                if self.experience_id:
                    sous_titre.update("Étape 3 : arène définie par le bac à sable (non modifiable)")
                    menu.add_options(["(arène imposée par l'expérience)"])
                else:
                    sous_titre.update("Étape 3 : choisir une arène (yaml)")
                    arenes = lister_arenes_ids(self._racine)
                    if not arenes:
                        menu.add_options(["(aucune arène trouvée)"])
                    else:
                        menu.add_options([f"{a}" for a in arenes])
            else:
                sous_titre.update("Étape 3 : choisir un journal (replay)")
                journaux = lister_journaux_replay(self._racine, self.experience_id)
                if not journaux:
                    menu.add_options(["(aucun journal trouvé)"])
                else:
                    menu.add_options([str(p) for p in journaux])
        elif self.etape == 4:
            sous_titre.update("Étape 4 : lancer")
            if self.domaine == "manual":
                menu.add_options(["Démarrer : commande manuelle"])
                menu.add_options(["(TODO) Éditer un épisode", "(TODO) Stats"])
            else:
                menu.add_options(["Démarrer : replay"])
                menu.add_options(["(TODO) Stats replay"])

        menu.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        # Étape 1 : domaine
        if self.etape == 1:
            self.domaine = "manual" if event.option_index == 0 else "replay"
            self.etape = 2
            self._rafraichir_options()
            return

        # Étape 2 : bac à sable
        if self.etape == 2:
            if event.option_index == 0:
                self.experience_id = None
                # nettoyer env de bac à sable
                os.environ.pop("SNAKE_JOURNAL_PATH", None)
            else:
                exps = lister_experiences_ids(self._racine)
                idx = event.option_index - 1
                if 0 <= idx < len(exps):
                    self.experience_id = exps[idx]
            # si live + bac à sable, l'arène est imposée : on saute l'étape arène
            if self.domaine == "manual" and self.experience_id:
                self.etape = 4
            else:
                self.etape = 3
            self._rafraichir_options()
            return

        # Étape 3 : sélection arène/journal
        if self.etape == 3:
            if self.domaine == "manual":
                if self.experience_id:
                    # arène imposée par le bac à sable (déjà appliquée via env au lancement)
                    self.arene_id = None
                else:
                    arenes = lister_arenes_ids(self._racine)
                    if not arenes:
                        self.app.bell()
                        return
                    self.arene_id = arenes[event.option_index]
            else:
                journaux = lister_journaux_replay(self._racine, self.experience_id)
                if not journaux:
                    self.app.bell()
                    return
                self.journal_path = journaux[event.option_index]
            self.etape = 4
            self._rafraichir_options()
            return

        # Étape 4 : lancer
        if self.etape == 4:
            if self.domaine == "manual" and event.option_index == 0:
                # appliquer bac à sable (si choisi) ; priorité à l'expérience
                if self.experience_id:
                    _bac, _journal_path, run_dir = preparer_bac_a_sable(self._racine, self.experience_id)
                    arene_affichee = os.getenv("SNAKE_ARENE")
                else:
                    if self.arene_id:
                        os.environ["SNAKE_ARENE"] = self.arene_id
                    arene_affichee = self.arene_id
                self.app.push_screen(EcranSession(mode="manual", journal=None, experience=self.experience_id, arene=arene_affichee))
            elif self.domaine == "replay" and event.option_index == 0:
                if self.journal_path:
                    os.environ["SNAKE_JOURNAL_PATH"] = str(self.journal_path)
                self.app.push_screen(EcranSituation(mode="replay", experience=self.experience_id, arene=None, journal=self.journal_path, run_dir=None))
            else:
                self.app.push_screen(EcranPlaceholder("TODO", "Fonctionnalité à implémenter."))
            return

    def key_escape(self) -> None:
        if self.etape == 1:
            self.app.bell()
            return
        if self.etape == 2:
            self.etape = 1
            self.domaine = None
        elif self.etape == 3:
            self.etape = 2
            self.arene_id = None
            self.journal_path = None
        elif self.etape == 4:
            # si live + bac à sable, l'arène est imposée : on saute l'étape arène
            if self.domaine == "manual" and self.experience_id:
                self.etape = 4
            else:
                self.etape = 3
        self._rafraichir_options()


class EcranSituation(Screen):
    """Écran de présentation de la situation (configuration effective).
    But : rendre explicite ce qui est chargé (bac à sable, arène, agent, latent, journal, run dir).
    """

    BINDINGS = [
        ("enter", "demarrer", "Démarrer"),
        ("escape", "retour", "Retour"),
        ("q", "app.quitter", "Quitter"),
    ]

    def __init__(
        self,
        mode: str,
        experience: Optional[str],
        arene: Optional[str],
        journal: Optional[Path],
        run_dir: Optional[Path],
    ) -> None:
        super().__init__()
        self.mode = mode
        self.experience = experience
        self.arene = arene
        self.journal = journal
        self.run_dir = run_dir

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="situation_root"):
            yield Static("Situation", id="sit_titre")
            yield Static(self._texte_situation(), id="sit_texte")
            yield Static("Entrée = démarrer | esc = retour", id="sit_hint")
        yield Footer()

    def _texte_situation(self) -> str:
        env = os.environ
        lignes = []
        lignes.append(f"mode        : {self.mode}")
        lignes.append(f"bac à sable  : {self.experience or '(aucun)'}")
        lignes.append(f"arène        : {self.arene or env.get('SNAKE_ARENE','(inconnue)')}")
        lignes.append(f"agent        : {env.get('SNAKE_AGENT','(non défini)')}")
        lignes.append(f"latent       : {env.get('SNAKE_AGENT_LATENT','(non défini)')}")
        lignes.append(f"seed         : {env.get('SNAKE_AGENT_SEED','(non défini)')}")
        lignes.append(f"epsilon      : {env.get('SNAKE_AGENT_EPSILON','(non défini)')}")
        lignes.append(f"journal      : {str(self.journal or env.get('SNAKE_JOURNAL_PATH','(non défini)'))}")
        if self.run_dir:
            lignes.append(f"run dir      : {self.run_dir}")
        return "\n".join(lignes)

    def action_retour(self) -> None:
        self.app.pop_screen()

    def action_demarrer(self) -> None:
        # On démarre la session après présentation
        self.app.push_screen(
            EcranSession(mode=self.mode, journal=self.journal, experience=self.experience, arene=self.arene)
        )

class EcranSession(Screen):
    BINDINGS = [
        ("q", "app.quitter", "Quitter"),
        ("escape", "retour_menu", "Menu"),
        ("p", "pause", "Play/Pause"),
        ("s", "step", "Step"),
        ("r", "reset", "Reset"),
        ("t", "toggle_stats", "Stats"),
    ]

    def __init__(self, mode: str, journal: Optional[Path] = None, experience: Optional[str] = None, arene: Optional[str] = None) -> None:
        super().__init__()
        self.mode = mode
        self.journal = journal
        self.experience = experience
        self.arene = arene

        self.src = None
        self.controle = None
        self.bus = None

        self.grille: Optional[Grille] = None
        self.bandeau: Optional[Bandeau] = None
        self.stats_widget: Optional[Static] = None
        self._stats_visible = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            self.bandeau = Bandeau(id="bandeau")
            yield self.bandeau
            with Horizontal():
                self.grille = Grille(lambda: self.bus.dernier() if self.bus else None, id="grille")
                yield self.grille
                self.stats_widget = Static("", id="stats", markup=False)
                yield self.stats_widget
        yield Footer()

    def on_mount(self) -> None:
        # construit la source (live ou replay)
        self.src, self.bus, self.controle = construire_source(self.mode, journal_path=self.journal)

        titre = "LIVE — commande manuelle" if self.mode == "manual" else "REPLAY"
        extra = []
        if self.experience:
            extra.append(f"bac:{self.experience}")
        if self.arene:
            extra.append(f"arène:{self.arene}")
        if self.mode == "replay" and self.journal:
            extra.append(self.journal.name)
        extra_txt = (" | " + " ".join(extra)) if extra else ""

        if self.bandeau:
            self.bandeau.set_msg(f"{titre}{extra_txt} | p=play/pause s=step r=reset t=stats esc=menu")

        # stats cachées par défaut
        if self.stats_widget:
            self.stats_widget.display = self._stats_visible

        self.set_interval(0.05, self._tick)

    def _tick(self) -> None:
        # rafraîchir grille
        if self.grille:
            self.grille.update(self.grille.texte())

        # afficher erreur thread si disponible
        if self.src is not None:
            err_fn = getattr(self.src, "erreur", None)
            if callable(err_fn):
                msg = err_fn()
                if msg:
                    if self.bandeau:
                        first = msg.strip().splitlines()[0]
                        self.bandeau.set_msg(f"ERREUR runner: {first}")

                    # FORCER l’affichage du panneau stats et y mettre la trace
                    if self.stats_widget:
                        self._stats_visible = True
                        self.stats_widget.display = True
                        self.stats_widget.update(msg)

                    return  # on arrête le refresh normal

        # si stats visibles, afficher au moins un étatif self._stats_visible and self.stats_widget:
        dernier = self.bus.dernier() if self.bus else None
        if dernier is not None and self.stats_widget:
            self.stats_widget.update(Text(str(dernier)))


    def action_retour_menu(self) -> None:
        try:
            if self.src:
                self.src.stop()
        finally:
            self.app.pop_screen()

    def action_pause(self) -> None:
        if self.controle:
            self.controle.basculer_pause()

    def action_step(self) -> None:
        if self.controle:
            self.controle.demander_step()

    def action_reset(self) -> None:
        if self.controle:
            self.controle.demander_reset()

    def action_toggle_stats(self) -> None:
        self._stats_visible = not self._stats_visible
        if self.stats_widget:
            self.stats_widget.display = self._stats_visible
            if self._stats_visible:
                self.stats_widget.update("(stats) en attente…")


def _rafraichir(self) -> None:
    # 0) état courant
    if self.grille:
        self.grille.update(self.grille.texte())

    # 1) si le runner/replay a crashé, on le rend visible immédiatement
    err = None
    if self.src is not None:
        err_fn = getattr(self.src, "erreur", None)
        if callable(err_fn):
            err = err_fn()

    if err:
        if self.bandeau:
            first = err.strip().splitlines()[0]
            self.bandeau.set_msg(f"ERREUR runner: {first} (t=stats)")
        # on force l'affichage des stats pour montrer la trace
        if not self._stats_visible:
            self._stats_visible = True
            self._set_side_visibility()
        if self.stats_widget:
            self.stats_widget.update(err)
        return

    # 2) pas d'observation = runner muet ou pas démarré
    if self.bus and self.bus.dernier() is None:
        if self.bandeau:
            self.bandeau.set_msg("(en attente...) aucune observation reçue (t=stats)")
    else:
        # bandeau normal (déjà set au mount), on ne le spam pas ici
        pass

    # 3) panneaux
    if self._journal_visible:
        self._maj_journal()
    if self._stats_visible:
        self._maj_stats()

    def _maj_journal(self) -> None:
        if self.journal_widget:
            self.journal_widget.update("(journal) TODO — brancher sur événements/obs")

def _maj_stats(self) -> None:
    if not self.stats_widget:
        return

    # si erreur runner, la trace est déjà injectée dans _rafraichir()
    # sinon on affiche un minimum d'info utile
    dernier = self.bus.dernier() if self.bus else None
    if dernier is None:
        self.stats_widget.update("(stats) en attente… aucune observation reçue")
    else:
        # fallback simple : représentation texte de l'observation
        self.stats_widget.update(str(dernier)[:4000])

    def _set_side_visibility(self) -> None:
        if self.journal_widget:
            self.journal_widget.display = self._journal_visible
        if self.stats_widget:
            self.stats_widget.display = self._stats_visible

    def action_retour_menu(self) -> None:
        try:
            if self.src:
                self.src.stop()
        finally:
            self.app.pop_screen()

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

def action_toggle_stats(self) -> None:
    self._stats_visible = not self._stats_visible
    self._set_side_visibility()
    if self._stats_visible and self.stats_widget:
        # ne pas écraser un éventuel traceback déjà injecté
        if not self.stats_widget.plain:
            self.stats_widget.update("(stats) en attente…")

    def __init__(self, titre: str, msg: str) -> None:
        super().__init__()
        self.titre = titre
        self.msg = msg

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Static(self.titre)
            yield Static(self.msg)
            yield Static("esc=retour")
        yield Footer()

    def action_retour(self) -> None:
        self.app.pop_screen()
