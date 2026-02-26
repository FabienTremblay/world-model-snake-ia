from __future__ import annotations

import argparse, json
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True, help="artefacts/journaux/journal_agent.jsonl")
    ap.add_argument("--quantiles", default="0.5,0.75,0.9,0.95,0.99")
    args = ap.parse_args()

    qs = [float(x) for x in args.quantiles.split(",") if x.strip()]
    s=[]
    modes=[]
    with open(args.journal, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            e=json.loads(line)
            s.append(float(e.get("surprise", 0.0)))
            modes.append(e.get("mode"))
    s=np.array(s, dtype=np.float64)
    print("n", len(s), "mean", float(s.mean()), "std", float(s.std()), "min", float(s.min()), "max", float(s.max()))
    for q in qs:
        print(f"p{int(q*100):02d}", float(np.quantile(s, q)))

    if modes:
        from collections import Counter
        c=Counter(modes)
        print("modes:", dict(c))

if __name__ == "__main__":
    main()
