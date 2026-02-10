#!/usr/bin/env bash
set -euo pipefail

# Activité SAI-A108 — Éprouver un agent
#
# 1) Lance un run minimal avec agent_personne
# 2) Récupère automatiquement le dernier répertoire de run
# 3) Produit un résumé (actions, fins d'épisodes, score/longueur)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="services"

experience="${1:-cours4}"
arene="${2:-cours4_tiny_planification}"
agent_personne_id="${3:-ap_cours4_v1}"
episodes="${4:-1}"
max_ticks="${5:-50}"
seed="${6:-123}"

python -m ui_cli.app.main \
  --experience "$experience" \
  --arene "$arene" \
  --agent agent_personne \
  --agent-personne-id "$agent_personne_id" \
  --episodes "$episodes" \
  --max-ticks "$max_ticks" \
  --seed "$seed"

dernier_run="$(ls -1dt "donnees/config/experiences/${experience}/artefacts/runs/"* | head -n 1)"
echo
echo "Dernier run: $dernier_run"

export DERNIER_RUN="$dernier_run"

python - <<'PY'
import json
import os
from collections import Counter, defaultdict

dernier_run = os.environ.get("DERNIER_RUN")
if not dernier_run:
    raise SystemExit("DERNIER_RUN manquant")

path = os.path.join(dernier_run, "journal_episodes.jsonl")

actions = Counter()
raisons = Counter()
par_episode = defaultdict(lambda: {"score": None, "longueur": None, "termine": False, "raison_fin": None, "ticks": 0})

with open(path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        ep = obj.get("episode_id")
        act = obj.get("action")
        actions[str(act)] += 1

        par_episode[ep]["score"] = obj.get("score")
        par_episode[ep]["longueur"] = obj.get("longueur")
        par_episode[ep]["ticks"] = max(par_episode[ep]["ticks"], int(obj.get("tick") or 0))

        if obj.get("termine"):
            par_episode[ep]["termine"] = True
            par_episode[ep]["raison_fin"] = obj.get("raison_fin")
            raisons[str(obj.get("raison_fin"))] += 1

print("\n=== Résumé A108 ===")
print(f"Journal: {path}")

print("\nActions (top 15):")
for k, v in actions.most_common(15):
    print(f"  {k:>16} : {v}")

print("\nFin d'épisodes:")
if not raisons:
    print("  (aucune fin enregistrée dans la fenêtre de ticks)\n")
else:
    for k, v in raisons.most_common():
        print(f"  {k:>16} : {v}")

print("\nDétails par épisode:")
for ep in sorted(par_episode.keys()):
    d = par_episode[ep]
    print(f"  ep {ep:>3} | ticks≈{d['ticks']:<3} | score={d['score']:<3} | longueur={d['longueur']:<3} | termine={d['termine']} | raison_fin={d['raison_fin']}")

print("\nExtrait (20 premières lignes action):")
shown = 0
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        print(f"  tick={obj.get('tick'):>3}  action={obj.get('action')}")
        shown += 1
        if shown >= 20:
            break
PY
