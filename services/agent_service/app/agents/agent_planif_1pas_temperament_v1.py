# services/agent_service/app/agents/agent_planif_1pas_temperament_v1.py
from __future__ import annotations

"""Agent planificateur 1-pas avec tempérament (Cours 4).

Idée: choisir l'action qui maximise une valeur locale, calculée à partir de
modèles tabulaires appris offline depuis un journal.

Contraintes pédagogiques:
- aucune règle ad hoc (ex: interdiction du demi-tour)
- l'inconnu n'est pas "mauvais" par principe: il peut devenir préférable si le connu est néfaste
- un paramètre de tempérament module l'arbitrage prudence/curiosité

Score d'une action a depuis l'état latent z:
  score(a) =
      E[delta_score | z,a]
    + bonus_survie_par_pas
    + cout_par_pas
    - lambda_risque * E[p(termine) | z,a]
    + beta_curiosite * bonus_curiosite(support(z,a))

Avec un a priori sur l'inconnu:
- si (z,a) est inconnu, on utilise un a priori (p_term_prior_inconnu, delta_prior=0)
- le bonus de curiosité est maximal (support=0)

Ce design rend l'inconnu:
- pénalisé si le tempérament est très prudent (lambda élevé, beta faible)
- attractif si le connu est mauvais (mort probable) et que beta_curiosite>0
"""

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from commun.contrats import Pixel

from agent_service.app.modele_monde.entrainement_depuis_journal import (
    entrainer_modele_tabulaire_v1,
    entrainer_utilite_tabulaire_v1,
)
from agent_service.app.modele_monde.latent_v1 import ModeLatent, encoder_latent
from world_sim.app.arenes_yaml import charger_arene_v0

from agent_service.app.contrats_agents import ContexteDecision, IAgentArene
from .utils_observations import pixels_depuis_contexte


def _bonus_curiosite_support(support: int) -> float:
    """Bonus monotone décroissant avec le support.

    - support=0 => bonus=1.0 (inconnu)
    - support augmente => bonus diminue
    """
    s = max(0, int(support))
    return 1.0 / (1.0 + float(s) ** 0.5)


@dataclass(frozen=True)
class ParametresTemperament:
    """Paramètres de tempérament pour l'arbitrage risque / curiosité."""

    # styles: "prudent" | "equilibre" | "curieux" | "audacieux"
    style: str = "equilibre"

    # poids principaux
    lambda_risque: float = 6.0
    beta_curiosite: float = 1.0

    # a priori sur l'inconnu
    p_term_prior_inconnu: float = 0.20
    delta_prior_inconnu: float = 0.0

    # espace d'actions
    actions: Tuple[str, ...] = ("haut", "bas", "gauche", "droite")

    @staticmethod
    def depuis_style(style: str) -> "ParametresTemperament":
        s = (style or "").strip().lower()
        if s == "prudent":
            return ParametresTemperament(style="prudent", lambda_risque=10.0, beta_curiosite=0.3, p_term_prior_inconnu=0.25)
        if s == "curieux":
            return ParametresTemperament(style="curieux", lambda_risque=5.0, beta_curiosite=2.5, p_term_prior_inconnu=0.20)
        if s == "audacieux":
            return ParametresTemperament(style="audacieux", lambda_risque=3.0, beta_curiosite=1.8, p_term_prior_inconnu=0.18)
        # défaut: équilibré
        return ParametresTemperament(style="equilibre", lambda_risque=6.0, beta_curiosite=1.0, p_term_prior_inconnu=0.20)


