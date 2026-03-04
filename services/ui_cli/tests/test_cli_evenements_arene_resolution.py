from __future__ import annotations

from pathlib import Path

from ui_cli.app.evenements.cli_evenements import _racine_projet, _resoudre_path_arene


def test_resoudre_arene_par_id_standard_repo():
    racine = _racine_projet()
    p = _resoudre_path_arene(racine, "demo_v0")
    assert isinstance(p, Path)
    # convention repo: donnees/config/arenes
    assert "donnees/config/arenes" in str(p).replace("\\", "/")
    assert p.name == "demo_v0.yml"
    assert p.exists()
