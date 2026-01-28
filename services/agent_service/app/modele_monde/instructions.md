# Comment l’exécuter (depuis la racine)
Évaluation split (recommandée pour présenter le concept)
```
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes.jsonl \
  --mode split \
  --ratio-train 0.7
```

évaluation online (pédagogie “prédire puis corriger”)

```
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes.jsonl \
  --mode online
```

sans écrire le jsonl détaillé

```
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes.jsonl \
  --sans-out
```

## Ce que tu vas pouvoir expliquer, preuves à l’appui

modèle du monde = estimation empirique de la dynamique :

(z_t, a_t) -> distribution(z_{t+1})

z_t (état latent v1) = checksum(capteurs) (déterministe, traçable)

incertitude = entropie (plusieurs successeurs possibles)

confiance = probabilité empirique du meilleur successeur

couverture = proportion de transitions où le modèle avait déjà appris la clé (z_t, a_t)
