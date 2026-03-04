# Traçabilité des runs

## Principe

Un run est une observation expérimentale.

On veut pouvoir :

- reproduire
- auditer
- comparer
- expliquer une évolution

## Artefacts d'un run

Dans `artefacts/runs/<run>/` :

- `evenements.jsonl` : flux d'événements (source d'analyse)
- `meta.json` : configuration effective et métadonnées
- `individu_entree.yml` : snapshot de l'individu au début
- `individu_sortie.yml` : snapshot après évolution (entraînement seulement)
- `lineage.json` : parent → enfant (hashes) + run_id

## Règles

- les snapshots dans runs sont immuables (on ne les réécrit pas)
- le catalogue est mis à jour uniquement par promotion explicite
