# services/agent_service/app/agents/agent_planif_mpc_observateur_tabulaire.py
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene
from agent_service.app.agents.utils_observations import pixels_depuis_contexte
from agent_service.app.modele_monde.entrainement_depuis_journal import (
    entrainer_modele_tabulaire_v1,
    entrainer_utilite_observateur_tabulaire_v1,
)
from agent_service.app.modele_monde.latent_v1 import encoder_latent
from agent_service.app.modele_monde.planification_mpc_observateur_v1 import (
    ParametresMPCObservateur,
    choisir_action_mpc_observateur,
)


@dataclass(frozen=True)
class ParametresAgentPlanifMPCObservateur:
    horizon: int = 10
    rollouts_par_action: int = 30
    gamma: float = 1.0
    bonus_survie_par_pas: float = 0.01
    penalite_inconnu: float = 0.2
    penalite_fin: float = 1.0
    proba_fin_inconnue: float = 0.5
    actions: Sequence[str] = ("haut", "bas", "gauche", "droite")


class AgentPlanifMPCObservateurTabulaire(IAgentArene):
    """MPC tabulaire, objectif = utilité d'observateur (signaux_percus)."""

    id_agent = "planif_mpc_observateur_tabulaire"

    def __init__(
        self,
        seed: int | None,
        mode_latent: str,
        params: ParametresAgentPlanifMPCObservateur | None = None,
        instruments: list[object] | None = None,
    ) -> None:
        self._rng = random.Random(int(seed) if seed is not None else None)
        self._mode_latent = str(mode_latent)
        self._params = params or ParametresAgentPlanifMPCObservateur()
        self._instruments = list(instruments or [])

        p = os.environ.get("SNAKE_MODELE_JOURNAL")
        if not p:
            raise ValueError("SNAKE_MODELE_JOURNAL manquant (journal pour entraîner les modèles).")
        journal_path = Path(p)
        if not journal_path.exists():
            raise FileNotFoundError(f"SNAKE_MODELE_JOURNAL introuvable: {journal_path}")

        # IMPORTANT (Cours 4):
        # - champ_latent="checksum" => états injectifs => faible généralisation
        # - champ_latent="signaux_hash" (ou autre) => regroupe par signaux perçus
        champ_latent = os.environ.get("SNAKE_CHAMP_LATENT", "checksum").strip() or "checksum"

        self.modele_monde, _ = entrainer_modele_tabulaire_v1(journal_path, champ_latent=champ_latent)
        self.modele_u, self.modele_t, _ = entrainer_utilite_observateur_tabulaire_v1(journal_path, champ_latent=champ_latent)

    def definir_instruments(self, instruments: list[object]) -> None:
        self._instruments = list(instruments)

    def instruments(self) -> list[object]:
        return list(self._instruments)

    def choisir_action(self, ctx: ContexteDecision) -> str:
        capteurs = pixels_depuis_contexte(ctx)
        z = int(encoder_latent(capteurs, self._mode_latent))
        p = ParametresMPCObservateur(
            horizon=int(self._params.horizon),
            rollouts_par_action=int(self._params.rollouts_par_action),
            gamma=float(self._params.gamma),
            bonus_survie_par_pas=float(self._params.bonus_survie_par_pas),
            penalite_inconnu=float(self._params.penalite_inconnu),
            penalite_fin=float(self._params.penalite_fin),
            proba_fin_inconnue=float(self._params.proba_fin_inconnue),
        )
        return choisir_action_mpc_observateur(
            rng=self._rng,
            modele_monde=self.modele_monde,
            modele_u=self.modele_u,
            modele_t=self.modele_t,
            z0=z,
            actions=self._params.actions,
            params=p,
        )

