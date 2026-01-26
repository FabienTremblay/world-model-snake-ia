# services/runner/app/contrats.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Observation:
    tick: int
    grille_ascii: List[str]   # lignes de texte (TUI friendly)
    score: int
    longueur: int
    termine: bool
    raison_fin: str | None = None


@dataclass(frozen=True)
class Action:
    direction: str  # "haut" | "bas" | "gauche" | "droite"
