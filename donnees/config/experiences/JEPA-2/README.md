# JEPA-2

Objectif : isoler les prochaines évolutions JEPA sans copier d'outils entre expériences.

Exécution canonique (racine du repo) :

```bash
PYTHONPATH=services python -m ui_cli.app.main pipeline run --experience JEPA-2 --phase all
```

Notes :
- Les artefacts sont produits sous `artefacts/runs/<horodatage>_<tag>/...`.
- Les pointeurs stabilisés (datasets/poids/agents/journaux) restent sous `artefacts/` de l'expérience.
