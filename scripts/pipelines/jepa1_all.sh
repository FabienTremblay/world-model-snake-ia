#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${PYTHONPATH:-services}"
python -m ui_cli.app.main pipeline run --experience JEPA-1 --phase all
