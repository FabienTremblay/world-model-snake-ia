#!/usr/bin/env bash
set -euo pipefail

# --- paramètres ---
PROJET="."
RACINE="$(pwd)/$PROJET"

# --- création des dossiers ---
mkdir -p "$RACINE"/{docs,scripts,services,infra,artefacts,tmp}

# services (minimum v1)
mkdir -p "$RACINE/services/world-sim"/{app,tests}
mkdir -p "$RACINE/services/agent-service"/{app,tests}
mkdir -p "$RACINE/services/runner"/{app,tests}
mkdir -p "$RACINE/services/ui"/{app,tests}

# infra (vide pour l’instant, on mettra le compose plus tard)
mkdir -p "$RACINE/infra/compose"
mkdir -p "$RACINE/infra/env"

# --- fichiers racine ---
cat > "$RACINE/README.md" <<'MD'
# snake-world-model

Architecture minimale (v1) : simulateur (`world-sim`), agent (`agent-service`), orchestrateur (`runner`), ui (`ui`).

Objectif : permettre un mode entraînement (exploration) et un mode compétition (exploitation), en respectant la séparation "monde réel" vs "monde interne agent".

> Le docker-compose viendra plus tard dans `infra/compose/`.
MD

cat > "$RACINE/.gitignore" <<'TXT'
# python
__pycache__/
*.pyc
.venv/
.venv*/
.pytest_cache/
.mypy_cache/

# node / ui
node_modules/
dist/
.next/
out/

# artefacts & runs
artefacts/
tmp/
*.log
*.sqlite
.DS_Store
TXT

cat > "$RACINE/.editorconfig" <<'TXT'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4
TXT

# --- docs ---
cat > "$RACINE/docs/architecture.md" <<'MD'
# Architecture (v1)

## Services
- **world-sim** : monde réel (état, règles θ), expose reset/step et renvoie des observations sous forme d'attributs.
- **agent-service** : monde interne, maintient b(θ) et choisit des actions.
- **runner** : boucle d'épisodes, collecte traces, métriques, artefacts.
- **ui** : visualisation/debug (optionnel en v1, mais on garde le slot).

## Principes
- l’observation ne doit jamais contenir d’étiquette sémantique (ex. "warp"), seulement des attributs.
- θ est stable durant un épisode (peut changer entre épisodes).
MD

# --- scripts ---
cat > "$RACINE/scripts/dev.sh" <<'BASH'
#!/usr/bin/env bash
set -euo pipefail
echo "Scripts dev (placeholder)."
echo "À venir: commandes pour lancer runner/world-sim localement."
BASH
chmod +x "$RACINE/scripts/dev.sh"

# --- squelettes minimalistes par service ---
creer_service_python_minimal () {
  local service="$1"
  local dir="$RACINE/services/$service"

  cat > "$dir/pyproject.toml" <<'TOML'
[project]
name = "SERVICE_NAME"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
TOML
  # remplacer SERVICE_NAME
  sed -i "s/SERVICE_NAME/$service/g" "$dir/pyproject.toml"

  cat > "$dir/app/__init__.py" <<'PY'
PY

  cat > "$dir/app/main.py" <<'PY'
def main() -> None:
    print("Service démarré (placeholder).")

if __name__ == "__main__":
    main()
PY

  cat > "$dir/tests/test_smoke.py" <<'PY'
def test_smoke() -> None:
    assert True
PY

  cat > "$dir/README.md" <<MD
# $service

Service **$service** (squelette v1).
MD
}

creer_service_python_minimal "world-sim"
creer_service_python_minimal "agent-service"
creer_service_python_minimal "runner"

# ui: juste un squelette texte (on décidera plus tard: Next.js, Vite, etc.)
cat > "$RACINE/services/ui/README.md" <<'MD'
# ui

Slot UI (v1). On décidera plus tard si c'est:
- Next.js
- Vite + React
- autre

Pour l’instant, structure vide.
MD

# --- infra env placeholders ---
cat > "$RACINE/infra/env/.env.exemple" <<'ENV'
# exemple (à compléter)
SNAKE_MODE=train
SNAKE_SEED=12345
ENV

# --- note de structure ---
cat > "$RACINE/docs/structure.md" <<'MD'
# Structure du projet

- `services/world-sim/` : simulateur du monde
- `services/agent-service/` : agent (b(θ), politique)
- `services/runner/` : orchestrateur d'épisodes
- `services/ui/` : ui (plus tard)
- `infra/` : docker compose et config infra (plus tard)
- `artefacts/` : sorties de runs, modèles, replays
- `tmp/` : fichiers temporaires
MD

echo "OK: structure créée dans: $RACINE"
echo "Prochaines étapes (quand tu voudras):"
echo "  - définir les contrats HTTP (reset/step/observe) entre runner et world-sim"
echo "  - ajouter un docker-compose minimal dans infra/compose/"
