#!/usr/bin/env bash
set -euo pipefail

# JEPA-1 — Collecte contrôlée d'observations (agent fourmi)
#
# Produit un journal d'épisodes via ui_cli, puis crée :
#   - artefacts/datasets/journal_episodes_fourmi.jsonl
#   - artefacts/datasets/paires_capteurs.pt
#
# Le pipeline JEPA-1 (A107/A108 offline) réutilise ensuite ces paires.

RACINE_REPO="$(cd "$(dirname "$0")/../../../../.." && pwd)"
EXP_DIR="$RACINE_REPO/donnees/config/experiences/JEPA-1"

export PYTHONPATH="$RACINE_REPO/services"

RUN_TAG="jepa1_collecte_fourmi"
ARENE_PATH="$EXP_DIR/arenes/fourmi_v1.yml"

echo "[JEPA-1] collecte: experience=JEPA-1 agent=snake_collectif_v1_fourmi arene=$ARENE_PATH"

python -m ui_cli.app.main \
  --experience JEPA-1 \
  --run-tag "$RUN_TAG" \
  --arene "$ARENE_PATH" \
  --agent snake_collectif_v1_fourmi \
  --episodes 30 \
  --max-ticks 300 \
  --seed 123 \
  --niveau-bruit 0 \
  --truncate \
  --capture-stdout

# Trouver le dernier run correspondant au tag
RUNS_DIR="$EXP_DIR/artefacts/runs"
DERNIER_RUN="$(ls -1 "$RUNS_DIR" | grep "_${RUN_TAG}$" | tail -n 1 || true)"
if [[ -z "$DERNIER_RUN" ]]; then
  echo "[JEPA-1] ERREUR: aucun run trouvé avec tag $RUN_TAG dans $RUNS_DIR" >&2
  exit 2
fi

JOURNAL_SRC="$RUNS_DIR/$DERNIER_RUN/journal_episodes.jsonl"
if [[ ! -f "$JOURNAL_SRC" ]]; then
  echo "[JEPA-1] ERREUR: journal introuvable: $JOURNAL_SRC" >&2
  exit 2
fi

DATASETS_DIR="$EXP_DIR/artefacts/datasets"
mkdir -p "$DATASETS_DIR"
JOURNAL_DST="$DATASETS_DIR/journal_episodes_fourmi.jsonl"

cp -f "$JOURNAL_SRC" "$JOURNAL_DST"
echo "[JEPA-1] OK: $JOURNAL_DST"

# Extraire paires (t -> t+1) sur capteurs_compact
python "$EXP_DIR/outils/extraire_paires_capteurs_depuis_journal.py" \
  --journal "$JOURNAL_DST" \
  --sortie "$DATASETS_DIR/paires_capteurs.pt" \
  --champ-capteurs capteurs_compact \
  --dim 256 \
  --n-grams 3

echo "[JEPA-1] OK: $DATASETS_DIR/paires_capteurs.pt"
