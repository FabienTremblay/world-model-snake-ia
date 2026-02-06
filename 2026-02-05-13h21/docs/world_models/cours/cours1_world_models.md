# World Models — Cours 1  
## Exploration, états latents et couverture

### Objectif pédagogique
Comprendre ce qu’est un *world model* avant toute notion de deep learning :
- apprendre la dynamique locale du monde
- mesurer ce qui est connu vs inconnu
- observer les limites d’un état latent trop discriminant

---

## Contexte expérimental
- Environnement : Snake (runner)
- Agent : explorateur (aléatoire ou curiosité tabulaire)
- Observation : capteurs bruts
- État latent v1 : checksum(capteurs)
- Modèle du monde : tabulaire (lookup)

---

## Étape 1 — Génération des données (CLI headless)

### Commande (agent aléatoire)
```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 200 \
  --max-ticks 2000 \
  --agent aleatoire \
  --seed 123 \
  --truncate \
  --journal artefacts/episodes.jsonl
```

### Commande (agent curiosité tabulaire)
```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 200 \
  --max-ticks 2000 \
  --agent curiosite_tabulaire \
  --epsilon 0.05 \
  --seed 123 \
  --truncate \
  --journal artefacts/episodes.jsonl \
  --metrics artefacts/exploration_metrics.jsonl
```

---

## Étape 2 — Évaluation du world model (offline)

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes.jsonl \
  --mode split \
  --ratio-train 0.7
```

---

## Indicateurs observés
- **Couverture** : proportion des couples (etat_latent, action) déjà connus
- **Exactitude conditionnelle** : exactitude quand la clé est connue
- **Support** : nombre d’occurrences par clé
- **Entropie** : incertitude sur l’état suivant

---

## Observation clé
- Exactitude = 1.0 quand connu
- Entropie = 0.0
- Couverture limitée (~35–40%)

### Interprétation
L’état latent (checksum) est trop spécifique :
- il mémorise parfaitement
- il généralise très peu
- le bruit crée de nouveaux états

---

## Conclusion du cours 1
> Un world model tabulaire basé sur un état latent trop discriminant apprend
> parfaitement ce qu’il connaît, mais connaît peu de choses.

Cela motive le **cours 2 : apprendre un état latent invariant**.