class AgentPlanif1PasTemperamentV1(IAgentArene):
    """Planification 1-pas: compare des futurs immédiats (imagination courte)."""

    id_agent = "planif_1pas_temperament"

    def __init__(
        self,
        seed: int | None = None,
        mode_latent: ModeLatent = "checksum",
        params: ParametresTemperament | None = None,
        instruments: list[object] | None = None,
    ) -> None:
        self._rng = random.Random(seed)
        self._mode_latent: ModeLatent = mode_latent
        self._params: ParametresTemperament = params or ParametresTemperament.depuis_style(os.environ.get("SNAKE_TEMPERAMENT", "equilibre"))
        self._instruments = list(instruments or [])

        # Ce planificateur s'appuie sur les journaux "checksum" (cours 1/4).
        if self._mode_latent != "checksum":
            raise ValueError(
                f"mode_latent={self._mode_latent!r} non supporté pour cet agent: utilisez --latent checksum (ou recodez le journal en latent_id)."
            )

        # journal source du monde tabulaire
        p = os.environ.get("SNAKE_MODELE_JOURNAL")
        if not p:
            raise EnvironmentError(
                "SNAKE_MODELE_JOURNAL manquant. Exemple: export SNAKE_MODELE_JOURNAL=artefacts/episodes_cours4_recompense.jsonl"
            )
        journal_path = Path(p)
        if not journal_path.exists():
            raise FileNotFoundError(f"SNAKE_MODELE_JOURNAL introuvable: {journal_path}")

        # coût par pas (epsilon) depuis l'arène courante si disponible
        self._cout_par_pas = 0.0
        self._bonus_survie_par_pas = 0.0
        p_arene = os.environ.get("SNAKE_ARENE_PATH")
        if p_arene:
            try:
                ar = charger_arene_v0(Path(p_arene))
                self._cout_par_pas = float(getattr(ar, "epsilon_par_pas", 0.0))
            except Exception:
                self._cout_par_pas = 0.0

        # shaping optionnel piloté par env (pédagogie)
        try:
            self._bonus_survie_par_pas = float(os.environ.get("SNAKE_BONUS_SURVIE_PAR_PAS", "0.0"))
        except Exception:
            self._bonus_survie_par_pas = 0.0

        # apprentissage offline (tabulaire)
        champ_latent = os.environ.get("SNAKE_CHAMP_LATENT", "checksum").strip() or "checksum"
        self.modele_monde, _ = entrainer_modele_tabulaire_v1(journal_path, champ_latent=champ_latent)
        self.modele_r, self.modele_t, _ = entrainer_utilite_tabulaire_v1(journal_path, champ_latent=champ_latent)

    def _evaluer_action(self, z: int, a: str) -> float:
        pred = self.modele_monde.predire(z, a)
        support = int(getattr(pred, "support", 0))

        # inconnu => a priori
        if support <= 0 or not getattr(pred, "distribution", None):
            exp_delta = float(self._params.delta_prior_inconnu)
            exp_p_fin = float(self._params.p_term_prior_inconnu)
            bonus_curio = _bonus_curiosite_support(0)
        else:
            dist: Dict[int, float] = {int(k): float(v) for k, v in pred.distribution.items()}
            exp_delta = 0.0
            exp_p_fin = 0.0
            for z1, pz1 in dist.items():
                pr = self.modele_r.predire(z, a, int(z1))
                delta = float(pr.esperance) if pr.support > 0 else 0.0

                pt = self.modele_t.predire(z, a, int(z1))
                p_fin = float(pt.proba_termine) if pt.support > 0 else 0.0

                exp_delta += float(pz1) * float(delta)
                exp_p_fin += float(pz1) * float(p_fin)

            bonus_curio = _bonus_curiosite_support(support)

        score = 0.0
        score += exp_delta
        score += float(self._bonus_survie_par_pas)
        score += float(self._cout_par_pas)
        score -= float(self._params.lambda_risque) * float(exp_p_fin)
        score += float(self._params.beta_curiosite) * float(bonus_curio)
        return float(score)

    def definir_instruments(self, instruments: list[object]) -> None:
        self._instruments = list(instruments)

    def instruments(self) -> list[object]:
        return list(self._instruments)

    def choisir_action(self, contexte: ContexteDecision) -> str:
        capteurs = pixels_depuis_contexte(contexte)
        z = int(encoder_latent(capteurs, self._mode_latent))

        meilleur = float("-inf")
        meilleures: list[str] = []

        for a in self._params.actions:
            s = self._evaluer_action(z, a)
            if s > meilleur + 1e-12:
                meilleur = s
                meilleures = [a]
            elif abs(s - meilleur) <= 1e-12:
                meilleures.append(a)

        if not meilleures:
            return self._rng.choice(list(self._params.actions))
        return self._rng.choice(meilleures)

