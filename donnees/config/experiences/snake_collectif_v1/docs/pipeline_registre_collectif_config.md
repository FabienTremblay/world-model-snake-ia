# configuration du pipeline (registre collectif)

Le but du pipeline est de pouvoir **rejouer la recette sans mémoriser des chemins**, et de rendre explicite *où sont les artefacts* et *quels observateurs sont activés*.

## 1) fichier de configuration

Un fichier `*.env` (format `KEY=VALUE`) permet de paramétrer le pipeline :

- `SNAKE_O1_PREFIX_BITS` : liste des valeurs testées pour `--prefix-bits` de l\x27observateur `o1`.
- `SNAKE_O1_REQUIRE_METRICS` : `1` => échec si `metrics.jsonl` manque (sinon `o1` est simplement sauté).
- `SNAKE_RUN_DIR` : (optionnel) fixe explicitement le `run-dir`.

Filtrage (optionnel, sur le nom du dossier run) :

- `SNAKE_RUN_INCLUDE_REGEX` : inclut seulement les runs dont le nom matche l'expression.
- `SNAKE_RUN_EXCLUDE_REGEX` : exclut les runs dont le nom matche l'expression.
- `SNAKE_RUN_MAX` : limite le nombre de runs (après tri décroissant).

Un exemple est fourni : `outils/pipeline_registre_collectif_v1.env`.

## 2) exécution

```bash
# auto: dernier run "complet" (journal+metrics) et config par défaut
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh

# avec config
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh \
  --config donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.env

# en fixant un run-dir (et une config)
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh \
  --config donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.env \
  --run-dir donnees/config/experiences/snake_collectif_v1/artefacts/runs/<run>

# afficher les runs détectés (complets / incomplets)
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh --list-runs

# traiter tous les runs complets sélectionnés et fusionner
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh --all-runs
```

## 3) philosophie

- Le pipeline **ne doit pas dépendre d\x27un run TUI incomplet** : il peut exister, mais il ne doit pas "casser" le flux.
- La présence d\x27un registre vide `registre_epistemique_v2.json` est acceptable (responsabilité SAI-A106), mais le pipeline le *rend explicite* via un warning.
- Les chemins de sortie sont centralisés sous `artefacts/registres/` pour être consommables par SAI-A107.
