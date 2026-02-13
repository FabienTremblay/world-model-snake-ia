# epistemique_v2 — observateur estrade (bac-à-sable)

Version 2 de l'observateur **épistémique** (point de vue estrade).

## Principe
L'épistémique v2 ne reçoit pas une forêt de paramètres : il lit `experience.yml` et se branche sur
les artefacts d'un **run** :

- `journal.jsonl` (obligatoire) : faits (actions, fins, capteurs caméra)
- `metrics.jsonl` (optionnel) : transitions instrumentées (ex: checksum avant/après)

Sortie : `registre_epistemique_v2.json` dans le répertoire du run.

## Exécution
```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli --experience <id_experience>
```

### Cibler un run précis
`--run-id` correspond au **nom de répertoire** sous `donnees/config/experiences/<id>/artefacts/runs/`.

```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli \
  --experience <id_experience> \
  --run-id 2026-02-12_17h08_087842
```

### Surcharger ponctuellement le latent (si utile)
```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli \
  --experience <id_experience> \
  --latent checksum
```

## Contenu du registre (résumé)
- `indices` : agrégats sur le run (raisons de fin, distribution d'actions, etc.)
- `hypotheses` : hypothèses "diagnostic" (biais, stationnaire, revisite, etc.)
- `concepts_candidates` : concepts candidats *instillables* (ex: actions nulles, transitions dominantes)
