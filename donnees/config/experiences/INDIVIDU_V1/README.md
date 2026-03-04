# INDIVIDU_V1

Expérience de travail pour réaliser l'individu transportable (agent en arène).

## Run (événements)

```bash
PYTHONPATH=services python -m ui_cli.app.main evenements --experience INDIVIDU_V1
```

Si tu veux surcharger:
```bash
PYTHONPATH=services python -m ui_cli.app.main evenements --experience INDIVIDU_V1 --mode entrainement --ticks 100 --publier-ticks
```

## Artefacts

- `artefacts/runs/<timestamp>_.../evenements.jsonl`
- `artefacts/runs/<timestamp>_.../stdout.txt` (si capture activée)
- `artefacts/runs/<timestamp>_.../meta.json`
