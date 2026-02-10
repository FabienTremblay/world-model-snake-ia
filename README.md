# Projet SnakeAI - Explication Détaillée

## Vue d'ensemble

Ce projet est un **environnement d'entraînement et d'évaluation d'agents intelligents** (IA) basé sur le jeu classique Snake. Il s'agit d'un système modulaire conçu pour permettre l'apprentissage, l'expérimentation et la compétition d'agents autonomes dans un environnement contrôlé.

### Concept fondamental

Le projet repose sur une distinction claire entre :
- **Le monde réel** : la simulation du jeu Snake avec ses règles physiques
- **Le monde interne de l'agent** : le modèle mental que l'agent se construit du monde

## Architecture du Système

Le projet est organisé en **microservices** indépendants qui communiquent entre eux :

### 1. **world_sim** - Simulateur du monde
Le simulateur du jeu Snake qui gère :
- La grille de jeu (30x12 par défaut)
- Le serpent (position, direction, croissance)
- La nourriture
- Les collisions et règles du jeu
- Les arènes (environnements configurables)
- Les portes et obstacles spéciaux
- Le bruit sur les observations (pour ajouter de l'incertitude)

**Fichier principal** : `monde_snake.py`

### 2. **agent_service** - Service des agents IA
Contient les différents types d'agents et leur logique de décision :

#### Types d'agents disponibles :
- `agent_aleatoire` : prend des décisions aléatoires
- `agent_curiosite_tabulaire` : explore en favorisant les états peu visités
- `agent_planif_mpc_tabulaire` : planifie ses actions avec Model Predictive Control
- `agent_planif_mpc_observateur_tabulaire` : planification avec observateur d'état
- `agent_planif_1pas_temperament_v1` : planification à 1 pas avec personnalité

#### Composants clés :
- **Modèle monde** : l'agent construit un modèle interne du monde
  - Tabulaire (états discrets)
  - Encodeur contrastif (représentation latente)
  - Simulateur interne pour prédire les conséquences des actions
  
- **Système épistémique** : gestion des connaissances
  - Registre épistémique : ce que l'agent "sait"
  - Agent producteur de connaissances (APK)
  - Diagnostics de la qualité des connaissances

### 3. **instrument** - Capteurs et perception
Simule les capteurs de l'agent (ses "yeux") :
- `camera_egocentree_v1` : vision centrée sur l'agent
- `camera_estrade_absolue_v1` : vue d'ensemble
- `gps_v1` : position absolue
- `projection_capteurs` : transforme l'état du monde en observations
- Ajout de bruit pour simuler l'incertitude

### 4. **runner** - Orchestrateur
Coordonne l'exécution des parties :
- Initialise le monde et l'agent
- Gère la boucle de jeu (tick par tick)
- Enregistre les journaux d'épisodes
- Supporte le mode replay
- Génère les métriques de performance

### 5. **ui_tui** - Interface utilisateur textuelle
Interface terminal pour visualiser le jeu en temps réel :
- Affichage ASCII du jeu
- Mode live (partie en cours)
- Mode replay (rejouer des parties enregistrées)
- Visualisation des capteurs de l'agent
- Statistiques en temps réel

### 6. **ui_cli** - Interface ligne de commande
Outils pour l'expérimentation :
- Préparer des agents
- Lancer des sessions d'entraînement
- Gérer les expériences (bac à sable)

## Flux de Travail Principal

### Phase 1 : Entraînement (SAI-A100)

```
1. SAI-A102 : Générer des épisodes
   - L'agent joue dans l'arène
   - Chaque action, observation et résultat est enregistré
   - Création d'un "journal d'épisodes"

2. SAI-A104 : Inférer des connaissances
   - Analyse du journal d'épisodes
   - L'agent construit son modèle du monde
   - Apprentissage des règles (transitions, récompenses)

3. SAI-A106 : Produire des hypothèses
   - Création d'un "registre épistémique"
   - L'agent formule des croyances sur le monde
   - Identification des dangers et opportunités

4. SAI-A108 : Éprouver l'agent
   - Tests de performance
   - Diagnostics de la qualité du modèle
   - Validation avant compétition
```

### Phase 2 : Compétition (SAI-B)
Une fois entraîné, l'agent peut participer à des compétitions où il exploite ses connaissances.

## Concepts Clés

### 1. Arènes (`donnees/config/arenes/`)
Fichiers YAML qui définissent les environnements :
- Taille de la grille
- Position des obstacles
- Règles spéciales (portes, conditions de victoire)
- Nombre de nourritures
- Exemples : `tiny_v0.yml`, `cours4_tiny_planification.yml`

### 2. Expériences (`donnees/config/experiences/`)
Dossiers organisés pour chaque session d'expérimentation :
- `experience.yml` : configuration
- `artefacts/` : résultats
  - `runs/` : journaux horodatés
  - `datasets/` : données d'entraînement
  - `diagnostics/` : analyses
  - `registres/` : connaissances accumulées

### 3. Journal d'épisodes
Fichier JSONL contenant pour chaque pas de temps :
- État du monde
- Observation de l'agent
- Action choisie
- Récompense reçue
- État suivant

### 4. Modèle Monde
Représentation interne que l'agent se construit :
- **Tabulaire** : table de transitions état-action-état'
- **Latent** : espace de représentation compressé
- Permet la planification et la prédiction

### 5. Signaux
Le système utilise différents types de signaux :
- `signaux_percus_v1` : ce que l'agent observe
- `signaux_transition_v1` : changements d'état
- `signaux_monde_v1` : état réel du monde
- Encodage par hash pour compresser l'espace d'états

## Objectifs Pédagogiques

Ce projet illustre des concepts avancés en IA :

1. **Model-based Reinforcement Learning** : l'agent apprend un modèle du monde
2. **Exploration vs Exploitation** : balance entre découvrir et utiliser
3. **Planification** : anticiper les conséquences avant d'agir
4. **Incertitude** : gérer l'observation partielle et bruitée
5. **Méta-cognition** : l'agent raisonne sur ses propres connaissances
6. **Architecture cognitive** : séparation perception / décision / action

## Utilisation Typique

### Entraîner un nouvel agent :
```bash
# 1. Générer des épisodes d'exploration
./scripts/dev.sh --arene tiny_v0 --agent agent_curiosite_tabulaire

# 2. Analyser et apprendre
python -m ui_cli.app.preparation_agent.cli_preparer_agent

# 3. Tester l'agent entraîné
./scripts/a108_eprouver_agent_personne.sh

# 4. Visualiser en mode TUI
./scripts/tui.sh
```

### Rejouer une session :
```bash
./scripts/replay_tui.sh
```

## Technologies Utilisées

- **Python** : langage principal
- **Dataclasses** : structures de données
- **YAML** : configuration
- **JSONL** : stockage des journaux
- **NumPy** : calculs numériques (modèles)
- **pytest** : tests unitaires

## Structure des Dossiers

```
snake-world-model/
├── services/           # Microservices
│   ├── world_sim/     # Simulateur
│   ├── agent_service/ # Agents IA
│   ├── instrument/    # Capteurs
│   ├── runner/        # Orchestrateur
│   ├── ui_tui/        # Interface TUI
│   └── ui_cli/        # CLI
├── donnees/
│   └── config/
│       ├── arenes/         # Définition des environnements
│       └── experiences/    # Sessions d'expérimentation
├── docs/              # Documentation
├── scripts/           # Scripts d'exécution
└── artefacts/        # Résultats (legacy)
```

## Points Forts du Projet

1. **Modularité** : chaque service est indépendant et testable
2. **Traçabilité** : tout est loggé pour analyse ultérieure
3. **Reproductibilité** : seed aléatoire fixé, replay possible
4. **Évolutivité** : facile d'ajouter de nouveaux agents ou arènes
5. **Pédagogique** : concepts d'IA clairement séparés et observables

## Évolutions Possibles

D'après les fichiers, le projet prévoit :
- Docker-compose pour orchestration (`infra/compose/`)
- Système de compétitions multi-agents
- Cours 5 en préparation
- Nouveaux types d'agents et d'arènes

## Résumé

Ce projet est un **laboratoire d'apprentissage automatique** où des agents IA apprennent à jouer au Snake en construisant progressivement leur compréhension du monde. C'est à la fois un environnement de recherche et un outil pédagogique pour comprendre comment les systèmes intelligents peuvent apprendre, planifier et s'adapter dans un environnement contrôlé mais non trivial.
