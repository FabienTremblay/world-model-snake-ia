# runner

Le **runner** est le composant qui exécute une expérience (arène + agent + règles) et produit un **journal d’épisodes** exploitable pour les diagnostics, la relecture et l’entraînement.

---

## responsabilités (ce que le runner fait)
 
- charger une expérience (arène, paramètres d’exécution, seed)
- instancier un agent (selon l’incarnation demandée)
- exécuter les ticks (boucle principale)
- produire un journal `journal_episodes.jsonl` (un événement par tick)
- gérer la sortie des artefacts (stdout.log, résumé, etc.)

## non-responsabilités (ce que le runner ne doit pas faire)
- **ne pas contenir** de logique de jeu (murs, nourriture, fin, score) : c’est l’arène / moteur du monde
- **ne pas décider** de la stratégie de l’agent : c’est l’agent
- **ne pas inventer** de métriques ad hoc : ce sont les diagnostics/analyses

Il doit rester **rigoureux et neutre**.

---

## capteurs et “projection” (absolue vs égocentrée)
Le runner journalise ce que l’agent “voit” via `capteurs_compact`. Or, **la même scène** peut être projetée de deux façons :
- **projection absolue** (référentiel fixe de l’arène)  
  Utile pour le **point de vue “estrade”** : comparer des états indépendamment de l’orientation de l’agent.
- **projection égocentrée / orientée** (référentiel de l’agent)  
  Utile pour le **point de vue incarné** : lorsque l’agent tourne, la représentation tourne avec lui (donc les capteurs changent même si la position ne change pas).

✅ le runner doit rester **agnostique** : il ne choisit pas la projection “par magie”.  
La projection doit être **fournie** par le point de vue/agent (ou par une couche d’adaptation) et être **traçable** dans le journal.

### exigence de traçabilité dans le journal
Pour éviter les malentendus en diagnostic, le journal devrait porter explicitement la projection utilisée, par exemple :

- soit via un champ dédié : `projection_capteurs: "absolue" | "egocentree"`
- soit via `format_capteurs`, par ex.  
  `capteurs_b64_v1(u16_teinte,u8_int,u8_pack;projection=absolue)`  
  `capteurs_b64_v1(u16_teinte,u8_int,u8_pack;projection=egocentree)`

## 2. Noyau partagé : `runner.app.noyau`

Le noyau vit dans :

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
