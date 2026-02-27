# JEPA-5 — adaptation locale des hypothèses (v1)

## intention
au lieu de garder un ensemble fixe ou une compétition winner-take-all, on adapte les poids des hypothèses au fil des transitions selon leur performance.

## signaux par transition
- s1 = mse(yhat1, y)
- s2 = mse(yhat2, y)
- ema_s1, ema_s2 (moyenne mobile exponentielle)
- w1, w2 (poids adaptatifs, w1+w2=1)
- yhat = w1*yhat1 + w2*yhat2
- surprise = mse(yhat, y)
- disagree = mse(yhat1, yhat2) (optionnel mais recommandé)

## gate (proposition)
inconnu si surprise > seuil_surprise OU disagree > seuil_disagree
(seuils par quantiles)

## critères de succès
- les poids w1/w2 ne sont pas dégénérés (pas ~1.0 constant)
- les poids se déplacent selon des régimes (variabilité mesurable)
- gate produit une partition intéressante
- action conforme contrat
