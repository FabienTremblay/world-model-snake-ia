# snake_collectif_v1 — outils d'analyse

## agrégation

Exécution depuis la racine du repo :

```bash
python donnees/config/experiences/snake_collectif_v1/outils/aggregate_snake_collectif_v1.py
```

Sorties :

- `donnees/config/experiences/snake_collectif_v1/artefacts/analyses/resume_par_run.csv`
- `donnees/config/experiences/snake_collectif_v1/artefacts/analyses/resume_global.csv`

## lecture des métriques actuelles

Tes journaux montrent :

- `episode_id` progresse (100 épisodes en train, 50 en eval)
- `tick` va jusqu’à 1000, mais `termine=false` et `raison_fin=null`

Donc, à ce stade, les épisodes finissent par **coupure max-ticks**, pas par collision/famine,
et les “raisons fin” ne sont pas disponibles.

Pour démontrer l’effectivité, la prochaine étape utile n’est pas d’agréger plus fin,
mais d’obtenir au moins une de ces deux choses :

1) un agent qui mange (score > 0)  
2) une terminaison “vraie” (termine=true avec raison_fin)

On peut y arriver sans ajouter de mécanique : en ajustant l'arène d'évaluation
(placement nourriture) ou en ajoutant un agent baseline (aleatoire) dans la campagne.
