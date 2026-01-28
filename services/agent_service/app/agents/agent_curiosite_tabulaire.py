from __future__ import annotations

"""Agent explorateur guidé par un world model tabulaire (offline/CLI).

- utilise un état latent paramétrable: checksum(capteurs) ou discret_v1(capteurs)
- score d'action:
  - très élevé si la clé (z, action) est inconnue
  - sinon combinaison de l'entropie et de (1 - confiance)
- expose `apprendre_transition(z_avant, action, z_apres)` pour permettre
  l'apprentissage en ligne par l'orchestrateur (ui_cli).
"""

import random
from dataclasses import dataclass
from typing import Tuple

from commun.contrats import Pixel

from agent_service.app.modele_monde.latent_v1 import ModeLatent, encoder_latent
from agent_service.app.modele_monde.tabulaire_v1 import ModeleMondeTabulaireV1

from .contrats import ContexteDecision, IAgent


@dataclass(frozen=True)
class ParametresCuriosite:
    """Paramètres de la stratégie de curiosité (epsilon-greedy)."""

    epsilon: float = 0.05
    w_inconnu: float = 10.0
    w_entropie: float = 1.0
    w_inconfiance: float = 1.0  # multiplie (1 - confiance)
    actions: Tuple[str, ...] = ("haut", "bas", "gauche", "droite")


class AgentCuriositeTabulaire(IAgent):
    """Choisit l'action la plus informative selon un modèle tabulaire."""

    def __init__(
        self,
        seed: int | None = None,
        params: ParametresCuriosite | None = None,
        mode_latent: ModeLatent = "checksum",
    ) -> None:
        self.rng = random.Random(seed)
        self.params = params or ParametresCuriosite()
        self.mode_latent: ModeLatent = mode_latent
        self.modele = ModeleMondeTabulaireV1()

    def choisir_action(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> str:
        # epsilon-greedy
        if self.rng.random() < float(self.params.epsilon):
            return self.rng.choice(list(self.params.actions))

        z = encoder_latent(capteurs, self.mode_latent)

        meilleur_score = float("-inf")
        meilleures: list[str] = []

        for a in self.params.actions:
            pred = self.modele.predire(z, a)

            if pred.etat_suivant is None:
                score = float(self.params.w_inconnu)
            else:
                score = (
                    float(self.params.w_entropie) * float(pred.entropie)
                    + float(self.params.w_inconfiance) * float(1.0 - pred.confiance)
                )

            if score > meilleur_score + 1e-12:
                meilleur_score = score
                meilleures = [a]
            elif abs(score - meilleur_score) <= 1e-12:
                meilleures.append(a)

        return self.rng.choice(meilleures) if meilleures else self.rng.choice(list(self.params.actions))

    def apprendre_transition(self, z_avant: int, action: str, z_apres: int) -> None:
        self.modele.apprendre_transition(z_avant, action, z_apres)
