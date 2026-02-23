from __future__ import annotations

import argparse, json, os, time
from typing import Any, Dict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True, help="artefacts/journaux/journal_agent.jsonl")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    src = args.journal
    if not os.path.exists(src):
        raise SystemExit(f"introuvable: {src}")
    tmp = src + ".tmp"
    bak = src + ".bak"

    n=0
    with open(src, "r", encoding="utf-8") as fin, open(tmp, "w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            e: Dict[str, Any] = json.loads(line)
            if e.get("mode") == "connu_planifier":
                e["mode"] = "connu_exploiter"
            e.setdefault("horodatage_normalisation", time.strftime("%Y-%m-%d_%Hh%M"))
            fout.write(json.dumps(e, ensure_ascii=False) + "\n")
            n += 1

    if args.overwrite:
        if os.path.exists(bak):
            os.remove(bak)
        os.rename(src, bak)
        os.rename(tmp, src)
        print("OK:", src, "(backup:", bak, ")")
    else:
        print("OK:", tmp, "(dry-run, utiliser --overwrite)")
    print("lignes:", n)

if __name__ == "__main__":
    main()
