# JEPA-1 — Patch journal + registre

## But
1) Marquer explicitement les journaux produits par la fourmi comme **collecte** (agent spécialisé).
2) Enrichir le registre épistémique avec les stats du gate et l'effet observé.
3) Normaliser les libellés de mode dans le journal d'épreuve : `connu_exploiter` / `inconnu_explorer`.

## Effets
- un nouveau fichier de collecte est produit : `journal_episodes_fourmi.enrichi.jsonl`
  - ajoute : `agent_id=fourmi`, `role_agent=collecteur`, `objectif=couverture_observations`
- `registre_epistemique.json` contient :
  - `gate.stats_surprise` (mean/std/min/max + quantiles)
  - `gate.effet` (ratios connu/inconnu)
- `journal_agent.jsonl` utilise des modes cohérents :
  - `connu_exploiter`, `inconnu_explorer`

## Note
Ce patch reste confiné à `donnees/config/experiences/JEPA-1/`.
