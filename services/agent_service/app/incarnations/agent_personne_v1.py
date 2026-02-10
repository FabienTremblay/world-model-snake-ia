from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene
from agent_service.app.agents.utils_observations import pixels_depuis_contexte
from agent_service.app.modele_monde.latent_v1 import extraire_signaux_percus_voisinage_v1
from instrument.app.instruments import CameraEgocentreeV1, InstrumentGPSV1


ACTIONS_PAR_DEFAUT = ("avant", "gauche", "droite")


@dataclass
class SortiesTetes:
    """Sorties des têtes spécialisées au tick courant (journalisable)."""

    valeurs: dict[str, Any]


class AgentPersonneV1(IAgentArene):
    """Incarnation runtime d'un AgentPersonne (artefact SAI-E107) pour SAI-A108.

    Rupture : l'agent consomme maintenant les *observations instrumentées* via
    `ContexteDecision.observations`.
    """

    id_agent = "agent_personne_v1"

    def __init__(self, agent_personne_path: str, seed: int | None = None, mode_latent: str = "checksum"):
        self.agent_personne_path = str(agent_personne_path)
        self.seed = seed
        self.mode_latent = str(mode_latent)

        self.agent_personne = self._charger_agent_personne(self.agent_personne_path)

        self.memoire: dict[str, Any] = {
            "tick": 0,
            "dernier_latent": None,
            "derniere_action": None,
        }

        self._sorties_tetes = SortiesTetes(valeurs={})

        # instruments par défaut : caméra incarnée + gps (données)
        self._instruments: list[object] = [CameraEgocentreeV1(rayon=2, niveau_bruit=0, seed_bruit=1), InstrumentGPSV1()]

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

    def definir_instruments(self, instruments: list[object]) -> None:
        self._instruments = list(instruments)

    def instruments(self) -> list[object]:
        return list(self._instruments)

    def choisir_action(self, contexte: ContexteDecision) -> str:
        capteurs = pixels_depuis_contexte(contexte)

        self.memoire["tick"] = int(contexte.tick)
        self._sorties_tetes = self._evaluer_tetes_placeholder(capteurs=capteurs, contexte=contexte)

        action = self._policy_placeholder(capteurs=capteurs, contexte=contexte)
        if not action:
            action = ACTIONS_PAR_DEFAUT[0]
        self.memoire["derniere_action"] = action
        return action

    def get_sorties_tetes(self) -> dict[str, Any]:
        return dict(self._sorties_tetes.valeurs)

    def _evaluer_tetes_placeholder(self, capteurs, contexte: ContexteDecision) -> SortiesTetes:
        tetes = self.agent_personne.get("tetes") or []
        out: dict[str, Any] = {}
        for t in tetes:
            tid = t.get("id") or "tete_sans_id"
            if t.get("type_sortie") == "classification_multiclasse":
                out[tid] = "inconnu"
            else:
                out[tid] = None
        out.setdefault("mode_enjeu", "neutre")
        return SortiesTetes(valeurs=out)

    def _policy_placeholder(self, capteurs, contexte: ContexteDecision) -> str:
        """Policy anti-mur/anti-corps, sans ML (phase 1)."""

        MOTIF_CORPS = 2

        def _est_dangereux(motif: int) -> bool:
            return int(motif) != 0

        extras = extraire_signaux_percus_voisinage_v1(capteurs)
        if extras is None:
            return ACTIONS_PAR_DEFAUT[0]

        motif_avant = int(extras.get("motif_avant", 1))
        motif_gauche = int(extras.get("motif_gauche", 1))
        motif_droite = int(extras.get("motif_droite", 1))

        if not _est_dangereux(motif_avant):
            return "avant"
        # sinon, on privilégie un côté libre
        if not _est_dangereux(motif_gauche):
            return "gauche"
        if not _est_dangereux(motif_droite):
            return "droite"
        return "gauche"
