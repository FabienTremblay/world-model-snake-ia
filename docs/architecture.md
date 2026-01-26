# Architecture (v1)

## Services
- **world-sim** : monde réel (état, règles θ), expose reset/step et renvoie des observations sous forme d'attributs.
- **agent-service** : monde interne, maintient b(θ) et choisit des actions.
- **runner** : boucle d'épisodes, collecte traces, métriques, artefacts.
- **ui** : visualisation/debug (optionnel en v1, mais on garde le slot).

## Principes
- l’observation ne doit jamais contenir d’étiquette sémantique (ex. "warp"), seulement des attributs.
- θ est stable durant un épisode (peut changer entre épisodes).

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
