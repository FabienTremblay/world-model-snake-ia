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

Code original archivé dans `Archives/code_original_*/`

