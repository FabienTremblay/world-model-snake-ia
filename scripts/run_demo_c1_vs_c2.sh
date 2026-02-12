#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=services

# Campagne
EXP="snake_collectif_v1"

# Arènes (spécifiques à la campagne)
ARENE_TRAIN="snake_collectif_v1_train"
ARENE_EVAL="snake_collectif_v1_eval"

# Agents (norme plug-in v1 / catalogue)
AGENT_C1="snake_collectif_v1_c1"
AGENT_C2="snake_collectif_v1_c2"

# Latent (peut être override par experience.yml ; ok pour la démo)
LATENT="signaux_percus_hash_v1"

# Budgets (démo courte)
EP_TRAIN=100
EP_EVAL=50
MAX_TICKS=1000

# Seeds
SEEDS=(0 1 2)

# Où sont les runs quand --experience est utilisé
EXP_DIR="donnees/config/experiences/${EXP}"
RUNS_DIR="${EXP_DIR}/artefacts/runs"

# Où l'on veut centraliser les sorties de campagne (stable)
OUT_ROOT="artefacts/experiences/${EXP}"

run_one () {
  local CONDITION="$1"   # C1 ou C2
  local AGENT="$2"
  local SEED="$3"
  local PHASE="$4"       # train | eval
  local ARENE="$5"
  local EPISODES="$6"

  local TAG="${EXP}__${CONDITION}__seed${SEED}__${PHASE}"
  echo "=== ${TAG} ==="

  # Lance via bac à sable (le --journal CLI est ignoré et remplacé par run_dir/journal_episodes.jsonl)
  python -m ui_cli.app.main     --experience "${EXP}"     --run-tag "${TAG}"     --arene "${ARENE}"     --agent "${AGENT}"     --latent "${LATENT}"     --episodes "${EPISODES}"     --max-ticks "${MAX_TICKS}"     --seed "${SEED}"     --truncate

  # Résoudre le répertoire de run créé (robuste à un préfixe horodaté)
  if [[ ! -d "${RUNS_DIR}" ]]; then
    echo "[ERREUR] runs_dir introuvable: ${RUNS_DIR}" >&2
    exit 2
  fi

  # Cherche le run le plus récent contenant le TAG dans son nom
  local RUN_DIR
  RUN_DIR=$(ls -1dt "${RUNS_DIR}"/* 2>/dev/null | grep "${TAG}" | head -n 1 || true)
  if [[ -z "${RUN_DIR}" ]]; then
    echo "[ERREUR] Impossible de retrouver le run pour tag=${TAG} sous ${RUNS_DIR}" >&2
    echo "Contenu runs:" >&2
    ls -1 "${RUNS_DIR}" >&2 || true
    exit 3
  fi

  local SRC="${RUN_DIR}/journal_episodes.jsonl"
  if [[ ! -f "${SRC}" ]]; then
    echo "[ERREUR] journal introuvable: ${SRC}" >&2
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
