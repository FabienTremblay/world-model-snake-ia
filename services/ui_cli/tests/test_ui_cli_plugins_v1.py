from __future__ import annotations

import os
from pathlib import Path

from agent_service.app.catalogue_agents import creer_agent


def test_ui_cli_instancie_agent_depuis_plugins(tmp_path: Path):
    """
    Test d'intégration minimal:
    - prouve que le chemin d'instanciation utilisé par UI_CLI/Runner
      est compatible avec le mode plug-ins (catalogue YAML).
    - on ne lance pas un épisode complet (ça reste un smoke).
    """

    # Agents sans prérequis
    a = creer_agent("aleatoire", params={})
    assert type(a).__name__ == "AgentAleatoire"

    # Agent avec prérequis via env (comme tu l'as fixé pour MPC et 1pas)
    j = tmp_path / "train.jsonl"
    j.write_text('{"tick":0}\n', encoding="utf-8")
    os.environ["SNAKE_MODELE_JOURNAL"] = str(j)

    b = creer_agent("planif_1pas_temperament", params={})
    assert "AgentPlanif1PasTemperament" in type(b).__name__

