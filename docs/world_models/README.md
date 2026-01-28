# World Models — parcours pédagogique et expérimental

Ce dossier documente un **parcours progressif et reproductible** pour comprendre,
implémenter et expliquer le concept de *World Models* à partir d’un environnement simple (Snake),
avant toute introduction du deep learning.

L’objectif n’est pas la performance, mais la **compréhension instrumentée** :
chaque étape est validée par des métriques observables et des artefacts rejouables.

---

## Principes directeurs

- **Séparation stricte des rôles**
  - *runner* : monde réel (état, règles, transitions)
  - *agent_service* : agents, décisions, monde interne
  - *ui_tui / ui_cli* : modes d’exécution (humain / batch)

- **Traçabilité**
  - toute affirmation doit être appuyée par un journal (`episodes.jsonl`)
  - toute évaluation est reproductible par une commande CLI

- **Progressivité**
  - on ne saute aucune étape conceptuelle
  - chaque limite observée motive explicitement l’étape suivante

---

## Structure des cours

```
docs/world_models/
  README.md
  cours/
    cours1_world_models.md
    cours2_world_models.md
    cours3_world_models.md
```

Chaque cours est un **palier conceptuel** :
- une hypothèse
- une instrumentation
- des commandes exactes
- des résultats attendus
- une interprétation

---

## Vue d’ensemble du parcours

### Cours 1 — Exploration et dynamique locale
**Question traitée :**
> Que peut apprendre un agent s’il mémorise exactement ce qu’il observe ?

- état latent : `checksum(capteurs)`
- world model : tabulaire `(etat, action) → etat_suivant`
- agent : aléatoire / curiosité tabulaire
- métriques : couverture, exactitude conditionnelle, entropie

**Résultat clé :**
- exactitude parfaite quand connu
- couverture limitée
- aucune généralisation

➡️ Motive la recherche d’un état latent plus invariant.

---

### Cours 2 — État latent invariant (sans deep learning)
**Question traitée :**
> Comment augmenter la couverture sans perdre toute précision ?

- état latent : version compressée / discrétisée
- même monde, mêmes agents, mêmes métriques
- comparaison directe avec le Cours 1

➡️ Introduit la notion d’invariance et de regroupement d’états.

---

### Cours 3 — État latent appris (encodeur)
**Question traitée :**
> Pourquoi apprendre une représentation plutôt que la définir à la main ?

- encodeur (ML)
- latent continu ou discret appris
- bruit et robustesse
- entropie non nulle possible

➡️ Entrée officielle du deep learning.

---

### Cours suivants (indicatifs)

- **Cours 4** — Simulation et imagination
  - rollouts dans le monde interne
- **Cours 5** — Planification multi-étapes
  - A*, MCTS, politiques basées sur le modèle

---

## Artefacts clés

- `artefacts/episodes.jsonl`  
  Journal canonique des interactions (live ou CLI)

- `artefacts/exploration_metrics.jsonl`  
  Journal explicatif des décisions d’exploration

- `artefacts/modele_monde_eval_*.jsonl`  
  Résultats d’évaluation offline

Ces fichiers sont considérés comme des **preuves expérimentales**.

---

## Philosophie pédagogique

> Un world model n’est pas défini par une architecture,
> mais par la relation mesurable entre
> ce qui est observé, ce qui est prédit, et ce qui est encore inconnu.

Ce parcours est conçu pour :
- répondre aux questions difficiles (*pourquoi ça marche ? pourquoi ça échoue ?*)
- éviter les “sauts de foi” vers le deep learning
- permettre à un tiers de **refaire exactement les mêmes observations**

---

## Comment utiliser ces documents

1. Lire un cours
2. Exécuter les commandes associées
3. Examiner les artefacts produits
4. Comparer avec les résultats attendus
5. Passer au cours suivant

Aucune étape n’est optionnelle.

---

## Public visé

- développeurs
- architectes
- enseignants
- étudiants avancés
- toute personne voulant comprendre les *World Models* autrement que par des schémas abstraits

---

## Statut

- Cours 1 : **complet et validé**
- Cours 2 : en préparation
- Cours 3+ : à venir

Ce README évoluera au rythme des cours, mais chaque cours publié est considéré comme **stable**.
