from __future__ import annotations

"""Agent "fourmi" pour la campagne snake_collectif_v1.

Objectif : produire un journal "riche" et reproductible, utile aux observateurs.

Contraintes :
- l'agent en arène ne code pas en dur des "concepts".
- il fournit surtout de l'expérience (exploration) pour alimenter le registre.

Actions : respect du contrat ActionSnake (avant / observer_gauche / observer_droite).
"""

from dataclasses import dataclass
from typing import Any, Dict, Tuple, Optional

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene
from commun.actions_snake import ActionSnake
from commun.contrats import Pixel
from instrument.app.contrats import ObservationDonnees, ObservationPixels
from world_sim.app.arenes_yaml import PALETTE_DEFAUT

Position = Tuple[int, int]


def _egal_pixel(a: Pixel, b: Pixel) -> bool:
    return (
        a.teinte == b.teinte
        and a.intensite == b.intensite
        and a.motif == b.motif
        and a.clignote == b.clignote
    )


def _vecteur_depuis_action(action: Action) -> Tuple[int, int]:
    # repère absolu: x -> droite, y -> bas
    if action == "haut":
        return (0, -1)
    if action == "bas":
        return (0, 1)
    if action == "droite":
        return (1, 0)
    if action == "gauche":
        return (-1, 0)
    raise ValueError(f"action invalide: {action!r}")


def _droite(v: Tuple[int, int]) -> Tuple[int, int]:
    dx, dy = v
    return (-dy, dx)


def _gauche(v: Tuple[int, int]) -> Tuple[int, int]:
    dx, dy = v
    return (dy, -dx)


def _normaliser_dir(v: Tuple[int, int]) -> Tuple[int, int]:
    dx, dy = v
    if (dx, dy) in ((0, -1), (0, 1), (1, 0), (-1, 0)):
        return (dx, dy)
    return (0, -1)


def _pixel_cible(patch: list[list[Pixel]], rel: str) -> Pixel:
    # patch carré (2r+1), centre = tête
    n = len(patch)
    c = n // 2
    if rel == "avant":
        return patch[c - 1][c]
    if rel == "droite":
        return patch[c][c + 1]
    if rel == "arriere":
        return patch[c + 1][c]
    if rel == "gauche":
        return patch[c][c - 1]
    raise ValueError(f"rel invalide: {rel!r}")


def _relatif(cand: Tuple[int, int], dir_actuelle: Tuple[int, int]) -> Optional[str]:
    if cand == dir_actuelle:
        return "avant"
    if cand == _droite(dir_actuelle):
        return "droite"
    if cand == (-dir_actuelle[0], -dir_actuelle[1]):
        return "arriere"
    if cand == _gauche(dir_actuelle):
        return "gauche"
    return None


@dataclass
class ParamsFourmi:
    poids_nouveaute: float = 1.0
    bonus_nourriture: float = 5.0
    penalite_demi_tour: float = 0.25
    epsilon: float = 0.02

