# changelog

Ce fichier suit les changements structurants du projet.

## unreleased (2026-02-10)

### ajouté
- clarification documentaire : séparation monde canonique (`world_sim`) vs perception instrumentée (`instrument`)
- recommandation d’un format de journal non compatible `episodes_v2` (état + observations instrumentées)

### modifié
- `docs/runner.md` : orchestration par instruments + journal `episodes_v2`
- `services/agent_service/app/decoupage_point_de_vue_agents.md` : état actuel vs cible (égocentré) et introduction du package `instrument`
- `services/agent_service/app/agent_runtime/README.md` et `MIGRATION.md` : alignement sur la cible et mention explicite de l’état actuel

### notes
- ce changelog accompagne un tag github créé côté dépôt ; il documente la nouvelle direction (sans compat) pour `journal.jsonl` (v2).
