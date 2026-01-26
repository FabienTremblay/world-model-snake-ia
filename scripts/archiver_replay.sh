#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SRC="artefacts/episodes.jsonl"
DIR="artefacts/replays"
MANIFEST="$DIR/manifest.json"

mkdir -p "$DIR"

if [[ ! -f "$SRC" ]]; then
  echo "Journal introuvable: $SRC" >&2
  exit 1
fi

slot="${1:-}"
if [[ -z "$slot" ]]; then
  echo "Usage: $0 <slot>   # ex: 10,20,...,100" >&2
  exit 2
fi

if ! [[ "$slot" =~ ^[0-9]+$ ]]; then
  echo "slot invalide: $slot" >&2
  exit 2
fi

dst="$DIR/replay-$(printf "%04d" "$slot").jsonl"
cp -f "$SRC" "$dst"

SLOT="$slot" DST="$dst" MANIFEST="$MANIFEST" python - <<'PY'
import json, os
from pathlib import Path

slot = int(os.environ["SLOT"])
dst = os.environ["DST"]
manifest = Path(os.environ["MANIFEST"])
manifest.parent.mkdir(parents=True, exist_ok=True)

data = {"slots": {}}
if manifest.exists():
    data = json.loads(manifest.read_text(encoding="utf-8"))
data.setdefault("slots", {})[str(slot)] = dst
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"OK: slot {slot} -> {dst}")
PY


