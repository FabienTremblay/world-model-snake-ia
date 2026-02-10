# Bac à sable (expérience) — structure et usage

Une **expérience** (bac à sable) est une manière de regrouper :

- la configuration (le *quoi* et le *comment* on exécute)
- les artefacts produits (journaux, métriques, stdout, etc.)

…dans un répertoire unique, afin de pouvoir répéter, comparer, archiver.

## Emplacement

Un bac à sable vit sous :

```
donnees/config/experiences/<experience_id>/
  experience.yml
  artefacts/
    runs/
      <run_id>/
        journal.jsonl
        stdout.log
        meta.json
        metrics.jsonl   # optionnel
```

Le ui_cli **crée automatiquement** ce squelette si vous lancez une expérience qui n'existe pas.

## Lancer un run dans une expérience

Exemple (création automatique du bac à sable si absent) :

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours5 \
  --arene cours5_tiny_planification \
  --agent planif_mpc_observateur_tabulaire \
  --latent signaux_percus_hash_v1 \
  --episodes 200 --max-ticks 2000 --seed 123 \
  --capture-stdout
```

### Ce que le ui_cli fait

- résout `donnees/config/experiences/cours5/`
- crée `artefacts/runs/<run_id>/`
- écrit par défaut le journal dans `journal.jsonl`
- si `--capture-stdout` : écrit aussi `stdout.log`
- écrit `meta.json` (paramètres résolus)

## `experience.yml`

Ce fichier sert de **point d'ancrage** pour l'expérience. Au stade actuel, le ui_cli :

- le crée s'il manque (template minimal)
- n'en consomme pas encore les champs pour injecter des défauts

Mais on garde la place pour la suite (ex.: défauts, listes de runs attendus, variantes, etc.).

## Bonnes pratiques

- Une expérience = une intention claire (ex.: `cours5_signauxhash`, `cours5_trainmix`, `cours5_recompense`).
- Ne pas réutiliser un même `run_id`.
- Si vous comparez deux approches : deux expériences, ou deux `run_tag` distincts.
ences/cle_ou_nom_experience/
  experience.yml
  artefacts/
    runs/
      <run_id>/
        journal.jsonl
        stdout.log
        meta.json
        metrics.jsonl
```

`<run_id>` est un identifiant unique (par défaut : `time.time_ns()`), ce qui évite d'écraser les résultats.

## Lancer une expérience

Commande typique :

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours5 \
  --arene cours5_tiny_planification \
  --agent planif_mpc_observateur_tabulaire \
  --latent signaux_percus_hash_v1 \
  --episodes 200 --max-ticks 2000 --seed 123 \
  --capture-stdout
```

Effets :

- crée `donnees/config/experiences/cours5/` s'il n'existe pas
- crée un nouveau `artefacts/runs/<run_id>/`
- écrit par défaut le journal dans `journal.jsonl`
- si `--capture-stdout` est activé, écrit aussi `stdout.log`
- écrit `meta.json` (paramètres résolus)

## Structure de `experience.yml`

Le fichier `experience.yml` sert d'ancrage : il identifie l'expérience et peut porter des valeurs par défaut.

Exemple minimal :

```yaml
experience_id: cours5

defauts:
  arene: cours5_tiny_planification
  agent: aleatoire
  latent: checksum
  episodes: 200
  max_ticks: 2000
  seed: 123
  niveau_bruit: 0
```

> Dans la version actuelle, le ui_cli **n'applique pas encore** automatiquement les `defauts` du YAML.
> Le YAML est surtout un repère stable + un futur point d'intégration. Le CLI reste la source de vérité.

## Pourquoi ce design ?

- **Reproductibilité** : chaque run est isolé
- **Lisibilité** : on n'a plus un répertoire `artefacts/` global qui mélange tout
- **Traçabilité** : `meta.json` reconstitue l'exécution

## Nettoyage / archivage

Comme tout est regroupé par expérience et par run, tu peux :

- supprimer un run : `rm -rf .../artefacts/runs/<run_id>`
- archiver un run : `tar -czf run_<run_id>.tgz .../artefacts/runs/<run_id>`

.main \
  --experience cours5 \
  --arene cours5_tiny_planification \
  --agent planif_mpc_observateur_tabulaire \
  --latent signaux_percus_hash_v1 \
  --episodes 200 --max-ticks 2000 --seed 123 \
  --capture-stdout
```

