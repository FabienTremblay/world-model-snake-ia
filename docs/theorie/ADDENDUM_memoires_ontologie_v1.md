# Addendum — Mémoire (instance) vs Ontologie (partagée) — v1

Date : 2026-03-04

## Décision

- **Mémoire courte** : état épisodique, interne à l'instance (individu).
- **Mémoire longue** : consolidation individuelle, interne à l'instance (individu).
- **Registre épistémique** : objet partagé en entraînement, sert à déclarer classes et cas d'entraînement.
- **Ontologie** : structure conceptuelle stabilisée par entraînement (et donc intégrée via paramètres / conventions), **distincte** de la mémoire longue.

## Règle

En mode arène/épreuve :
- aucun apprentissage (poids figés)
- l'individu peut ne produire **aucun événement** (inaction dérivable à l'analyse)

En mode entraînement :
- le registre épistémique produit les jeux d'entraînement
- mise à jour des paramètres neuronaux et conventions
