# Architecture (v1)

## Services
- **world-sim** : monde réel (état, règles θ), expose reset/step et renvoie des observations sous forme d'attributs.
- **agent-service** : monde interne, maintient b(θ) et choisit des actions.
- **runner** : boucle d'épisodes, collecte traces, métriques, artefacts.
- **ui** : visualisation/debug (optionnel en v1, mais on garde le slot).

## Principes
- l’observation est un **signal perceptif**, jamais une description sémantique du monde.
- elle ne contient que des attributs (visuels, intensités, motifs, etc.).
- toute représentation lisible (ASCII, métriques, checksum) est une **donnée dérivée**,
- produite hors du monde à des fins de debug, visualisation ou mesure.
- θ est stable durant un épisode (peut changer entre épisodes).

## Cycle de vie d’exécution

- **run** : une exécution logique complète du système (identifiée par `run_id`)
- **episode** : une trajectoire continue dans un run (identifiée par `episode_id`)
- **tick** : un pas discret de simulation à l’intérieur d’un épisode

Règles :
- un run peut contenir plusieurs épisodes
- un épisode commence à `tick=0`
- un épisode se termine lorsque `termine=true`
- **aucun nouvel épisode ne démarre automatiquement**
- un reset explicite est requis pour lancer un nouvel épisode

## Modes de fonctionnement

Le système distingue clairement les **modes cognitifs** des **modes de contrôle**.

### Modes cognitifs (intention de l’agent)

Ces modes définissent l’objectif poursuivi par l’agent lorsqu’il produit des actions.

- **Exploration**
  - objectif : réduire l’incertitude sur les règles du monde (θ)
  - priorité au gain d’information plutôt qu’au score
  - l’agent peut accepter des actions sous-optimales ou risquées

- **Exploitation**
  - objectif : maximiser la performance (score)
  - les règles du monde sont supposées connues ou suffisamment estimées
  - toute prise de risque doit être justifiée par un gain attendu

### Mode de contrôle (non cognitif)

- **Mode assisté**
  - les actions sont fournies par un humain via le TUI
  - le monde et le moteur ne distinguent pas l’origine de l’action
  - l’observation produite est identique à celle reçue par un agent

Le mode assisté n’est pas un mode cognitif : il sert à valider le monde,
à générer des trajectoires de référence et à comparer humain et agent à observation égale.
Les trajectoires produites en mode assisté sont journalisées et rejouables exactement comme celles produites par un agent.

## Replay

Le système permet le rejeu déterministe (ou quasi déterministe) de trajectoires
à partir des artefacts produits lors d’un run.

- les replays sont sélectionnés par `run_id`
- un replay rejoue un seul run à la fois
- chaque tick rejoué réémet une Observation sur le bus
- le TUI et les spectateurs consomment le replay exactement comme du live

