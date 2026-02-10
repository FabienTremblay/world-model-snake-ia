# migration vers `agent_runtime` (cours 5)

## but

Stabiliser une frontière « agents en arène » vs « agents d’estrade » et préparer :
- l’introduction d’approches plug-in,
- l’introduction de tempéraments orthogonaux,
- des traces de décision exploitables par l’épistémique (estrade),
- la séparation **monde canonique** (`world_sim`) vs **perception instrumentée** (`instrument`).

## clarification : point de vue local = cible, pas état actuel

Le design cible des agents en arène est un **point de vue incarné** (perception egocentrée orientée).
À ce stade, l’observation effectivement journalisée peut encore être une projection absolue ; la migration vise à rendre ce point explicite via `instrument` + journal d’épisodes traçable.

## stratégie

- Les modules de cours 4 restent dans `agent_service.app.agents.*` pour historique.
- `agent_runtime.agents_in_arene.*` ré-exporte ces implémentations afin d’éviter de casser l’existant.
- Les nouveaux contrats et points d’extension sont introduits dans `agent_runtime.*` (approches, traits, incarnation).

## étapes (résumé)

1. introduire `instrument` : caméra estrade absolue et caméra egocentrée
2. déplacer la projection hors de `world_sim` (le monde fournit un état canonique)
3. faire évoluer `journal_episodes.jsonl` vers un format non compatible (episodes_v2) :
   - état canonique
   - observations[] avec instrument_id/repere/params
4. brancher le choix de l’instrument dans la définition d’agent (yaml d’agent) — discuté plus tard
