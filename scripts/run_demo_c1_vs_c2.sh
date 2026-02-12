
#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=services

EXP="snake_collectif_v1"
ARENE_TRAIN="snake_collectif_v1_train"
ARENE_EVAL="snake_collectif_v1_eval"

AGENT_C1="snake_collectif_v1_c1"
AGENT_C2="snake_collectif_v1_c2"

LATENT="signaux_percus_hash_v1"

EP_TRAIN=100
EP_EVAL=50
MAX_TICKS=1000
SEEDS=(0 1 2)

run_one () {
  local CONDITION="$1"
  local AGENT="$2"
  local SEED="$3"
  local PHASE="$4"
  local ARENE="$5"
  local EPISODES="$6"
  local OUT="artefacts/experiences/${EXP}/${CONDITION}/seed_${SEED}/${PHASE}.jsonl"

  mkdir -p "$(dirname "$OUT")"

  python -m ui_cli.app.main     --experience "$EXP"     --arene "$ARENE"     --agent "$AGENT"     --latent "$LATENT"     --episodes "$EPISODES"     --max-ticks "$MAX_TICKS"     --seed "$SEED"     --journal "$OUT"     --truncate
}

for SEED in "${SEEDS[@]}"; do
  run_one "C1" "$AGENT_C1" "$SEED" "train" "$ARENE_TRAIN" "$EP_TRAIN"
  run_one "C1" "$AGENT_C1" "$SEED" "eval" "$ARENE_EVAL" "$EP_EVAL"
  run_one "C2" "$AGENT_C2" "$SEED" "train" "$ARENE_TRAIN" "$EP_TRAIN"
  run_one "C2" "$AGENT_C2" "$SEED" "eval" "$ARENE_EVAL" "$EP_EVAL"
done

echo "Démo terminée."
