# observateurs collectifs (snake_collectif_v1)

Ce dossier documente les observateurs utilisés pour construire un registre épistémique collectif.

## composants

### o2_transformer_registre_epistemique_v2.py (O2)

- rôle : transformer `registre_epistemique_v2.json` (produit par SAI-A106) en propositions JSONL.
- robustesse : si le registre est manquant, le pipeline crée un registre vide (mais A106 reste responsable).

### o1_observateur_surprise_v1.py (O1)

- rôle : produire des propositions de type "surprise" à partir de `journal.jsonl` et `metrics.jsonl`.
- remarque : si l'état est trop stable (ou trop complet/déterministe), O1 peut produire 0 proposition.

### conventionneur_v1.py

- rôle : fusionner plusieurs flux de propositions JSONL en un registre collectif unique.

## pipeline recommandé

Voir `docs/pipeline_registre_collectif.md` et lancer :

```
bash donnees/config/experiences/snake_collectif_v1/outils/pipeline_registre_collectif_v1.sh
```

Le pipeline exécute O1 à **plusieurs granularités** (`prefix-bits`) afin de capter des surprises à différentes échelles.
