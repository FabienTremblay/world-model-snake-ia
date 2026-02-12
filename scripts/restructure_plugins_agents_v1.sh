#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

agents_dir="services/agent_service/app/agents"
incarnations_dir="services/agent_service/app/incarnations"

mkdir -p "$agents_dir" "$incarnations_dir"

# Déplace un fichier en utilisant git mv si le fichier est suivi, sinon mv.
deplacer () {
  local src="$1"
  local dst="$2"

  [ -f "$src" ] || return 0

  mkdir -p "$(dirname "$dst")"

  if git ls-files --error-unmatch "$src" >/dev/null 2>&1; then
    git mv "$src" "$dst"
  else
    mv "$src" "$dst"
  fi
}

# Déplace agent_*.yml -> <agent>/agent.yml
deplacer_yaml_agent () {
  local src="$1"
  local agent_dir="$2"
  deplacer "$src" "$agent_dir/agent.yml"
}

# agents "classiques"
deplacer_yaml_agent "$agents_dir/agent_aleatoire.yml" "$agents_dir/aleatoire"
deplacer_yaml_agent "$agents_dir/agent_curiosite_tabulaire.yml" "$agents_dir/curiosite_tabulaire"
deplacer_yaml_agent "$agents_dir/agent_planif_mpc_tabulaire.yml" "$agents_dir/planif_mpc_tabulaire"
deplacer_yaml_agent "$agents_dir/agent_planif_mpc_observateur_tabulaire.yml" "$agents_dir/planif_mpc_observateur_tabulaire"
deplacer_yaml_agent "$agents_dir/agent_planif_1pas_temperament_v1.yml" "$agents_dir/planif_1pas_temperament"

# agent_personne devient une "incarnation"
if [ -f "$agents_dir/agent_personne.yml" ]; then
  mkdir -p "$incarnations_dir/agent_personne"
  deplacer "$agents_dir/agent_personne.yml" "$incarnations_dir/agent_personne/agent.yml"
fi

# fabrique(s) d'infra (si présent)
if [ -f "$agents_dir/fabriques_catalogue_v1.py" ]; then
  mkdir -p "$agents_dir/_infra"
  deplacer "$agents_dir/fabriques_catalogue_v1.py" "$agents_dir/_infra/fabriques_catalogue_v1.py"
fi

echo "ok: restructuration faite. vérifie avec: git status"

