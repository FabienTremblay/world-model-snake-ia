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

EXP_DIR="donnees/config/experiences/${EXP}"
RUNS_DIR="${EXP_DIR}/artefacts/runs"
OUT_ROOT="artefacts/experiences/${EXP}"

trouver_journal () {
  local RUN_DIR="$1"
  # ordre de préférence : nouveau nom -> ancien nom
  if [[ -f "${RUN_DIR}/journal_episodes.jsonl" ]]; then
    echo "${RUN_DIR}/journal_episodes.jsonl"
  elif [[ -f "${RUN_DIR}/journal.jsonl" ]]; then
    echo "${RUN_DIR}/journal.jsonl"
  else
    echo ""
  fi
}

run_one () {
  local CONDITION="$1"
  local AGENT="$2"
  local SEED="$3"
  local PHASE="$4"
  local ARENE="$5"
  local EPISODES="$6"

  local TAG="${EXP}__${CONDITION}__seed${SEED}__${PHASE}"
  echo "=== ${TAG} ==="

  python -m ui_cli.app.main     --experience "${EXP}"     --run-tag "${TAG}"     --arene "${ARENE}"     --agent "${AGENT}"     --latent "${LATENT}"     --episodes "${EPISODES}"     --max-ticks "${MAX_TICKS}"     --seed "${SEED}"     --truncate

  if [[ ! -d "${RUNS_DIR}" ]]; then
    echo "[ERREUR] runs_dir introuvable: ${RUNS_DIR}" >&2
    exit 2
  fi

  local RUN_DIR
  RUN_DIR=$(ls -1dt "${RUNS_DIR}"/* 2>/dev/null | grep "${TAG}" | head -n 1 || true)
  if [[ -z "${RUN_DIR}" ]]; then
    echo "[ERREUR] Impossible de retrouver le run pour tag=${TAG} sous ${RUNS_DIR}" >&2
    ls -1 "${RUNS_DIR}" >&2 || true
    exit 3
  fi

  local SRC
  SRC=$(trouver_journal "${RUN_DIR}")
  if [[ -z "${SRC}" ]]; then
    echo "[ERREUR] journal introuvable dans ${RUN_DIR} (attendu: journal_episodes.jsonl ou journal.jsonl)" >&2
    ls -la "${RUN_DIR}" >&2 || true
    exit 4
  fi

  local DST_DIR="${OUT_ROOT}/${CONDITION}/seed_${SEED}"
  local DST="${DST_DIR}/${PHASE}.jsonl"
  mkdir -p "${DST_DIR}"
  cp -f "${SRC}" "${DST}"
  echo "➡️  Copié: ${DST}"
}

for SEED in "${SEEDS[@]}"; do
  run_one "C1" "${AGENT_C1}" "${SEED}" "train" "${ARENE_TRAIN}" "${EP_TRAIN}"
  run_one "C1" "${AGENT_C1}" "${SEED}" "eval"  "${ARENE_EVAL}"  "${EP_EVAL}"

  run_one "C2" "${AGENT_C2}" "${SEED}" "train" "${ARENE_TRAIN}" "${EP_TRAIN}"
  run_one "C2" "${AGENT_C2}" "${SEED}" "eval"  "${ARENE_EVAL}"  "${EP_EVAL}"
done

echo
echo "Démo terminée."
echo "Résultats centralisés sous : ${OUT_ROOT}/"
