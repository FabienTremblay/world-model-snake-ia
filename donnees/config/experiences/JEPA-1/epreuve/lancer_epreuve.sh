#!/usr/bin/env bash
set -euo pipefail

# JEPA-1 — SAI-A108 (Éprouver) — prototype offline
# Évalue l'agent préparé (policy minimale dérivée du gate) et produit journaux/résultats.

cd "$(dirname "$0")/.."

python outils/entrainer_v2.py --config epreuve/config_epreuve.json --mode epreuve
