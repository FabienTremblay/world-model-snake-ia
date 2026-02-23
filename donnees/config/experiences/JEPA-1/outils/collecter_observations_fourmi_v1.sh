#!/usr/bin/env bash
set -euo pipefail

# JEPA-1 — collecte d'observations via l'agent fourmi + post-traitement du journal
# Notes:
# - ui_cli accepte --run-tag (pas --run_tag)
# - ui_cli ne connaît pas --headless (la collecte est déjà non-interactive)
# - on conserve le journal brut + on produit un journal enrichi pour identifier le rôle "collecteur"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP_DIR="$(cd "$HERE/.." && pwd)"
EXP_NAME="JEPA-1"

AGENT_ID="snake_collectif_v1_fourmi"
ARENE="$EXP_DIR/arenes/fourmi_v1.yml"

echo "[JEPA-1] collecte: experience=$EXP_NAME agent=$AGENT_ID arene=$ARENE"

if [[ -z "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="services"
fi

RUN_TAG="jepa1_collecte_fourmi"
python -m ui_cli.app.main \
  --experience "$EXP_NAME" \
  --arene "$ARENE" \
  --agent "$AGENT_ID" \
  --run-tag "$RUN_TAG" \
  --capture-stdout

# Par convention JEPA-1: le script de collecte écrit ici
JOURNAL="$EXP_DIR/artefacts/datasets/journal_episodes_fourmi.jsonl"
if [[ ! -f "$JOURNAL" ]]; then
  echo "[JEPA-1] ERREUR: journal introuvable: $JOURNAL" >&2
  exit 1
fi
echo "[JEPA-1] OK: $JOURNAL"

# Journal enrichi (non-bloquant si tu ne l'utilises pas encore)
JOURNAL_ENRICHI="$EXP_DIR/artefacts/datasets/journal_episodes_fourmi.enrichi.jsonl"
python "$EXP_DIR/outils/post_traiter_journal_collecte.py" \
  --journal "$JOURNAL" \
  --sortie "$JOURNAL_ENRICHI" \
  --agent-id "fourmi" \
  --role-agent "collecteur" \
  --objectif "couverture_observations" \
  --overwrite
echo "[JEPA-1] OK: $JOURNAL_ENRICHI"

# Extraction paires capteurs (base64 -> vecteur 560)
PAIRES="$EXP_DIR/artefacts/datasets/paires_capteurs.pt"
python "$EXP_DIR/outils/extraire_paires_capteurs_depuis_journal.py" \
  --journal "$JOURNAL" \
  --sortie "$PAIRES" \
  --champ-capteurs capteurs_compact \
  --dim 560 \
  --mode-string base64_bytes

echo "[JEPA-1] OK: $PAIRES"
