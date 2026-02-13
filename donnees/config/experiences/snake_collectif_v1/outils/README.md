# Outils — observateurs collectifs (snake_collectif_v1)

Ce répertoire contient des outils *spécifiques à l'expérience* (pas au repo).

## Pipeline minimal

1) Produire / mettre à jour le registre épistémique v2 (observateur estrade existant)

```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli \
  --experience snake_collectif_v1 \
  --run-id <RUN_ID>
```

2) Observateur O1 (surprise) — sur metrics.jsonl

```bash
python donnees/config/experiences/snake_collectif_v1/outils/o1_observateur_surprise_v1.py \
  --experience-dir donnees/config/experiences/snake_collectif_v1 \
  --run-id <RUN_ID>
```

3) Observateur O2 (transformer) — sur registre_epistemique_v2.json

```bash
python donnees/config/experiences/snake_collectif_v1/outils/o2_transformer_registre_epistemique_v2.py \
  --experience-dir donnees/config/experiences/snake_collectif_v1 \
  --run-id <RUN_ID>
```

4) Conventionneur — fusion + canonisation

```bash
python donnees/config/experiences/snake_collectif_v1/outils/conventionneur_v1.py \
  --experience-dir donnees/config/experiences/snake_collectif_v1 \
  --inputs \
    donnees/config/experiences/snake_collectif_v1/artefacts/registres/observateur_o1_surprise_v1__<RUN_ID>.jsonl \
    donnees/config/experiences/snake_collectif_v1/artefacts/registres/observateur_o2_from_epistemique_v2__<RUN_ID>.jsonl
```

Sortie:
- `donnees/config/experiences/snake_collectif_v1/artefacts/registres/registre_epistemique_collectif_v1__<RUN_ID>.jsonl`

## Notes
- O1 et O2 émettent des propositions structurées (type, cible, hypothese, support, confiance).
- le conventionneur fusionne et assigne un `concept_id` stable.
