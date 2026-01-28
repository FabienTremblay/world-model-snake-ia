# ui_cli — exécution headless (batch) pour génération de journaux

ce service fournit une entrée cli pour exécuter des épisodes snake sans interface (headless),
afin de générer des journaux compatibles avec le mode live (ui_tui) et les outils d’évaluation
du world model.

## objectifs

- produire `artefacts/episodes.jsonl` au format canonique
- permettre des campagnes reproductibles (`--seed`)
- supporter différents agents (`aleatoire`, `curiosite_tabulaire`, etc.)
- servir d’outil pédagogique : comparer exploration vs apprentissage du world model

## prérequis

depuis la racine du projet :

- python disponible
- `PYTHONPATH=services`

## usage

### génération de données (agent aléatoire)

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 500 \
  --max-ticks 2000 \
  --agent aleatoire \
  --seed 123 \
  --journal artefacts/episodes.jsonl
```

### génération de données (agent curiosité tabulaire)

cet agent tente de maximiser la couverture des couples (etat_latent, action) et/ou de réduire
l’incertitude (entropie) du modèle tabulaire.

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 500 \
  --max-ticks 2000 \
  --agent curiosite_tabulaire \
  --epsilon 0.05 \
  --seed 123 \
  --journal artefacts/episodes.jsonl \
  --metrics artefacts/exploration_metrics.jsonl
```

## paramètres

- `--arene` : chemin vers une arène `.yml`, ou id d’arène (ex: `demo_v0`)
- `--episodes` : nombre d’épisodes à exécuter
- `--max-ticks` : nombre maximal de ticks par épisode (sécurité)
- `--agent` : `aleatoire` | `curiosite_tabulaire`
- `--seed` : graine de reproductibilité (si fournie)
- `--seed-episode` : (optionnel) dérive la seed par épisode (`seed + episode_id`)
- `--niveau-bruit` : (optionnel) override du niveau de bruit de l’arène
- `--journal` : chemin de sortie du journal `episodes.jsonl`
- `--metrics` : (optionnel) chemin de sortie d’un journal de métriques d’exploration

## sorties

### journal principal : episodes.jsonl

le fichier `episodes.jsonl` est identique au format produit en mode live (ui_tui).
convention importante :

- tick 0 : `action = null` (observation initiale)
- tick t>=1 : `action[t]` est l’action appliquée pour passer de (t-1) à t

ce format est consommé directement par l’outil :

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes.jsonl \
  --mode split \
  --ratio-train 0.7
```

### journal optionnel : exploration_metrics.jsonl

si `--metrics` est fourni, une ligne par tick est enregistrée pour expliquer le choix d’action.
champs typiques :

- `episode_id`, `tick`, `action`
- `checksum_avant`, `checksum`
- `cle_connue` (couple (checksum_avant, action) connu du modèle ?)
- `confiance`, `entropie`, `support` (si disponible)

## recommandations

- pour obtenir une couverture non nulle avec un modèle tabulaire, exécuter beaucoup d’épisodes
  (ex. 200 à 2000) afin de revisiter des états et répéter des couples (etat, action)
- comparer `aleatoire` vs `curiosite_tabulaire` à budget de ticks égal
