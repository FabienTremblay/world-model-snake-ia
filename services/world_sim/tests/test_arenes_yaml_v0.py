# services/world_sim/tests/test_arenes_yaml_v0.py
from __future__ import annotations

from pathlib import Path

from commun.contrats import Pixel
from world_sim.app.arenes_yaml import PalettePixels, charger_arene_v0


def _racine_projet() -> Path:
    # .../services/world_sim/tests/test_*.py -> root = parents[3]
    return Path(__file__).resolve().parents[3]


def test_arenes_yaml_charge_ok() -> None:
    racine = _racine_projet()
    base = racine / "donnees" / "config" / "arenes"

    demo = charger_arene_v0(base / "demo_v0.yml")
    tiny = charger_arene_v0(base / "tiny_v0.yml")

    # --- demo_v0.yml
    assert demo.id == "demo_v0"
    assert demo.largeur == 30
    assert demo.hauteur == 12
    assert demo.seed == 12345
    assert demo.porte_position == (1, 1)

    assert isinstance(demo.palette, PalettePixels)
    # vérif palette (quelques points "load-bearing")
    assert demo.palette.sol == Pixel(teinte=200, intensite=40, motif=0, clignote=0)
    assert demo.palette.mur == Pixel(teinte=210, intensite=120, motif=3, clignote=0)
    assert demo.palette.nourriture == Pixel(teinte=30, intensite=220, motif=6, clignote=1)
    assert demo.palette.porte_fermee == Pixel(teinte=300, intensite=180, motif=1, clignote=0)
    assert demo.palette.porte_ouverte == Pixel(teinte=300, intensite=240, motif=1, clignote=1)

    # --- tiny_v0.yml
    assert tiny.id == "tiny_v0"
    assert tiny.largeur == 12
    assert tiny.hauteur == 8
    assert tiny.seed == 7
    assert tiny.porte_position == (2, 2)

    assert isinstance(tiny.palette, PalettePixels)
    # la palette tiny_v0 est identique dans tes YAML, donc on vérifie une autre paire
    assert tiny.palette.serpent_tete == Pixel(teinte=120, intensite=230, motif=5, clignote=0)
    assert tiny.palette.serpent_corps == Pixel(teinte=120, intensite=160, motif=2, clignote=0)
