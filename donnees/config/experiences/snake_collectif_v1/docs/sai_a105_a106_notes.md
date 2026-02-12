# snake_collectif_v1 — SAI-A105 / SAI-A106 (notes opérationnelles)

## SAI-A105 — analyser résultats (diagnostic)

### Entrées disponibles (observé)
Dans `journal.jsonl` (tick-level) on a typiquement :
- `episode_id`, `tick`, `action` (ex.: "droite", "bas"), `score`, `termine`, `raison_fin`, `largeur`, `hauteur`, `capteurs_compact`, etc.

Dans `metrics.jsonl` on a :
- `checksum_avant`, `checksum`, `action` (mêmes libellés), `episode_id`, `tick`.

### Problème actuel visible
Sur l’extrait fourni :
- `score = 0` constant
- `termine = false` et `raison_fin = null` (même fin d'épisode)
- épisodes courts côté metrics (ex.: épisode 50 tick 24) → **fin par coupure / reset**, pas fin "déclarée".

### Diagnostic recommandé
On utilise `metrics.jsonl` comme proxy de "couverture" (exploration):
- nb d'états uniques (`checksum`) par épisode
- ratio stationnaire (`checksum == checksum_avant`)
- entropie des actions

Lancer :
```bash
python donnees/config/experiences/snake_collectif_v1/outils/a105_diagnostic_snake_collectif_v1.py
```

Sorties :
- `donnees/config/experiences/snake_collectif_v1/artefacts/analyses/a105_diagnostic_par_run.csv`
- `donnees/config/experiences/snake_collectif_v1/artefacts/analyses/a105_diagnostic_global.csv`

---

## SAI-A106 — produire hypothèses (à partir du diagnostic)

### Hypothèses plausibles (à tester, pas à croire)
1) **Vocabulaire d’actions** : le moteur attend "haut|bas|gauche|droite".
   Si un agent envoie N/E/S/W, il peut bouger "par hasard" ou être ignoré.
2) **Fin d’épisode non journalisée** : l’épisode est coupé (budget ticks / reset) mais `termine` n'est pas mis à true.
3) **Nourriture** : rare/inatteignable → score reste à 0.
4) **Boucles** : ratio stationnaire élevé (actions non effectives) → collision évitée mais pas de progression.

### Expériences minimales
- Comparer **fourmi vs aleatoire** sur `etats_uniques_moyen` et `ratio_stationnaire`.
- Ensuite: arène `eval` plus "mangeable" pour produire `score>0`.

### Sortie attendue
Un tableau "hypothèses → tests → métriques → conclusion".
