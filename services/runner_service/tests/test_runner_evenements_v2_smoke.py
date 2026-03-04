from __future__ import annotations

from services.runner_service.app.runner_evenements_v2 import RunnerEvenementsV2, ConfigRunnerEvenementsV2
from services.world_sim.app.monde_snake import MondeSnake, ConfigMonde
from services.world_sim.app.monde_snake_evenementiel import MondeSnakeEvenementiel
from services.agent_service.app.individu_objet_du_monde_v1 import AgentIndividuStubV1


def test_runner_evenements_v2_smoke_entrainement():
    monde = MondeSnake(ConfigMonde(seed=123, largeur=12, hauteur=8, nb_nourriture=1))
    monde_evt = MondeSnakeEvenementiel(monde=monde)

    # Individu stub : action "avant" => le monde avance
    individu = AgentIndividuStubV1(direction="avant")

    runner = RunnerEvenementsV2(
        monde=monde_evt,
        objets=[individu],
        config=ConfigRunnerEvenementsV2(mode="entrainement", ticks=3, publier_ticks=True),
    )

    journal = runner.run()

    # Le monde a avancé 3 ticks
    assert monde.tick == 3

    # On a au moins les ticks annoncés/survenus dans le journal
    assert any(e.type == "tick_annonce" for e in journal)
    assert any(e.type == "tick_survenu" for e in journal)
    assert any(e.type == "action_motrice" for e in journal)


def test_runner_evenements_v2_smoke_epreuve_push_sans_actions():
    monde = MondeSnake(ConfigMonde(seed=456, largeur=12, hauteur=8, nb_nourriture=1))
    monde_evt = MondeSnakeEvenementiel(monde=monde)

    # Individu qui n'émet rien (inaction)
    individu = AgentIndividuStubV1(direction=None)

    runner = RunnerEvenementsV2(
        monde=monde_evt,
        objets=[individu],
        config=ConfigRunnerEvenementsV2(mode="epreuve", ticks=2, publier_ticks=True),
    )

    journal = runner.run()

    # En mode épreuve (F), le runner ne force pas l'émission de l'individu.
    assert not any(e.type == "action_motrice" for e in journal)
    assert monde.tick == 2
