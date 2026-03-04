
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

import pytest

from services.runner_service.app.runner_evenements_v2 import RunnerEvenementsV2, ConfigRunnerEvenementsV2
from services.world_sim.app.evenements import Evenement


class MondeStub:
    def __init__(self) -> None:
        self.ticks = 0
        self.recu: List[Evenement] = []

    def appliquer_evenements(self, evts: List[Evenement]) -> None:
        # le runner ne filtre pas: on doit recevoir exactement ce qu'il draine.
        self.recu.extend(evts)

    def tick(self) -> None:
        self.ticks += 1


class ObjetActifStub:
    def __init__(self, source_id: str = "objet_stub") -> None:
        self.source_id = source_id

    def est_actif(self) -> bool:
        return True

    def emettre_evenements(self, ctx: Any, bus: Any) -> None:
        # publie une action à chaque tick (direction fixe)
        bus.publier(
            Evenement(
                type="action_motrice",
                source_id=self.source_id,
                tick=int(getattr(ctx, "tick")),
                payload={"direction": "avant"},
            )
        )


class ObjetQuiNeDoitPasEtreAppelee:
    def est_actif(self) -> bool:
        return True

    def emettre_evenements(self, ctx: Any, bus: Any) -> None:
        raise AssertionError("emettre_evenements ne doit pas être appelée en mode=epreuve")


def _group_par_tick(journal: List[Evenement]) -> dict[int, list[Evenement]]:
    out: dict[int, list[Evenement]] = {}
    for e in journal:
        out.setdefault(int(e.tick), []).append(e)
    return out


def test_timeline_entrainement_tick_annonce_action_tick_survenu():
    monde = MondeStub()
    objets = [ObjetActifStub("ia_demo_0001")]
    cfg = ConfigRunnerEvenementsV2(mode="entrainement", ticks=3, publier_ticks=True)

    runner = RunnerEvenementsV2(monde=monde, objets=objets, config=cfg)
    journal = runner.run()

    # le monde doit avoir reçu exactement la même séquence d'événements
    assert [(e.type, int(e.tick)) for e in monde.recu] == [(e.type, int(e.tick)) for e in journal]
    assert monde.ticks == 3

    g = _group_par_tick(journal)
    assert set(g.keys()) == {0, 1, 2}

    for t in (0, 1, 2):
        types = [e.type for e in g[t]]
        # ordre canonique attendu à l'intérieur d'un tick
        assert types[0] == "tick_annonce"
        assert types[-1] == "tick_survenu"
        assert "action_motrice" in types

        # l'action doit porter le bon tick
        actions = [e for e in g[t] if e.type == "action_motrice"]
        assert len(actions) == 1
        assert int(actions[0].tick) == t
        assert actions[0].payload.get("direction") == "avant"


def test_mode_epreuve_ne_force_pas_emission_objets():
    monde = MondeStub()
    objets = [ObjetQuiNeDoitPasEtreAppelee()]
    cfg = ConfigRunnerEvenementsV2(mode="epreuve", ticks=2, publier_ticks=True)

    runner = RunnerEvenementsV2(monde=monde, objets=objets, config=cfg)
    journal = runner.run()

    # seulement les ticks (annonce/survenu), aucune action
    assert all(e.type in {"tick_annonce", "tick_survenu"} for e in journal)
    assert monde.ticks == 2


def test_publier_ticks_false_ne_genere_aucun_tick_event():
    monde = MondeStub()
    objets = [ObjetActifStub("ia_demo_0001")]
    cfg = ConfigRunnerEvenementsV2(mode="entrainement", ticks=2, publier_ticks=False)

    runner = RunnerEvenementsV2(monde=monde, objets=objets, config=cfg)
    journal = runner.run()

    assert all(e.type != "tick_annonce" for e in journal)
    assert all(e.type != "tick_survenu" for e in journal)
    # mais on a toujours les actions
    assert [e.type for e in journal] == ["action_motrice", "action_motrice"]
