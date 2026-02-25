# JEPA-2

Deuxième expérimentation JEPA.

Objectif : isoler les prochaines évolutions tout en réutilisant le pipeline canonique via `ui_cli pipeline`.

## Commandes

```bash
PYTHONPATH=services python -m ui_cli.app.main pipeline run --experience JEPA-2 --phase all --seed 0
PYTHONPATH=services python -m ui_cli.app.main pipeline list-runs --experience JEPA-2
PYTHONPATH=services python -m ui_cli.app.main pipeline describe-run --experience JEPA-2 --run-id <run_id>
```
