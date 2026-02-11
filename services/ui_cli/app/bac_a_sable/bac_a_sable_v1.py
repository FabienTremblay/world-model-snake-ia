# services/ui_cli/app/bac_a_sable/bac_a_sable_v1.py
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import yaml


def _horodatage_compact() -> str:
    """Horodatage lisible pour nommer un répertoire d'exécution (ex: 2026-02-02_14h31)."""
    t = time.localtime()
    return f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}_{t.tm_hour:02d}h{t.tm_min:02d}"


@dataclass(frozen=True)
class PathsBacASableV1:
    experience_dir: Path
    artefacts_dir: Path
    runs_dir: Path
    datasets_dir: Path
    diagnostics_dir: Path
    registres_dir: Path
    notes_dir: Path


class BacASableV1:
    """Mini utilitaire commun pour résoudre un bac à sable d'expérience.

    Rôles:
    - charger experience.yml
    - fournir des répertoires canoniques (datasets/diagnostics/registres/runs/notes)
    - préparer un run (run_dir + chemins attendus)
    - (optionnel) exporter quelques env liées au modèle monde
    """

    def __init__(self, racine_projet: Path, experience_id: str, experience_dir: Path, cfg: Dict[str, Any]):
        self.racine_projet = Path(racine_projet).resolve()
        self.experience_id = str(experience_id)
        self.experience_dir = Path(experience_dir).resolve()
        self.cfg = cfg or {}

        sorties = self.cfg.get("sorties") if isinstance(self.cfg, dict) else None
        sorties = sorties if isinstance(sorties, dict) else {}

        artefacts_dir = self.experience_dir / "artefacts"
        runs_rel = str(sorties.get("run_dir") or "artefacts/runs")
        runs_dir = (self.experience_dir / runs_rel).resolve()

        self.paths = PathsBacASableV1(
            experience_dir=self.experience_dir,
            artefacts_dir=artefacts_dir,
            runs_dir=runs_dir,
            datasets_dir=(self.experience_dir / "artefacts" / "datasets").resolve(),
            diagnostics_dir=(self.experience_dir / "artefacts" / "diagnostics").resolve(),
            registres_dir=(self.experience_dir / "artefacts" / "registres").resolve(),
            notes_dir=(self.experience_dir / "artefacts" / "notes").resolve(),
        )

    # ---------------------------------------------------------------------
    # Construction / chargement

    @classmethod
    def charger_depuis_id(cls, racine_projet: Path, experience_id: str) -> "BacASableV1":
        exp_dir = Path(racine_projet) / "donnees" / "config" / "experiences" / str(experience_id)
        cfg = cls._charger_experience_yml(exp_dir)
        return cls(racine_projet=racine_projet, experience_id=str(experience_id), experience_dir=exp_dir, cfg=cfg)

    @staticmethod
    def _charger_experience_yml(experience_dir: Path) -> Dict[str, Any]:
        fp = Path(experience_dir) / "experience.yml"
        if not fp.exists():
            return {}
        data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}

    # ---------------------------------------------------------------------
    # Résolution de chemins / structure

    def resoudre_chemin(self, p: str | Path) -> Path:
        """Résout un chemin relatif en chemin absolu (base = dossier expérience)."""
        pp = Path(p)
        if pp.is_absolute():
            return pp
        return (self.experience_dir / pp).resolve()

    def assurer_structure(self) -> Dict[str, Any]:
        """Crée la structure minimale si absente. Retourne un rapport (dict)."""
        cree: List[str] = []

        if not self.experience_dir.exists():
            self.experience_dir.mkdir(parents=True, exist_ok=True)
            cree.append(str(self.experience_dir))

        for p in [
            self.paths.artefacts_dir,
            self.paths.runs_dir,
            self.paths.datasets_dir,
            self.paths.diagnostics_dir,
            self.paths.registres_dir,
            self.paths.notes_dir,
        ]:
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                cree.append(str(p))

        exp_yml = self.experience_dir / "experience.yml"
        if not exp_yml.exists():
            exp_yml.write_text(
                """# donnees/config/experiences/<id>/experience.yml
# Bac à sable d'expérience (SAI).

id: CHANGER_MOI
description: ""

modele_monde:
  journal: artefacts/datasets/train.jsonl
  champ_latent: signaux_hash
  latent_cli: checksum

arene:
  # id d'arène (raccourci) ou chemin .yml
  id: demo_v0

agent:
  id: aleatoire

latent: checksum

generation:
  episodes: 100
  max_ticks: 2000
  seed: 123
  niveau_bruit: null

sorties:
  run_dir: artefacts/runs
  journal_basename: journal.jsonl
  capture_stdout: false
""",
                encoding="utf-8",
            )
            cree.append(str(exp_yml))

        readme = self.experience_dir / "README.md"
        if not readme.exists():
            readme.write_text(
                f"""# bac à sable : {self.experience_id}\n\n"""
                "ce README sert de page d'accueil de l'expérience.\n"
                "\n"
                "- objectif\n"
                "- protocole\n"
                "- runs significatifs\n"
                "- résultats (synthèse)\n"
                ,
                encoding="utf-8",
            )
            cree.append(str(readme))

        return {"experience_dir": str(self.experience_dir), "creations": cree}

    # ---------------------------------------------------------------------
    # Sorties d'exécution (runs)

    def capture_stdout_defaut(self) -> bool:
        sorties = self.cfg.get("sorties") if isinstance(self.cfg, dict) else None
        sorties = sorties if isinstance(sorties, dict) else {}
        return bool(sorties.get("capture_stdout", False))

    def nom_fichier_journal_defaut(self) -> str:
        """Nom de fichier du journal (basename) pour les runs.

        Priorité:
        1) sorties.journal_basename (v2)
        2) sorties.journal (ancien, toléré pendant la transition)
        3) défaut: journal.jsonl (v2)
        """
        sorties = self.cfg.get("sorties") if isinstance(self.cfg, dict) else None
        sorties = sorties if isinstance(sorties, dict) else {}

        s = sorties.get("journal_basename")
        if s is None:
            s = sorties.get("journal")

        nom = str(s or "journal.jsonl").strip()
        return nom or "journal.jsonl"


    def verifier_journal_v2_strict(self) -> None:
        """Vérifie que l'expérience est configurée pour le journal v2 (strict).

        On ne cherche pas la rétro-compatibilité: si ce n'est pas `journal.jsonl`, on échoue.
        """
        nom = self.nom_fichier_journal_defaut()
        if nom != "journal.jsonl":
            raise ValueError(
                f"bac-a-sable '{self.experience_id}': sorties.journal_basename (ou sorties.journal) doit être 'journal.jsonl' (trouvé: {nom!r})"
            )

    def preparer_run(self, run_tag: Optional[str], run_id: str) -> Tuple[Path, Path, Path, Path]:

        """Retourne (run_dir, journal_path, stdout_path, meta_path)."""
        self.paths.runs_dir.mkdir(parents=True, exist_ok=True)

        suffix = _horodatage_compact()
        tag = (run_tag.strip() if run_tag else "").strip()
        nom_run = f"{suffix}_{tag}" if tag else suffix

        run_dir = self.paths.runs_dir / nom_run
        if run_dir.exists():
            run_dir = self.paths.runs_dir / f"{nom_run}_{run_id[-6:]}"
        run_dir.mkdir(parents=True, exist_ok=True)

        journal_path = run_dir / self.nom_fichier_journal_defaut()
        stdout_path = run_dir / "stdout.log"
        meta_path = run_dir / "meta.json"
        return run_dir, journal_path, stdout_path, meta_path

    def lister_runs(self) -> list[Path]:
        """Liste les répertoires de runs existants (triés du plus ancien au plus récent)."""
        if not self.paths.runs_dir.exists():
            return []
        runs = [p for p in self.paths.runs_dir.iterdir() if p.is_dir()]
        runs.sort(key=lambda p: p.name)
        return runs

    def resoudre_run_existant(self, run_id: Optional[str] = None) -> Tuple[Path, Path, Path, Path]:
        """Retourne (run_dir, journal_path, stdout_path, meta_path) pour un run existant.

        `run_id` correspond au nom de répertoire sous `artefacts/runs/`.
        Si absent, on choisit le dernier run disponible.
        """
        self.paths.runs_dir.mkdir(parents=True, exist_ok=True)
        runs = self.lister_runs()
        if not runs:
            raise FileNotFoundError(
                f"Aucun run trouvé pour l'expérience {self.experience_id!r}. "
                "Lance d'abord ui_cli / runner pour générer des épisodes."
            )

        if run_id:
            run_dir = self.paths.runs_dir / run_id
            if not run_dir.exists() or not run_dir.is_dir():
                raise FileNotFoundError(f"Run introuvable: {run_dir}")
        else:
            run_dir = runs[-1]

        journal_path = run_dir / self.nom_fichier_journal_defaut()
        stdout_path = run_dir / "stdout.log"
        meta_path = run_dir / "meta.json"

        if not journal_path.exists():
            raise FileNotFoundError(f"Journal du run introuvable: {journal_path}")

        return run_dir, journal_path, stdout_path, meta_path

    # ---------------------------------------------------------------------
    # Export env: modèle monde

    def appliquer_env_modele_monde(self) -> Dict[str, Any]:
        """Résout et exporte les variables d'environnement liées au modèle monde."""
        mm = self.cfg.get("modele_monde") if isinstance(self.cfg, dict) else None
        if not isinstance(mm, dict):
            return {"event": "modele_monde_absent", "experience": self.experience_id}

        journal_rel = mm.get("journal")
        champ_latent = mm.get("champ_latent")
        latent_cli = mm.get("latent_cli")

        journal_path: Optional[Path] = None
        if isinstance(journal_rel, str) and journal_rel.strip():
            journal_path = self.resoudre_chemin(journal_rel.strip())
            os.environ["SNAKE_MODELE_JOURNAL"] = str(journal_path)

        if isinstance(champ_latent, str) and champ_latent.strip():
            os.environ["SNAKE_CHAMP_LATENT"] = champ_latent.strip()

        if isinstance(latent_cli, str) and latent_cli.strip():
            os.environ["SNAKE_MODE_LATENT_CLI"] = latent_cli.strip()

        payload = {
            "event": "modele_monde_resolu",
            "experience": self.experience_id,
            "SNAKE_MODELE_JOURNAL": os.environ.get("SNAKE_MODELE_JOURNAL"),
            "SNAKE_CHAMP_LATENT": os.environ.get("SNAKE_CHAMP_LATENT"),
            "SNAKE_MODE_LATENT_CLI": os.environ.get("SNAKE_MODE_LATENT_CLI"),
            "source": str((self.experience_dir / "experience.yml").resolve()),
        }

        if journal_path is not None and not journal_path.exists():
            raise FileNotFoundError(
                "Journal du modèle monde introuvable: "
                f"{journal_path} (déclaré dans experience.yml → modele_monde.journal)"
            )

        return payload
