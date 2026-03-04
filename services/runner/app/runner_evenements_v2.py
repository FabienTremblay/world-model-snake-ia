from __future__ import annotations

from dataclasses import dataclass
from typing import List

from services.world_sim.app.evenements import BusEvenements, Evenement
from services.world_sim.app.objets_du_monde import ObjetDuMonde, ContexteTick
from services.world_sim.app.monde_evenementiel import MondeEvenementiel


@dataclass
class ConfigRunnerEvenementsV2:
    mode: str  # "entrainement" (E/pull) ou "epreuve" (F/push)
    ticks: int = 100
    publier_ticks: bool = True  # tick_annonce / tick_survenu


class RunnerEvenementsV2:
    """Runner événementiel v2.

    - entraînement (E/pull) :
        le runner donne la chance aux objets actifs d'émettre (collecte),
        puis transmet *tous* les événements au monde.
    - épreuve (F/push) :
        les objets publient sur le bus en autonomie;
        le runner ne fait que gérer l'horloge (tick events optionnels) et transmettre au monde.

    Important :
    - Inaction = aucun événement émis par l'objet à ce tick.
    - Le runner ne filtre pas et ne "réduit" rien.
    """

    def __init__(self, monde: MondeEvenementiel, objets: List[ObjetDuMonde], config: ConfigRunnerEvenementsV2) -> None:
        self.monde = monde
        self.objets = objets
        self.config = config
        self.bus = BusEvenements()

    def run(self) -> List[Evenement]:
        journal: List[Evenement] = []

        for t in range(self.config.ticks):
            ctx = ContexteTick(tick=t)

            if self.config.publier_ticks:
                self.bus.publier_tick_annonce(t)

            if self.config.mode == "entrainement":
                # E / pull
                for obj in self.objets:
                    if getattr(obj, "est_actif", False):
                        obj.emettre_evenements(ctx, self.bus)

            elif self.config.mode == "epreuve":
                # F / push : les objets ont pu publier en amont.
                # On ne force pas l'émission ici.
                pass
            else:
                raise ValueError(f"mode inconnu: {self.config.mode}")

            if self.config.publier_ticks:
                self.bus.publier_tick_survenu(t)

            evts = self.bus.drainer()
            journal.extend(evts)

            # Le monde reçoit tout.
            self.monde.appliquer_evenements(evts)
            self.monde.tick()

        return journal
