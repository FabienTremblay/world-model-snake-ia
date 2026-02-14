#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  pipeline_registre_collectif_v1.sh [--config fichier.env] [--run-dir <run_dir>] [--all-runs] [--list-runs]

Options:
  --config   Fichier .env KEY=VALUE à charger de manière robuste.
  --run-dir  Run explicite à analyser.
  --all-runs Traite tous les runs "complets" (journal.jsonl + metrics.jsonl) et fusionne.
  --list-runs Affiche les runs détectés (complets/incomplets) et sort.

Variables (par défaut si non fournies):
  SNAKE_O1_PREFIX_BITS="12 16 20"

Filtrage (optionnel):
  SNAKE_RUN_INCLUDE_REGEX   (ex: "__C1__|__C2__")
  SNAKE_RUN_EXCLUDE_REGEX   (ex: "_tui$")
  SNAKE_RUN_MAX             (ex: 20) limite le nombre de runs traités (après tri décroissant)
USAGE
}

strip_outer_quotes() {
  local v="$1"
  if [[ "$v" =~ ^\".*\"$ ]]; then
    echo "${v:1:${#v}-2}"
  elif [[ "$v" =~ ^\'.*\'$ ]]; then
    echo "${v:1:${#v}-2}"
  else
    echo "$v"
  fi
}

charger_config_env() {
  local env_file="$1"
  [[ -f "$env_file" ]] || { echo "[ERR] config introuvable: $env_file" >&2; exit 2; }
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      local k="${BASH_REMATCH[1]}"
      local v="${BASH_REMATCH[2]}"
      v="$(echo "$v" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
      v="$(strip_outer_quotes "$v")"
      export "$k=$v"
    fi
  done < "$env_file"
}

is_run_complet() {
  local rd="$1"
  [[ -f "$rd/journal.jsonl" && -f "$rd/metrics.jsonl" ]]
}

abspath() {
  python - <<'PY' "$1"
import os,sys
print(os.path.abspath(sys.argv[1]))
PY
}

matches_regex() {
  local text="$1"
  local re="$2"
  [[ -z "$re" ]] && return 0
  [[ "$text" =~ $re ]]
}

CONFIG=""
RUN_DIR=""
ALL_RUNS=0
LIST_RUNS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="${2:-}"; shift 2 ;;
    --run-dir) RUN_DIR="${2:-}"; shift 2 ;;
    --all-runs) ALL_RUNS=1; shift ;;
	    --list-runs) LIST_RUNS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERR] argument inconnu: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -n "${CONFIG:-}" ]]; then
  charger_config_env "$CONFIG"
fi

SNAKE_O1_PREFIX_BITS="${SNAKE_O1_PREFIX_BITS:-12 16 20}"
SNAKE_RUN_INCLUDE_REGEX="${SNAKE_RUN_INCLUDE_REGEX:-}"
SNAKE_RUN_EXCLUDE_REGEX="${SNAKE_RUN_EXCLUDE_REGEX:-}"
SNAKE_RUN_MAX="${SNAKE_RUN_MAX:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "[PIPELINE] exp_dir : $EXP_DIR"

ALL_DETECTES=()
while IFS= read -r rd; do
  [[ -z "$rd" ]] && continue
  ALL_DETECTES+=("$rd")
done < <(ls -1dt "$EXP_DIR/artefacts/runs/"* 2>/dev/null || true)

