# services/agent_service/app/agent_runtime/agent_incarnations/agent_personne_runtime_v1.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from commun.contrats import Pixel
from agent_service.app.agent_runtime.agents_in_arene.contrats import ContexteDecision, IAgent
from agent_service.app.modele_monde.latent_v1 import extraire_signaux_percus_voisinage_v1


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

    def _policy_placeholder(self, capteurs: list[list[Pixel]], contexte: ContexteDecision) -> str:
        """
        phase 1 (étape 1) : policy anti-mur/anti-corps, sans ml.

        - infère la direction courante via le 'cou' (corps adjacent à la tête, motif==1) si possible
        - calcule ce qu'il y a devant / à gauche / à droite relativement à cette direction
        - si devant est dangereux -> tourne vers le côté libre, sinon -> avance
        """
        # d'après dbg_motifs_voisins observé (gauche=2 au tick 1),
        # ton encodage indique le corps avec la valeur 2.
        MOTIF_CORPS = 2

        def _est_dangereux(motif: int) -> bool:
            # phase 1 robuste : tout ce qui n'est pas du vide est un obstacle
            return int(motif) != 0

        extras = extraire_signaux_percus_voisinage_v1(capteurs)
        if extras is None:
            return "avant"

        mh = int(extras["motif_haut"])
        mb = int(extras["motif_bas"])
        mg = int(extras["motif_gauche"])
        md = int(extras["motif_droite"])

        # debug minimal visible dans metrics.jsonl via sorties_tetes
        try:
            self._sorties_tetes.valeurs["dbg_motifs_voisins"] = {"haut": mh, "bas": mb, "gauche": mg, "droite": md}
        except Exception:
            pass

        # direction courante du monde (source: runner -> ContexteDecision)
        # la direction peut être absente/None selon le runner / le tick initial
        direction = getattr(contexte, "direction", None) or "droite"
        if direction is None:
            # fallback: si on a déjà une direction mémorisée, on la reprend,
            # sinon on se fixe un défaut stable.
            direction = self.memoire.get("direction") or "haut"

        # normaliser (au cas où)
        if direction not in ("haut", "bas", "gauche", "droite"):
            direction = "haut"

        # garder en mémoire pour les prochains ticks
        self.memoire["direction"] = direction


        motifs_abs = {"haut": mh, "bas": mb, "gauche": mg, "droite": md}
        gauche_abs = {"haut": "gauche", "gauche": "bas", "bas": "droite", "droite": "haut"}[direction]
        droite_abs = {"haut": "droite", "droite": "bas", "bas": "gauche", "gauche": "haut"}[direction]

        motif_devant = motifs_abs[direction]
        motif_gauche = motifs_abs[gauche_abs]
        motif_droite = motifs_abs[droite_abs]

        if not _est_dangereux(motif_devant):
            return "avant"

        gauche_ok = not _est_dangereux(motif_gauche)
        droite_ok = not _est_dangereux(motif_droite)
        if gauche_ok and not droite_ok:
            return "observer_gauche"
        if droite_ok and not gauche_ok:
            return "observer_droite"
        if gauche_ok and droite_ok:
            return "observer_gauche"
        return "avant"
