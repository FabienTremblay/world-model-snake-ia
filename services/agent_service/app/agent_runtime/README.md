# agent_runtime (cours 5)

Ce package introduit une frontière explicite : **agents en arène** (point de vue local)
vs **agents d'estrade** (épistémique, hors de l'arène).

## Sous-packages

- `agents_in_arene/` : agents qui observent localement (ex. 180°) et agissent.
- `approches/` : briques de décision (plug-ins) réutilisables par plusieurs agents.
- `traits/` : traits de tempérament (prudence, curiosité, etc.).

## Compatibilité / migration

Les implémentations existantes (cours 4) vivent dans `agent_service.app.agents.*`.
Pour éviter une rupture brutale, les modules d'`agents_in_arene` peuvent **ré-exporter**
ou **adapter** ces classes existantes.

Le but du cours 5 est de stabiliser les frontières pour pouvoir :
- brancher des "tempéraments" de façon orthogonale,
- introduire des traces explicables par tick,
- et laisser l'épistémique (estrade) consommer des artefacts sans agir dans l'arène.
