# cours 4 — imagination et planification (bilan + plan)

base: zip `2026-01-29-11h39.zip` (source unique de vérité)

---

## 1) bilan clair de l’état du projet

### 1.1 architecture actuelle (code)

Le projet est déjà structuré selon la séparation *monde réel* vs *monde interne* :

- `services/world_sim/`  
  **simulateur réel** (Snake).  
  - `monde_snake.py` : dynamique, collisions, score, fin d’épisode  
  - `projection_capteurs.py` : capteurs (grille de pixels)  
  - `arenes_yaml.py` + `donnees/config/arenes/*.yml` : configuration du monde

- `services/runner/`  
  **orchestrateur “monde réel”** + **journalisation**.  
  - `journal_v2.py` : écrit `journal.jsonl` (+ `obs/` pour les payloads lourds)
  - `replay_api.py` : relecture du journal (et lecture des payloads)

- `services/agent_service/`  
  **agents** + **monde interne** (world model).  
  - `modele_monde/tabulaire_v1.py` : modèle tabulaire `(etat, action) -> distribution(etat_suivant)`  
  - `modele_monde/entrainement_depuis_journal.py` : apprentissage offline depuis `episodes.jsonl`  
  - `modele_monde/evaluer_tabulaire_v1.py` : métriques (couverture, exactitude conditionnelle, entropie)  
  - `modele_monde/latent_v1.py` : latents “faits main” (checksum / discret_v1)  
  - `modele_monde/encodeur_contrastif_v1.py` + scripts associés : latent **appris** (cours 3)  
  - `agents/agent_curiosite_tabulaire.py` : agent explorateur (online) guidé par entropie/inconfiance

- `services/ui_cli/`  
  **exécution batch** (headless) pour produire des journaux rejouables.

- `services/ui_tui/`  
  **interface interactive** (pour observer et contrôler).

### 1.2 artefacts déjà produits (cours 1 à 3)

Dans `artefacts/` on voit déjà les preuves expérimentales typiques du parcours :

- `episodes.jsonl` : journal canonique (monde réel)
- `episodes_latent_discret.jsonl` : journal recodé avec latent discret (cours 2)
- `episodes_latent_appris.jsonl` : journal recodé avec `latent_id` (cours 3)
- `out_cours3/encodeur_contrastif_v1.npz` : encodeur linéaire appris (cours 3)
- `centroides_kmeans_v1.npy` + `stats_kmeans_v1.json` : quantification k-means (cours 3)
- `modele_monde_eval_tabulaire_v1.jsonl` et `modele_monde_eval_tabulaire_latent_v1.jsonl` : traces d’évaluation tabulaire

### 1.3 concepts déjà “en place” (cours 3 terminé)

- **état latent discret** appris :  
  `capteurs -> features (histogrammes 24 bins × 4 quadrants) -> encodeur linéaire -> embedding -> k-means -> latent_id`.

- **world model tabulaire** appris offline :  
  comptage de transitions, distribution empirique, **incertitude naturelle** (entropie non nulle, confiance < 1).

- pas de modèle probabiliste explicite, mais une *distribution empirique* (comptes normalisés) est déjà calculée et exposée par `Prediction`.

**ce qui manque volontairement pour passer au cours 4 :**
- le modèle sait prédire `etat_suivant` (distribution), mais il ne sait pas encore **simuler** (rollout multi-étapes) ni **planifier** (choisir une action en regardant des futurs possibles).

---

## 2) structure proposée pour le cours 4

Objectif global :  
> transformer le world model appris en un “simulateur interne” utilisable pour imaginer des trajectoires et choisir une action.

### section 4.1 — rappel minimal (où on en est)
- monde réel vs monde interne
- rappel des métriques du cours 3 : couverture / exactitude conditionnelle / entropie
- rappeler que “incertitude = mélange de futurs” (distribution empirique)

**expérience** : reprendre un `etat` réel et montrer que 2 actions ont des distributions très différentes (une quasi-déterministe, l’autre multi-modale).

