# services/world_sim/app/monde_snake.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import random

from commun.contrats import Pixel
from .arenes_yaml import PalettePixels, ReglePorteV0, PALETTE_DEFAUT
from .projection_capteurs import projeter_capteurs, rendre_debug_ascii, appliquer_bruit

Position = Tuple[int, int]


@dataclass
class ConfigMonde:
    largeur: int = 30
    hauteur: int = 12
    seed: int = 12345
    nb_nourriture: int = 1
    niveau_bruit: int = 0  # 0 = aucun, sinon jitter capteurs (signal)
    # v0 arène
    arene_id: str = "legacy_v1"
    epsilon_par_pas: float = 0.0
    bonus_fin: float = 0.0
    porte_position: Position | None = None
    porte_ouverte_initiale: bool = False
    regle_ouverture_porte: ReglePorteV0 = ReglePorteV0()
    palette: PalettePixels = PALETTE_DEFAUT


class MondeSnake:
    """
    Monde réel du snake (état interne).
    L'observation sera produite par une projection (ASCII).
    """

    def __init__(self, config: ConfigMonde) -> None:
        self.config = config
        self.rng = random.Random(config.seed)
        self.termine = False
        self.raison_fin: str | None = None

        self.score = 0
        self.tick = 0
        self.reward_total = 0.0

        # serpent: liste de positions, tête en dernier élément
        cx = config.largeur // 2
        cy = config.hauteur // 2
        self.serpent: List[Position] = [(cx - 2, cy), (cx - 1, cy), (cx, cy)]
        self.direction = "droite"  # direction courante

        self.nourritures: set[Position] = set()

        # porte doit exister avant tout spawn qui appelle _case_libre()
        self.porte_pos = config.porte_position
        self.porte_ouverte = bool(config.porte_ouverte_initiale)

        for _ in range(config.nb_nourriture):
            self._ajouter_nourriture()

    def reset(self) -> None:
        self.__init__(self.config)

    def _dans_monde(self, p: Position) -> bool:
        x, y = p
        return 0 <= x < self.config.largeur and 0 <= y < self.config.hauteur

    def _est_mur(self, p: Position) -> bool:
        x, y = p
        return x == 0 or y == 0 or x == self.config.largeur - 1 or y == self.config.hauteur - 1

    def _case_libre(self, p: Position) -> bool:

        porte_pos = getattr(self, "porte_pos", None)
        if porte_pos is not None and p == porte_pos:
            return False
        return (not self._est_mur(p)) and (p not in self.serpent) and (p not in self.nourritures)

    def _mettre_a_jour_porte(self) -> None:
        if self.porte_pos is None or self.porte_ouverte:
            return
        r = self.config.regle_ouverture_porte
        if (len(self.serpent) >= r.longueur_min) and (self.score >= r.score_min) and (self.tick >= r.tick_min):
            self.porte_ouverte = True


    def _ajouter_nourriture(self) -> None:
        # tente un nombre raisonnable de fois
        for _ in range(10_000):
            x = self.rng.randint(1, self.config.largeur - 2)
            y = self.rng.randint(1, self.config.hauteur - 2)
            p = (x, y)
            if self._case_libre(p):
                self.nourritures.add(p)
                return
        # si on ne trouve pas, monde saturé => terminer
        self.termine = True
        self.raison_fin = "plus_de_place_pour_nourriture"

    def _delta(self, direction: str) -> Position:
        if direction == "haut":
            return (0, -1)
        if direction == "bas":
            return (0, 1)
        if direction == "gauche":
            return (-1, 0)
        if direction == "droite":
            return (1, 0)
        return (0, 0)

    def _direction_opposée(self, d1: str, d2: str) -> bool:
        return (d1, d2) in {
            ("haut", "bas"),
            ("bas", "haut"),
            ("gauche", "droite"),
            ("droite", "gauche"),
        }

    def step(self, direction: str | None = None) -> None:
        """
        Applique une action (direction) et fait évoluer l'état interne.
        """
        if self.termine:
            return

        self.tick += 1
        self.reward_total += float(self.config.epsilon_par_pas)

        # appliquer la direction si valide (pas de demi-tour)
        if direction is not None and direction in {"haut", "bas", "gauche", "droite"}:
            if not self._direction_opposée(direction, self.direction):
                self.direction = direction

        dx, dy = self._delta(self.direction)
        tete_x, tete_y = self.serpent[-1]
        nouvelle_tete = (tete_x + dx, tete_y + dy)

        # collisions mur / soi-même
        if self._est_mur(nouvelle_tete):
            self.termine = True
            self.raison_fin = "collision_mur"
            return
        if nouvelle_tete in self.serpent:
            self.termine = True
            self.raison_fin = "collision_soi"
            return

        # avance
        self.serpent.append(nouvelle_tete)

        # nourriture ?
        if nouvelle_tete in self.nourritures:
            self.nourritures.remove(nouvelle_tete)
            self.score += 1
            # (v0) reward distincte du score, sans changer les contrats
            # self.reward_total += ...
            self._ajouter_nourriture()
            # croissance: on ne retire pas la queue
        else:
            # mouvement normal: retirer la queue
            self.serpent.pop(0)

        # porte v0 (seuils) + fin quand entrée dans porte ouverte
        self._mettre_a_jour_porte()
        if self.porte_pos is not None and self.porte_ouverte and (nouvelle_tete == self.porte_pos):
            self.termine = True
            self.raison_fin = "porte_fin"
            self.reward_total += float(self.config.bonus_fin)
            return

    def observer(self, niveau_bruit: int | None = None) -> tuple[List[List[Pixel]], List[str]]:
        """
        Retourne:
          - capteurs: signal brut (H x W)
          - rendu_debug: ASCII dérivé (DEV ONLY)
        """
        capteurs_canon = projeter_capteurs(
            largeur=self.config.largeur,
            hauteur=self.config.hauteur,
            serpent=self.serpent,
            nourritures=self.nourritures,
            porte=self.porte_pos,
            porte_ouverte=self.porte_ouverte,
            palette=self.config.palette,
        )
        # debug: à partir du canonique (stable, lisible)
        rendu_debug = rendre_debug_ascii(capteurs_canon)
        # capteurs: canonique + bruit (signal)
        capteurs = appliquer_bruit(
            capteurs_canon,
            rng=self.rng,
            niveau_bruit=self.config.niveau_bruit if niveau_bruit is None else int(niveau_bruit),
        )
        return capteurs, rendu_debug
