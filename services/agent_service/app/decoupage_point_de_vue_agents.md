# découpage applicatif et notion de point de vue

Ce document fixe explicitement le **découpage applicatif** et la **notion de point de vue** telle qu’utilisée dans SnakeAI (cours 5).
Il sert de référence stable pour éviter l’éparpillement conceptuel et structurel dans les packages python.

---

## 1. notion centrale : le point de vue

Dans ce projet, le **point de vue** désigne une **position informationnelle** par rapport au monde simulé.

Le point de vue définit :
- ce qui est visible,
- à quelle échelle,
- avec quel niveau de granularité,
- et avec quelle dépendance à l’orientation.

> le point de vue **n’est pas** :
> - une heuristique,
> - une stratégie,
> - un tempérament,
> - une préférence décisionnelle.

C’est une **contrainte structurelle d’accès au monde**.

---

## 2. deux rôles d’agents et deux référentiels visés

### 2.1 agents en arène (point de vue incarné)

Les agents :
- agent aléatoire,
- agent de curiosité,
- agent planificateur (mpc, etc.),

sont **dans l’arène**.

**cible (projection incarnée)** :
- perception orientée / égocentrée (la représentation dépend de la direction),
- information partielle possible (rayon, fov),
- action immédiate dans le monde.

**état actuel (à ce stade du projet)** :
- la projection réellement utilisée dans `capteurs_compact` est encore **absolue** (estrade),
- la direction de l’agent existe dans l’état du monde, mais **n’influence pas** la projection journalisée.

L’objectif du cours 5 est précisément d’introduire la projection incarnée de façon traçable.

---

### 2.2 agent épistémique (point de vue d’estrade)

L’agent épistémique (apk, agent producteur de connaissance) est **hors de l’arène**, en position d’estrade.

Caractéristiques :
- vision globale,
- référentiel fixe (invariant par rotation),
- accès à des agrégats spatiaux et temporels,
- n’agit pas dans l’arène : il observe, agrège, infère, qualifie.

---

## 3. projection perceptive : on introduit un package instrument

Le projet vise deux projections, implémentées comme des **instruments** :

- **caméra estrade absolue** (`repere=absolu`)
  - invariant par rotation
  - utilisée par : épistémique, observateurs, world models, analyses hors-sol

- **caméra orientée / égocentrée** (`repere=egocentre`)
  - dépend de la direction courante
  - utilisée par : agents incarnés en arène (agents « personne »)

Principe : `world_sim` fournit l’état canonique, `instrument` produit l’observation, le runner journalise le tout.

---

## 4. axes conceptuels distincts (à ne pas mélanger)

Pour éviter toute confusion, trois axes sont distingués.

### axe a — point de vue
- local / global
- incarné / distancié
- dépendant / indépendant de l’orientation

➡ fixé par l’instrument (et donc par la définition d’agent)

### axe b — approche
- aléatoire
- exploratoire
- planificatrice
- inférentielle

➡ méthode de traitement de l’information disponible

### axe c — tempérament
- prudent / téméraire
- curieux / conservateur
- aversion au risque, etc.

➡ paramétrage normatif de l’arbitrage

---

## 5. découpage des packages python

### 5.1 `world_sim` (monde canonique)
- règles du monde
- dynamique (`step`)
- exposition d’un **état canonique** (snapshot) consumé par les instruments
- aucune projection perceptive « implicite »

### 5.2 `instrument` (perception)
- interface `instrument.observer(etat, contexte) -> observation`
- implémentations :
  - `camera_estrade_absolue_v1`
  - `camera_egocentree_v1`

### 5.3 `agent_service.app.agent_runtime`
- agents en arène : décision à partir des observations reçues
- l’agent ne reconstruit pas « le monde » : il consomme une observation instrumentée

---

## 6. journal d’épisodes (sans compat)

Le journal `journal.jsonl` doit porter explicitement :
- l’état canonique,
- la(les) observation(s) et leur `instrument_id`,
- le repère (`absolu` / `egocentre`) et les paramètres effectifs.

Voir `docs/runner.md` pour le format recommandé (episodes_v2).
---

## 7. catalogue d’agents (plug-ins yaml) (ajout v1)

Les **types** d’agents (au sens « ce qui est sélectionnable par `--agent <id>` ») sont définis par plug-ins YAML.

- répertoire scanné : `services/agent_service/app/agents/`
- fichiers découverts : `agent*.yml`
- chaque `agent.yml` fournit :
  - `id` : identifiant du type
  - `fabrique` : `module:callable`

### 7.1 type vs incarnation

- un **type d’agent** est une définition instanciable (catalogue).
- une **incarnation** est une instance préparée / un artefact runtime (préparation, assemblage, etc.).

Une incarnation **n’est pas** un type d’agent du catalogue, et ne doit pas être découverte par le scan YAML.

### 7.2 lien avec le point de vue

Le point de vue est une contrainte structurelle d’accès au monde (via les instruments).
Le catalogue sert à rendre explicite :
- quels types d’agents existent,
- et, à terme, quels instruments / repères ils attendent (absolu vs égocentré),
sans déplacer cette logique dans le runner.
