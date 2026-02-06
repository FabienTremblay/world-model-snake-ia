# services/agent_service/app/agent_runtime/agent_incarnations/agent_personne_runtime_v1.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_service.app.agents.contrats import IAgent


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

    # --- API IAgent (tu adaptes si ton interface diffère) ---

    def reinitialiser(self) -> None:
        self.memoire = {
            "tick": 0,
            "dernier_latent": None,
            "derniere_action": None,
        }
        self._sorties_tetes = SortiesTetes(valeurs={})

    def decider(self, contexte_decision) -> str:
        """
        contexte_decision contient typiquement (selon ton runner) :
        - latent courant (z)
        - autres infos de perception (capteurs)
        """
        z = getattr(contexte_decision, "latent", None)
        self.memoire["tick"] = int(self.memoire.get("tick", 0)) + 1
        self.memoire["dernier_latent"] = z

        # 1) calculer sorties de têtes (placeholder)
        self._sorties_tetes = self._evaluer_tetes_placeholder(contexte_decision)

        # 2) décider action (placeholder)
        action = self._policy_placeholder(contexte_decision)

        self.memoire["derniere_action"] = action
        return action

    def get_sorties_tetes(self) -> dict[str, Any]:
        """accès pour journalisation côté ui_cli / hook."""
        return dict(self._sorties_tetes.valeurs)

    # --- implémentations placeholder (phase 1) ---

    def _evaluer_tetes_placeholder(self, contexte_decision) -> SortiesTetes:
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

    def _policy_placeholder(self, contexte_decision) -> str:
        # placeholder ultra-simple : avance sinon tourne (à remplacer par vraie policy)
        # si ton moteur a des contraintes d'action, c'est ici qu'on les intégrera.
        return ACTIONS_PAR_DEFAUT[0]
