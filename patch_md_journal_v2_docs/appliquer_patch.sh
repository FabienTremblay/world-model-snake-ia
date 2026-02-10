#!/usr/bin/env bash
set -euo pipefail

racine="$(pwd)"
if [ ! -d "${racine}/services" ]; then
  echo "ERREUR: exécute ce script depuis la racine du repo (dossier ./services introuvable)." >&2
  exit 1
fi

patch_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

copier_fichier(){
  local src="$1"
  local dst="${racine}/${src}"
  mkdir -p "$(dirname "$dst")"
  cp -f "${patch_dir}/${src}" "$dst"
  echo "Patch appliqué: ${src}"
}

fichiers=(
  "CHANGELOG.md"
  "docs/runner.md"
  "donnees/config/experiences/_template/README.md"
  "donnees/config/experiences/cours5/README.md"
  "donnees/config/experiences/preparation_cours_5/README.md"
  "docs/world_models/cours/cours4_bilan_et_plan.md"
  "services/agent_service/app/modele_monde/instructions.md"
)

for f in "${fichiers[@]}"; do
  if [ ! -f "${patch_dir}/${f}" ]; then
    echo "ERREUR: fichier manquant dans le patch: ${f}" >&2
    exit 1
  fi
  copier_fichier "$f"
done

echo "OK"
