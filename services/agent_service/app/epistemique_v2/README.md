# epistemique_v2 (cours 5)

Version 2 de l'agent épistémique (point de vue **estrade**).

## Principe (bac-à-sable)
L'épistémique v2 ne reçoit pas une forêt de paramètres : il lit **experience.yml** et se branche sur
les artefacts d'un **run** (journal, meta, metrics).

## Exécution
```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli --experience preparation_cours_5
```

### Cibler un run précis
`--run-id` correspond au **nom de répertoire** sous `artefacts/runs/` (ex: `2026-02-05_13h21`).

```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli       --experience preparation_cours_5       --run-id 2026-02-05_13h21
```

### Surcharger ponctuellement le latent
```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli       --experience preparation_cours_5       --latent discret_v1
```

## Frontières
- ne décide pas d'actions
- ne contrôle pas le monde
- consomme uniquement des artefacts (journal, meta, metrics)
