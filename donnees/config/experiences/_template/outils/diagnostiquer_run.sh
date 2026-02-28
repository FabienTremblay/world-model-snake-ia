#!/usr/bin/env bash
set -euo pipefail

ENTREE="${1:?usage: diagnostiquer_run.sh <path_run | path_racine_runs>}"

# Ajuste si ton repo n'utilise pas PYTHONPATH=services
export PYTHONPATH="${PYTHONPATH:-services}"

# Si on nous donne une racine de runs, on prend le plus récent sous-dossier
# Heuristique : un "run" a typiquement un sous-dossier "epreuve/"
RUN_PATH="$ENTREE"

if [ -d "$RUN_PATH" ] && [ -d "$RUN_PATH/epreuve" ]; then
  : # c'est un run
else
  # peut-être une racine de runs
  # on choisit le sous-dossier le plus récent contenant epreuve/
  CANDIDAT="$(find "$RUN_PATH" -mindepth 1 -maxdepth 1 -type d \
    -exec test -d "{}/epreuve" \; -print 2>/dev/null \
    | xargs -r ls -td 2>/dev/null | head -n 1 || true)"

  if [ -n "${CANDIDAT:-}" ]; then
    RUN_PATH="$CANDIDAT"
  fi
fi

test -d "$RUN_PATH" || { echo "Erreur: dossier introuvable: $RUN_PATH"; exit 1; }
test -d "$RUN_PATH/epreuve" || { echo "Erreur: '$RUN_PATH' ne ressemble pas à un run (epreuve/ manquant)."; exit 1; }

python -m agent_service.app.analyse.cli.main \
  --run "$RUN_PATH" \
  --out-md "rapport_diagnostics.md" \
  --out-json "diagnostics.json"
