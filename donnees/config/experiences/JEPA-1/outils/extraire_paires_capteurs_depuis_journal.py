from __future__ import annotations

import argparse, json, os, hashlib, base64
from typing import Any, Dict, List

import torch


def hashing_vector(s: str, dim: int, n_grams: int = 3) -> List[float]:
    """
    Fallback déterministe (prototype) si la décodification base64 échoue :
    - n-grams de caractères
    - hashing dans un vecteur de taille dim
    - comptage normalisé (L1)
    """
    v = [0.0] * dim
    if not s:
        return v
    s = str(s)
    n = max(1, int(n_grams))
    for i in range(0, max(0, len(s) - n + 1)):
        g = s[i:i+n]
        h = int(hashlib.sha256(g.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        v[idx] += 1.0
    tot = sum(v)
    if tot > 0:
        v = [x / tot for x in v]
    return v


def base64_bytes_vector(s: str, dim: int) -> List[float]:
    """
    Mode recommandé JEPA-1 :
    - capteurs_compact est une chaîne base64
    - on la décode en bytes
    - on produit un vecteur float dans [0,1] de longueur dim
    Note: si la longueur décodée diffère, on pad/truncate à dim.
    """
    b = base64.b64decode(s.encode("utf-8"), validate=False)
    bb = list(b)
    if len(bb) >= dim:
        bb = bb[:dim]
    else:
        bb = bb + [0] * (dim - len(bb))
    return [x / 255.0 for x in bb]


def to_vect(val: Any, dim: int, n_grams: int, mode_string: str) -> List[float]:
    """
    - si list -> vecteur numérique (pad/truncate)
    - si string -> base64_bytes (par défaut) ou hashing (fallback)
    """
    if isinstance(val, list):
        vv = [float(x) for x in val[:dim]]
        if len(vv) < dim:
            vv += [0.0] * (dim - len(vv))
        return vv

    if isinstance(val, str):
        if mode_string == "base64_bytes":
            try:
                return base64_bytes_vector(val, dim=dim)
            except Exception:
                # fallback hashing si base64 invalide
                return hashing_vector(val, dim=dim, n_grams=n_grams)
        # mode_string == "hashing"
        return hashing_vector(val, dim=dim, n_grams=n_grams)

    # dernier recours
    return hashing_vector(str(val), dim=dim, n_grams=n_grams)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True, help="journal_episodes.jsonl (source)")
    ap.add_argument("--sortie", required=True, help="artefacts/datasets/paires_capteurs.pt")
    ap.add_argument("--champ-capteurs", default="capteurs_compact")
    ap.add_argument("--dim", type=int, default=560, help="dim du vecteur capteurs (JEPA-1: 560)")
    ap.add_argument("--n-grams", type=int, default=3, help="uniquement pour fallback hashing")
    ap.add_argument("--mode-string", choices=["base64_bytes", "hashing"], default="base64_bytes")
    ap.add_argument("--champ-episode", default="episode_id")
    ap.add_argument("--champ-tick", default="tick")
    args = ap.parse_args()

    # Lecture et groupement par episode_id, puis tick
    episodes: Dict[str, Dict[int, Any]] = {}
    with open(args.journal, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            e = json.loads(line)
            ep = str(e.get(args.champ_episode, "0"))
            t = int(e.get(args.champ_tick, 0))
            cap = e.get(args.champ_capteurs)
            if cap is None:
                continue
            episodes.setdefault(ep, {})[t] = cap

    xs: List[List[float]] = []
    ys: List[List[float]] = []

    for ep, ticks in episodes.items():
        for t in sorted(ticks.keys()):
            if (t + 1) in ticks:
                x = to_vect(ticks[t], dim=args.dim, n_grams=args.n_grams, mode_string=args.mode_string)
                y = to_vect(ticks[t+1], dim=args.dim, n_grams=args.n_grams, mode_string=args.mode_string)
                xs.append(x)
                ys.append(y)

    os.makedirs(os.path.dirname(args.sortie), exist_ok=True)
    obj = {"x": torch.tensor(xs), "y": torch.tensor(ys), "meta": {
        "source_journal": args.journal,
        "champ_capteurs": args.champ_capteurs,
        "dim": args.dim,
        "mode_string": args.mode_string,
        "n_grams": args.n_grams,
        "nb_paires": len(xs),
    }}
    torch.save(obj, args.sortie)
    print("OK:", args.sortie)
    print("nb_paires:", len(xs))
    print("meta:", obj["meta"])


if __name__ == "__main__":
    main()
