# services/commun/contrats.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Pixel:
    """
    Capteur visuel minimal (signal).
    - teinte: 0..359 (style HSV hue)
    - intensite: 0..255 (luminosité)
    - motif: 0..7 (texture/pattern discret)
    - clignote: 0|1 (animation simple)
    """
    teinte: int
    intensite: int
    motif: int
    clignote: int


@dataclass(frozen=True)
class Observation:
    run_id: str
    episode_id: int
    tick: int
    capteurs: List[List[Pixel]]  # H x W (signal brut)
    rendu_debug: List[str]       # dérivé (pour TUI / dev seulement)
    mesure_bruit: str | None     # résumé court (DEV/diagnostic)
    score: int
    longueur: int
    termine: bool
    raison_fin: str | None = None


@dataclass(frozen=True)
class Action:
    direction: str  # "haut" | "bas" | "gauche" | "droite"
