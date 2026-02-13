# idées — observateurs collectifs (snake_collectif_v1)

## état actuel

- plusieurs observateurs peuvent produire des **propositions** (jsonl) à partir d'un run.
- un conventionneur fusionne ces propositions dans un registre collectif.

## contrat d'actions (nouvelle norme)

Les agents incarnés en arène retournent une action **relative** selon le contrat :

- `avant`
- `observer_gauche`
- `observer_droite`

Voir :
- `docs/contrats/CONTRAT_ACTIONS_SNAKE.md`
- `services/commun/actions_snake.py`

Conséquence épistémique :
- la découverte de concepts ne doit pas supposer des actions absolues (`haut/bas/...`).
- les observateurs travaillent sur des séquences de (classe_etat, action_relative, classe_etat_suivant).

## opérateurs de découverte (structurels)

On privilégie des opérateurs non-sémantiques :

1. **invariance** : transitions quasi déterministes (lois locales)
2. **surprise** : non-déterminisme après abstraction (compression/similarité)
3. **terminalité** : fin d'épisode (signal structurel répulsif)
4. **contraste** : mêmes signatures → issues différentes (variable manquante)

## stratégie

- ne pas coder dur une liste de concepts du monde.
- coder des opérateurs génériques, puis laisser la convention émerger via fusion / conflits / split de régimes.