---

### section 4.2 — simulateur interne (une étape)
Objectif : définir une opération **pas à pas** dans le monde latent :

`(z_t, a_t) -> échantillonner(z_{t+1})`

- utiliser la distribution `Prediction.distribution`
- définir un RNG contrôlable (seed) pour reproductibilité
- définir la notion de “transition inconnue” (support = 0)

**expérience** :  
sur un lot de transitions réelles, comparer :
- *z_{t+1} réel* vs *z_{t+1} imaginé* (en sampling)
- taux de “hit” : l’imaginé tombe-t-il souvent sur la vraie prochaine classe ?
- calibration simple : support vs entropie vs stabilité du sampling

---

### section 4.3 — simulateur interne enrichi (récompense + terminaison)
Pour planifier, il faut une notion d’utilité.  
Dans Snake, les signaux disponibles dans le journal :
- `score` (donc `delta_score`)
- `termine` et `raison_fin`

On apprend **deux modèles tabulaires supplémentaires** (empiriques, comme le modèle de transition) :

1) **modèle de récompense** : `(z_t, a_t, z_{t+1}) -> distribution(delta_score)`  
2) **modèle de terminaison** : `(z_t, a_t, z_{t+1}) -> P(termine)`

> pourquoi conditionner par `z_{t+1}` ?  
> parce que dans le journal, le gain (manger) et la mort sont observables après la transition.

**expérience** :  
sur le journal, mesurer :
- distribution des `delta_score` (rare, très sparse)
- probabilité de fin par action (approximée)
- et surtout : est-ce que certains latents sont “dangereux” (P(termine) élevé) ?

---

### section 4.4 — rollouts multi-étapes (imagination)
Objectif : simuler H pas dans le monde interne.

- algorithme : répéter `step_latent()` H fois
- accumulation d’un retour :
  - `G = somme(delta_score) - pénalité_fin` (ex: -1, -10, paramétrable)
- gérer transitions inconnues :
  - “mur d’inconnu” : arrêt, retour pénalisé
  - ou fallback : “stay” (z_{t+1} = z_t) avec pénalité (au choix)
- produire des métriques de rollout :
  - taux d’arrêt par inconnu
  - profondeur moyenne atteinte
  - diversité des états imaginés

**expérience** :  
choisir quelques états réels (observations) et visualiser :
- les 20 rollouts imaginés (suite de latent_id)
- la distribution des retours imaginés par action

---

### section 4.5 — première planification (MPC tabulaire)
On vise une planification simple, mesurable, et compréhensible :

Pour chaque action candidate `a ∈ {haut, bas, gauche, droite}` :
- lancer K rollouts de profondeur H en fixant `a` au premier pas
- puis politique par défaut pour les pas suivants (ex: aléatoire ou greedy sur P(survie))
- estimer `E[G | a]`
- choisir `argmax_a E[G | a]`

C’est un **Model Predictive Control** “monte-carlo”, mais 100% tabulaire.

**expériences** :
1) *ablation* : comparer (K,H) = (5,5), (20,10), (50,15)  
   - stabilité de la décision
   - coût CPU
2) comparaison agents :
   - agent aléatoire
   - agent curiosité (cours 1–2)
   - agent planif (cours 4)  
   métriques : score moyen, longueur moyenne, taux de mort précoce, etc.

---

### section 4.6 — limites observables et transitions vers cours 5
On veut terminer le cours 4 en montrant *pourquoi* on ira vers un cours 5.

Limites attendues (mesurables) :
- le latent discret compresse : aliasing → récompense imprécise
- le modèle tabulaire ignore certains facteurs (ex: direction actuelle si elle n’est pas dans le latent)
- rollouts dérivent (distribution multi-modale → explosion de variance)

➡️ motive :
- planification plus structurée (A*, MCTS)
- amélioration du latent (plus informatif)
- gestion explicite de l’incertitude (value of information)

