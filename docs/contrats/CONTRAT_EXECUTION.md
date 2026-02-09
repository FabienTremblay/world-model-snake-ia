# CONTRAT_EXECUTION.md

Ce document fixe le contrat d’exécution expérimental du projet ia-snake.
Il s’applique à tous les outils : runner, bac à sable, ui_cli, ui_tui, diagnostics.

Tant que la version 1 n’est pas figée, aucune compatibilité ascendante n’est requise.

---

## 1. Définitions fondamentales

### Situation (Run)

Une **situation** (appelée aussi *run*) est une exécution expérimentale complète.

Une situation est définie par :
- une arène
- un agent (et sa configuration)
- un contexte d’exécution (expérience, seed, paramètres)

Une situation est identifiée par :
- `run_id`

Une situation produit **un journal d’exécution** pouvant contenir **plusieurs épisodes**.

---

### Épisode

Un **épisode** est une trajectoire complète à l’intérieur d’une situation.

Un épisode :
- est identifié par `episode_id`
- commence à `tick = 0`
- se termine explicitement par :
  - `termine = true`
  - `raison_fin`

Un fichier de journal **peut contenir des centaines d’épisodes**.

👉 Hypothèse interdite :  
> “un journal = un épisode”

---

## 2. Journal d’exécution (contrat runner)

Le runner produit un journal append-only (JSONL).

Chaque ligne représente **un tick**.

### Champs minimaux attendus

- `run_id`
- `episode_id`
- `tick`
- `action`
- `score`
- `termine`
- `raison_fin`

Le journal est :
- immuable après écriture
- la **source de vérité post-exécution**

---

## 3. Bac à sable (source de vérité amont)

Le **bac à sable** est la source de vérité **avant exécution**.

Il est responsable de :
- résoudre une expérience (`experience.yml`)
- fixer :
  - l’arène
  - l’agent
  - les chemins d’artefacts

---

## 4. Responsabilités des outils

- runner : exécute, journalise
- ui_cli : prépare et lance
- ui_tui : visualise, rejoue
- diagnostics : analyse

---

## 5. Replay

Le replay :
- lit le journal
- sélectionne un épisode
- permet navigation et analyse

---

## 6. Principes non négociables

- pas de confusion run / épisode
- pas de parsing YAML hors bac
- pas d’hypothèse sur le nombre d’épisodes

---

## 7. Statut

Ce document fait foi.
