from __future__ import annotations

import argparse
import json
from pathlib import Path

from ui_cli.app.pipeline.pipeline_runner import PipelineRunner, exporter_run
from ui_cli.app.pipeline.repro import PlanPipeline, verifier_configs_strict


def construire_parser_pipeline() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ui_cli pipeline")
    sp = ap.add_subparsers(dest="cmd", required=True)

    ap_run = sp.add_parser("run", help="Exécute un pipeline (collecte/enrichissement/dataset/entrainement/epreuve)")
    ap_run.add_argument("--experience", required=True)
    ap_run.add_argument("--phase", default="all", help="collecte|enrichissement|dataset|entrainement|epreuve|all")
    ap_run.add_argument("--seed", type=int, default=0)
    ap_run.add_argument("--resume", action="store_true")
    ap_run.add_argument("--force", action="store_true")
    ap_run.add_argument("--strict", action="store_true")

    ap_list = sp.add_parser("list-runs", help="Liste les runs d'une expérience")
    ap_list.add_argument("--experience", required=True)

    ap_desc = sp.add_parser("describe-run", help="Décrit un run (plan + checksums)")
    ap_desc.add_argument("--experience", required=True)
    ap_desc.add_argument("--run-id", required=True, help="nom du répertoire sous artefacts/runs")

    ap_replay = sp.add_parser("replay", help="Rejoue un run à partir de son plan")
    ap_replay.add_argument("--experience", required=True)
    ap_replay.add_argument("--run-id", required=True)
    ap_replay.add_argument("--allow-drift", action="store_true", help="autorise des configs différentes du plan")

    ap_rerun = sp.add_parser("rerun", help="Relance un run à partir du plan, mais dans un NOUVEAU run_id (recalcule les inputs)")
    ap_rerun.add_argument("--experience", required=True)
    ap_rerun.add_argument("--from-run-id", required=True)
    ap_rerun.add_argument("--allow-drift", action="store_true", help="autorise des configs différentes du plan")

    ap_export = sp.add_parser("export-run", help="Exporte un run en zip")
    ap_export.add_argument("--experience", required=True)
    ap_export.add_argument("--run-id", required=True)
    ap_export.add_argument("--out", required=True)

    return ap


def _phases_from_arg(s: str) -> list[str]:
    s = (s or "").strip()
    if s == "all":
        return ["collecte", "enrichissement", "dataset", "entrainement", "epreuve"]
    return [s]


def main_pipeline(argv: list[str] | None = None) -> None:
    args = construire_parser_pipeline().parse_args(argv)
    racine_repo = Path(".").resolve()

    if args.cmd == "run":
        runner = PipelineRunner(racine_repo=racine_repo, experience_id=str(args.experience))
        phases = _phases_from_arg(str(args.phase))
        plan = runner.run(phases=phases, seed=int(args.seed), resume=bool(args.resume), force=bool(args.force), strict=bool(args.strict))
        print(json.dumps({"event": "pipeline_run_ok", "plan": str(Path(plan.run_dir) / 'plan_pipeline.json')}, ensure_ascii=False))
        return

    if args.cmd == "list-runs":
        runner = PipelineRunner(racine_repo=racine_repo, experience_id=str(args.experience))
        runs = runner.list_runs()
        items = []
        for r in runs:
            plan = r / "plan_pipeline.json"
            if plan.exists():
                try:
                    d = json.loads(plan.read_text(encoding="utf-8"))
                    items.append({"run_id": r.name, "date_utc": d.get("date_utc"), "phases": d.get("phases")})
                except Exception:
                    items.append({"run_id": r.name})
            else:
                items.append({"run_id": r.name})
        print(json.dumps({"event": "pipeline_list_runs", "experience": args.experience, "runs": items}, ensure_ascii=False, indent=2))
        return

    if args.cmd == "describe-run":
        runner = PipelineRunner(racine_repo=racine_repo, experience_id=str(args.experience))
        run_dir = runner.bac.paths.runs_dir / str(args.run_id)
        plan_path = run_dir / "plan_pipeline.json"
        checksums_path = run_dir / "checksums.json"
        payload = {
            "event": "pipeline_describe_run",
            "experience": args.experience,
            "run_id": args.run_id,
            "plan": json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else None,
            "checksums": json.loads(checksums_path.read_text(encoding="utf-8")) if checksums_path.exists() else None,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.cmd == "replay":
        runner = PipelineRunner(racine_repo=racine_repo, experience_id=str(args.experience))
        run_dir = runner.bac.paths.runs_dir / str(args.run_id)
        plan_path = run_dir / "plan_pipeline.json"
        if not plan_path.exists():
            raise SystemExit(f"plan introuvable: {plan_path}")
        plan = PlanPipeline.load(plan_path)
        if not args.allow_drift:
            verifier_configs_strict(plan)
        # rejoue les phases du plan (dans le même run_dir) avec inputs figés
        runner.run(
            phases=list(plan.phases),
            seed=int(plan.seed),
            resume=True,
            force=False,
            strict=not bool(args.allow_drift),
            replay_run_dir=run_dir,
            mode="replay",
        )
        print(json.dumps({"event": "pipeline_replay_ok", "run_id": args.run_id}, ensure_ascii=False))
        return

    if args.cmd == "rerun":
        runner = PipelineRunner(racine_repo=racine_repo, experience_id=str(args.experience))
        from_run_dir = runner.bac.paths.runs_dir / str(args.from_run_id)
        plan_path = from_run_dir / "plan_pipeline.json"
        if not plan_path.exists():
            raise SystemExit(f"plan introuvable: {plan_path}")
        plan = PlanPipeline.load(plan_path)
        if not args.allow_drift:
            verifier_configs_strict(plan)
        phases = list(plan.phases) if plan.phases else ["collecte", "enrichissement", "dataset", "entrainement", "epreuve"]
        # Nouveau run_id, recalcul des inputs (force=False, resume=False)
        new_plan = runner.run(
            phases=phases,
            seed=int(plan.seed),
            resume=False,
            force=False,
            strict=not bool(args.allow_drift),
            replay_run_dir=None,
            mode="run",
        )
        print(json.dumps({"event": "pipeline_rerun_ok", "from": args.from_run_id, "plan": str(Path(new_plan.run_dir) / 'plan_pipeline.json')}, ensure_ascii=False))
        return

    if args.cmd == "export-run":
        runner = PipelineRunner(racine_repo=racine_repo, experience_id=str(args.experience))
        run_dir = runner.bac.paths.runs_dir / str(args.run_id)
        out_zip = Path(str(args.out)).expanduser().resolve()
        exporter_run(run_dir, out_zip)
        print(json.dumps({"event": "pipeline_export_ok", "run_id": args.run_id, "zip": str(out_zip)}, ensure_ascii=False))
        return
