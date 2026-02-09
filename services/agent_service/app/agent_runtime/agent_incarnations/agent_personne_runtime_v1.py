# services/agent_service/app/agent_runtime/agent_incarnations/agent_personne_runtime_v1.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from commun.contrats import Pixel
from agent_service.app.agent_runtime.agents_in_arene.contrats import ContexteDecision, IAgent


ACTIONS_PAR_DEFAUT = ("avant", "gauche", "droite")  # adapte si tes actions diffèrent


@dataclass
class SortiesTetes:
    """sorties des têtes spécialisées au tick courant (journalisable)."""
    valeurs: dict[str, Any]


class AgentPersonneRuntimeV1(IAgent):
    """
    incarnation runtime d'un AgentPersonne (artefact sai-a107) pour sai-a108.

    - charge un agent_personne.json (structure + gouvernance + pointeurs de poids)
    - maintient une mémoire runtime (état interne d'instance)
    - calcule des sorties de têtes (placeholder pour l'instant)
    - choisit une action (placeholder pour l'instant)
    """

    def __init__(self, agent_personne_path: str, seed: int | None = None, mode_latent: str = "checksum"):
        self.agent_personne_path = str(agent_personne_path)
        self.seed = seed
        self.mode_latent = str(mode_latent)

        self.agent_personne = self._charger_agent_personne(self.agent_personne_path)

        # mémoire runtime (instance)
        self.memoire: dict[str, Any] = {
            "tick": 0,
            "dernier_latent": None,
            "derniere_action": None,
        }

        # sorties de têtes au dernier tick
        self._sorties_tetes = SortiesTetes(valeurs={})

    @staticmethod
    def _charger_agent_personne(path: str) -> dict[str, Any]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"agent_personne introuvable: {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def reinitialiser(self) -> None:
        self.memoire = {
            "tick": 0,
            "dernier_latent": None,
            "derniere_action": None,
        }
        self._sorties_tetes = SortiesTetes(valeurs={})


    # --- API IAgent ---
    def choisir_action(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> str:
        # tick courant (celui du monde AVANT l'action)
        self.memoire["tick"] = int(contexte.tick)

        # 1) sorties de têtes (placeholder)
        self._sorties_tetes = self._evaluer_tetes_placeholder(capteurs=capteurs, contexte=contexte)

        # 2) policy (placeholder) : doit TOUJOURS retourner une action valide
        action = self._policy_placeholder(capteurs=capteurs, contexte=contexte)
        if action is None:
            # garde-fou : ne jamais laisser None remonter au runner
            action = ACTIONS_PAR_DEFAUT[0]

        self.memoire["derniere_action"] = action
        return action

    def get_sorties_tetes(self) -> dict[str, Any]:
        """accès pour journalisation côté ui_cli / hook."""
        return dict(self._sorties_tetes.valeurs)

    # --- implémentations placeholder (phase 1) ---

    def _evaluer_tetes_placeholder(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> SortiesTetes:
        tetes = self.agent_personne.get("tetes") or []
        out: dict[str, Any] = {}
        for t in tetes:
            tid = t.get("id") or "tete_sans_id"
            # placeholder : on expose un état neutre
            if t.get("type_sortie") == "classification_multiclasse":
                out[tid] = "inconnu"
            else:
                out[tid] = None
        # utile: exposer un mode d'enjeu neutre, même si pas encore entraîné
        out.setdefault("mode_enjeu", "neutre")
        return SortiesTetes(valeurs=out)

    def _policy_placeholder(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> Optional[str]:
        # placeholder ultra-simple (mais total) : toujours une action
        return ACTIONS_PAR_DEFAUT[0]
