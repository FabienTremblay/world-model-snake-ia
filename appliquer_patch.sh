#!/usr/bin/env bash
set -euo pipefail

# applique les fichiers du patch dans le repo courant.
# attendu: lancé depuis la racine du repo (là où existe ./services)

racine="$(pwd)"
if [ ! -d "${racine}/services" ]; then
  echo "ERREUR: exécute ce script depuis la racine du repo (dossier ./services introuvable)." >&2
  exit 1
fi

patch_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

copier_fichier() {
  local src="$1"
  local dst="${racine}/${src}"
  mkdir -p "$(dirname "$dst")"
  cp -f "${patch_dir}/${src}" "$dst"
  echo "Patch appliqué: ${src}"
}

# liste explicite (évite de copier des fichiers accidentels)
fichiers=(
  "services/instrument/tests/__init__.py"
  "services/instrument/tests/conftest.py"
  "services/instrument/tests/test_core_instruments_v1.py"
  "services/instrument/tests/test_camera_estrade_absolue_v1.py"
  "services/instrument/app/__init__.py"
  "services/instrument/app/contrats.py"
  "services/instrument/app/instruments/__init__.py"
  "services/instrument/app/instruments/camera_estrade_absolue_v1.py"
)

for f in "${fichiers[@]}"; do
  if [ ! -f "${patch_dir}/${f}" ]; then
    echo "ERREUR: fichier manquant dans le patch: ${f}" >&2
    exit 1
  fi
  copier_fichier "$f"
done

echo "OK"