---

## 3) extensions minimales nécessaires du code existant

On vise des ajouts simples, sans refactor large, et compatibles avec l’existant.

### 3.1 nouveau “simulateur interne” (agent_service)
**nouveaux modules (proposés)**

- `services/agent_service/app/modele_monde/simulateur_interne_v1.py`  
  - `SimulateurInterneV1.step(z, action) -> (z1, delta_score, termine, debug)`  
  - sampling sur distribution tabulaire  
  - RNG seedable

- `services/agent_service/app/modele_monde/recompense_tabulaire_v1.py`  
  - compte `delta_score` conditionné sur `(z, a, z1)`  
  - expose distribution + espérance

- `services/agent_service/app/modele_monde/termination_tabulaire_v1.py`  
  - compte `termine` conditionné sur `(z, a, z1)`  
  - expose `proba_termine`

### 3.2 extension de l’apprentissage offline
Dans `entrainement_depuis_journal.py`, ajouter une fonction “cours4” :

- itérer transitions `(prev_evt, evt, z_prev, z, action)`
- calculer :
  - `delta_score = evt["score"] - prev_evt["score"]`
  - `termine = evt["termine"]`
- apprendre les modèles additionnels

=> aucun changement sur le simulateur réel / runner.

### 3.3 un nouvel agent “planif_tabulaire”
Ajouter un agent minimal (même style que `AgentCuriositeTabulaire`) :

- `services/agent_service/app/agents/agent_planif_tabulaire.py`
  - construit/charge le simulateur interne (modèles tabulaires)
  - paramètres :
    - `K` (nb rollouts), `H` (horizon)
    - `penalite_fin`, `penalite_inconnu`
    - `mode_latent` (checksum / discret / latent_id si on veut)
  - décision : `argmax_a E[G | a]`

### 3.4 instrumentation / expériences reproductibles
- ajouter un script CLI (dans `agent_service/app/modele_monde/`) :
  - `evaluer_rollouts_v1.py` : compare rollouts imaginés vs transitions réelles
- ajouter un mode `ui_cli --agent planif_tabulaire`
- produire des artefacts jsonl :
  - `artefacts/rollouts_imagines.jsonl` (traçage des trajectoires)

---

## 4) définition “concrète” de la première itération (ce qu’on fera au prochain diff)

Pour rester itératif et minimal, la **prochaine étape** (diff #1) peut se limiter à :

1) créer les classes tabulaires `recompense_tabulaire_v1` et `termination_tabulaire_v1`  
2) créer `simulateur_interne_v1.step()` + `rollout()`  
3) ajouter l’agent `AgentPlanifTabulaire` (sans intégration UI_tui, uniquement `ui_cli`)  
4) ajouter un petit test unitaire (smoke) : “un rollout ne plante pas et retourne une trajectoire de longueur <= H”.

Ensuite seulement :
- on instrumente plus finement,
- on ajoute les expériences et comparaisons d’agents.

---

## 5) checklist de cohérence avec cours 1 à 3

- même séparation des rôles (runner = réel, agent_service = interne)
- même principe “offline depuis journal”
- métriques observables et artefacts rejouables
- aucune magie end-to-end : tout est tabulaire ou linéaire + k-means, déjà assumé

---

## annexe — fichiers clés repérés dans le zip (pour navigation rapide)

- world model tabulaire : `services/agent_service/app/modele_monde/tabulaire_v1.py`
- apprentissage offline : `services/agent_service/app/modele_monde/entrainement_depuis_journal.py`
- évaluation tabulaire : `services/agent_service/app/modele_monde/evaluer_tabulaire_v1.py`
- encodeur contrastif : `services/agent_service/app/modele_monde/encodeur_contrastif_v1.py`
- recodage latent appris : `services/agent_service/app/modele_monde/recoder_journal_latent_v1.py`
- batch runner : `services/ui_cli/app/main.py`
- journal réel : `services/runner/app/journal_v2.py`
