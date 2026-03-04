from __future__ import annotations

from services.runner.app.runner_evenements_v2 import RunnerEvenementsV2, ConfigRunnerEvenementsV2
from services.world_sim.app.evenements import Evenement


class MondeStub:
    def __init__(self) -> None:
        self.ticks = 0
        self.recu: list[Evenement] = []

    def appliquer_evenements(self, evts: list[Evenement]) -> None:
        # le runner doit pouvoir pousser les événements au monde
        self.recu.extend(evts)

    def tick(self) -> None:
        self.ticks += 1


def test_runner_evenements_v2_smoke():
    monde = MondeStub()
    cfg = ConfigRunnerEvenementsV2(mode="epreuve", ticks=3, publier_ticks=True)
    runner = RunnerEvenementsV2(monde=monde, objets=[], config=cfg)
    journal = runner.run()

    # tick_annonce + tick_survenu par tick
    assert len(journal) == 3 * 2
    assert monde.ticks == 3
    # le monde reçoit la même séquence
    assert [(e.type, int(e.tick)) for e in monde.recu] == [(e.type, int(e.tick)) for e in journal]
