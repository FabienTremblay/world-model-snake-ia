# Outils — observateurs collectifs (snake_collectif_v1)

Ces outils vivent **dans l'expérience** (pas dans les scripts du repo) pour éviter
la pollution de la racine.

## 1) O1 — Surprise de transition

Exécuter sur tous les runs d'une expérience:

```bash
python donnees/config/experiences/snake_collectif_v1/outils/o1_observateur_surprise_v1.py \
  --runs-root donnees/config/experiences/snake_collectif_v1/artefacts/runs \
  --sortie donnees/config/experiences/snake_collectif_v1/artefacts/registres/observateur_o1_surprise_v1.jsonl
```

## 2) O2 — Transformer registre epistemique_v2 en propositions

```bash
python donnees/config/experiences/snake_collectif_v1/outils/o2_transformer_registre_epistemique_v2.py \
  --registre donnees/config/experiences/snake_collectif_v1/artefacts/runs/<run_id>/registre_epistemique_v2.json \
  --sortie donnees/config/experiences/snake_collectif_v1/artefacts/registres/observateur_o2_epistemique_v2.jsonl
```

## 3) Conventionneur

```bash
python donnees/config/experiences/snake_collectif_v1/outils/conventionneur_v1.py \
  --entrees \
    donnees/config/experiences/snake_collectif_v1/artefacts/registres/observateur_o1_surprise_v1.jsonl \
    donnees/config/experiences/snake_collectif_v1/artefacts/registres/observateur_o2_epistemique_v2.jsonl \
  --sortie donnees/config/experiences/snake_collectif_v1/artefacts/registres/registre_epistemique_collectif.jsonl
```

## Notes
- Le conventionneur v1 reste volontairement simple (dédoublonnage exact).
- On pourra raffiner vers une "convention" (canonisation d'IDs, regroupements, conflits).
