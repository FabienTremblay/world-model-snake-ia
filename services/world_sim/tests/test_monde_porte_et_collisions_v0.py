# services/world_sim/tests/test_monde_porte_et_collisions_v0.py
from __future__ import annotations

from pathlib import Path

from world_sim.app.arenes_yaml import charger_arene_v0, PALETTE_DEFAUT
from world_sim.app.monde_snake import ConfigMonde, MondeSnake


def _racine_projet() -> Path:
    # .../services/world_sim/tests/test_*.py -> root = parents[3]
    return Path(__file__).resolve().parents[3]


def _cfg_depuis_yaml(arene_id: str) -> ConfigMonde:
    racine = _racine_projet()
    path = racine / "donnees" / "config" / "arenes" / f"{arene_id}.yml"
    ar = charger_arene_v0(path)

    return ConfigMonde(
        largeur=ar.largeur,
        hauteur=ar.hauteur,
        seed=ar.seed,
        nb_nourriture=ar.nb_nourriture,
        niveau_bruit=0,  # tests déterministes (signal canonique)
        arene_id=ar.id,
        epsilon_par_pas=ar.epsilon_par_pas,
        bonus_fin=ar.bonus_fin,
        porte_position=ar.porte_position,
        porte_ouverte_initiale=(ar.porte_etat_initial == "ouverte"),
        regle_ouverture_porte=ar.regle_ouverture,
        palette=ar.palette,
    )


def _dir_vers(a: tuple[int, int], b: tuple[int, int]) -> str:
    ax, ay = a
    bx, by = b
    if bx > ax:
        return "droite"
    if bx < ax:
        return "gauche"
    if by > ay:
        return "bas"
    if by < ay:
        return "haut"
    return "droite"


def test_porte_ouvre_sur_seuils() -> None:
    # tiny_v0 : longueur_min=5, score_min=2 (selon ton YAML)
    cfg = _cfg_depuis_yaml("tiny_v0")
    monde = MondeSnake(cfg)

    assert monde.porte_pos is not None, "tiny_v0 doit définir une porte"
    assert monde.porte_ouverte is False, "tiny_v0 démarre porte fermée (attendu)"

    # Stratégie de test (test-only) :
    # on "pilote" vers la nourriture en lisant monde.nourritures
    # -> permet d'atteindre score/longueur de façon déterministe et rapide.
    max_ticks = 500
    for _ in range(max_ticks):
        if monde.termine:
            break

        tete = monde.serpent[-1]
        cible = next(iter(monde.nourritures))
        direction = _dir_vers(tete, cible)

        monde.step(direction)

        # Dès que score/longueur atteints, la porte doit s'ouvrir (après le step).
        r = cfg.regle_ouverture_porte
        if len(monde.serpent) >= r.longueur_min and monde.score >= r.score_min and monde.tick >= r.tick_min:
            assert monde.porte_ouverte is True
            return

    # Si on sort ici, on n'a pas réussi à atteindre les seuils dans la limite
    assert False, f"n'a pas atteint les seuils d'ouverture dans {max_ticks} ticks (score={monde.score}, len={len(monde.serpent)}, termine={monde.termine}, raison={monde.raison_fin})"


def test_fin_par_porte_fin() -> None:
    # On force une porte déjà ouverte et on place le serpent juste à côté.
    cfg = ConfigMonde(
        largeur=12,
        hauteur=8,
        seed=7,
        nb_nourriture=0,
        niveau_bruit=0,
        arene_id="test_fin_porte",
        epsilon_par_pas=0.0,
        bonus_fin=1.0,
        porte_position=(2, 2),
        porte_ouverte_initiale=True,
        regle_ouverture_porte=_cfg_depuis_yaml("tiny_v0").regle_ouverture_porte,  # peu importe ici
        palette=PALETTE_DEFAUT,
    )
    monde = MondeSnake(cfg)

    # Placer le serpent à (1,2) -> (2,2) en allant à droite
    # Important: la porte (2,2) ne doit pas déjà être occupée par le corps.
    monde.serpent = [(1, 4), (1, 3), (1, 2)]  # tête = (1,2)
    monde.direction = "droite"

    assert monde.porte_pos == (2, 2)
    assert monde.porte_ouverte is True

    monde.step(None)

    assert monde.termine is True
    assert monde.raison_fin == "porte_fin"


def test_collision_mur_termine() -> None:
    # On place la tête contre le mur et on avance dans le mur.
    cfg = ConfigMonde(
        largeur=12,
        hauteur=8,
        seed=7,
        nb_nourriture=0,
        niveau_bruit=0,
        arene_id="test_collision_mur",
        epsilon_par_pas=0.0,
        bonus_fin=0.0,
        porte_position=None,
        porte_ouverte_initiale=False,
        regle_ouverture_porte=_cfg_depuis_yaml("tiny_v0").regle_ouverture_porte,
        palette=PALETTE_DEFAUT,
    )
    monde = MondeSnake(cfg)

    # tête en (1,2), direction gauche -> nouvelle tête (0,2) => mur
    monde.serpent = [(3, 2), (2, 2), (1, 2)]
    monde.direction = "gauche"

    monde.step(None)

    assert monde.termine is True
    assert monde.raison_fin == "collision_mur"
