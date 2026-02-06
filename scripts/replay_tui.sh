#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="services"

# optionnel:
# export SNAKE_JOURNAL_PATH="artefacts/episodes.jsonl"

python -m ui_tui.app.main --mode replay
