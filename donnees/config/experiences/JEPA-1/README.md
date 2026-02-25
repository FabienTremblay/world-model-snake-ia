# Note JEPA-1 — capteurs_compact en base64 (mode recommandé)

Dans JEPA-1, `capteurs_compact` est typiquement une chaîne **base64**. Le prototype utilise désormais par défaut :

- décodage `base64` → `bytes`
- vecteur float **de longueur 560** (pad/truncate)
- normalisation `byte/255.0`

Cela conserve beaucoup plus d’information qu’un hashing de chaîne, et rend la distance t→t+1 (surprise) significative.

---

## 📌 Migration vers Modules Refactorisés

**Date:** 2026-02-24

JEPA-1 utilise maintenant les modules refactorisés:
- `entrainer_v2.py`: Script principal (remplace entrainer_hypothese_pred_capteurs_v1.py)
- Modules dans `services/agent_service/app/`

Notes d'exécution:
- `outils/collecter_observations_fourmi_v1.sh` lance `ui_cli`, récupère le **run** le plus récent du tag,
  puis copie le `journal_episodes.jsonl` sous `artefacts/datasets/journal_episodes_fourmi.jsonl` pour
  préserver les conventions historiques de JEPA-1.

Code original archivé dans `Archives/code_original_*/`

