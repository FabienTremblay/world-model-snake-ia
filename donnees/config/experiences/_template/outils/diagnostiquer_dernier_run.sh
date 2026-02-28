#!/usr/bin/env bash
set -euo pipefail

ROOT_RUNS="${1:-artefacts/runs}"

RUN_PATH="$(ls -td "$ROOT_RUNS"/* 2>/dev/null | head -n 1)"
test -n "${RUN_PATH:-}" || { echo "Aucun run trouvé dans $ROOT_RUNS"; exit 1; }

"$(dirname "$0")/diagnostiquer_run.sh" "$RUN_PATH"
