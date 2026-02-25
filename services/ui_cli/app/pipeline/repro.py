from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def fixer_seed(seed: int) -> None:
    """Fixe les seeds des principaux générateurs pseudo-aléatoires."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copier_fichier(src: Path, dst: Path, *, overwrite: bool = True) -> None:
    """Copie robuste (création des parents)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        raise FileExistsError(f"destination existe déjà: {dst}")
    dst.write_bytes(src.read_bytes())


def _git_commit_sha(racine_repo: Path) -> Optional[str]:
    """Récupère le commit courant si on est dans un repo git."""
    head = racine_repo / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        ref = head.read_text(encoding="utf-8").strip()
        if ref.startswith("ref:"):
            ref_path = racine_repo / ".git" / ref.split(" ", 1)[1].strip()
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8").strip()
        return ref
    except Exception:
        return None


@dataclass
class PlanPipeline:
    experience_id: str
    run_id: str
    run_dir: str
    phases: list[str]
    seed: int
    date_utc: str
    git_commit: Optional[str]
    python: str
    platform: str
    configs: Dict[str, Dict[str, Any]]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    # Optionnel (ajout rétro-compatible): instantanés des entrées figées du run.
    inputs_fixes: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "experience_id": self.experience_id,
            "run_id": self.run_id,
            "run_dir": self.run_dir,
            "phases": self.phases,
            "seed": self.seed,
            "date_utc": self.date_utc,
            "git_commit": self.git_commit,
            "python": self.python,
            "platform": self.platform,
            "configs": self.configs,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }
        if self.inputs_fixes:
            d["inputs_fixes"] = self.inputs_fixes
        return d

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def load(path: Path) -> "PlanPipeline":
        d = json.loads(path.read_text(encoding="utf-8"))
        return PlanPipeline(
            experience_id=d["experience_id"],
            run_id=d["run_id"],
            run_dir=d["run_dir"],
            phases=list(d.get("phases") or []),
            seed=int(d.get("seed") or 0),
            date_utc=d.get("date_utc") or "",
            git_commit=d.get("git_commit"),
            python=d.get("python") or "",
            platform=d.get("platform") or "",
            configs=dict(d.get("configs") or {}),
            inputs=dict(d.get("inputs") or {}),
            outputs=dict(d.get("outputs") or {}),
            inputs_fixes=dict(d.get("inputs_fixes") or {}) if d.get("inputs_fixes") else None,
        )


def construire_plan(
    *,
    racine_repo: Path,
    experience_id: str,
    run_id: str,
    run_dir: Path,
    phases: list[str],
    seed: int,
    config_files: Dict[str, Path],
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
) -> PlanPipeline:
    date_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cfgs: Dict[str, Dict[str, Any]] = {}
    for k, fp in config_files.items():
        if not fp.exists():
            continue
        b = fp.read_bytes()
        cfgs[k] = {
            "path": str(fp),
            "sha256": sha256_bytes(b),
        }
    return PlanPipeline(
        experience_id=experience_id,
        run_id=run_id,
        run_dir=str(run_dir),
        phases=phases,
        seed=seed,
        date_utc=date_utc,
        git_commit=_git_commit_sha(racine_repo),
        python=sys.version.split()[0],
        platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
        configs=cfgs,
        inputs=inputs,
        outputs=outputs,
        inputs_fixes=None,
    )


def ecrire_inputs_fixes_dans_plan(plan_path: Path, inputs_fixes: Dict[str, Any]) -> None:
    """Patch rétro-compatible: ajoute/écrase la clé inputs_fixes dans plan_pipeline.json."""
    d = json.loads(plan_path.read_text(encoding="utf-8"))
    d["inputs_fixes"] = inputs_fixes
    plan_path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verifier_checksums_strict(run_dir: Path, *, expected: Dict[str, str]) -> None:
    """Valide que les fichiers du run correspondent aux checksums attendus."""
    for rel, sha_attendu in expected.items():
        p = run_dir / rel
        if not p.exists():
            raise FileNotFoundError(f"replay strict: fichier manquant: {rel}")
        sha = sha256_file(p)
        if sha != sha_attendu:
            raise ValueError(f"replay strict: checksum différent pour {rel}")


def ecrire_checksums(run_dir: Path, paths: Iterable[Path]) -> Path:
    checks = {}
    for p in paths:
        try:
            if p.exists() and p.is_file():
                checks[str(p.relative_to(run_dir))] = sha256_file(p)
        except Exception:
            continue
    out = run_dir / "checksums.json"
    out.write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def verifier_configs_strict(plan: PlanPipeline) -> None:
    """Vérifie que les fichiers de config présents correspondent aux sha256 du plan."""
    for _, cfg in (plan.configs or {}).items():
        p = Path(cfg.get("path") or "")
        attendu = cfg.get("sha256")
        if not p.exists():
            raise FileNotFoundError(f"replay strict: config introuvable: {p}")
        if attendu and sha256_file(p) != attendu:
            raise ValueError(f"replay strict: config modifiée: {p}")
