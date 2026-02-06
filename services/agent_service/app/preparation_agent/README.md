# préparation d'un agent-personne (sai-a107)

ce package implémente le squelette du pipeline **sai-a107 préparer un agent**.

objectif :
- produire un artefact **agent-personne** (identité cognitive) qui pourra ensuite être
  **incarné** et éprouvé en arène via **sai-a108**.

ce module est **offline** :
- pas de boucle "tick -> action" ici (c'est `agent_runtime`)
- ici, on assemble et on entraîne des composantes (tronc + têtes)

## concepts clés

### tronc
représentation commune (encodeur + mémoire). c'est la base sur laquelle se branchent les têtes.

### tête spécialisée
un slot déclaratif :
- type de sortie (classification, score, gate, policy)
- supervision (labels/pseudo-labels/auto-supervision)
- influence (comment la tête module la décision)

### catalogue de têtes
ensemble versionné des têtes candidates / sélectionnées.

### agent-personne
artefact produit :
- référence tronc
- liste des têtes instanciées
- gouvernance (intentions + règles d'influence)
- pointeurs vers poids

## artefacts attendus (bac-à-sable)

dans l'esprit de tes conventions `donnees/config/experiences/<exp>/artefacts/` :

- `artefacts/catalogues/catalogue_tetes.json`
- `artefacts/agent_personne/<agent_personne_id>.json`
- `artefacts/runs_preparation/<agent_personne_id>/...` (logs, checkpoints)
- `artefacts/rapports_preparation/<agent_personne_id>.json`

le **résolveur bac-à-sable** peut fournir ces chemins au `PlanPreparationAgent.chemins`.

## api du prototype

- `assembler_agent_personne(plan, catalogue) -> AgentPersonne`
- `entrainer_agent_personne(plan, agent) -> (AgentPersonne, RapportEntrainement)`
- `preparer_agent_personne(plan, catalogue) -> (AgentPersonne, RapportEntrainement)`

dans ce prototype :
- l'entraînement est simulé (pas de torch)
- le but est de figer les contrats et la trajectoire d'artefacts

## prochaine itération (prévue)
- intégrer la lecture du registre épistémique v2 pour aider à construire le catalogue
- brancher un backend torch minimal (un tronc + une tête classification)
- écrire les artefacts dans les répertoires d'expérience
- ajouter une commande ui_cli pour:
  - editer une tête
  - assembler un agent-personne
  - entraîner et produire un rapport
