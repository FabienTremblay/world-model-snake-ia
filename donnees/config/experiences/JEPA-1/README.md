# Note JEPA-1 — capteurs_compact en base64 (mode recommandé)

Dans JEPA-1, `capteurs_compact` est typiquement une chaîne **base64**. Le prototype utilise désormais par défaut :

- décodage `base64` → `bytes`
- vecteur float **de longueur 560** (pad/truncate)
- normalisation `byte/255.0`

Cela conserve beaucoup plus d’information qu’un hashing de chaîne, et rend la distance t→t+1 (surprise) significative.
