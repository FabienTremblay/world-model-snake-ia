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
from textual.widgets import Footer, Header, Input, OptionList, Static
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
    except Exception as e:
        # ne jamais casser l'écran de stats
        return f"(stats) erreur: {e!r}"


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


def _stats_episode_depuis_jsonl(path: Path) -> dict[int, dict[str, Any]]:
    """Index rapide (en mémoire) : ticks, score_final, raison_fin, run_id."""
    stats: dict[int, dict[str, Any]] = {}
    if not path.exists():
        return stats
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except Exception:
                continue
            ep = int(j.get("episode_id", 0))
            st = stats.setdefault(ep, {"ticks": 0})
            st["ticks"] = st.get("ticks", 0) + 1
            st["run_id"] = j.get("run_id", st.get("run_id"))
            st["score_final"] = j.get("score", st.get("score_final"))
            st["longueur_final"] = j.get("longueur", st.get("longueur_final"))
            if j.get("termine"):
                st["termine"] = True
                st["raison_fin"] = j.get("raison_fin")
    return stats


class EcranSession(Screen[None]):
    BINDINGS = [
        ("escape", "retour_menu", "Menu"),
        ("p", "pause", "Play/Pause"),
        ("s", "step", "Step"),
        ("r", "reset", "Reset"),
        ("j", "toggle_journal", "Journal"),
        ("t", "toggle_stats", "Stats"),
        ("[", "episode_prec", "Épisode -"),
        ("]", "episode_suiv", "Épisode +"),
        ("g", "episode_aller", "Aller"),
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
        self._stats_index: Optional[dict[int, dict[str, Any]]] = None

        self._episode_id_affiche = 0
        self._runner_err: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="situation_root"):
            yield Static("", id="sit_texte")
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
        msg = f"{self.choix.mode.upper()} — gérer un épisode" + (" | " + " ".join(extra) if extra else "")
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

        # stats
        if self._stats_visible and self.bus:
            dernier = self.bus.dernier()
            if dernier is not None:
                self._episode_id_affiche = int(getattr(dernier, "episode_id", self._episode_id_affiche))
                txt = _resume_observation(dernier)
            else:
                txt = "(stats) en attente…"

            # en replay, ajouter un résumé par épisode depuis le jsonl
            if self.choix.mode == "replay" and self.choix.journal_path:
                if self._stats_index is None:
                    self._stats_index = _stats_episode_depuis_jsonl(self.choix.journal_path)
                st = self._stats_index.get(self._episode_id_affiche)
                if st:
                    txt += "\n\n" + (
                        f"Épisode {self._episode_id_affiche} | ticks={st.get('ticks')} | score_final={st.get('score_final')} | longueur_final={st.get('longueur_final')} | termine={st.get('termine', False)}"
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

    def action_toggle_stats(self) -> None:
        self._stats_visible = not self._stats_visible
        self._set_side_visibility()
        if self._stats_visible:
            self.query_one("#stats", Static).update("(stats) …")

    # --- navigation épisode (replay)

    def _max_episode(self) -> int:
        if self._stats_index is None and self.choix.journal_path:
            self._stats_index = _stats_episode_depuis_jsonl(self.choix.journal_path)
        if not self._stats_index:
            return 0
        return max(self._stats_index.keys())

    def action_episode_prec(self) -> None:
        if self.choix.mode != "replay" or not self.controle:
            return
        cible = max(0, self._episode_id_affiche - 1)
        self.controle.demander_episode(cible)

    def action_episode_suiv(self) -> None:
        if self.choix.mode != "replay" or not self.controle:
            return
        max_ep = self._max_episode()
        cible = min(max_ep, self._episode_id_affiche + 1)
        self.controle.demander_episode(cible)

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
            callback=lambda n: self.controle.demander_episode(n) if isinstance(n, int) else None,
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
