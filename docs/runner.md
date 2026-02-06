# runner — documentation (cours 5)

Le service `runner` fournit le **cadre d'exécution** : il orchestre la simulation (monde Snake),
l'appel aux agents, et l'écriture d'un journal d'épisodes.

À partir du cours 5, on introduit un **noyau d'exécution partagé** pour éviter la duplication
entre le CLI et les autres interfaces.

---

## 1. Responsabilités du runner

Le runner est responsable de :

- **instancier et configurer le monde** à partir d'une arène (YAML) et d'une configuration (`ConfigMonde`)
- **faire progresser le temps** (ticks) et gérer la vie d'un épisode
- **appeler l'agent** pour obtenir une action à partir des capteurs
- **appliquer l'action** au monde
- **journaliser** l'évolution (capteurs, action, score, fin, etc.) via `JournalEpisodes`
- (optionnel) **publier des observations** sur un bus mémoire pour des UI live (hors du noyau batch)

Le runner **ne fait pas** :
- diagnostic,
- épistémique (registre, hypothèses),
- planification,
- évaluation des performances.

Il doit rester **rigoureux et neutre**.

---

## 2. Noyau partagé : `runner.app.noyau`

Le noyau (cours 5) vit dans :

- `services/runner/app/noyau.py`

Il expose :
- `ParametresExecution` : nombre d'épisodes, ticks max, variation du seed par épisode
- `executer_episodes_headless(...)` : exécution batch / headless

### 2.1 Convention temporelle et journal

La convention du journal est la suivante :

- on écrit systématiquement **tick 0** avec `action_direction = null`
- à chaque pas :
  - l'agent choisit une action depuis l'état courant (tick *t*)
  - on applique l'action
  - on observe l'état résultant (tick *t+1*)
  - on écrit ce tick avec `action_direction = <action>`

Cette convention permet :
- de reconstruire proprement les transitions,
- d'aligner les métriques et l'apprentissage en ligne sur les ticks du monde.

---

## 3. Intégration CLI (ui_cli)

Le CLI (`services/ui_cli/`) reste responsable de :
- la gestion du bac-à-sable d'expérience,
- les chemins de sortie (runs, datasets, diagnostics, registres),
- les options de génération,
- l'écriture des métriques.

**Mais** l'exécution des épisodes est déléguée au noyau : `executer_episodes_headless`.

Le CLI peut brancher des comportements additionnels via des **hooks** :
- écriture de métriques
- apprentissage en ligne (si l'agent expose une méthode dédiée)
- autres instrumentations de cours

---

## 4. Frontières à respecter (important)

Pour maintenir un découpage sain (cours 5) :

- le runner ne doit pas connaître les règles épistémiques
- le runner ne doit pas décider pour l'agent
- le runner ne doit pas interpréter les résultats (diagnostics, conclusions)
- le runner doit rester déterministe et reproductible (seed, paramètres explicites)

---

## 5. Évolution attendue (cours 5+)

Prochaines extensions naturelles, sans casser les frontières :

- ajout de **traces de décision** (optionnelles) écrites au journal (mais produites par l'agent)
- mode interactif (TUI) qui réutilise partiellement le noyau, tout en gardant ses contrôles
- instrumentation d'évaluation (dans un composant dédié, pas dans le runner)
