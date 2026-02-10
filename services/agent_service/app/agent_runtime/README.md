# agent_runtime

Ce package regroupe les agents « cours 5 » et stabilise la frontière entre :
- agents **en arène** (incarnés),
- agents **d’estrade** (épistémiques, hors-arène).

## sous-packages

- `agents_in_arene/` : agents incarnés, qui décident à partir d’une **observation** (produite par un instrument)
- `approches/` : briques de décision (plug-ins) réutilisables
- `traits/` : tempéraments et paramètres normatifs (orthogonaux au point de vue)

## note importante (état actuel vs cible)

La cible du cours 5 est d’équiper les agents en arène d’une observation **égocentrée orientée**.

À ce stade du projet, une partie des runs journalisent encore une observation **absolue (estrade)**.
La séparation nette se fait via un package `instrument` (caméra estrade vs caméra egocentrée) et un journal d’épisodes traçable.
