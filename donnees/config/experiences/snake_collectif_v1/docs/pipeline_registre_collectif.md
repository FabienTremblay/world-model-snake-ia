# pipeline registre collectif (v1)

Ce pipeline assemble un **registre épistémique collectif** à partir du **dernier run** de l’expérience `snake_collectif_v1`.

## objectifs

- ne pas casser si l’étape SAI-A106 n’a pas encore produit `registre_epistemique_v2.json`
- permettre plusieurs granularités de détection de surprises (multi-échelles) via `--prefix-bits`
- consolider les propositions issues de plusieurs observateurs (o2 + o1 multi-prefix)

## exécution

Depuis la racine du dépôt :

```bash
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh
```

### choisir un run-dir

```bash
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh   --run-dir donnees/config/experiences/snake_collectif_v1/artefacts/runs/<run>
```

### ajuster les granularités o1

Par défaut: `12 16 20`

```bash
SNAKE_O1_PREFIX_BITS="10 12 14 16 18 20 22"   bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh
```

## sorties

- `.../artefacts/registres/o2_propositions.jsonl`
- `.../artefacts/registres/o1_surprises_prefix<BITS>.jsonl` (un fichier par granularité)
- `.../artefacts/registres/registre_epistemique_collectif.jsonl`

## notes sur la robustesse

Le script **ne dépend pas du répertoire courant** : il calcule la racine de l’expérience à partir de son propre emplacement.
