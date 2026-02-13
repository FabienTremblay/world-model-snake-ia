# changelog

Ce fichier suit les changements structurants du projet.

## 2026-02-13

### ajouté
- snake_collectif_v1 :
  - agents c1 et c2 (catalogue plugins v1).
  - expérience `snake_collectif_v1` avec jeu de données `train.jsonl`.
- world_model :
  - prise en charge explicite du champ latent configurable (`SNAKE_CHAMP_LATENT`).
  - résolution déclarative via `experience.yml`.
- format journal :
  - support consolidé du format `episodes_v2` (non rétrocompatible).

### corrigé
- snake_collectif_v1_c1 :
  - suppression de l’usage incorrect de `ActionSnake` (type `Literal`) en runtime ;
  - utilisation explicite des constantes canon (`ACTION_AVANT`, `ACTION_OBSERVER_GAUCHE`, `ACTION_OBSERVER_DROITE`) ou chaînes équivalentes.
- snake_collectif_v1_c2 :
  - suppression des imports invalides `ACTION_TOURNER_GAUCHE` et `ACTION_TOURNER_DROITE` inexistants dans `commun.actions_snake` ;
  - réalignement sur l’espace d’action canon.
- catalogue plugins v1 :
  - rétablissement de l’instanciation sans paramètres pour les agents `snake_collectif_v1_c1` et `snake_collectif_v1_c2`.

### clarifié
- contrat d’actions snake :
  - `avant` déclenche un déplacement.
  - `observer_gauche` / `observer_droite` signifient “tourner relatif sans avancer”.
  - les alias legacy présents dans `MondeSnake.step()` restent supportés pour compatibilité, mais ne font pas partie du contrat canon pour les agents cibles.
- stabilisation de l’espace d’action :
  - l’espace canon restreint (`avant`, `observer_gauche`, `observer_droite`) est maintenu afin de préserver la cohérence :
    - du journal,
    - de l’apprentissage tabulaire,
    - du simulateur interne,
    - et des agents planificateurs.

### tests
- `test_catalogue_plugins_v1::test_agents_instanciables_sans_params[...]` :
  - confirmé comme garde-fou d’intégrité du contrat d’actions.
  - aucune modification du test requise ; détection correcte des ruptures d’api.

## unreleased (2026-02-10)

### ajouté
- clarification documentaire : séparation monde canonique (`world_sim`) vs perception instrumentée (`instrument`)
- recommandation d’un format de journal non compatible `episodes_v2` (état + observations instrumentées)

### modifié
- `docs/runner.md` : orchestration par instruments + journal `episodes_v2`
- `services/agent_service/app/decoupage_point_de_vue_agents.md` : état actuel vs cible (égocentré) et introduction du package `instrument`

### supprimé
- ancien package `agent_runtime` (refonte canonique des types d’agents)

### notes
- ce changelog accompagne un tag github créé côté dépôt ; il documente la nouvelle direction (sans compat) pour `journal.jsonl` (schema `journal_v2`).
