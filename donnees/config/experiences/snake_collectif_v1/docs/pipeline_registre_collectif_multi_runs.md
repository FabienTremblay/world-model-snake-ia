# pipeline registre épistémique collectif — multi-runs

ce pipeline produit un **registre épistémique collectif** (jsonl) à partir :

- du registre épistémique v2 produit par **sai-a106** (même s’il est vide)
- d’observateurs (ex. o1 = surprises, o2 = transformation du registre v2)

## run complet

un **run complet** contient :

- `journal.jsonl`
- `metrics.jsonl`

si `registre_epistemique_v2.json` est absent, le pipeline crée un registre vide dans le run.

## exécution

### run le plus récent complet

```bash
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh
```

### run explicite

```bash
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh   --run-dir donnees/config/experiences/snake_collectif_v1/artefacts/runs/<run>
```

### tous les runs complets

```bash
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh --all-runs
```

### config `.env`

```bash
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh   --config donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.env
```

variables :

- `SNAKE_O1_PREFIX_BITS="12 16 20"` : liste d’entiers (un o1 par valeur)

## sorties

- final :
  - `artefacts/registres/registre_epistemique_collectif.jsonl`
- par run :
  - `artefacts/registres/runs/<run_basename>/o2_propositions.jsonl`
  - `artefacts/registres/runs/<run_basename>/o1_surprises_prefixXX.jsonl`

## pourquoi par run ?

pour éviter d’écraser les sorties quand tu changes de run, et pour garder la traçabilité des diagnostics.
