#!/usr/bin/env bash
set -euo pipefail
# À lancer à la racine du repo ia-snake
mkdir -p services/world_sim/app
cp -f monde_snake.py services/world_sim/app/monde_snake.py
echo "Patch appliqué: services/world_sim/app/monde_snake.py"