NB_TOTAL=${#ALL_DETECTES[@]}
NB_COMPLETS=0
NB_INCOMPLETS=0
for rd in "${ALL_DETECTES[@]}"; do
  if is_run_complet "$rd"; then
    ((NB_COMPLETS+=1))
  else
    ((NB_INCOMPLETS+=1))
  fi
done

if [[ "$LIST_RUNS" -eq 1 ]]; then
  echo "[PIPELINE] runs détectés : $NB_TOTAL (complets=$NB_COMPLETS, incomplets=$NB_INCOMPLETS)"
  for rd in "${ALL_DETECTES[@]}"; do
    rd_abs="$(abspath "$rd")"
    if is_run_complet "$rd"; then
      echo "  [OK ] $rd_abs"
    else
      echo "  [SKP] $rd_abs (incomplet)"
    fi
  done
  exit 0
fi

RUNS=()
if [[ -n "${RUN_DIR:-}" ]]; then
  RUNS+=("$RUN_DIR")
elif [[ "$ALL_RUNS" -eq 1 ]]; then
  for rd in "${ALL_DETECTES[@]}"; do
    [[ -z "$rd" ]] && continue
    if is_run_complet "$rd"; then
      rd_abs="$(abspath "$rd")"
      base="$(basename "$rd_abs")"
      if ! matches_regex "$base" "$SNAKE_RUN_INCLUDE_REGEX"; then
        continue
      fi
      if [[ -n "$SNAKE_RUN_EXCLUDE_REGEX" ]] && matches_regex "$base" "$SNAKE_RUN_EXCLUDE_REGEX"; then
        continue
      fi
      RUNS+=("$rd")
      if [[ -n "$SNAKE_RUN_MAX" && "${#RUNS[@]}" -ge "$SNAKE_RUN_MAX" ]]; then
        break
      fi
    fi
  done
else
  for rd in "${ALL_DETECTES[@]}"; do
    [[ -z "$rd" ]] && continue
    if is_run_complet "$rd"; then
      rd_abs="$(abspath "$rd")"
      base="$(basename "$rd_abs")"
      if ! matches_regex "$base" "$SNAKE_RUN_INCLUDE_REGEX"; then
        continue
      fi
      if [[ -n "$SNAKE_RUN_EXCLUDE_REGEX" ]] && matches_regex "$base" "$SNAKE_RUN_EXCLUDE_REGEX"; then
        continue
      fi
      RUNS+=("$rd")
      break
    fi
  done
fi

if [[ "${#RUNS[@]}" -eq 0 ]]; then
  echo "[ERR] Aucun run-dir complet sélectionné." >&2
  echo "      Détectés: total=$NB_TOTAL (complets=$NB_COMPLETS, incomplets=$NB_INCOMPLETS)" >&2
  echo "      Filtres: include='${SNAKE_RUN_INCLUDE_REGEX:-}' exclude='${SNAKE_RUN_EXCLUDE_REGEX:-}' max='${SNAKE_RUN_MAX:-}'" >&2
  echo "      Lance d'abord une exécution qui produit artefacts/runs/<run> avec journal.jsonl + metrics.jsonl." >&2
  exit 2
fi

echo "[PIPELINE] runs    : ${#RUNS[@]} (détectés=$NB_TOTAL, complets=$NB_COMPLETS, incomplets=$NB_INCOMPLETS)"
echo "[PIPELINE] prefix-bits: ${SNAKE_O1_PREFIX_BITS}"
if [[ -n "${SNAKE_RUN_INCLUDE_REGEX:-}" || -n "${SNAKE_RUN_EXCLUDE_REGEX:-}" || -n "${SNAKE_RUN_MAX:-}" ]]; then
  echo "[PIPELINE] filtres : include='${SNAKE_RUN_INCLUDE_REGEX:-}' exclude='${SNAKE_RUN_EXCLUDE_REGEX:-}' max='${SNAKE_RUN_MAX:-}'"
fi

REG_DIR="$EXP_DIR/artefacts/registres"
mkdir -p "$REG_DIR"
RUN_REG_DIR="$REG_DIR/runs"
mkdir -p "$RUN_REG_DIR"

INPUTS=()

for rd in "${RUNS[@]}"; do
  rd_abs="$(abspath "$rd")"
  run_base="$(basename "$rd_abs")"
  echo "[PIPELINE] run_dir : $rd_abs"

  if ! is_run_complet "$rd_abs"; then
    echo "[WARN] run incomplet (skip): $rd_abs"
    continue
  fi

  reg="$rd_abs/registre_epistemique_v2.json"
  if [[ ! -f "$reg" ]]; then
    echo "[WARN] registre manquant: création d'un registre vide à $reg"
    printf '{"version":"v2","propositions":[]}\n' > "$reg"
  fi

  out_run="$RUN_REG_DIR/$run_base"
  mkdir -p "$out_run"

  out_o2="$out_run/o2_propositions.jsonl"
  python "$EXP_DIR/outils/o2_transformer_registre_epistemique_v2.py" \
    --run-dir "$rd_abs" \
    --sortie "$out_o2"
  INPUTS+=("$out_o2")

  for pb in $SNAKE_O1_PREFIX_BITS; do
    out_o1="$out_run/o1_surprises_prefix${pb}.jsonl"
    python "$EXP_DIR/outils/o1_observateur_surprise_v1.py" \
      --run-dir "$rd_abs" \
      --prefix-bits "$pb" \
      --sortie "$out_o1"
    INPUTS+=("$out_o1")
  done
done

INPUTS_OK=()
for f in "${INPUTS[@]}"; do
  [[ -f "$f" ]] && INPUTS_OK+=("$f")
done

if [[ "${#INPUTS_OK[@]}" -eq 0 ]]; then
  echo "[ERR] Aucune entrée produite. Vérifie O1/O2." >&2
  exit 3
fi

OUT_REG="$REG_DIR/registre_epistemique_collectif.jsonl"
python "$EXP_DIR/outils/conventionneur_v1.py" \
  --sortie "$OUT_REG" \
  --inputs "${INPUTS_OK[@]}"

echo "[OK] registre collectif: $OUT_REG"
