from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1
from ui_cli.app.pipeline.repro import (
    PlanPipeline,
    copier_fichier,
    construire_plan,
    ecrire_checksums,
    ecrire_inputs_fixes_dans_plan,
    fixer_seed,
    sha256_file,
    verifier_configs_strict,
    verifier_checksums_strict,
)


@dataclass
class ConfigPipelineExp:
    run_tag_collecte: str
    journal_stable: str
    journal_enrichi_stable: str
    paires_stable: str
    champ_capteurs: str
    dim_vecteur: int
    config_entrainement: Optional[str]
    config_epreuve: Optional[str]


def _charger_cfg_pipeline(exp_dir: Path) -> ConfigPipelineExp:
    yml = exp_dir / "experience.yml"
    cfg = yaml.safe_load(yml.read_text(encoding="utf-8")) if yml.exists() else {}
    pipeline = cfg.get("pipeline") if isinstance(cfg, dict) else None
    pipeline = pipeline if isinstance(pipeline, dict) else {}

    return ConfigPipelineExp(
        run_tag_collecte=str(pipeline.get("run_tag_collecte") or "collecte"),
        journal_stable=str(pipeline.get("journal_stable") or "artefacts/datasets/journal_episodes.jsonl"),
        journal_enrichi_stable=str(
            pipeline.get("journal_enrichi_stable") or "artefacts/datasets/journal_episodes.enrichi.jsonl"
        ),
        paires_stable=str(pipeline.get("paires_stable") or "artefacts/datasets/paires_capteurs.pt"),
        champ_capteurs=str(pipeline.get("champ_capteurs") or "capteurs_compact"),
        dim_vecteur=int(pipeline.get("dim_vecteur") or 560),
        config_entrainement=(str(pipeline.get("config_entrainement")) if pipeline.get("config_entrainement") else None),
        config_epreuve=(str(pipeline.get("config_epreuve")) if pipeline.get("config_epreuve") else None),
    )


def _subprocess_ui_cli_collecte(*, racine_repo: Path, experience_id: str, arene: str, agent: str, run_tag: str) -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", "services")
    cmd = [
        sys.executable,
        "-m",
        "ui_cli.app.main",
        "--experience",
        experience_id,
        "--arene",
        arene,
        "--agent",
        agent,
        "--run-tag",
        run_tag,
        "--capture-stdout",
    ]
    subprocess.run(cmd, cwd=str(racine_repo), env=env, check=True)


def _resoudre_path_arene(racine_repo: Path, exp_dir: Path, arene: str) -> str:
    """Résout un chemin d'arène (id dans experience.yml).

    Tolère:
    - chemin absolu
    - chemin relatif au repo (ex: donnees/config/...)
    - chemin relatif à l'expérience (ex: arenes/fourmi_v1.yml)
    """
    p = Path(arene)
    if p.is_absolute():
        return str(p)
    cand_repo = (racine_repo / p).resolve()
    if cand_repo.exists():
        return str(cand_repo)
    return str((exp_dir / p).resolve())


