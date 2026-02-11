# services/ui_cli/app/bac_a_sable/tests/test_bac_a_sable_v1.py
from __future__ import annotations

from pathlib import Path

import pytest

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1


def _ecrire_experience_yml(exp_dir: Path, journal_basename: str = "journal.jsonl", run_dir: str = "artefacts/runs") -> None:
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "experience.yml").write_text(
        f"""id: test
description: ""
sorties:
  run_dir: {run_dir}
  journal_basename: {journal_basename}
  capture_stdout: false
""",
        encoding="utf-8",
    )


def test_bac_a_sable_resout_runs_dir_depuis_experience_yml(tmp_path: Path) -> None:
    racine = tmp_path
    exp_id = "exp_test"
    exp_dir = racine / "donnees" / "config" / "experiences" / exp_id
    _ecrire_experience_yml(exp_dir, journal_basename="journal.jsonl", run_dir="artefacts/runs")

    bac = BacASableV1.charger_depuis_id(racine, exp_id)

    assert bac.paths.experience_dir == exp_dir.resolve()
    assert bac.paths.runs_dir == (exp_dir / "artefacts" / "runs").resolve()

    run_dir, journal_path, stdout_path, meta_path = bac.preparer_run(run_tag="x", run_id="r1")
    assert run_dir.exists()
    assert journal_path.name == "journal.jsonl"
    assert stdout_path.name == "stdout.log"
    assert meta_path.name == "meta.json"


def test_bac_a_sable_verifie_journal_v2_strict_ok(tmp_path: Path) -> None:
    racine = tmp_path
    exp_id = "exp_ok"
    exp_dir = racine / "donnees" / "config" / "experiences" / exp_id
    _ecrire_experience_yml(exp_dir, journal_basename="journal.jsonl")
    bac = BacASableV1.charger_depuis_id(racine, exp_id)

    bac.verifier_journal_v2_strict()  # ne doit pas lever


def test_bac_a_sable_verifie_journal_v2_strict_echoue_si_non_jsonl(tmp_path: Path) -> None:
    racine = tmp_path
    exp_id = "exp_ko"
    exp_dir = racine / "donnees" / "config" / "experiences" / exp_id
    _ecrire_experience_yml(exp_dir, journal_basename="journal_episodes.jsonl")
    bac = BacASableV1.charger_depuis_id(racine, exp_id)

    with pytest.raises(ValueError):
        bac.verifier_journal_v2_strict()
