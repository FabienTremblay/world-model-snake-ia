#!/usr/bin/env bash
set -euo pipefail

# JEPA-1 — SAI-A107 (Entrainer) — prototype offline
# Exécute l'entraînement de l'hypothèse prédictive sur dataset de paires capteurs.

cd "$(dirname "$0")/.."

python outils/entrainer_v2.py --config entrainement/config_entrainement.json --mode entrainement
