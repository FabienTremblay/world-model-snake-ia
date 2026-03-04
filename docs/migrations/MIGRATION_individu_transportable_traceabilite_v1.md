# Migration — individu transportable + traçabilité (v1)

## Objectif
- Charger un individu depuis le catalogue
- L'utiliser dans `ui_cli evenements`
- Écrire des snapshots (entrée/sortie) dans `artefacts/runs/<run>/`

## Nouveau
- `--individu <id>` (override) ou `experience.yml: evenements.individu_id`
- fichiers générés:
  - `individu_entree.yml`
  - `individu_sortie.yml` (mode entrainement)
  - `lineage.json`
  - `meta.json` enrichi (hashes)

## Discipline
- En mode `epreuve`: pas d'évolution/promotion
- En mode `entrainement`: évolution minimale (mémoire courte + provenance + version)
