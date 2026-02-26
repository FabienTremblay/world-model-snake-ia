from __future__ import annotations

import argparse, json

ACTIONS = {"avant", "observer_gauche", "observer_droite"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True, help="journal_agent.jsonl")
    args = ap.parse_args()

    nb = 0
    bad = 0
    exemples = []
    with open(args.journal, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            e = json.loads(line)
            a = e.get("action")
            nb += 1
            if a not in ACTIONS:
                bad += 1
                if len(exemples) < 5:
                    exemples.append({"idx": e.get("idx"), "action": a})
    if bad:
        print(f"ECHEC: {bad}/{nb} actions non conformes.")
        print("exemples:", exemples)
        raise SystemExit(2)
    print(f"OK: {nb} actions conformes ({sorted(ACTIONS)}).")

if __name__ == "__main__":
    main()