def _enrichir_journal(src: Path, dst: Path, *, overwrite: bool) -> int:
    if dst.exists() and not overwrite:
        raise FileExistsError(f"sortie existe déjà: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    import time

    with open(src, "r", encoding="utf-8") as fin, open(dst, "w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            e = json.loads(line)
            e.setdefault("agent_id", "fourmi")
            e.setdefault("role_agent", "collecteur")
            e.setdefault("objectif", "couverture_observations")
            e.setdefault("horodatage_traitement", time.strftime("%Y-%m-%d_%Hh%M"))
            fout.write(json.dumps(e, ensure_ascii=False) + "\n")
            n += 1
    return n


def _extraire_paires(src_journal: Path, dst_pt: Path, *, champ_capteurs: str, cle_episode_id: str, dim: int) -> Dict[str, Any]:
    from services.agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs

    dst_pt.parent.mkdir(parents=True, exist_ok=True)
    e = ExtracteurPairesCapteurs(dim)
    meta = e.extraire_et_sauvegarder(
        str(src_journal),
        str(dst_pt),
        cle_capteurs=champ_capteurs,
        cle_episode_id=cle_episode_id,
    )
    return meta


def _entrainer_depuis_cfg(config_path: Path, *, exp_dir: Path, run_dir: Path) -> Dict[str, Path]:
    """Entraîne et écrit tout sous run_dir, puis retourne les chemins produits."""
    from services.agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs
    from services.agent_service.app.preparation_agent.entraineur_modele_predictif import EntraineurModelePredicdictif
    from services.agent_service.app.modele_monde.predictif import ModelePredCapteursV1

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    # dataset
    paires_path = (exp_dir / cfg["dataset_paires_pt"]).resolve()
    x, y, metadata = ExtracteurPairesCapteurs.charger_paires(str(paires_path))

    dim = int(cfg["capteurs"]["dim_vecteur"])
    hidden = int(cfg.get("entrainement", {}).get("hidden", 64))
    model = ModelePredCapteursV1(dim_in=dim, hidden=hidden)

    entr_cfg = cfg["entrainement"]
    entraineur = EntraineurModelePredicdictif(
        model=model,
        device=entr_cfg.get("device", "cpu"),
        lr=float(entr_cfg["lr"]),
        batch_size=int(entr_cfg["batch_size"]),
        epochs=int(entr_cfg["epochs"]),
        seed=int(entr_cfg.get("seed", 0)),
    )

    rapport = entraineur.entrainer(x, y, verbose=True)

    poids_path = run_dir / "entrainement" / "poids" / "agent_personne.poids.pt"
    poids_path.parent.mkdir(parents=True, exist_ok=True)
    model.sauvegarder(str(poids_path), metadata=rapport)

    spec = {
        "agent_personne_id": cfg.get("agent_personne_id", "agent_personne"),
        "experience": cfg.get("experience"),
        "artefacts": {"poids_pt": str(poids_path)},
    }
    spec_path = run_dir / "entrainement" / "agents" / "agent_personne.json"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"poids_pt": poids_path, "agent_json": spec_path}


def _epreuve_depuis_cfg(config_path: Path, *, exp_dir: Path, run_dir: Path) -> Dict[str, Path]:
    from services.agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs
    from services.agent_service.app.preparation_agent.entraineur_modele_predictif import EntraineurModelePredicdictif
    from services.agent_service.app.modele_monde.predictif import ModelePredCapteursV1
    from services.agent_service.app.epistemique_v2.gates import GateSurprise, ConfigGate

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    poids_path = (exp_dir / cfg["poids_pt"]).resolve()
    model = ModelePredCapteursV1.depuis_checkpoint(str(poids_path), device=cfg.get("epreuve", {}).get("device", "cpu"))
    model.eval()

    paires_path = (exp_dir / cfg["dataset_paires_pt"]).resolve()
    x, y, _ = ExtracteurPairesCapteurs.charger_paires(str(paires_path))

    entraineur = EntraineurModelePredicdictif(model=model, device=cfg.get("epreuve", {}).get("device", "cpu"))
    surprises = entraineur.calculer_surprises(x, y)

    gate_cfg = cfg.get("gate", {})
    config_gate = ConfigGate(
        mode=gate_cfg.get("mode", "quantile"),
        quantile=float(gate_cfg.get("quantile", 0.90)),
        seuil_connu=float(gate_cfg.get("seuil_connu", 0.10)),
    )
    gate = GateSurprise(config_gate)
    gate.calibrer(surprises)

    journal_agent_path = run_dir / "epreuve" / "journal_agent.jsonl"
    journal_agent_path.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_agent_path, "w", encoding="utf-8") as jf:
        for idx, surprise in enumerate(surprises):
            surprise_val = float(surprise.item())
            mode, _action_type = gate.decider_mode(surprise_val)
            if mode == "connu_exploiter":
                action = cfg["policy"]["strategie_connu"]
            else:
                action = cfg["policy"]["strategie_inconnu"]
            jf.write(
                json.dumps(
                    {
                        "idx": idx,
                        "mode": mode,
                        "surprise": surprise_val,
                        "seuil_connu": gate.seuil_calibre,
                        "action": action,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    registre_path = run_dir / "epreuve" / "registre_epistemique.json"
    registre = {"experience": cfg.get("experience"), "gate": gate.to_dict()}
    registre_path.write_text(json.dumps(registre, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"journal_agent": journal_agent_path, "registre": registre_path}


class PipelineRunner:
    def __init__(self, *, racine_repo: Path, experience_id: str):
        self.racine_repo = Path(racine_repo).resolve()
        self.bac = BacASableV1.charger_depuis_id(racine_projet=self.racine_repo, experience_id=experience_id)
        self.bac.assurer_structure()
        self.exp_dir = self.bac.experience_dir
        self.cfg_pipeline = _charger_cfg_pipeline(self.exp_dir)

    def creer_run(self, run_tag: str, run_id: str) -> Path:
        run_dir, _journal, _stdout, _meta = self.bac.preparer_run(run_tag=run_tag, run_id=run_id)
        return run_dir

    def list_runs(self) -> list[Path]:
        return self.bac.lister_runs()

    def run(
        self,
        *,
        phases: list[str],
        seed: int,
        resume: bool,
        force: bool,
        strict: bool,
        replay_run_dir: Optional[Path] = None,
        mode: str = "run",  # run|replay
    ) -> PlanPipeline:
        fixer_seed(seed)

        # run_dir
        if replay_run_dir is not None:
            run_dir = replay_run_dir
            run_id = run_dir.name
        else:
            run_id = str(os.getpid()) + "_" + str(seed) + "_" + str(int.from_bytes(os.urandom(4), "big"))
            run_dir = self.creer_run(run_tag="pipeline", run_id=run_id)
            run_id = run_dir.name

        plan_path = run_dir / "plan_pipeline.json"
        if plan_path.exists() and not resume:
            raise FileExistsError(f"run déjà initialisé: {plan_path} (utiliser --resume ou --run-id différent)")

        # inputs/outputs canon
        cfg = self.bac.cfg
        arene_cfg = cfg.get("arene", {}) if isinstance(cfg, dict) else {}
        agent_cfg = cfg.get("agent", {}) if isinstance(cfg, dict) else {}
        arene = arene_cfg.get("id") or arene_cfg.get("path")
        agent = agent_cfg.get("id")
        if not isinstance(arene, str) or not arene:
            raise ValueError("experience.yml: arene.id (ou path) requis")
        if not isinstance(agent, str) or not agent:
            raise ValueError("experience.yml: agent.id requis")

        # chemins stabilisés
        journal_stable = (self.exp_dir / self.cfg_pipeline.journal_stable).resolve()
        journal_enrichi = (self.exp_dir / self.cfg_pipeline.journal_enrichi_stable).resolve()
        paires_stable = (self.exp_dir / self.cfg_pipeline.paires_stable).resolve()

        config_files: Dict[str, Path] = {"experience_yml": self.exp_dir / "experience.yml"}
        if self.cfg_pipeline.config_entrainement:
            config_files["config_entrainement"] = (self.exp_dir / self.cfg_pipeline.config_entrainement).resolve()
        if self.cfg_pipeline.config_epreuve:
            config_files["config_epreuve"] = (self.exp_dir / self.cfg_pipeline.config_epreuve).resolve()

        inputs = {
            "arene": str(arene),
            "agent": str(agent),
        }
        outputs = {
            "journal_stable": str(journal_stable),
            "journal_enrichi_stable": str(journal_enrichi),
            "paires_stable": str(paires_stable),
        }

        plan = construire_plan(
            racine_repo=self.racine_repo,
            experience_id=self.bac.experience_id,
            run_id=run_id,
            run_dir=run_dir,
            phases=phases,
            seed=seed,
            config_files=config_files,
            inputs=inputs,
            outputs=outputs,
        )
        plan.save(plan_path)

        if replay_run_dir is not None and strict:
            verifier_configs_strict(plan)

        # ---- inputs figés (reproductibilité)
        inputs_dir = run_dir / "inputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)

        # Convention des fichiers figés (dans run_dir)
        snap_journal = inputs_dir / "journal_episodes.jsonl"
        snap_journal_enrichi = inputs_dir / "journal_episodes.enrichi.jsonl"
        snap_paires = inputs_dir / "paires_capteurs.pt"

        # En replay strict: on restaure les inputs figés vers les pointeurs stables,
        # et on refuse si les checksums diffèrent.
        if mode == "replay" and strict:
            checksums_path = run_dir / "checksums.json"
            expected = json.loads(checksums_path.read_text(encoding="utf-8")) if checksums_path.exists() else {}
            expected_inputs = {
                "inputs/journal_episodes.jsonl": expected.get("inputs/journal_episodes.jsonl"),
                "inputs/journal_episodes.enrichi.jsonl": expected.get("inputs/journal_episodes.enrichi.jsonl"),
                "inputs/paires_capteurs.pt": expected.get("inputs/paires_capteurs.pt"),
            }
            expected_inputs = {k: v for k, v in expected_inputs.items() if v}
            if expected_inputs:
                verifier_checksums_strict(run_dir, expected=expected_inputs)
            # restauration (overwrite)
            if snap_journal.exists():
                copier_fichier(snap_journal, journal_stable, overwrite=True)
            if snap_journal_enrichi.exists():
                copier_fichier(snap_journal_enrichi, journal_enrichi, overwrite=True)
            if snap_paires.exists():
                copier_fichier(snap_paires, paires_stable, overwrite=True)
            print(json.dumps({"event": "pipeline_replay_inputs_restaures", "run_id": run_id}, ensure_ascii=False))

        # ---------------- phases
        for phase in phases:
            if phase == "collecte":
                # En replay: ne recalcule pas. On utilise l'instantané figé.
                if mode == "replay":
                    if not snap_journal.exists():
                        raise FileNotFoundError(f"replay strict: input manquant: {snap_journal}")
                    print(json.dumps({"event": "pipeline_collecte_replay_use_inputs", "run_id": run_id}, ensure_ascii=False))
                else:
                    # si journal stable existe déjà et resume/skip
                    if journal_stable.exists() and not force and not resume:
                        # snapshot quand même dans le run
                        copier_fichier(journal_stable, snap_journal, overwrite=True)
                        copier_fichier(journal_stable, run_dir / "journal_episodes.jsonl", overwrite=True)
                        print(json.dumps({"event": "pipeline_collecte_skip", "run_id": run_id}, ensure_ascii=False))
                        continue
                    # lance ui_cli pour produire un run de collecte
                    run_tag_collecte = self.cfg_pipeline.run_tag_collecte
                    _subprocess_ui_cli_collecte(
                        racine_repo=self.racine_repo,
                        experience_id=self.bac.experience_id,
                        arene=_resoudre_path_arene(self.racine_repo, self.exp_dir, str(arene)),
                        agent=str(agent),
                        run_tag=run_tag_collecte,
                    )
                    # récupère le dernier run correspondant
                    run_dirs = [p for p in self.bac.lister_runs() if run_tag_collecte in p.name]
                    if not run_dirs:
                        raise FileNotFoundError(f"collecte: aucun run trouvé pour tag {run_tag_collecte}")
                    derniere = run_dirs[-1]
                    journal_run = derniere / "journal_episodes.jsonl"
                    if not journal_run.exists():
                        raise FileNotFoundError(f"collecte: journal introuvable: {journal_run}")
                    journal_stable.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(journal_run, journal_stable)
                    # copie aussi dans run_dir + snapshot inputs
                    copier_fichier(journal_run, run_dir / "journal_episodes.jsonl", overwrite=True)
                    copier_fichier(journal_run, snap_journal, overwrite=True)
                    print(
                        json.dumps(
                            {
                                "event": "pipeline_collecte_ok",
                                "run_id": run_id,
                                "journal": str(journal_stable),
                                "source": str(journal_run),
                            },
                            ensure_ascii=False,
                        )
                    )

            elif phase == "enrichissement":
                if mode == "replay":
                    if not snap_journal_enrichi.exists():
                        raise FileNotFoundError(f"replay strict: input manquant: {snap_journal_enrichi}")
                    print(json.dumps({"event": "pipeline_enrichissement_replay_use_inputs", "run_id": run_id}, ensure_ascii=False))
                else:
                    if journal_enrichi.exists() and not force and not resume:
                        copier_fichier(journal_enrichi, snap_journal_enrichi, overwrite=True)
                        copier_fichier(journal_enrichi, run_dir / "journal_episodes.enrichi.jsonl", overwrite=True)
                        print(json.dumps({"event": "pipeline_enrichissement_skip", "run_id": run_id}, ensure_ascii=False))
                        continue
                    n = _enrichir_journal(journal_stable, journal_enrichi, overwrite=True)
                    copier_fichier(journal_enrichi, run_dir / "journal_episodes.enrichi.jsonl", overwrite=True)
                    copier_fichier(journal_enrichi, snap_journal_enrichi, overwrite=True)
                    print(
                        json.dumps(
                            {
                                "event": "pipeline_enrichissement_ok",
                                "run_id": run_id,
                                "journal_enrichi": str(journal_enrichi),
                                "lignes": n,
                            },
                            ensure_ascii=False,
                        )
                    )

            elif phase == "dataset":
                if mode == "replay":
                    if not snap_paires.exists():
                        raise FileNotFoundError(f"replay strict: input manquant: {snap_paires}")
                    print(json.dumps({"event": "pipeline_dataset_replay_use_inputs", "run_id": run_id}, ensure_ascii=False))
                else:
                    if paires_stable.exists() and not force and not resume:
                        copier_fichier(paires_stable, snap_paires, overwrite=True)
                        copier_fichier(paires_stable, run_dir / "paires_capteurs.pt", overwrite=True)
                        print(json.dumps({"event": "pipeline_dataset_skip", "run_id": run_id}, ensure_ascii=False))
                        continue
                    meta = _extraire_paires(
                        journal_stable,
                        paires_stable,
                        champ_capteurs=self.cfg_pipeline.champ_capteurs,
                        cle_episode_id="episode_id",
                        dim=self.cfg_pipeline.dim_vecteur,
                    )
                    copier_fichier(paires_stable, run_dir / "paires_capteurs.pt", overwrite=True)
                    copier_fichier(paires_stable, snap_paires, overwrite=True)
                    print(json.dumps({"event": "pipeline_dataset_ok", "run_id": run_id, "meta": meta}, ensure_ascii=False))

            elif phase == "entrainement":
                if not self.cfg_pipeline.config_entrainement:
                    raise ValueError("pipeline: config_entrainement manquant dans experience.yml")
                out_marker = run_dir / "entrainement" / "agents" / "agent_personne.json"
                if out_marker.exists() and not force and not resume:
                    print(json.dumps({"event": "pipeline_entrainement_skip", "run_id": run_id}, ensure_ascii=False))
                else:
                    produced = _entrainer_depuis_cfg((self.exp_dir / self.cfg_pipeline.config_entrainement).resolve(), exp_dir=self.exp_dir, run_dir=run_dir)

                    # pointeurs stables (compat)
                    stable_agents = self.exp_dir / "artefacts" / "agents"
                    stable_poids = self.exp_dir / "artefacts" / "poids"
                    stable_agents.mkdir(parents=True, exist_ok=True)
                    stable_poids.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(produced["agent_json"], stable_agents / "agent_personne.json")
                    shutil.copy2(produced["poids_pt"], stable_poids / "agent_personne.poids.pt")

                    print(
                        json.dumps(
                            {
                                "event": "pipeline_entrainement_ok",
                                "run_id": run_id,
                                "agent_json": str(produced["agent_json"]),
                                "poids_pt": str(produced["poids_pt"]),
                            },
                            ensure_ascii=False,
                        )
                    )

            elif phase == "epreuve":
                if not self.cfg_pipeline.config_epreuve:
                    raise ValueError("pipeline: config_epreuve manquant dans experience.yml")
                out_marker = run_dir / "epreuve" / "journal_agent.jsonl"
                if out_marker.exists() and not force and not resume:
                    print(json.dumps({"event": "pipeline_epreuve_skip", "run_id": run_id}, ensure_ascii=False))
                else:
                    produced = _epreuve_depuis_cfg((self.exp_dir / self.cfg_pipeline.config_epreuve).resolve(), exp_dir=self.exp_dir, run_dir=run_dir)

                    stable_journaux = self.exp_dir / "artefacts" / "journaux"
                    stable_journaux.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(produced["journal_agent"], stable_journaux / "journal_agent.jsonl")
                    # compat: registre sous journaux (historique JEPA)
                    shutil.copy2(produced["registre"], stable_journaux / "registre_epistemique.json")

                    print(
                        json.dumps(
                            {
                                "event": "pipeline_epreuve_ok",
                                "run_id": run_id,
                                "journal_agent": str(produced["journal_agent"]),
                                "registre": str(produced["registre"]),
                            },
                            ensure_ascii=False,
                        )
                    )

            else:
                raise ValueError(f"phase inconnue: {phase}")

        # checksums
        paths_a_hasher = [plan_path]
        for rel in [
            "inputs/journal_episodes.jsonl",
            "inputs/journal_episodes.enrichi.jsonl",
            "inputs/paires_capteurs.pt",
            "journal_episodes.jsonl",
            "journal_episodes.enrichi.jsonl",
            "paires_capteurs.pt",
            "entrainement/poids/agent_personne.poids.pt",
            "entrainement/agents/agent_personne.json",
            "epreuve/journal_agent.jsonl",
            "epreuve/registre_epistemique.json",
        ]:
            p = run_dir / rel
            if p.exists():
                paths_a_hasher.append(p)
        ecrire_checksums(run_dir, paths_a_hasher)

        # patch plan: inputs_fixes (chemins relatifs + sha256)
        inputs_fixes = {}
        for rel in [
            "inputs/journal_episodes.jsonl",
            "inputs/journal_episodes.enrichi.jsonl",
            "inputs/paires_capteurs.pt",
        ]:
            p = run_dir / rel
            if p.exists():
                inputs_fixes[rel] = {"sha256": sha256_file(p)}
        if inputs_fixes:
            ecrire_inputs_fixes_dans_plan(plan_path, inputs_fixes)
        return plan


def exporter_run(run_dir: Path, out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    # make_archive requires base_name without extension
    base = str(out_zip)
    if base.endswith(".zip"):
        base = base[:-4]
    shutil.make_archive(base, "zip", root_dir=str(run_dir))
