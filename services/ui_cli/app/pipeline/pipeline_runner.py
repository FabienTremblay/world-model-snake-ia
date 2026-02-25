from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ConventionsPipeline:
    run_tag_collecte: str
    journal_stable: str
    journal_enrichi_stable: str
    paires_stable: str
    config_entrainement: str
    config_epreuve: str


def _racine_projet() -> Path:
    """Reproduit la logique du repo : racine = dossier qui contient `services/` et `donnees/`."""
    ici = Path(__file__).resolve()
    for p in [ici] + list(ici.parents):
        if (p / "services").exists() and (p / "donnees").exists():
            return p
    # fallback (utile en tests isolés)
    return Path.cwd().resolve()


def _chemin_experience(racine: Path, experience_id: str) -> Path:
    return racine / "donnees" / "config" / "experiences" / experience_id


def _charger_experience_yml(exp_dir: Path) -> dict[str, Any]:
    fp = exp_dir / "experience.yml"
    if not fp.exists():
        return {}
    data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _conventions_pipeline_depuis_experience(exp_dir: Path, experience_id: str) -> ConventionsPipeline:
    cfg = _charger_experience_yml(exp_dir)
    p = cfg.get("pipeline") if isinstance(cfg, dict) else None

    def _get(key: str, default: str) -> str:
        if isinstance(p, dict) and isinstance(p.get(key), str) and p.get(key).strip():
            return str(p.get(key)).strip()
        return default

    # defaults raisonnables
    run_tag = _get("run_tag_collecte", f"{experience_id.lower().replace('_','-')}_collecte")
    return ConventionsPipeline(
        run_tag_collecte=run_tag,
        journal_stable=_get("journal_stable", "artefacts/datasets/journal_episodes_collecte.jsonl"),
        journal_enrichi_stable=_get("journal_enrichi_stable", "artefacts/datasets/journal_episodes_collecte.enrichi.jsonl"),
        paires_stable=_get("paires_stable", "artefacts/datasets/paires_capteurs.pt"),
        config_entrainement=_get("config_entrainement", "entrainement/config_entrainement.json"),
        config_epreuve=_get("config_epreuve", "epreuve/config_epreuve.json"),
    )


