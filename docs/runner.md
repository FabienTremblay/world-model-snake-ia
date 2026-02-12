# runner

Le **runner** exécute une expérience (arène + agent + règles) et produit un **journal** (`journal.jsonl`) exploitable pour :
- diagnostics,
- relecture (replay),
- entraînement (world models / agents).

---

## responsabilités (ce que le runner fait)

- charger une expérience (arène, paramètres d’exécution, seed)
- instancier un agent (selon l’incarnation demandée)
- exécuter les ticks (boucle principale)
- produire un journal `journal.jsonl` (un événement par tick)
- gérer la sortie des artefacts (stdout.log, meta.json, etc.)

## non-responsabilités (ce que le runner ne doit pas faire)

- **ne pas contenir** de logique de jeu (murs, nourriture, fin, score) : c’est `world_sim`
- **ne pas décider** de la stratégie de l’agent : c’est l’agent
- **ne pas inventer** de métriques ad hoc : ce sont les diagnostics/analyses

Il doit rester **rigoureux et neutre**.

---

## perception : le runner orchestre, l’instrument observe

Dans ce projet, l’agent n’accède pas au monde « directement » : il reçoit une **observation** produite par un **instrument**.

- `world_sim` fournit un **état canonique** du monde (snapshot complet / rejouable).
- `instrument` transforme cet état canonique en **observation** (ex. caméra estrade absolue, caméra égocentrée orientée, gps).
- le runner **orchestre** : à chaque tick, il récupère l’état canonique, passe cet état aux instruments, puis journalise.

> objectif : rendre explicite la chaîne *monde → instrument → observation → agent → décision → action*.

---

## journal : format sans compat (`journal_v2`)

Le journal n’est pas seulement « l’action + des pixels ». Il doit porter :

- l’état canonique (ou sa forme minimale),
- la décision de l’agent,
- les observations produites par instrument,
- les métadonnées permettant de **comprendre** et **rejouer**.

### structure d’un tick (v2)

Champs minimaux :

- `schema` : `journal_v2`
- `run_id`, `episode_id`, `tick`, `ts_ns`
- `monde_canonique` : snapshot du monde (largeur/hauteur, serpent, direction, nourritures, porte, score, termine, raison_fin, etc.)
- `decision` : ce que l’agent renvoie (au minimum `action`)
- `observations` : dictionnaire `{instrument_id: observation}`

Notes importantes :

- les observations peuvent être **légères** (ex. gps) ou **lourdes** (ex. caméra). Pour les payloads lourds, le journal peut contenir un pointeur (fichier) plutôt que les pixels inline.
- ce format casse volontairement la compatibilité : on assume que nous sommes encore en phase de découverte.

---

## noyau partagé : `runner.app.noyau`

Le noyau vit dans :

- `services/runner/app/noyau.py`

Il expose :

- `ParametresExecution` : nombre d’épisodes, ticks max, variation du seed par épisode
- `executer_episodes_headless(...)` : exécution batch / headless

### convention temporelle (action vs tick)

- l’observation et l’état canonique sont ceux **après** l’application de la décision `decision.action` pour produire le tick `t`.
- autrement dit : `decision.action` est l’action qui a été appliquée pour arriver à l’état journalisé au tick `t`.
---

## sélection d’agent via catalogue plug-ins (ajout v1)

L’instanciation d’un agent doit passer par l’API stricte :

```python
creer_agent(nom, params=...)
```

Le runner ne doit pas connaître la nature des agents (ni leurs classes), ni contenir un `if/elif` par agent.
Les agents disponibles sont chargés depuis un catalogue YAML.

- répertoire scanné : `services/agent_service/app/agents/`
- fichiers découverts : `agent*.yml`
- champ clé : `fabrique: module:callable`

### prérequis

Certains agents exigent des prérequis (ex. journaux d’entraînement).
Ces prérequis doivent être fournis via :
- `params`
- ou variables d’environnement (ex. `SNAKE_MODELE_JOURNAL`)

Si les prérequis manquent, l’agent doit refuser explicitement (exception claire).
