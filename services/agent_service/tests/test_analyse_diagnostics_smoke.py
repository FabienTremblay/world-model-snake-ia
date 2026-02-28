from __future__ import annotations

import json
from pathlib import Path

from agent_service.app.analyse.cli.main import executer


def test_analyse_diagnostics_smoke(tmp_path: Path):
    # Structure run minimale
    run_dir = tmp_path / "run1"
    epreuve = run_dir / "epreuve"
    epreuve.mkdir(parents=True)

    # config_epreuve.json local (fallback)
    cfg = {"dummy": True}
    (epreuve / "config_epreuve.json").write_text(json.dumps(cfg), encoding="utf-8")

    # registre_epistemique.json minimal
    reg = {
        "adaptive": {"poids_min": 0.05},
        "gate": {"seuil_surprise": 0.2, "seuil_disagree": 0.3},
        "effets_gate": {
            "ratio_connu_total": 0.8,
            "ratio_inconnu_total": 0.2,
            "ratio_inconnu_surprise": 0.6,
            "ratio_inconnu_disagree": 0.4,
        },
    }
    (epreuve / "registre_epistemique.json").write_text(json.dumps(reg), encoding="utf-8")

    # journal_agent.jsonl minimal
    lignes = [
        {
            "idx": 0,
            "w1": 0.2,
            "w2": 0.8,
            "disagree": 0.1,
            "surprise": 0.1,
            "seuil_disagree": 0.3,
        },
        {
            "idx": 1,
            "w1": 0.21,
            "w2": 0.79,
            "disagree": 0.3,
            "surprise": 0.1,
            "seuil_disagree": 0.3,
        },
    ]
    (epreuve / "journal_agent.jsonl").write_text("\n".join(json.dumps(x) for x in lignes) + "\n", encoding="utf-8")

    res = executer(str(run_dir))

    assert Path(res["rapport_md"]).exists()
    assert Path(res["sortie_json"]).exists()

    payload = json.loads(Path(res["sortie_json"]).read_text(encoding="utf-8"))
    assert "schema_version" in payload
    assert payload["schema_version"] == "sai-a105.diagnostics.v1"
    assert "diagnostics" in payload
    assert len(payload["diagnostics"]) == 3
