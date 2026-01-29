# services/agent_service/app/modele_monde/recoder_journal_latent_v1.py
from __future__ import annotations

"""
CLI - recoder_journal_latent_v1

Lit episodes.jsonl
Charge un encodeur (encodeur_contrastif_v1.npz)
Encode toutes les observations -> embeddings (z)
Fit k-means (k=512)
Écrit episodes_latent_appris.jsonl où chaque evt reçoit: latent_id
et écrit stats_kmeans_v1.json
"""

import argparse
import json
from pathlib import Path
from typing import List, Optional

import numpy as np

from agent_service.app.modele_monde.encodeur_contrastif_v1 import (
    EncodeurContrastifV1,
    features_depuis_evt,
    kmeans_v1,
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", required=True, help="Path vers episodes.jsonl")
    p.add_argument("--encodeur", required=True, help="Path vers encodeur_contrastif_v1.npz")
    p.add_argument("--out", required=True, help="Sortie episodes_latent_appris.jsonl")

    # defaults figés (doc)
    p.add_argument("--k", type=int, default=512)

    # knobs
    p.add_argument("--iters", type=int, default=25)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--limite", type=int, default=None)
    return p


def main() -> int:
    args = _parser().parse_args()
    episodes_path = Path(args.episodes)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    enc = EncodeurContrastifV1.charger_npz(str(Path(args.encodeur)))

    # 1) lire + encoder en mémoire (N,d)
    evts: List[dict] = []
    Zs: List[np.ndarray] = []
    with open(episodes_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            evt = json.loads(line)
            try:
                x = features_depuis_evt(evt)
                z = enc.encoder(x)
            except Exception:
                continue
            evts.append(evt)
            Zs.append(z.astype(np.float32))
            if args.limite is not None and len(evts) >= int(args.limite):
                break

    if not evts:
        raise SystemExit("Aucun événement valide à recoder")

    Z = np.stack(Zs, axis=0).astype(np.float32)

    # 2) k-means
    C, labels, stats = kmeans_v1(Z, k=int(args.k), iters=int(args.iters), seed=int(args.seed))

    # 3) écrire jsonl recodé
    with open(out_path, "w", encoding="utf-8") as out:
        for evt, lab in zip(evts, labels):
            evt2 = dict(evt)
            evt2["latent_id"] = int(lab)
            out.write(json.dumps(evt2, ensure_ascii=False) + "\n")

    # stats
    stats_path = out_path.with_name("stats_kmeans_v1.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # centroides (utile si tu veux ensuite projeter de nouveaux obs sans refit)
    cent_path = out_path.with_name("centroides_kmeans_v1.npy")
    np.save(str(cent_path), C.astype(np.float32))

    print(f"[ok] recodé:    {out_path}")
    print(f"[ok] stats:    {stats_path}")
    print(f"[ok] centres:  {cent_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
