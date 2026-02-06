# services/world_sim/tests/test_monde_spawn_v0.py
from __future__ import annotations

import random

from world_sim.app.arenes_yaml import PALETTE_DEFAUT, ReglePorteV0
from world_sim.app.monde_snake import ConfigMonde, MondeSnake


def test_monde_spawn_nourriture_pas_sur_porte() -> None:
    # rendre le test déterministe
    random.seed(12345)

    porte = (5, 3)  # milieu d'une petite grille
    cfg = ConfigMonde(
        largeur=12,
        hauteur=8,
        seed=7,
        nb_nourriture=1,
        niveau_bruit=0,
        arene_id="test",
        epsilon_par_pas=0.0,
        bonus_fin=0.0,
        porte_position=porte,
        porte_ouverte_initiale=False,
        regle_ouverture_porte=ReglePorteV0(longueur_min=999, score_min=999, tick_min=999),
        palette=PALETTE_DEFAUT,
    )

    monde = MondeSnake(cfg)

    # au démarrage
    assert porte not in monde.nourritures

    # forcer plusieurs respawns
    # On provoque un "mange" en téléportant la tête sur la nourriture (DEV/test only)
    for _ in range(50):
        assert porte not in monde.nourritures

        # si pas de nourriture (cas pathologique), on en ajoute une
        if not monde.nourritures:
            monde._ajouter_nourriture()  # volontairement test-only
            assert porte not in monde.nourritures

        # simuler qu'on mange la nourriture pour déclencher respawn
        cible = next(iter(monde.nourritures))
        monde.nourritures.remove(cible)
        monde._ajouter_nourriture()

        assert porte not in monde.nourritures
