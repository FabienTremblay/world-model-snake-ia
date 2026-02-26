# JEPA-1 — Gate calibré sur la surprise (prédiction), pas sur Δ observation

La fourmi est un **agent explorateur**. Dans ce contexte, il est normal d’observer très souvent `x_t == x_{t+1}`
(pas de changement perceptible au tick suivant), donc `MSE(x_t, x_{t+1})` est un mauvais signal pour calibrer
*connu / inconnu*.

## Ce qu’on veut
La surprise épistémique = `MSE(ŷ_{t+1}, x_{t+1})` où `ŷ_{t+1}` est la **prédiction du modèle** entraîné.

## Changement dans l’épreuve
- `gate.mode="quantile"` : le seuil est fixé au quantile de la surprise (ex: 0.90)
- on obtient automatiquement une proportion d’“inconnu” contrôlée (~10% ici)

## Outil
`outils/analyser_surprise_journal_agent.py` imprime les quantiles de surprise et le comptage des modes.
