# ui_cli — exécution headless (batch) pour génération de journaux

ce service fournit une entrée cli pour exécuter des épisodes snake sans interface (headless),
afin de générer des journaux compatibles avec le mode live (ui_tui) et les outils d’évaluation
du world model.

## nouveautés (cours 2)
- `--latent` permet de choisir la définition de l’état latent :
  - `checksum` : très discriminant (cours 1)
  - `discret_v1` : plus invariant au bruit (cours 2)

## usage

### curiosité tabulaire + latent discret (invariance au bruit)
```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 200 \
  --max-ticks 2000 \
  --agent curiosite_tabulaire \
  --latent discret_v1 \
  --epsilon 0.05 \
  --seed 123 \
  --truncate \
  --journal artefacts/episodes_latent_discret.jsonl \
  --metrics artefacts/exploration_metrics_latent_discret.jsonl
```

### évaluation (offline)
```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes_latent_discret.jsonl \
  --mode split \
  --ratio-train 0.7
```