def _copier_stable(source: Path, dest: Path, force: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        return
    dest.write_bytes(source.read_bytes())


def _charger_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _phase_collecte(racine: Path, experience_id: str, run_tag: str, force: bool) -> dict[str, Any]:
    """Collecte = délègue à `ui_cli` (épisodes headless) et stabilise le journal."""
    from ui_cli.app.main import main as ui_cli_main

    exp_dir = _chemin_experience(racine, experience_id)
    conv = _conventions_pipeline_depuis_experience(exp_dir, experience_id)

    # On délègue à ui_cli (même point d'entrée) : il crée artefacts/runs/<horodatage>_<run_tag>/journal_episodes.jsonl
    ui_cli_main(
        [
            "--experience",
            experience_id,
            "--run-tag",
            run_tag,
            "--capture-stdout",
            "--truncate",
        ]
    )

    # Résoudre le dernier run correspondant au tag (même logique que tes .sh)
    runs_dir = exp_dir / "artefacts" / "runs"
    candidats = sorted([p for p in runs_dir.glob(f"*{run_tag}*") if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidats:
        raise FileNotFoundError(f"Aucun run trouvé sous {runs_dir} (tag={run_tag})")
    run_dir = candidats[0]
    journal_run = run_dir / "journal_episodes.jsonl"
    if not journal_run.exists():
        raise FileNotFoundError(f"Journal introuvable dans run: {journal_run}")

    journal_stable = exp_dir / conv.journal_stable
    _copier_stable(journal_run, journal_stable, force=force)

    return {
        "event": "pipeline_collecte_ok",
        "experience": experience_id,
        "run_tag": run_tag,
        "run_dir": str(run_dir),
        "journal_run": str(journal_run),
        "journal_stable": str(journal_stable),
    }


def _phase_enrichissement(racine: Path, experience_id: str, force: bool) -> dict[str, Any]:
    """Enrichissement minimal du journal (ajouts de champs de traçabilité)."""
    exp_dir = _chemin_experience(racine, experience_id)
    conv = _conventions_pipeline_depuis_experience(exp_dir, experience_id)

    src = exp_dir / conv.journal_stable
    dst = exp_dir / conv.journal_enrichi_stable
    if (not force) and dst.exists():
        return {
            "event": "pipeline_enrichissement_skip",
            "experience": experience_id,
            "journal_enrichi": str(dst),
        }
    if not src.exists():
        raise FileNotFoundError(f"Journal stable introuvable: {src}")

    # Implémentation intégrée (équivalent du mini-labo post_traiter_journal_collecte.py)
    n = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    horo = time.strftime("%Y-%m-%d_%Hh%M")
    with src.open("r", encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            e = json.loads(line)
            if isinstance(e, dict):
                e.setdefault("agent_id", "collecteur")
                e.setdefault("role_agent", "collecteur")
                e.setdefault("objectif", "collecte")
                e.setdefault("horodatage_traitement", horo)
            fout.write(json.dumps(e, ensure_ascii=False) + "\n")
            n += 1

    return {
        "event": "pipeline_enrichissement_ok",
        "experience": experience_id,
        "journal_source": str(src),
        "journal_enrichi": str(dst),
        "lignes": n,
    }


def _phase_dataset(racine: Path, experience_id: str, force: bool) -> dict[str, Any]:
    exp_dir = _chemin_experience(racine, experience_id)
    conv = _conventions_pipeline_depuis_experience(exp_dir, experience_id)

    journal = exp_dir / conv.journal_stable
    if not journal.exists():
        raise FileNotFoundError(f"Journal stable introuvable: {journal}")

    dest = exp_dir / conv.paires_stable
    if dest.exists() and not force:
        return {"event": "pipeline_dataset_skip", "experience": experience_id, "paires": str(dest)}

    from agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs

    # dimension: soit depuis config entrainement, soit fallback 560
    dim = 560
    cfg_path = exp_dir / conv.config_entrainement
    if cfg_path.exists():
        cfg = _charger_json(cfg_path)
        try:
            dim = int(cfg.get("capteurs", {}).get("dim_vecteur", dim))
        except Exception:
            pass

    e = ExtracteurPairesCapteurs(dim)
    meta = e.extraire_et_sauvegarder(
        str(journal),
        str(dest),
        cle_capteurs="capteurs_compact",
        cle_episode_id="episode_id",
    )

    return {
        "event": "pipeline_dataset_ok",
        "experience": experience_id,
        "paires": str(dest),
        "meta": meta,
    }


def _phase_entrainement(racine: Path, experience_id: str, force: bool) -> dict[str, Any]:
    exp_dir = _chemin_experience(racine, experience_id)
    conv = _conventions_pipeline_depuis_experience(exp_dir, experience_id)
    cfg_path = exp_dir / conv.config_entrainement
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config entrainement introuvable: {cfg_path}")
    cfg = _charger_json(cfg_path)

    from agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs
    from agent_service.app.preparation_agent.entraineur_modele_predictif import EntraineurModelePredicdictif
    from agent_service.app.modele_monde.predictif import ModelePredCapteursV1

    paires_path = exp_dir / str(cfg["dataset_paires_pt"])
    x, y, metadata = ExtracteurPairesCapteurs.charger_paires(str(paires_path))

    dim = int(cfg.get("capteurs", {}).get("dim_vecteur", x.shape[1]))
    hidden = int(cfg.get("entrainement", {}).get("hidden", 64))
    model = ModelePredCapteursV1(dim_in=dim, hidden=hidden)

    ent_cfg = cfg.get("entrainement", {})
    entraineur = EntraineurModelePredicdictif(
        model=model,
        device=str(ent_cfg.get("device", "cpu")),
        lr=float(ent_cfg.get("lr", 1e-3)),
        batch_size=int(ent_cfg.get("batch_size", 64)),
        epochs=int(ent_cfg.get("epochs", 5)),
        seed=int(ent_cfg.get("seed", 123)),
    )
    rapport = entraineur.entrainer(x, y, verbose=True)

    sortie_dir = exp_dir / str(cfg.get("sortie_dir", "artefacts"))
    sortie_dir.mkdir(parents=True, exist_ok=True)

    poids_path = sortie_dir / "poids" / "agent_personne.poids.pt"
    poids_path.parent.mkdir(parents=True, exist_ok=True)
    model.sauvegarder(str(poids_path), metadata=rapport)

    spec = {
        "agent_personne_id": cfg.get("agent_personne_id", "agent_personne"),
        "experience": cfg.get("experience", experience_id),
        "artefacts": {"poids_pt": str(poids_path.relative_to(exp_dir))},
    }
    spec_path = sortie_dir / "agents" / "agent_personne.json"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "event": "pipeline_entrainement_ok",
        "experience": experience_id,
        "agent_personne": str(spec_path),
        "poids": str(poids_path),
        "rapport": rapport,
    }


def _phase_epreuve(racine: Path, experience_id: str, force: bool) -> dict[str, Any]:
    exp_dir = _chemin_experience(racine, experience_id)
    conv = _conventions_pipeline_depuis_experience(exp_dir, experience_id)
    cfg_path = exp_dir / conv.config_epreuve
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config epreuve introuvable: {cfg_path}")
    cfg = _charger_json(cfg_path)

    from agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs
    from agent_service.app.preparation_agent.entraineur_modele_predictif import EntraineurModelePredicdictif
    from agent_service.app.modele_monde.predictif import ModelePredCapteursV1
    from agent_service.app.epistemique_v2.gates import GateSurprise, ConfigGate

    poids_path = exp_dir / str(cfg["poids_pt"])
    model = ModelePredCapteursV1.depuis_checkpoint(str(poids_path), device=str(cfg.get("epreuve", {}).get("device", "cpu")))
    model.eval()

    paires_path = exp_dir / str(cfg["dataset_paires_pt"])
    x, y, _ = ExtracteurPairesCapteurs.charger_paires(str(paires_path))

    entraineur = EntraineurModelePredicdictif(model=model, device=str(cfg.get("epreuve", {}).get("device", "cpu")))
    surprises = entraineur.calculer_surprises(x, y)

    gate_cfg = cfg.get("gate", {})
    config_gate = ConfigGate(
        mode=str(gate_cfg.get("mode", "quantile")),
        quantile=float(gate_cfg.get("quantile", 0.90)),
        seuil_connu=float(gate_cfg.get("seuil_connu", 0.10)),
    )
    gate = GateSurprise(config_gate)
    gate.calibrer(surprises)

    journal_agent = exp_dir / str(cfg["sorties"]["journal_agent"])
    journal_agent.parent.mkdir(parents=True, exist_ok=True)
    with journal_agent.open("w", encoding="utf-8") as jf:
        for idx, surprise in enumerate(surprises):
            sv = float(surprise.item())
            mode, _ = gate.decider_mode(sv)
            action = cfg.get("policy", {}).get("strategie_connu") if mode == "connu_exploiter" else cfg.get("policy", {}).get("strategie_inconnu")
            jf.write(
                json.dumps(
                    {
                        "idx": idx,
                        "mode": mode,
                        "surprise": sv,
                        "seuil_connu": gate.seuil_calibre,
                        "action": action,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    registre_path = exp_dir / str(cfg["sorties"]["registre_epistemique"])
    registre_path.parent.mkdir(parents=True, exist_ok=True)
    registre = {"experience": cfg.get("experience", experience_id), "gate": gate.to_dict()}
    registre_path.write_text(json.dumps(registre, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "event": "pipeline_epreuve_ok",
        "experience": experience_id,
        "journal_agent": str(journal_agent),
        "registre_epistemique": str(registre_path),
    }


def executer_pipeline(
    *,
    experience_id: str,
    phase: str,
    run_tag: str | None,
    force: bool,
    run_id: str | None,
) -> None:
    """Point d'entrée principal du pipeline.

    `run_id` est réservé pour du replay; actuellement le pipeline s'appuie sur la logique `ui_cli` pour nommer les runs.
    """
    _ = run_id  # non utilisé pour l'instant

    racine = _racine_projet()
    exp_dir = _chemin_experience(racine, experience_id)
    if not exp_dir.exists():
        raise FileNotFoundError(f"Expérience introuvable: {exp_dir}")

    conv = _conventions_pipeline_depuis_experience(exp_dir, experience_id)
    rt = run_tag or conv.run_tag_collecte

    phases = [phase] if phase != "all" else ["collecte", "enrichissement", "dataset", "entrainement", "epreuve"]
    for ph in phases:
        if ph == "collecte":
            payload = _phase_collecte(racine, experience_id, rt, force=force)
        elif ph == "enrichissement":
            payload = _phase_enrichissement(racine, experience_id, force=force)
        elif ph == "dataset":
            payload = _phase_dataset(racine, experience_id, force=force)
        elif ph == "entrainement":
            payload = _phase_entrainement(racine, experience_id, force=force)
        elif ph == "epreuve":
            payload = _phase_epreuve(racine, experience_id, force=force)
        else:
            raise SystemExit(f"Phase inconnue: {ph}")

        print(json.dumps(payload, ensure_ascii=False))
