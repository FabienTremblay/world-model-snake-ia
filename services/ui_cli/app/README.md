# ui_cli — exécution headless (batch) pour génération de journaux

ce service fournit une entrée cli pour exécuter des épisodes snake sans interface (headless),
afin de générer des journaux compatibles avec le mode live (ui_tui) et les outils d’évaluation
du world model.

## nouveautés (cours 2)
- `--latent` permet de choisir la définition de l’état latent :
  - `checksum` : très discriminant (cours 1)
  - `discret_v1` : plus invariant au bruit (cours 2)

## usage

### curiosité tabulaire + latent discret (invariance au bruit)
```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 200 \
  --max-ticks 2000 \
  --agent curiosite_tabulaire \
  --latent discret_v1 \
  --epsilon 0.05 \
  --seed 123 \
  --truncate \
  --journal artefacts/episodes_latent_discret.jsonl \
  --metrics artefacts/exploration_metrics_latent_discret.jsonl
```

### évaluation (offline)
```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes_latent_discret.jsonl \
  --mode split \
  --ratio-train 0.7
```

# ui_cli — exécution headless et bacs-à-sable d’expérience

`ui_cli` fournit une interface en ligne de commande pour exécuter des épisodes *Snake* **sans interface graphique** (mode headless), afin de :

- générer des journaux d’épisodes (`.jsonl`)
- alimenter les recoders, diagnostics et APK
- soutenir l’apprentissage et l’évaluation des *world models*

À partir du **cours 4**, `ui_cli` introduit la notion de **bac-à-sable d’expérience**, qui devient la manière recommandée d’orchestrer les exécutions.

---

## idée clé : le bac-à-sable d’expérience

Un **bac-à-sable** est un dossier d’expérience auto-contenu, décrit par un fichier :

```
donnees/config/experiences/<id>/experience.yml
```

Il définit :
- le contexte expérimental (arène, agent, latent, paramètres)
- les jeux de données d’entrée (journaux existants)
- les sorties standardisées (runs, datasets, diagnostics, registres)

Lorsque `--experience <id>` est fourni :
- `ui_cli` **crée ou détecte** la structure du bac-à-sable
- les chemins relatifs sont résolus par rapport à l’expérience
- les sorties sont automatiquement organisées sous `artefacts/`

👉 le bac-à-sable devient la **source de vérité** pour :
- la reproductibilité
- la traçabilité
- l’enchaînement des outils (recoders, diagnostics, APK)

---

## structure d’un bac-à-sable

```
donnees/config/experiences/cours4/
├── experience.yml
├── README.md
└── artefacts/
    ├── runs/          # exécutions ui_cli (journaux + métriques)
    ├── datasets/      # journaux recodés
    ├── diagnostics/   # rapports d’analyse
    ├── registres/     # registres épistémiques (APK)
    └── notes/
```

---

## usage recommandé (avec bac-à-sable)

### exécution minimale pilotée par `experience.yml`

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --episodes 200
```

- l’arène, l’agent, le latent et la seed peuvent être définis dans `experience.yml`
- un nouveau *run* est créé sous `artefacts/runs/<timestamp>/`
- le journal d’épisodes est automatiquement nommé et placé

### surcharge ponctuelle depuis la ligne de commande

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --agent planif_mpc_observateur_tabulaire \
  --episodes 50
```

Règle :
- **CLI > experience.yml > valeurs par défaut**
- seules les options explicitement passées sur la CLI remplacent l’expérience

---

## variables d’environnement résolues automatiquement

Si `experience.yml` contient une section `modele_monde`, `ui_cli` exporte :

- `SNAKE_MODELE_JOURNAL`
- `SNAKE_CHAMP_LATENT`
- `SNAKE_MODE_LATENT_CLI`

Ces variables sont utilisées **sans duplication** par :
- recoders
- diagnostics
- agents de planification
- APK épistémiques

---

## usage historique (sans bac-à-sable)

L’usage direct reste supporté, notamment pour les cours initiaux.

### curiosité tabulaire + latent discret

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 200 \
  --max-ticks 2000 \
  --agent curiosite_tabulaire \
  --latent discret_v1 \
  --epsilon 0.05 \
  --seed 123 \
  --truncate \
  --journal artefacts/episodes_latent_discret.jsonl \
  --metrics artefacts/exploration_metrics_latent_discret.jsonl
```

⚠️ dans ce mode :
- l’utilisateur est responsable de l’organisation des fichiers
- les outils aval (recoders, diagnostics) doivent être configurés à la main

---

## philosophie

- le bac-à-sable **n’est pas un framework**
- c’est un *contrat léger* entre les outils
- il permet de raisonner en **expériences**, pas en fichiers isolés

À mesure que les cours avancent, il devient le support naturel pour :
- comparer des hypothèses
- versionner des datasets
- accumuler des connaissances épistémiques
