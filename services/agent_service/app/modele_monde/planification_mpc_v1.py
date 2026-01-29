# services/agent_service/app/modele_monde/planification_mpc_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence
import random

from agent_service.app.modele_monde.tabulaire_v1 import ModeleMondeTabulaireV1
from agent_service.app.modele_monde.recompense_tabulaire_v1 import ModeleRecompenseTabulaireV1
from agent_service.app.modele_monde.termination_tabulaire_v1 import ModeleTerminaisonTabulaireV1


def _tirer_distribution(dist: dict, rng: random.Random) -> Optional[int]:
    """Tire une clé (int) selon une distribution {etat: proba}."""
    if not dist:
        return None
    r = rng.random()
    acc = 0.0
    # ordre stable pour reproductibilité
    for k in sorted(dist.keys()):
        acc += float(dist[k])
        if r <= acc:
            return int(k)
    # fallback (erreurs d'arrondi)
    k_last = next(reversed(sorted(dist.keys())))
    return int(k_last)


@dataclass(frozen=True)
class ParametresMPC:
    horizon: int = 10
    rollouts_par_action: int = 30
    bonus_survie_par_pas: float = 0.0
    cout_par_pas: float = 0.0
    gamma: float = 1.0
    # pénalités : arrêt si inconnu, mort très mauvais
    penalite_inconnu: float = 3.0
    penalite_fin: float = 10.0


def rollout_imagine(
    rng: random.Random,
    modele_monde: ModeleMondeTabulaireV1,
    modele_r: ModeleRecompenseTabulaireV1,
    modele_t: ModeleTerminaisonTabulaireV1,
    z0: int,
    actions: Sequence[str],
    params: ParametresMPC,
) -> float:
    """Rollout imaginé (multi-étapes) dans l'espace latent.

    Politique interne (t>0) : aléatoire uniforme sur l'espace d'actions.
    Récompense : delta_score appris + pénalités.
    """
    z = int(z0)
    G = 0.0
    w = 1.0

    for _ in range(int(params.horizon)):
        a = rng.choice(list(actions))  # politique interne (sera améliorée)

        pred = modele_monde.predire(z, a)
        if pred.support <= 0 or not getattr(pred, "distribution", None):
            # transition inconnue => arrêt + pénalité
            G -= float(params.penalite_inconnu) * w
            break

        z1 = _tirer_distribution(pred.distribution, rng)
        if z1 is None:
            G -= float(params.penalite_inconnu) * w
            break

        pr = modele_r.predire(z, a, z1)
        delta = float(pr.esperance) if pr.support > 0 else 0.0

        pt = modele_t.predire(z, a, z1)
        p_fin = float(pt.proba_termine) if pt.support > 0 else 0.0
        termine = (rng.random() < p_fin)

        # cumul: récompense + shaping (survie) + coût par pas
        G += delta * w
        G += float(params.bonus_survie_par_pas) * w
        G += float(params.cout_par_pas) * w

        if termine:
            G -= float(params.penalite_fin) * w
            break

        z = int(z1)
        w *= float(params.gamma)

    return float(G)


def choisir_action_mpc(
    rng: random.Random,
    modele_monde: ModeleMondeTabulaireV1,
    modele_r: ModeleRecompenseTabulaireV1,
    modele_t: ModeleTerminaisonTabulaireV1,
    z0: int,
    actions: Sequence[str],
    params: ParametresMPC,
) -> str:
    """MPC 1-pas : évalue chaque action au temps t par K rollouts futurs."""
    meilleures: List[tuple[float, str]] = []

    for a0 in actions:
        # on force le 1er pas avec a0, puis politique aléatoire ensuite
        pred0 = modele_monde.predire(int(z0), str(a0))
        if pred0.support <= 0 or not getattr(pred0, "distribution", None):
            score_a = -float(params.penalite_inconnu)
            meilleures.append((score_a, str(a0)))
            continue

        s = 0.0
        for _ in range(int(params.rollouts_par_action)):
            z1 = _tirer_distribution(pred0.distribution, rng)
            if z1 is None:
                s += -float(params.penalite_inconnu)
                continue

            pr = modele_r.predire(int(z0), str(a0), int(z1))
            delta0 = float(pr.esperance) if pr.support > 0 else 0.0

            pt = modele_t.predire(int(z0), str(a0), int(z1))
            p_fin0 = float(pt.proba_termine) if pt.support > 0 else 0.0
            termine0 = (rng.random() < p_fin0)

            G = float(delta0)
            G += float(params.bonus_survie_par_pas)
            G += float(params.cout_par_pas)
            if termine0:
                G -= float(params.penalite_fin)
            else:
                # futurs (t+1..)
                G += rollout_imagine(
                    rng=rng,
                    modele_monde=modele_monde,
                    modele_r=modele_r,
                    modele_t=modele_t,
                    z0=int(z1),
                    actions=actions,
                    params=params,
                )

            s += float(G)

        score_a = s / float(params.rollouts_par_action)
        meilleures.append((score_a, str(a0)))

    meilleures.sort(reverse=True, key=lambda x: x[0])
    return meilleures[0][1]

