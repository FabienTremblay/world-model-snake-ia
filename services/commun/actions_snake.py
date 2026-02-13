"""Langage canonique des actions pour le jeu Snake (TUI/CLI/runner/agents).

Objectif :
  - fournir une norme unique de libellés d'actions pour tous les agents incarnés en arène
  - éviter les divergences (ex. 'haut/bas/gauche/droite' vs 'avant/observer_gauche/observer_droite')
  - stabiliser le replay et les interfaces (TUI, ui_cli)

Règle :
  - L'agent retourne une action *relative* (par rapport à la direction actuelle de la tête)
  - Le monde applique la dynamique (mise à jour de direction + déplacement)
  - Le journal peut enregistrer séparément la direction absolue appliquée si nécessaire
"""

from __future__ import annotations

from typing import Final, Literal

# Identifiants canoniques (compat TUI)
ACTION_AVANT: Final[str] = "avant"
ACTION_OBSERVER_GAUCHE: Final[str] = "observer_gauche"
ACTION_OBSERVER_DROITE: Final[str] = "observer_droite"

ActionSnake = Literal["avant", "observer_gauche", "observer_droite"]

ACTIONS_SNAKE: Final[set[str]] = {
    ACTION_AVANT,
    ACTION_OBSERVER_GAUCHE,
    ACTION_OBSERVER_DROITE,
}


def est_action_snake(action: object) -> bool:
    """Vérifie si `action` respecte le langage canonique Snake."""
    return isinstance(action, str) and action in ACTIONS_SNAKE


def valider_action_snake(action: str) -> None:
    """Lève une exception explicite si l'action n'est pas conforme."""
    if action not in ACTIONS_SNAKE:
        raise ValueError(
            f"action snake invalide: {action!r}. Attendu: {sorted(ACTIONS_SNAKE)}"
        )