class AgentSnakeCollectifV1Fourmi(IAgentArene):
    id_agent = "snake_collectif_v1_fourmi"

    def __init__(
        self,
        seed: int | None = None,
        instruments: list[object] | None = None,
        params: ParamsFourmi | None = None,
    ) -> None:
        import random
        self.rng = random.Random(seed)
        self._instruments = list(instruments or [])
        self.params = params or ParamsFourmi()

        self._dernier_tick_visite: Dict[Position, int] = {}
        self._position_precedente: Optional[Position] = None
        self._dir_precedente: Tuple[int, int] = (0, -1)  # haut

    def definir_instruments(self, instruments: list[object]) -> None:
        self._instruments = list(instruments)

    def instruments(self) -> list[Any]:
        return list(self._instruments)

    def _extraire_position(self, contexte: ContexteDecision) -> Position:
        obs = contexte.observations.get("gps_v1")
        if obs is None:
            raise ValueError("gps_v1 manquant (agent fourmi requiert gps_v1)")
        if not isinstance(obs, ObservationDonnees):
            raise TypeError(f"gps_v1 attendu ObservationDonnees, reçu {type(obs)}")
        tete = obs.donnees.get("tete")
        if not (isinstance(tete, (list, tuple)) and len(tete) == 2):
            raise ValueError(f"gps_v1.donnees['tete'] invalide: {tete!r}")
        return (int(tete[0]), int(tete[1]))

    def _extraire_patch_camera(self, contexte: ContexteDecision) -> list[list[Pixel]]:
        obs = contexte.observations.get("camera_egocentree_v1")
        if obs is None:
            raise ValueError("camera_egocentree_v1 manquant (agent fourmi requiert camera_egocentree_v1)")
        if not isinstance(obs, ObservationPixels):
            raise TypeError(f"camera_egocentree_v1 attendu ObservationPixels, reçu {type(obs)}")
        return obs.pixels

    def choisir_action(self, contexte: ContexteDecision) -> ActionSnake:
        pos = self._extraire_position(contexte)
        patch = self._extraire_patch_camera(contexte)

        if self._position_precedente is not None:
            dx = pos[0] - self._position_precedente[0]
            dy = pos[1] - self._position_precedente[1]
            if (dx, dy) != (0, 0):
                self._dir_precedente = _normaliser_dir((dx, dy))
        dir_actuelle = self._dir_precedente

        self._dernier_tick_visite[pos] = int(contexte.tick)

        actions = [ActionSnake.AVANT, ActionSnake.OBSERVER_GAUCHE, ActionSnake.OBSERVER_DROITE]

        if self.rng.random() < self.params.epsilon:
            # petite exploration aléatoire
            self._position_precedente = pos
            a = self.rng.choice(actions)
            # met à jour l'orientation interne si on tourne
            if a == ActionSnake.OBSERVER_GAUCHE:
                self._dir_precedente = _gauche(dir_actuelle)
            elif a == ActionSnake.OBSERVER_DROITE:
                self._dir_precedente = _droite(dir_actuelle)
            return a

        palette = PALETTE_DEFAUT
        obstacles = {palette.mur, palette.serpent_corps, palette.serpent_tete, palette.porte_fermee}

        def est_obstacle(px: Pixel) -> bool:
            return any(_egal_pixel(px, o) for o in obstacles)

        def est_nourriture(px: Pixel) -> bool:
            return _egal_pixel(px, palette.nourriture)

        # On évalue 3 options relatives : AVANT, tourner gauche, tourner droite.
        # Pour un tournant, on "projette" la case qui serait devant après la rotation,
        # mais l'action du tick ne bouge pas : elle ne fait qu'orienter.
        def score_action(a: ActionSnake) -> float:
            if a == ActionSnake.AVANT:
                dir_proj = dir_actuelle
                px = _pixel_cible(patch, "avant")
                if est_obstacle(px):
                    return -1e18
            elif a == ActionSnake.OBSERVER_GAUCHE:
                dir_proj = _gauche(dir_actuelle)
                px = _pixel_cible(patch, "gauche")
                if est_obstacle(px):
                    return -1e18
            else:
                dir_proj = _droite(dir_actuelle)
                px = _pixel_cible(patch, "droite")
                if est_obstacle(px):
                    return -1e18

            pos_suiv = (pos[0] + dir_proj[0], pos[1] + dir_proj[1])
            dernier = self._dernier_tick_visite.get(pos_suiv)
            nouveaute = 1.0 if dernier is None else max(0.0, float(contexte.tick - dernier))

            score = self.params.poids_nouveaute * nouveaute
            if est_nourriture(px):
                score += self.params.bonus_nourriture
            # évite les oscillations inutiles
            if a != ActionSnake.AVANT:
                score -= 0.05
            score += self.rng.random() * 0.001
            return score

        best = max(actions, key=score_action)
        self._position_precedente = pos
        if best == ActionSnake.OBSERVER_GAUCHE:
            self._dir_precedente = _gauche(dir_actuelle)
        elif best == ActionSnake.OBSERVER_DROITE:
            self._dir_precedente = _droite(dir_actuelle)
        # AVANT: l'orientation interne se mettra à jour via le gps au tick suivant
        return best
