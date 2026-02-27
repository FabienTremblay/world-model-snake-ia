#!/usr/bin/env bash
set -euo pipefail

# Ménage prudent : supprime surtout les artefacts lourds et temporaires.
# Usage:
#   bash outils/menage_jepa5.sh           # dry-run (affiche)
#   bash outils/menage_jepa5.sh --apply   # applique

if ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  echo "[ERREUR] pas dans un repo git (ou git indisponible)."
  echo "         lance depuis l'intérieur du repo (ou installe git)."
  exit 1
fi
APPLY=0
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
fi

echo "[MENAGE] root=$ROOT apply=$APPLY"

# 1) artefacts/runs (gros) : on garde les 3 derniers runs par expérience JEPA-3/4/5
#    Ajuste N si tu veux.
GARDER_N=3

nettoyer_runs() {
  local exp="$1"
  local runs_dir="$ROOT/donnees/config/experiences/$exp/artefacts/runs"
  if [[ ! -d "$runs_dir" ]]; then
    echo "[MENAGE] $exp: pas de runs_dir"
    return
  fi

  echo "[MENAGE] $exp: nettoyage runs (garder $GARDER_N derniers)"
  mapfile -t runs < <(ls -1 "$runs_dir" | sort)
  local total="${#runs[@]}"
  if (( total <= GARDER_N )); then
    echo "  rien à supprimer ($total <= $GARDER_N)"
    return
  fi

  local a_supprimer_count=$(( total - GARDER_N ))
  for ((i=0; i<a_supprimer_count; i++)); do
    local d="$runs_dir/${runs[$i]}"
    echo "  supprimer: $d"
    if (( APPLY == 1 )); then
      rm -rf "$d"
    fi
  done
}

for exp in JEPA-3 JEPA-4 JEPA-5; do
  nettoyer_runs "$exp"
done

# 2) stdout.log accumulés (si tu en as ailleurs)
# (rien de destructif ici, juste un exemple)
echo "[MENAGE] fichiers *.log (dry listing) sous donnees/config/experiences/JEPA-* :"
find "$ROOT/donnees/config/experiences" -maxdepth 4 -type f -name "*.log" | sed 's/^/  /'

echo "[MENAGE] terminé. relance avec --apply pour supprimer réellement."
