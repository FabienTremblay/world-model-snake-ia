#!/usr/bin/env bash
set -euo pipefail

# Valide syntaxe YAML de tous les agent*.yml découverts
PYTHONPATH=services python - <<'PY'
from pathlib import Path
import yaml

base = Path("services/agent_service/app/agents")
paths = sorted(list(base.glob("**/agent*.yml")) + list(base.glob("**/agent*.yaml")))
if not paths:
    print("aucun agent*.yml trouvé")
    raise SystemExit(1)

ok = 0
ko = 0
for p in paths:
    try:
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("document YAML doit être un dict (map), pas une liste/scalaire")
        ok += 1
    except Exception as e:
        ko += 1
        print(f"[KO] {p}: {e}")

print(f"OK={ok}  KO={ko}")
if ko:
    raise SystemExit(2)
PY
