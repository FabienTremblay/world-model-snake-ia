from __future__ import annotations

import threading
import os
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from runner.app.main import boucle_episodes

from agent_service.app.main import lancer_spectateur


class Grille(Static):
    def __init__(self, bus: BusEtatMemoire, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bus = bus

    def texte(self) -> str:
        obs = self.bus.dernier()
        if obs is None:
            return "(en attente...)"
        return "\n".join(obs.rendu_debug)


class SnakeTui(App):
    BINDINGS = [
        ("q", "quitter", "Quitter"),
        ("p", "pause", "Pause"),
        ("s", "step", "Step"),
        ("r", "reset", "Reset épisode"),
        ("b", "bruit_plus", "Bruit +"),
        ("v", "bruit_moins", "Bruit -"),
        ("1", "replay_10", "Replay 10"),
        ("2", "replay_20", "Replay 20"),
        ("3", "replay_30", "Replay 30"),
        ("4", "replay_40", "Replay 40"),
        ("5", "replay_50", "Replay 50"),
        ("6", "replay_60", "Replay 60"),
        ("7", "replay_70", "Replay 70"),
        ("8", "replay_80", "Replay 80"),
        ("9", "replay_90", "Replay 90"),
        ("0", "replay_100", "Replay 100"),
        ("+", "plus_vite", "Plus vite"),
        ("-", "moins_vite", "Moins vite"),
        ("up", "dir_haut", "Haut"),
        ("down", "dir_bas", "Bas"),
        ("left", "dir_gauche", "Gauche"),
        ("right", "dir_droite", "Droite"),
        ("k", "dir_haut", "Haut (k)"),
        ("j", "dir_bas", "Bas (j)"),
        ("h", "dir_gauche", "Gauche (h)"),
        ("l", "dir_droite", "Droite (l)"),
    ]

    def __init__(self, bus, controle):
        super().__init__()
        self.bus = bus
        self.controle = controle

    def compose(self) -> ComposeResult:
        mode = os.getenv("SNAKE_MODE", "LIVE")
        yield Header()
        with Vertical():
            yield Static(f"Snake TUI (v0) — {mode} — rendu ASCII + flux runner", id="titre")
            yield Grille(self.bus, id="grille")
            yield Static("", id="hud")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.05, self._rafraichir)

    def _rafraichir(self) -> None:
        obs = self.bus.dernier()
        hud = self.query_one("#hud", Static)
        grille = self.query_one("#grille", Grille)

        delai_ms = int(self.controle.delai_s() * 1000)
        etat_pause = "pause" if self.controle.est_en_pause() else "run"
        niveau_bruit = self.controle.niveau_bruit()
        mode = os.getenv("SNAKE_MODE", "LIVE")

        if obs is None:
            hud.update(f"mode: {mode} | tick: - | score: - | longueur: - | {etat_pause} | delai: {delai_ms}ms | bruit: {niveau_bruit}")
            grille.update("(en attente...)")
        else:
            hud.update(
                f"mode: {mode} | run: {obs.run_id} | episode: {obs.episode_id} | tick: {obs.tick} | score: {obs.score} | longueur: {obs.longueur} | {etat_pause} | delai: {delai_ms}ms | bruit: {niveau_bruit}"
                + (f" | {obs.mesure_bruit}" if obs.mesure_bruit else "")
                + (f" | termine: {obs.raison_fin}" if obs.termine else "")
            )
            # mise à jour explicite de la grille (fiable)
            grille.update("\n".join(obs.rendu_debug))

        # pas besoin d'un refresh global, update() gère le repaint

    def action_quitter(self) -> None:
        self.exit()

    def action_pause(self) -> None:
        self.controle.basculer_pause()

    def action_step(self) -> None:
        # step utile seulement si en pause (sinon, ça ne change rien)
        self.controle.demander_step()

    def action_reset(self) -> None:
        self.controle.demander_reset()

    def action_bruit_plus(self) -> None:
        self.controle.ajuster_bruit(+1)

    def action_bruit_moins(self) -> None:
        self.controle.ajuster_bruit(-1)

    def _mode_replay(self) -> bool:
        return os.getenv("SNAKE_MODE", "LIVE").upper() == "REPLAY"

    def _charger_slot(self, slot: int) -> None:
        if self._mode_replay():
            self.controle.demander_replay_slot(slot)

    def action_replay_10(self) -> None: self._charger_slot(10)
    def action_replay_20(self) -> None: self._charger_slot(20)
    def action_replay_30(self) -> None: self._charger_slot(30)
    def action_replay_40(self) -> None: self._charger_slot(40)
    def action_replay_50(self) -> None: self._charger_slot(50)
    def action_replay_60(self) -> None: self._charger_slot(60)
    def action_replay_70(self) -> None: self._charger_slot(70)
    def action_replay_80(self) -> None: self._charger_slot(80)
    def action_replay_90(self) -> None: self._charger_slot(90)
    def action_replay_100(self) -> None: self._charger_slot(100)

    def action_plus_vite(self) -> None:
        self.controle.ajuster_delai(-0.01)

    def action_moins_vite(self) -> None:
        self.controle.ajuster_delai(+0.01)

    def action_dir_haut(self) -> None:
        self.controle.definir_direction("haut")
        if self.controle.est_en_pause():
            self.controle.demander_step()

    def action_dir_bas(self) -> None:
        self.controle.definir_direction("bas")
        if self.controle.est_en_pause():
            self.controle.demander_step()

    def action_dir_gauche(self) -> None:
        self.controle.definir_direction("gauche")
        if self.controle.est_en_pause():
            self.controle.demander_step()

    def action_dir_droite(self) -> None:
        self.controle.definir_direction("droite")
        if self.controle.est_en_pause():
            self.controle.demander_step()

def main() -> None:
    bus = BusEtatMemoire()
    controle = ControleExecution(delai_s=0.05, demarrer_en_pause=True)

    lancer_spectateur(bus)

    t = threading.Thread(
        target=boucle_episodes,
        args=(bus, controle),
        kwargs={"ticks_max": 10_000},
        daemon=True,
    )

    t.start()

    SnakeTui(bus, controle).run()


if __name__ == "__main__":
    main()
