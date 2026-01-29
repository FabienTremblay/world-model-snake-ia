# services/agent_service/app/modele_monde/simulateur_interne_v1.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, Tuple

from agent_service.app.modele_monde.contrats import IModeleMonde, Prediction
from agent_service.app.modele_monde.recompense_tabulaire_v1 import ModeleRecompenseTabulaireV1
from agent_service.app.modele_monde.termination_tabulaire_v1 import ModeleTerminaisonTabulaireV1


def echantillonner_suivant(distribution: dict[int, float], rng: random.Random) -> Optional[int]:
    """Échantillonne un état suivant à partir d'une distribution {etat: prob}.

    Retourne None si la distribution est vide.
    """
    if not distribution:
        return None

    # Par robustesse: on ne suppose pas que la distribution somme exactement à 1.
    items = list(distribution.items())
    total = sum(max(0.0, float(p)) for _k, p in items)
    if total <= 0.0:
        return None

    r = rng.random() * total
    cum = 0.0
    dernier_etat = None
    for etat, p in items:
        dernier_etat = int(etat)
        w = max(0.0, float(p))
        cum += w
        if r <= cum:
            return int(etat)

    # Effets numériques: retourne le dernier.
    return dernier_etat


@dataclass
class ResultatPasInterne:
    etat_suivant: Optional[int]
    inconnu: bool
    prediction: Prediction


@dataclass
class ResultatPasInterneEnrichi:
    etat_suivant: Optional[int]
    delta_score: int
    termine: bool
    inconnu: bool
    prediction_transition: Prediction


class SimulateurInterneV1:
    """Simulateur interne minimal basé sur un modèle du monde tabulaire.

    - 1 pas: (etat, action) -> etat_suivant (sampling)
    - transitions inconnues: renvoie inconnu=True et etat_suivant=None
    """

    def __init__(self, modele: IModeleMonde, seed: Optional[int] = None):
        self._modele = modele
        self._rng = random.Random(seed)

    def step(self, etat: int, action: str) -> ResultatPasInterne:
        pred = self._modele.predire(int(etat), str(action))
        if pred.support <= 0 or not pred.distribution:
            return ResultatPasInterne(etat_suivant=None, inconnu=True, prediction=pred)

        etat_suivant = echantillonner_suivant(pred.distribution, self._rng)
        if etat_suivant is None:
            return ResultatPasInterne(etat_suivant=None, inconnu=True, prediction=pred)

        return ResultatPasInterne(etat_suivant=int(etat_suivant), inconnu=False, prediction=pred)

    def step_enrichi(
        self,
        etat: int,
        action: str,
        modele_recompense: ModeleRecompenseTabulaireV1,
        modele_termination: ModeleTerminaisonTabulaireV1,
    ) -> ResultatPasInterneEnrichi:
        """Pas interne enrichi: transition + récompense + terminaison.

        Convention:
        - si transition inconnue: inconnu=True, etat_suivant=None, delta_score=0, termine=True (arrêt)
        - sinon:
            - etat_suivant est échantillonné depuis le modèle de transition
            - delta_score est échantillonné depuis le modèle de récompense conditionné par (etat, action, etat_suivant)
            - termine est échantillonné via Bernoulli(proba_termine) conditionné par (etat, action, etat_suivant)
        """
        res = self.step(etat, action)
        if res.inconnu or res.etat_suivant is None:
            return ResultatPasInterneEnrichi(
                etat_suivant=None,
                delta_score=0,
                termine=True,
                inconnu=True,
                prediction_transition=res.prediction,
            )

        z1 = int(res.etat_suivant)

        pr = modele_recompense.predire(int(etat), str(action), int(z1))
        delta = 0
        if pr.support > 0 and pr.distribution:
            d = echantillonner_suivant(pr.distribution, self._rng)
            if d is not None:
                delta = int(d)

        pt = modele_termination.predire(int(etat), str(action), int(z1))
        termine = False
        if pt.support > 0:
            termine = (self._rng.random() < float(pt.proba_termine))

        return ResultatPasInterneEnrichi(
            etat_suivant=z1,
            delta_score=int(delta),
            termine=bool(termine),
            inconnu=False,
            prediction_transition=res.prediction,
        )

    def seed(self, seed: int) -> None:
        """Réinitialise le RNG pour reproductibilité."""
        self._rng.seed(int(seed))

    def get_state(self) -> Tuple[int, ...]:
        """Expose l'état interne du RNG (diagnostics)."""
        s = self._rng.getstate()
        # état = (version, tuple, gauss_next)
        return (int(s[0]),) + tuple(s[1])  # type: ignore[arg-type]

