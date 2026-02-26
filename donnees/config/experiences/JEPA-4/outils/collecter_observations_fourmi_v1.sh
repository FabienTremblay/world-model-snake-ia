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

# ui_cli écrit le journal dans un run horodaté.
# On récupère le run le plus récent correspondant au tag.
RUN_DIR="$(ls -1dt "$EXP_DIR/artefacts/runs/"*"$RUN_TAG"* 2>/dev/null | head -n 1 || true)"
if [[ -z "$RUN_DIR" ]]; then
  echo "[JEPA-1] ERREUR: aucun run trouvé sous $EXP_DIR/artefacts/runs (tag=$RUN_TAG)" >&2
  exit 1
fi

JOURNAL_RUN="$RUN_DIR/journal_episodes.jsonl"
if [[ ! -f "$JOURNAL_RUN" ]]; then
  echo "[JEPA-1] ERREUR: journal introuvable dans run: $JOURNAL_RUN" >&2
  exit 1
fi

# On copie le journal dans artefacts/datasets pour conserver les conventions JEPA-1.
JOURNAL="$EXP_DIR/artefacts/datasets/journal_episodes_fourmi.jsonl"
mkdir -p "$(dirname "$JOURNAL")"
cp -f "$JOURNAL_RUN" "$JOURNAL"
echo "[JEPA-1] OK: $JOURNAL (source: $JOURNAL_RUN)"

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
python "$EXP_DIR/outils/extraire_paires_v2.py" \
  --journal "$JOURNAL" \
  --sortie "$PAIRES" \
  --champ-capteurs capteurs_compact \
  --cle-episode-id episode_id \
  --dim 560

echo "[JEPA-1] OK: $PAIRES"
