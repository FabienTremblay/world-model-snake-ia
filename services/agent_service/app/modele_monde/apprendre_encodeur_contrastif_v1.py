# services/agent_service/app/modele_monde/apprendre_encodeur_contrastif_v1.py
from __future__ import annotations

"""
CLI - apprendre_encodeur_contrastif_v1

Lit episodes.jsonl
Entraîne un encodeur contrastif linéaire (InfoNCE)
Écrit:
  - encodeur_contrastif_v1.npz
  - stats_encodeur_contrastif_v1.json
"""

import argparse
import json
from pathlib import Path

from agent_service.app.modele_monde.encodeur_contrastif_v1 import (
    charger_features_depuis_jsonl,
    entrainer_encodeur_contrastif_v1,
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", required=True, help="Path vers episodes.jsonl")
    p.add_argument("--out-dir", required=True, help="Répertoire de sortie")

    # defaults figés (doc)
    p.add_argument("--d", type=int, default=16)
    p.add_argument("--batch", type=int, default=256)
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--tau", type=float, default=0.2)

    # knobs (facultatifs)
    p.add_argument("--lr", type=float, default=0.25)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--p-drop", type=float, default=0.15)
    p.add_argument("--bruit", type=float, default=0.01)
    p.add_argument("--limite", type=int, default=None, help="Limiter le nombre d'obs pour accélérer")
    return p


def main() -> int:
    args = _parser().parse_args()

    episodes = Path(args.episodes)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    X = charger_features_depuis_jsonl(str(episodes), limite=args.limite)
    if X.shape[0] == 0:
        raise SystemExit("Aucune observation valide dans episodes.jsonl")

    enc, stats = entrainer_encodeur_contrastif_v1(
        X,
        d=int(args.d),
        batch=int(args.batch),
        epochs=int(args.epochs),
        tau=float(args.tau),
        lr=float(args.lr),
        seed=int(args.seed),
        p_drop=float(args.p_drop),
        bruit=float(args.bruit),
    )

    path_npz = out_dir / "encodeur_contrastif_v1.npz"
    enc.sauver_npz(str(path_npz))

    path_stats = out_dir / "stats_encodeur_contrastif_v1.json"
    with open(path_stats, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"[ok] encodeur: {path_npz}")
    print(f"[ok] stats:    {path_stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

