#!/usr/bin/env python
import argparse
from pathlib import Path
import sys

def _ajouter_racine_repo_au_pythonpath():
    # Remonte jusqu’au dossier qui contient "services"
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "services").exists():
            sys.path.insert(0, str(parent))
            return
    raise RuntimeError("Impossible de trouver la racine du repo (dossier 'services' introuvable).")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--champ-capteurs", default="capteurs_compact")
    ap.add_argument("--cle-episode-id", default="episode_id")
    ap.add_argument("--dim", type=int, default=560)
    args = ap.parse_args()

    _ajouter_racine_repo_au_pythonpath()

    from services.agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs

    e = ExtracteurPairesCapteurs(args.dim)
    e.extraire_et_sauvegarder(
        args.journal,
        args.sortie,
        cle_capteurs=args.champ_capteurs,
        cle_episode_id=args.cle_episode_id,
    )

if __name__ == "__main__":
    main()
