#!/usr/bin/env bash
set -euo pipefail

# Pipeline canonique JEPA (via ui_cli).
# Usage:
#   bash scripts/pipelines/jepa_run_v1.sh JEPA-1
#   bash scripts/pipelines/jepa_run_v1.sh JEPA-2

EXP="${1:-}"
if [[ -z "$EXP" ]]; then
  echo "usage: $0 <EXPERIENCE_ID>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export PYTHONPATH="services"

python -m ui_cli.app.main pipeline run --experience "$EXP" --phase all --seed 0
