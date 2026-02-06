# epistemique_v2 (cours 5)

Version 2 de l'agent épistémique (point de vue **estrade**).

## Objectif
- Lire le journal factuel (`episodes.jsonl`)
- Calculer des indices (support, distribution actions, raisons de fin, etc.)
- Inférer des hypothèses simples
- Écrire un registre versionné `registre_epistemique_v2.json`

## Exécution
```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli --latent checksum
```

## Frontières
- ne décide pas d'actions
- ne contrôle pas le monde
- consomme uniquement des artefacts (journal, diagnostics éventuels)
