# Migration vers `agent_runtime` (cours 5)

## But
Stabiliser une frontière "agents en arène" (point de vue local) et préparer :
- l'introduction d'approches plug-in,
- l'introduction de tempéraments orthogonaux,
- des traces de décision exploitables par l'épistémique (estrade).

## Stratégie
- Les modules de cours 4 restent dans `agent_service.app.agents.*` pour historique.
- `agent_runtime.agents_in_arene.*` ré-exporte ces implémentations afin d'éviter de casser l'existant.
- Les nouveaux contrats/extensions (TraceDecision, IAgentEnArene) vivent dans `agent_runtime`.

## Mapping
- `agent_service.app.agents.contrats` → `agent_runtime.agents_in_arene.contrats` (copie + extensions)
- `agent_service.app.agents.agent_aleatoire` → `agent_runtime.agents_in_arene.agent_aleatoire`
- `agent_service.app.agents.agent_curiosite_tabulaire` → `agent_runtime.agents_in_arene.agent_curiosite_tabulaire`
- agents planificateurs : wrappers présents, non exportés par défaut.

## Prochaine étape (cours 5)
Déplacer progressivement l'implémentation source vers `agent_runtime` quand :
- l'API des traces est stabilisée,
- l'orchestrateur (ui_cli) écrit les traces dans le journal,
- et les tests sont au vert.
