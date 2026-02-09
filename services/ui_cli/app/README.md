# ui_cli — exécution headless (batch) ancrée sur une expérience

`ui_cli` exécute des épisodes *Snake* **sans interface graphique** (mode headless) et produit des journaux `.jsonl` compatibles avec l'écosystème (*recoders*, diagnostics, APK, agents de planification, etc.).

## règle de discipline

- `ui_cli` **n'écrit plus jamais dans `./artefacts`** à la racine du projet.
- `--experience <id>` est **obligatoire**.
- les sorties vont sous :
  - `donnees/config/experiences/<id>/artefacts/runs/<run>/...`

Cette discipline garantit : reproductibilité, traçabilité, et enchaînement outillé sans chemins “à la main”.

---

## bac-à-sable d'expérience

Une expérience est décrite par :

```
donnees/config/experiences/<id>/experience.yml
```

Quand `--experience <id>` est fourni, `ui_cli` :
- crée/détecte la structure du bac-à-sable
- applique des *defaults* depuis `experience.yml` (si l'utilisateur n'a pas surchargé sur la CLI)
- prépare un répertoire de run horodaté sous `artefacts/runs/`

---

## commandes

### exécution minimale (pilotée par `experience.yml`)

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --episodes 200
```

### surcharge ponctuelle depuis la CLI

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --agent planif_mpc_observateur_tabulaire \
  --episodes 50
```

Règle : **CLI > experience.yml > valeurs par défaut**.

---

## métriques

Par défaut, si `--metrics` n'est pas fourni, `ui_cli` écrit :

- `artefacts/runs/<run>/metrics.jsonl`

Si l'agent expose `get_sorties_tetes()`, le champ `sorties_tetes` est ajouté aux lignes de métriques.

---

## agent_personne (A107/A108)

### exécuter un agent-personne par id

L'agent-personne est un artefact produit par le pipeline de préparation (A107) :

```
donnees/config/experiences/<exp>/artefacts/agent_personne/<agent_personne_id>/agent_personne.json
```

Exécution :

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --arene cours4_tiny_planification \
  --agent agent_personne \
  --agent-personne-id ap_cours4_v1 \
  --episodes 5 --max-ticks 2000 --seed 123
```

### exécuter un agent-personne par chemin

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --arene cours4_tiny_planification \
  --agent agent_personne \
  --agent-personne-path artefacts/agent_personne/ap_cours4_v1/agent_personne.json \
  --episodes 5 --max-ticks 2000 --seed 123
```

Note : les chemins relatifs sont résolus **dans le bac-à-sable** (pas dans `./`).

---

## variables d'environnement (modèle du monde)

Si `experience.yml` contient une section `modele_monde`, `ui_cli` exporte automatiquement :

- `SNAKE_MODELE_JOURNAL`
- `SNAKE_CHAMP_LATENT`
- `SNAKE_MODE_LATENT_CLI`

Ces variables sont consommées par les recoders/diagnostics/agents sans duplication.
