# Structure du projet

Note : les dossiers suivent la convention **snake_case** (ex. `world_sim`).

Les règles et paramètres de jeu sont externalisés sous forme de données,
afin de garantir la reproductibilité et la traçabilité des épisodes.

- `services/world_sim/` : simulateur du monde
- `services/agent_service/` : agent (b(θ), politique)
- `services/commun/` : contrats, bus, contrôle (partagé)
- `services/runner/` : orchestrateur d'épisodes
- `services/ui_tui/` : ui texte (TUI)
- `services/ui_web/` : ui web (plus tard)
- `infra/` : docker compose et config infra (plus tard)

- `donnees/config/` : définitions de configuration (YAML)
  - arènes (grille, objets, portes, règles latentes, récompenses)

- `artefacts/` : sorties de runs, épisodes, replays, métriques et journaux d’observation
- `tmp/` : fichiers temporaires