Ce que fait le `ui_cli` quand `--experience` est présent :

1. crée si besoin `donnees/config/experiences/<experience>/`
2. crée `artefacts/runs/<run_id>/`
3. résout les chemins de sortie (journal, metrics, stdout, meta)
4. affiche ces chemins dans stdout

## Options CLI ajoutées

- `--experience <id>` : active le mode bac à sable
- `--run-tag <texte>` : optionnel, ajoute un suffixe lisible au `run_dir`
- `--capture-stdout` : écrit `stdout.log` dans le `run_dir` (en plus de l'affichage console)

## Structure de `experience.yml`

Le fichier `experience.yml` est un mémo de *configuration*. Le code actuel ne le lit pas encore (c'est volontairement une étape 2), mais il sert de :

- document de référence
- point d'ancrage pour des valeurs par défaut futures (ex. `defauts.*`)

Exemple minimal :

```yml
experience_id: cours5

defauts:
  arene: cours5_tiny_planification
  agent: aleatoire
  latent: checksum
  episodes: 200
  max_ticks: 2000
  seed: 123
  niveau_bruit: 0
```

## Artefacts produits

- `journal.jsonl` : événements tick-by-tick (entrée principale pour les scripts de diagnostic / recodage)
- `metrics.jsonl` : métriques agrégées (si activé)
- `stdout.log` : sortie de run (si `--capture-stdout`)
- `meta.json` : paramètres résolus (utile pour reproduire)
6. écrit un `meta.json` (paramètres effectifs)

### Options ajoutées

- `--experience <id>` : active le bac à sable
- `--run-tag <texte>` : ajoute un suffixe lisible au répertoire de run (ex. `2026-02-02_14h31_mpc_v2`)
- `--capture-stdout` : enregistre stdout/stderr dans `stdout.log` (tout en gardant l'affichage console)

## Format `experience.yml`

Le format est volontairement minimal au départ :

```yaml
experience_id: cours5

defauts:
  arene: cours5_tiny_planification
  agent: aleatoire
  latent: checksum
  episodes: 200
  max_ticks: 2000
  seed: 123
  niveau_bruit: 0
```

Aujourd'hui, `ui_cli` **ne lit pas encore** ces défauts : le fichier sert de documentation et de point d'ancrage du bac à sable.
Quand on fera évoluer l'architecture, on pourra faire en sorte que `ui_cli` charge ces défauts et n'exige plus autant d'arguments.

## Artefacts produits

- `journal.jsonl` : un événement JSON par tick
- `metrics.jsonl` : métriques optionnelles (si `--metrics` ou créé via bac à sable)
- `stdout.log` : sortie console capturée (si `--capture-stdout`)
- `meta.json` : paramètres et chemins résolus
 moment :

- `experience_id` : identifiant (informatif)
- `defauts` : valeurs par défaut suggérées

Le `ui_cli` ne consomme pas encore ces valeurs pour surcharger automatiquement la ligne de commande (on pourra le faire dans une itération suivante). Pour l'instant, le fichier sert :

- de documentation locale
- de “contrat” de reproductibilité

## Bonnes pratiques

- Un run = un répertoire. Ne réutilise pas le même run pour “corriger” une expérience : relance et compare.
- Donne un `--run-tag` lorsque tu fais des variantes (ex. `murfix`, `signauxhash`, `trainmix`).
- Garde le `meta.json` : c'est ce qui te permet d'expliquer les stdout dans tes schémas.
