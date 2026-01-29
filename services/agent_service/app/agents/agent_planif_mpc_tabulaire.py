# services/agent_service/app/agents/agent_planif_mpc_tabulaire.py
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from agent_service.app.agents.contrats import ContexteDecision, IAgent
from agent_service.app.modele_monde.entrainement_depuis_journal import (
    entrainer_modele_tabulaire_v1,
    entrainer_utilite_tabulaire_v1,
)
from agent_service.app.modele_monde.latent_v1 import encoder_latent
from agent_service.app.modele_monde.planification_mpc_v1 import ParametresMPC, choisir_action_mpc
from world_sim.app.arenes_yaml import charger_arene_v0

@dataclass(frozen=True)
class ParametresAgentPlanifMPC:
    horizon: int = 10
    rollouts_par_action: int = 30
    bonus_survie_par_pas: float = 0.01
    gamma: float = 1.0
    penalite_inconnu: float = 3.0
    penalite_fin: float = 10.0
    # espace d'actions
    actions: Sequence[str] = ("haut", "bas", "gauche", "droite")


class AgentPlanifMPCTabulaire(IAgent):
    """Agent MPC tabulaire (cours 4).

    Charge/entraîne offline des modèles depuis un journal existant.
    Le chemin est lu depuis la variable d'environnement:
      - SNAKE_MODELE_JOURNAL (obligatoire)
    """

    def __init__(self, seed: int | None, mode_latent: str, params: ParametresAgentPlanifMPC | None = None) -> None:
        self._rng = random.Random(int(seed) if seed is not None else None)
        self._mode_latent = str(mode_latent)
        self._params = params or ParametresAgentPlanifMPC()
        self._cout_par_pas = 0.0
        # optionnel: pour aligner l'objectif MPC avec l'arène courante
        # (le monde applique déjà epsilon_par_pas, mais le score journalisé ne le reflète pas)

        p = os.environ.get("SNAKE_MODELE_JOURNAL")
        if not p:
            raise ValueError("SNAKE_MODELE_JOURNAL manquant (chemin du journal pour entraîner les modèles MPC).")
        journal_path = Path(p)
        if not journal_path.exists():
            raise FileNotFoundError(f"SNAKE_MODELE_JOURNAL introuvable: {journal_path}")
        # Lire l'arène si fournie (sinon cout=0). Permet de régler via YAML.
        p_arene = os.environ.get("SNAKE_ARENE_PATH")
        if p_arene:
            try:
                ar = charger_arene_v0(Path(p_arene))
                self._cout_par_pas = float(getattr(ar, "epsilon_par_pas", 0.0))
            except Exception:
                # si l'arène n'est pas lisible, on reste à 0 (agent robuste)
                self._cout_par_pas = 0.0


        # modèles offline (tabulaires)
        self.modele_monde, _ = entrainer_modele_tabulaire_v1(journal_path, champ_latent="checksum" if self._mode_latent == "checksum" else "checksum")
        self.modele_r, self.modele_t, _ = entrainer_utilite_tabulaire_v1(journal_path, champ_latent="checksum" if self._mode_latent == "checksum" else "checksum")

    def choisir_action(self, capteurs, ctx: ContexteDecision) -> str:
        z = int(encoder_latent(capteurs, self._mode_latent))

        p = ParametresMPC(
            horizon=int(self._params.horizon),
            rollouts_par_action=int(self._params.rollouts_par_action),
            bonus_survie_par_pas=float(self._params.bonus_survie_par_pas),
            cout_par_pas=float(self._cout_par_pas),
            gamma=float(self._params.gamma),
            penalite_inconnu=float(self._params.penalite_inconnu),
            penalite_fin=float(self._params.penalite_fin),
        )

        return choisir_action_mpc(
            rng=self._rng,
            modele_monde=self.modele_monde,
            modele_r=self.modele_r,
            modele_t=self.modele_t,
            z0=z,
            actions=self._params.actions,
            params=p,
        )

