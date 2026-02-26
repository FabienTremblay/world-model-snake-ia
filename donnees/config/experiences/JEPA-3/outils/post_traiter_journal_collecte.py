from __future__ import annotations

import argparse, json, os, time
from typing import Any, Dict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True, help="journal_episodes_fourmi.jsonl (source)")
    ap.add_argument("--sortie", required=True, help="journal enrichi (dest)")
    ap.add_argument("--agent-id", default="fourmi")
    ap.add_argument("--role-agent", default="collecteur")
    ap.add_argument("--objectif", default="couverture_observations")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    if (not args.overwrite) and os.path.exists(args.sortie):
        raise SystemExit(f"sortie existe déjà: {args.sortie} (utiliser --overwrite)")

    os.makedirs(os.path.dirname(args.sortie), exist_ok=True)

    n=0
    with open(args.journal, "r", encoding="utf-8") as fin, open(args.sortie, "w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            e: Dict[str, Any] = json.loads(line)
            e.setdefault("agent_id", args.agent_id)
            e.setdefault("role_agent", args.role_agent)
            e.setdefault("objectif", args.objectif)
            e.setdefault("horodatage_traitement", time.strftime("%Y-%m-%d_%Hh%M"))
            fout.write(json.dumps(e, ensure_ascii=False) + "\n")
            n += 1

    print("OK:", args.sortie)
    print("lignes:", n)

if __name__ == "__main__":
    main()
