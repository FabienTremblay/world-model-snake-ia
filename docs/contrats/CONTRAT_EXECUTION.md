# contrat d’exécution (v1 — expérimental)

Ce document définit le **contrat d’exécution** commun aux outils du projet *ia-snake* : runner, bac à sable, ui_cli, ui_tui, diagnostics.

> Tant que v1 n’est pas figée, aucune compatibilité ascendante n’est exigée.

---

## 1) définitions

### 1.1 situation (run)
Une **situation** (run) est une exécution expérimentale complète, définie par :
- une arène
- un agent (et sa configuration)
- un contexte d’exécution (expérience, seed, paramètres)

Identifiant : `run_id`

Une situation produit un journal JSONL pouvant contenir **plusieurs épisodes**.

✅ règle : **un journal = un run**  
❌ hypothèse interdite : **un journal = un épisode**

### 1.2 épisode
Un **épisode** est une trajectoire complète à l’intérieur d’un run.

Champs structurants :
- `episode_id`
- `tick` (commence à 0)
- fin explicite : `termine = true` et `raison_fin != null`

---

## 2) journal d’exécution (runner)

Le runner écrit un journal *append-only* (JSONL).  
Chaque ligne représente **un tick d’un épisode**.

### 2.1 champs minimaux (obligatoires)
- `run_id`
- `episode_id`
- `tick`
- `action`
- `score`
- `termine`
- `raison_fin`

Le journal est :
- immuable après écriture
- la **source de vérité post‑exécution** (replay, diagnostics)

---

## 3) bac à sable (source de vérité amont)

Le **bac à sable** est la source de vérité **avant exécution**.

Responsabilités :
- résoudre `experience.yml`
- fixer l’arène et l’agent effectifs
- exposer les chemins d’artefacts (datasets, runs, etc.)

✅ règle : **ui_cli / ui_tui / diagnostics ne parsant pas le YAML**  
Ils consomment les résultats du bac à sable.

---

## 4) sémantique des ticks et des actions

### 4.1 tick 0 = snapshot initial
À `tick = 0`, le journal doit contenir un **snapshot initial** :

- `action` peut être `null`
- l’état (capteurs, score, longueur, etc.) correspond à *avant toute action*

Conséquence pour le replay :
- le replay **initialise l’état** avec `tick 0`
- puis applique les actions à partir de `tick >= 1`

### 4.2 espace d’actions (minimum)
Pour `tick >= 1`, `action` est une chaîne appartenant à l’espace d’actions.

Contrat minimal actuel :
- `"avant"` : tentative d’avancer d’une case selon la **direction courante**
- `"observer_gauche"` / `"observer_droite"` : **changement d’orientation uniquement**, sans déplacement

> important : **on a séparé “tourner la tête” de “se déplacer”**.  
> Le déplacement n’est tenté que lorsque `action == "avant"`.

### 4.3 robustesse (tolérance future)
- une action inconnue **ne doit pas faire planter** ui_tui/diagnostics :
  - afficher “action non supportée” / ignorer pour le rendu,
  - mais conserver l’enregistrement pour l’analyse.

---

## 5) responsabilités par outil

- **runner** : exécute la simulation et journalise
- **ui_cli** : prépare (bac à sable) puis lance
- **ui_tui** : visualise / rejoue (à partir du journal)
- **diagnostics** : analyse offline (à partir du journal)

---

## 6) exigences de replay (ui_tui)

Le replay :
1) sélectionne un `episode_id` dans le journal du run  
2) charge `tick 0` comme **état initial**  
3) applique séquentiellement les actions (`tick >= 1`)  
4) n’infère jamais un déplacement à partir du tick :  
   - seul `"avant"` implique une tentative de déplacement
   - `"observer_*"` modifie l’orientation sans déplacer

### exemple minimal (extrait conceptuel)
- tick 0 : `action=null` (snapshot)
- tick 1 : `action="avant"`
- tick 2 : `action="avant"`
- tick 3 : `action="observer_gauche"`
- tick 4 : `action="avant"`

---

## 7) principes non négociables

- pas de confusion run/épisode
- pas de parsing YAML hors bac à sable
- pas d’hypothèse sur le nombre d’épisodes dans un journal

---

## 8) statut

Ce document fait foi.
