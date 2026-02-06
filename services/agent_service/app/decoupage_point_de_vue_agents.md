# Découpage applicatif et notion de point de vue

Ce document fixe explicitement le **découpage applicatif** et la **notion de point de vue** telle qu’utilisée dans le projet SnakeAI (cours 5).  
Il sert de référence stable pour éviter l’éparpillement conceptuel et structurel dans les packages Python.

---

## 1. Notion centrale : le point de vue

Dans ce projet, le **point de vue** désigne une **position informationnelle** par rapport au monde simulé.

Le point de vue définit :
- ce qui est visible,
- à quelle échelle,
- avec quel niveau de granularité,
- et avec quelle temporalité.

> Le point de vue **n’est pas** :
> - une heuristique,
> - une stratégie,
> - un tempérament,
> - une préférence décisionnelle.

Il s’agit d’une **contrainte structurelle d’accès au monde**.

---

## 2. Deux points de vue fondamentaux

### 2.1 Agents en arène (point de vue incarné)

Les agents suivants :
- agent aléatoire,
- agent de curiosité,
- agent planificateur,

sont **dans l’arène**.

**Caractéristiques du point de vue :**
- vision locale (ex. 180° devant l’agent),
- information partielle,
- perception directe et instantanée,
- action immédiate dans le monde.

Ces agents :
- observent,
- décident,
- agissent.

Ils sont soumis aux mêmes contraintes perceptives, et ne diffèrent **pas** par leur point de vue.

---

### 2.2 Agent épistémique (point de vue d’estrade)

L’agent épistémique (APK, agent producteur de connaissance) est **hors de l’arène**, en position d’estrade.

**Caractéristiques du point de vue :**
- vision globale de l’arène,
- accès à des agrégats spatiaux et temporels,
- absence de perception locale fine,
- accès post-hoc aux épisodes et diagnostics.

Cet agent :
- n’agit pas directement,
- n’influence pas l’arène par des actions,
- observe, agrège, infère et qualifie le savoir.

---

## 3. Axes conceptuels distincts (à ne pas mélanger)

Pour éviter toute confusion, trois axes sont distingués :

### Axe A — Point de vue
- local / global
- incarné / distancié
- temps réel / post-hoc

➡ **Fixé par le package et le type d’agent**

### Axe B — Approche
- aléatoire
- exploratoire
- planificatrice
- inférentielle

➡ Méthode de traitement de l’information disponible

### Axe C — Tempérament
- prudent / téméraire
- curieux / conservateur
- aversion au risque, etc.

➡ Paramétrage normatif de l’arbitrage

---

## 4. Découpage des packages Python

### 4.1 Agents en arène

```
agent_runtime/
└── agents_in_arene/
    ├── base.py
    ├── agent_aleatoire.py
    ├── agent_curiosite.py
    └── agent_planificateur.py
```

**Contrat conceptuel :**

```python
class AgentEnArene:
    def observer(self, perception_locale):
        ...

    def decider(self, observation):
        ...

    def agir(self, action):
        ...
```

Tous les agents de ce package :
- partagent le même point de vue,
- diffèrent uniquement par leur approche et leur tempérament.

---

### 4.2 Approches décisionnelles

```
agent_runtime/
└── approches/
    ├── base.py
    ├── aleatoire.py
    ├── exploration.py
    └── planification.py
```

```python
class ApprocheDecision:
    def choisir_action(self, observation, contexte):
        ...
```

---

### 4.3 Tempéraments

```
agent_runtime/
└── traits/
    └── temperament.py
```

```python
class Temperament:
    prudence: float
    curiosite: float
    aversion_risque: float
```

Les tempéraments :
- influencent l’arbitrage,
- ne modifient pas le point de vue.

---

### 4.4 Agent épistémique (estrade)

```
agent_epistemique/
└── estrade/
    ├── observateur_epistemique.py
    ├── diagnostics.py
    ├── hypotheses.py
    └── registre.py
```

```python
class ObservateurEpistemique:
    def observer_episode(self, episode):
        ...

    def diagnostiquer(self, episodes):
        ...

    def produire_hypotheses(self):
        ...

    def mettre_a_jour_registre(self):
        ...
```

Cet agent :
- ne possède aucun tempérament,
- ne prend aucune action directe,
- n’a pas accès à la perception locale.

---

## 5. Principe de séparation à respecter

- Aucun agent en arène ne doit accéder à une vision globale.
- L’agent épistémique ne doit jamais agir dans l’arène.
- Le point de vue est fixé **par le package**, pas par configuration dynamique.

---

## 6. Formulation de référence

> Les agents en arène partagent un point de vue local et incarné : ils voient partiellement le monde et doivent agir.  
> L’agent épistémique adopte un point de vue global et distancié : il ne voit pas le détail, mais observe les structures, les régularités et les fragilités du savoir produit.  
> Les différences d’approche et de tempérament s’expriment à l’intérieur de ces points de vue, sans jamais les traverser.

---

**Statut : document de référence (cours 5).**
