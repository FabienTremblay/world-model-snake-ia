# runner

le **runner** exécute une expérience (arène + agent + règles) et produit des **artefacts** rejouables :
- diagnostics,
- relecture (replay),
- entraînement (world models / agents).

---

## responsabilités

- charger une expérience (arène, paramètres d’exécution, seed)
- instancier un agent (depuis le catalogue `agent_service`)
- exécuter les ticks (boucle principale)
- produire un **journal v2** (sans compat) + **meta.json**
- gérer la sortie des artefacts (stdout.log, métriques, etc.)

## non-responsabilités

- **ne pas contenir** de logique de jeu (murs, nourriture, fin, score) : c’est `world_sim`
- **ne pas décider** de la stratégie de l’agent : c’est l’agent
- **ne pas définir** les métriques d’analyse : ce sont les diagnostics

---

## perception : le runner orchestre, l’instrument observe

l’agent n’accède pas au monde « directement » : il reçoit une **observation** produite par un **instrument**.

chaîne explicite :

`monde canonique (world_sim) → instrument(s) → observation(s) → agent → action`

- `world_sim` fournit un **état canonique** (snapshot) consumé par les instruments.
- `instrument` transforme cet état canonique en observation (ex. caméra estrade absolue, caméra égocentrée, gps).
- le runner orchestre et journalise.

---

## artefacts du runner (journal v2)

un run produit un répertoire :

```
<experience_dir>/artefacts/runs/<run_id>/
  meta.json
  journal.jsonl
  obs/
    ...
  stdout.log      # si --capture-stdout
  metrics.jsonl   # optionnel
```

### `meta.json`

`meta.json` est la **source de vérité** pour rejouer :
- paramètres résolus (bac à sable),
- seeds,
- identifiants arène / agent,
- liste des instruments + paramètres effectifs.

> principe : si un paramètre influence le run, il doit apparaître dans `meta.json`.

### `journal.jsonl`

un événement JSON par tick.

champs clés (tick-level) :
- `episode_id`, `tick`
- `monde` : état canonique minimal (rejouable/validable)
- `decision` : action appliquée
- `perception` : observations par instrument

exemple (schéma, pas une spec exhaustive) :

```json
{
  "episode_id": 0,
  "tick": 3,
  "monde": {
    "largeur": 12,
    "hauteur": 8,
    "serpent": [[1,4],[1,3],[1,2]],
    "direction": "droite",
    "nourritures": [[5,6]],
    "porte": {"pos": [2,2], "ouverte": true},
    "score": 0,
    "longueur": 3,
    "termine": false,
    "raison_fin": null
  },
  "decision": {"action": "droite"},
  "perception": {
    "instruments": {
      "gps_v1": {"payload": {"tete": [1,2]}},
      "camera_egocentree_v1": {"payload_ref": "obs/ep0000/t0003/camera_egocentree_v1.npz"}
    }
  }
}
```

### `obs/`

dossier des **payloads lourds** référencés depuis `journal.jsonl`.

- caméra : fichier `.npz` (ou `.npy`) contenant la matrice de pixels (et éventuellement du debug)
- gps : reste un petit payload JSON inline (pas dans `obs/`)

---

## convention temporelle (action vs tick)

- tick `0` : observation initiale (pas d’action appliquée)
- tick `t>0` : le journal porte l’action qui a été **appliquée** pour passer du tick `t-1` au tick `t`

cette convention est indispensable pour aligner :
- décision (avant `step`) et observation (après `step`)
- replays et diagnostics non ambigus
