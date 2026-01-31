# Trace — spec minimale de l’agent producteur de connaissances (apk)

version: v0.1  
date: 2026-01-31  
package cible: `services/agent_service/app/epistemique/`

## 0. Décision de terminologie

### 0.1 Principe canonique

La **terminologie** (noms des concepts, catégories, relations) est définie dans la **langue de l’agent producteur de connaissances**.

Autrement dit :

- le monde **n’impose** aucune sémantique ;
- les signaux et données sont **pré-sémantiques** ;
- l’**apk** est l’acteur qui **nomme** et **stabilise** un vocabulaire ;
- ce vocabulaire alimente ensuite les autres agents (observateur, coach, joueur, planificateur).

Conséquence directe :

- une même configuration perceptive peut recevoir **des noms différents** selon l’apk (donc selon l’ontologie en construction),
- et ces noms peuvent être **révisés** (hypothèses invalidées, renommage, spécialisation, fusion).

### 0.2 Contrainte d’architecture

Aucun composant du monde (`world_sim`) ne doit dépendre de ces noms.

Les noms apparaissent uniquement dans la couche épistémique :
- comme **artefacts cognitifs**,
- comme **ontologie/corpus**,
- comme **règles d’inférence** et **hypothèses**.

---

## 1. Clarification sur 3.3 “relation causale” (mise à jour)

### 1.1 Formulation corrigée

Une “relation causale” produite par l’apk doit être comprise comme :

> une **connaissance** exprimée dans le vocabulaire de l’apk, reliant une information (désignation) à des conséquences possibles, de manière située et révisable.

Elle n’est pas une propriété du monde.

### 1.2 Exemples (dans la langue de l’apk)

- `mur` → `collision`
- `collision` → `fin_irreversible`
- `croissance` + `delta_score_pos` → `nourriture_consomme`

Ici, `mur`, `collision`, `fin_irreversible`, `nourriture_consomme` sont des **noms de concepts** définis par l’apk.

---

## 2. Rappel des artefacts attendus (minimum)

L’apk produit et maintient un corpus comprenant au minimum :

- **Hypothèse** (testable, révisable, avec support empirique)
- **Règle d’inférence** (transformation information → information)
- **Relation causale** (information → conséquences possibles)
- **Ontologie partielle** (graphe de concepts/relations/règles, dans la langue de l’apk)
- **Évaluation** (support, contradictions, confiance, conditions de validité)

---

## 3. Placement dans le code (décision)

Le nouveau périmètre conceptuel vit dans :

`services/agent_service/app/epistemique/`

Rôle : héberger les contrats, structures, registres et mécanismes liés à :
- la production de terminologie,
- la production d’hypothèses/règles,
- la validation/réfutation,
- la transmission d’artefacts cognitifs.

---

## 4. Prochaine étape directe (suite proposée)

1. Définir les **contrats minimaux** (dataclasses) en français pour :
   - `HypotheseEpistemiqueV1`
   - `RegleInferenceV1`
   - `EvaluationHypotheseV1`
2. Définir un `RegistreEpistemiqueV1` :
   - ajout / mise à jour / versionnage local
   - index par concept, par relation, par statut (candidate/confirmée/infirmée)
3. Ajouter un petit script de diagnostic “smoke” :
   - charger un journal
   - produire 2–3 hypothèses candidates (ex. sur `collision_mur` et `croissance`)
   - afficher support + confiance

Ce bloc est volontairement “offline”, cohérent avec les cours 1 à 4.
