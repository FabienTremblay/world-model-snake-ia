"""donnees/config/experiences/JEPA-1/outils/entrainer_v2.py

Script d'entraînement JEPA-1 utilisant les modules refactorisés.

But:
- conserver des points d'entrée simples (.sh) pour JEPA-1
- sans dépendre d'un PYTHONPATH externe
- en important les modules canoniques sous services/agent_service

Remplace: entrainer_hypothese_pred_capteurs_v1.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _ajouter_racine_repo_au_pythonpath() -> None:
    """Ajoute la racine du repo (celle qui contient 'services/') au sys.path."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "services").exists():
            sys.path.insert(0, str(parent))
            return
    raise RuntimeError("Impossible de trouver la racine du repo (dossier 'services' introuvable).")


_ajouter_racine_repo_au_pythonpath()

from services.agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs
from services.agent_service.app.preparation_agent.entraineur_modele_predictif import (
    EntraineurModelePredicdictif,
)
from services.agent_service.app.modele_monde.predictif import ModelePredCapteursV1
from services.agent_service.app.epistemique_v2.gates import GateSurprise, ConfigGate


def charger_config(config_path: str):
    """Charger la configuration depuis JSON."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def entrainer_mode(config_path: str) -> None:
    """
    Mode entraînement.
    
    Équivalent de l'ancien mode --mode=entrainement
    """
    cfg = charger_config(config_path)
    base_dir = Path(config_path).parent.parent
    
    # 1. Charger les paires
    paires_path = base_dir / cfg["dataset_paires_pt"]
    x, y, metadata = ExtracteurPairesCapteurs.charger_paires(str(paires_path))
    
    # 2. Créer le modèle
    dim = cfg["capteurs"]["dim_vecteur"]
    hidden = cfg["entrainement"].get("hidden", 64)
    model = ModelePredCapteursV1(dim_in=dim, hidden=hidden)
    
    # 3. Entraîner
    entraineur = EntraineurModelePredicdictif(
        model=model,
        device=cfg["entrainement"].get("device", "cpu"),
        lr=cfg["entrainement"]["lr"],
        batch_size=cfg["entrainement"]["batch_size"],
        epochs=cfg["entrainement"]["epochs"],
        seed=cfg["entrainement"]["seed"]
    )
    
    rapport = entraineur.entrainer(x, y, verbose=True)
    
    # 4. Sauvegarder
    sortie_dir = base_dir / cfg["sortie_dir"]
    sortie_dir.mkdir(parents=True, exist_ok=True)
    
    poids_path = sortie_dir / "poids" / "agent_personne.poids.pt"
    poids_path.parent.mkdir(exist_ok=True)
    model.sauvegarder(str(poids_path), metadata=rapport)
    
    # 5. Spec agent
    spec = {
        "agent_personne_id": cfg.get("agent_personne_id", "agent_personne"),
        "experience": cfg.get("experience"),
        "artefacts": {"poids_pt": str(poids_path.relative_to(base_dir))},
    }
    spec_path = sortie_dir / "agents" / "agent_personne.json"
    spec_path.parent.mkdir(exist_ok=True)
    with open(spec_path, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"OK: {spec_path.relative_to(base_dir)}")
    print(f"OK: {poids_path.relative_to(base_dir)}")


def eprouver_mode(config_path: str) -> None:
    """
    Mode épreuve.
    
    Équivalent de l'ancien mode --mode=epreuve
    """
    cfg = charger_config(config_path)
    base_dir = Path(config_path).parent.parent
    
    # 1. Charger le modèle
    poids_path = base_dir / cfg["poids_pt"]
    model = ModelePredCapteursV1.depuis_checkpoint(
        str(poids_path),
        device=cfg["epreuve"].get("device", "cpu")
    )
    model.eval()
    
    # 2. Charger les paires
    paires_path = base_dir / cfg["dataset_paires_pt"]
    x, y, _ = ExtracteurPairesCapteurs.charger_paires(str(paires_path))
    
    # 3. Calculer surprises
    entraineur = EntraineurModelePredicdictif(
        model=model,
        device=cfg["epreuve"].get("device", "cpu")
    )
    surprises = entraineur.calculer_surprises(x, y)
    
    # 4. Calibrer gate
    gate_cfg = cfg.get("gate", {})
    config_gate = ConfigGate(
        mode=gate_cfg.get("mode", "quantile"),
        quantile=gate_cfg.get("quantile", 0.90),
        seuil_connu=gate_cfg.get("seuil_connu", 0.10)
    )
    gate = GateSurprise(config_gate)
    gate.calibrer(surprises)
    
    # 5. Générer journal agent
    sortie_dir = base_dir / cfg["sorties"]["journal_agent"]
    sortie_dir.parent.mkdir(parents=True, exist_ok=True)
    
    with open(sortie_dir, 'w', encoding='utf-8') as jf:
        for idx, surprise in enumerate(surprises):
            surprise_val = float(surprise.item())
            mode, action_type = gate.decider_mode(surprise_val)
            
            # Choisir action selon stratégie
            if mode == "connu_exploiter":
                action = cfg["policy"]["strategie_connu"]
            else:
                action = cfg["policy"]["strategie_inconnu"]
            
            jf.write(json.dumps({
                "idx": idx,
                "mode": mode,
                "surprise": surprise_val,
                "seuil_connu": gate.seuil_calibre,
                "action": action,
            }, ensure_ascii=False) + "\n")
    
    # 6. Registre épistémique
    registre_path = base_dir / cfg["sorties"]["registre_epistemique"]
    registre = {
        "experience": cfg.get("experience"),
        "gate": gate.to_dict(),
    }
    with open(registre_path, 'w', encoding='utf-8') as f:
        json.dump(registre, f, indent=2, ensure_ascii=False)
    
    print(f"OK: {sortie_dir}")
    print(f"OK: {registre_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["entrainement", "epreuve"], required=True)
    args = parser.parse_args()
    
    if args.mode == "entrainement":
        entrainer_mode(args.config)
    else:
        eprouver_mode(args.config)
