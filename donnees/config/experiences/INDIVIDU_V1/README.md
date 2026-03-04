# INDIVIDU_V1

Expérience démontrant :

- individu transportable
- évolution contrôlée (uniquement en entraînement)
- traçabilité scientifique des runs (snapshots + lineage)
- promotion contrôlée vers le catalogue (opt-in)

## Lancer

```bash
PYTHONPATH=services python -m ui_cli.app.main evenements --experience INDIVIDU_V1
```

## Modes

Deux modes sont possibles.

### entrainement

L'individu peut évoluer après le run (production d'un `individu_sortie.yml`).

Artefacts produits dans `artefacts/runs/<run>/` :

- `evenements.jsonl`
- `meta.json`
- `individu_entree.yml` (snapshot exact au début)
- `individu_sortie.yml` (snapshot exact après évolution)
- `lineage.json` (parent -> enfant via hash)

### epreuve

Mode reproductible :

- aucune évolution d'individu
- pas d'`individu_sortie.yml`
- `lineage.json` indique l'absence d'enfant

## Promotion catalogue

En entraînement, on peut choisir de promouvoir l'état de sortie vers le catalogue :

```bash
PYTHONPATH=services python -m ui_cli.app.main evenements --experience INDIVIDU_V1 --promouvoir
```

Effets :

- mise à jour de l'état courant :
  - `donnees/catalogues/individus/<individu_id>/individu.yml`
- archivage immuable :
  - `donnees/catalogues/individus/<individu_id>/historique/<hash>.yml`

## Objectif scientifique

Chaque run est une observation expérimentale :

- les snapshots (`individu_entree.yml`, `individu_sortie.yml`) rendent l'évolution traçable
- `lineage.json` relie formellement parent -> enfant
- le catalogue ne bouge que sur décision explicite (promotion)
