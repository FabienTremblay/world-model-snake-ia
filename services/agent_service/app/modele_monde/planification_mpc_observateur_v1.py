# services/agent_service/app/modele_monde/planification_mpc_observateur_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence
import random

from agent_service.app.modele_monde.tabulaire_v1 import ModeleMondeTabulaireV1
from agent_service.app.modele_monde.termination_tabulaire_v1 import ModeleTerminaisonTabulaireV1
from agent_service.app.modele_monde.utilite_observateur_tabulaire_v1 import ModeleUtiliteObservateurTabulaireV1


def _tirer_distribution(dist: dict, rng: random.Random) -> Optional[int]:
    if not dist:
        return None
    r = rng.random()
    acc = 0.0
    for k in sorted(dist.keys()):
        acc += float(dist[k])
        if r <= acc:
            return int(k)
    k_last = next(reversed(sorted(dist.keys())))
    return int(k_last)


@dataclass(frozen=True)
class ParametresMPCObservateur:
    horizon: int = 10
    rollouts_par_action: int = 30
    gamma: float = 1.0
    # quantité subjective : l'observateur préfère "continuer" plutôt que finir vite
    bonus_survie_par_pas: float = 0.01
    # quantité subjective : petit coût (optionnel) pour limiter les errances
    cout_par_pas: float = 0.0
    penalite_inconnu: float = 0.2   # petite, car "inconnu = espoir" possible
    # prudence : une terminaison probable vaut une pénalité (en espérance)
    penalite_fin: float = 1.0
    # contrainte (subjective) : on rejette les actions trop risquées à court terme
    seuil_risque_fin_1pas: float = 0.20
    risque_fin_1pas_mode: str = "esperance"  # "esperance" | "max"


def rollout_imagine(
    rng: random.Random,
    modele_monde: ModeleMondeTabulaireV1,
    modele_u: ModeleUtiliteObservateurTabulaireV1,
    modele_t: ModeleTerminaisonTabulaireV1,
    z0: int,
    actions: Sequence[str],
    params: ParametresMPCObservateur,
) -> float:
    z = int(z0)
    G = 0.0
    w = 1.0

    for _ in range(int(params.horizon)):
        a = rng.choice(list(actions))
        pred = modele_monde.predire(z, a)
        if pred.support <= 0 or not getattr(pred, "distribution", None):
            G -= float(params.penalite_inconnu) * w
            break

        z1 = _tirer_distribution(pred.distribution, rng)
        if z1 is None:
            G -= float(params.penalite_inconnu) * w
            break

        pu = modele_u.predire(z, a, int(z1))
        u = float(pu.esperance) if pu.support > 0 else 0.0

        pt = modele_t.predire(z, a, int(z1))
        p_fin = float(pt.proba_termine) if pt.support > 0 else 0.0

        # jugement subjectif : survivre/continuer vaut quelque chose
        G += (u + float(params.bonus_survie_par_pas) + float(params.cout_par_pas)) * w
        # prudence (espérance) : pénaliser le risque de fin au lieu de tirer au hasard
        G -= float(params.penalite_fin) * float(p_fin) * w

        if p_fin >= 1.0:
            break

        z = int(z1)
        w *= float(params.gamma)

    return float(G)


def _risque_fin_1pas(
    modele_monde: ModeleMondeTabulaireV1,
    modele_t: ModeleTerminaisonTabulaireV1,
    z0: int,
    a0: str,
    mode: str,
) -> Optional[float]:
    pred0 = modele_monde.predire(int(z0), str(a0))
    if pred0.support <= 0 or not getattr(pred0, "distribution", None):
        return None

    dist = dict(pred0.distribution)
    if not dist:
        return None

    if str(mode) == "max":
        rmax = 0.0
        for z1, p in dist.items():
            pt = modele_t.predire(int(z0), str(a0), int(z1))
            p_fin = float(pt.proba_termine) if pt.support > 0 else 0.0
            rmax = max(rmax, float(p_fin))
        return float(rmax)

    # mode = "esperance"
    r = 0.0
    for z1, p in dist.items():
        pt = modele_t.predire(int(z0), str(a0), int(z1))
        p_fin = float(pt.proba_termine) if pt.support > 0 else 0.0
        r += float(p) * float(p_fin)
    return float(r)


def choisir_action_mpc_observateur(
    rng: random.Random,
    modele_monde: ModeleMondeTabulaireV1,
    modele_u: ModeleUtiliteObservateurTabulaireV1,
    modele_t: ModeleTerminaisonTabulaireV1,
    z0: int,
    actions: Sequence[str],
    params: ParametresMPCObservateur,
) -> str:
    meilleures: List[tuple[float, str]] = []
    meilleures_sures: List[tuple[float, str]] = []
    nb_filtrees = 0

    for a0 in actions:
        risque = _risque_fin_1pas(modele_monde, modele_t, int(z0), str(a0), str(params.risque_fin_1pas_mode))
        # si on ne sait pas, on ne filtre pas ici (c'est géré par penalite_inconnu)
        if risque is not None and float(risque) >= float(params.seuil_risque_fin_1pas):
            nb_filtrees += 1

        pred0 = modele_monde.predire(int(z0), str(a0))
        if pred0.support <= 0 or not getattr(pred0, "distribution", None):
            meilleures.append((-float(params.penalite_inconnu), str(a0)))
            continue

        s = 0.0
        for _ in range(int(params.rollouts_par_action)):
            z1 = _tirer_distribution(pred0.distribution, rng)
            if z1 is None:
                s += -float(params.penalite_inconnu)
                continue

            pu = modele_u.predire(int(z0), str(a0), int(z1))
            u0 = float(pu.esperance) if pu.support > 0 else 0.0

            pt = modele_t.predire(int(z0), str(a0), int(z1))
            p_fin0 = float(pt.proba_termine) if pt.support > 0 else 0.0

            # jugement subjectif : même au tick 0, on valorise "continuer"
            G = u0 + float(params.bonus_survie_par_pas) + float(params.cout_par_pas)
            # prudence (espérance)
            G -= float(params.penalite_fin) * float(p_fin0)
            if p_fin0 < 1.0:
                G += rollout_imagine(
                    rng=rng,
                    modele_monde=modele_monde,
                    modele_u=modele_u,
                    modele_t=modele_t,
                    z0=int(z1),
                    actions=actions,
                    params=params,
                )
            s += float(G)

        score = (s / float(params.rollouts_par_action), str(a0))
        meilleures.append(score)
        if risque is None or float(risque) < float(params.seuil_risque_fin_1pas):
            meilleures_sures.append(score)

    # Si on a au moins une action "sûre", on choisit parmi celles-là.
    base = meilleures_sures if meilleures_sures else meilleures
    base.sort(reverse=True, key=lambda x: x[0])

    # tie-break : si plusieurs actions sont quasi équivalentes, choisir au hasard
    meilleur_score = base[0][0]
    eps = 1e-9
    candidats = [a for (s, a) in base if (meilleur_score - s) <= eps]
    if len(candidats) <= 1:
        return base[0][1]
    return rng.choice(candidats)

