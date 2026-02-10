from __future__ import annotations

import random

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene


class AgentAleatoire(IAgentArene):
    """Agent d'exploration simple.

    Choisit une direction aléatoire à chaque tick.
    Il évite le demi-tour immédiat (haut<->bas, gauche<->droite)
    afin de ne pas générer une séquence d'actions inutilement dégradée.
    """

    ACTIONS = ("haut", "bas", "gauche", "droite")
    OPPOSÉES = {
        ("haut", "bas"),
        ("bas", "haut"),
        ("gauche", "droite"),
        ("droite", "gauche"),
    }

    id_agent = "aleatoire"

    def __init__(self, seed: int | None = None, epsilon: float = 0.0, instruments: list[object] | None = None) -> None:
        self.rng = random.Random(seed)
        self.derniere_action: str | None = None
        # epsilon: probabilité d'ignorer la contrainte d'opposition (rarement utile)
        self.epsilon = float(epsilon)
        self._instruments = list(instruments or [])

    def definir_instruments(self, instruments: list[object]) -> None:
        self._instruments = list(instruments)

    def instruments(self) -> list[object]:
        return list(self._instruments)

    def choisir_action(self, contexte: ContexteDecision) -> str:
        if self.derniere_action is None:
            a = self.rng.choice(list(self.ACTIONS))
            self.derniere_action = a
            return a

        actions = list(self.ACTIONS)
        if self.rng.random() >= self.epsilon:
            actions = [a for a in actions if (a, self.derniere_action) not in self.OPPOSÉES]
            if not actions:
                actions = list(self.ACTIONS)

        a = self.rng.choice(actions)
        self.derniere_action = a
        return a
