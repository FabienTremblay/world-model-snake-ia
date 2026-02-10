# runner

Le **runner** exécute une expérience (arène + agent + règles) et produit un **journal d’épisodes** (`journal_episodes.jsonl`) exploitable pour :
- diagnostics,
- relecture (replay),
- entraînement (world models / agents).

---

## responsabilités (ce que le runner fait)

- charger une expérience (arène, paramètres d’exécution, seed)
- instancier un agent (selon l’incarnation demandée)
- exécuter les ticks (boucle principale)
- produire un journal `journal_episodes.jsonl` (un événement par tick)
- gérer la sortie des artefacts (stdout.log, résumé, etc.)

## non-responsabilités (ce que le runner ne doit pas faire)

- **ne pas contenir** de logique de jeu (murs, nourriture, fin, score) : c’est `world_sim`
- **ne pas décider** de la stratégie de l’agent : c’est l’agent
- **ne pas inventer** de métriques ad hoc : ce sont les diagnostics/analyses

Il doit rester **rigoureux et neutre**.

---

## perception : le runner orchestre, l’instrument observe

Dans ce projet, l’agent n’accède pas au monde « directement » : il reçoit une **observation** produite par un **instrument**.

- `world_sim` fournit un **état canonique** du monde (snapshot / état complet nécessaire à la perception).
- `instrument` transforme cet état canonique en **observation** (ex. caméra estrade absolue, caméra égocentrée orientée).
- le runner **orchestre** : pour chaque tick, il demande au monde un état canonique, le passe à l’instrument, puis journalise l’observation.

> objectif : rendre explicite la chaîne *monde → instrument → observation → agent → action*.

---

## journal d’épisodes : format sans compat (episodes_v2)

Le journal n’est pas seulement « l’action + des pixels ». Il doit porter :
- l’état canonique (ou sa forme minimale),
- la(les) observation(s) produite(s) par instrument,
- les métadonnées permettant de comprendre et rejouer.

### structure recommandée d’un tick (v2)

Champs minimaux :

- `run_id`, `episode_id`, `tick`
- `action` : action appliquée pour produire le tick observé
- `etat` : snapshot canonique (largeur/hauteur, positions, direction, objets)
- `observations` : liste d’observations (une par instrument)

Chaque observation :

- `instrument_id` : ex. `camera_estrade_absolue_v1`, `camera_egocentree_v1`
- `repere` : `absolu` | `egocentre`
- `params` : paramètres effectifs (rayon, fov, bruit, etc.)
- `capteurs_format` : ex. `pixels_b64_v1`
- `capteurs_compact` : payload compacté (base64)
- `meta_observation` : optionnel (checksum, stats, etc.)

> ce format casse volontairement la compatibilité : on assume que nous sommes encore en phase de découverte.

---

## noyau partagé : `runner.app.noyau`

Le noyau vit dans :

- `services/runner/app/noyau.py`

Il expose :

- `ParametresExecution` : nombre d’épisodes, ticks max, variation du seed par épisode
- `executer_episodes_headless(...)` : exécution batch / headless

### convention temporelle (action vs tick)

- tick `0` : observation initiale (pas d’action appliquée)
- tick `t>0` : le journal porte l’action qui a été **appliquée** pour passer du tick `t-1` au tick `t`

Cette convention est indispensable pour :
- aligner décision (avant `step`) et observation (après `step`)
- conserver des replays et diagnostics non ambigus
