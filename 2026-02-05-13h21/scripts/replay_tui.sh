#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# optionnel: pointer vers un autre journal
# export SNAKE_JOURNAL_PATH="/chemin/vers/episodes.jsonl"

export PYTHONPATH="services"

python -m ui_tui.app.replay_main

