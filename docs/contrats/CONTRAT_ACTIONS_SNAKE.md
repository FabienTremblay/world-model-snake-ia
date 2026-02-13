# contrat — langage des actions snake

ce document fixe la norme des **libellés d’actions** échangés entre :
- les **agents** (services/agent_service)
- le **runner** (services/runner)
- les interfaces (**ui_cli**, **ui_tui**)

objectif : empêcher les divergences de vocabulaire qui brisent le replay et les outils.

## norme canonique

pour snake (agents incarnés en arène), l’action est un identifiant **relatif** à la direction de la tête :

| identifiant | sens |
|---|---|
| `avant` | avancer d’une case dans la direction actuelle |
| `observer_gauche` | tourner à gauche (relative, sans avancer) |
| `observer_droite` | tourner à droite (relative, sans avancer) |

ces valeurs sont définies dans : `services/commun/actions_snake.py`.

## responsabilités

- **agent (IAgentArene)** : retourne `Action` (canonique) via `choisir_action(...)`.
- **monde / dynamique** : applique l’action (mise à jour direction + déplacement).
- **runner** : orchestre perception/décision/exécution et journalise l’action canonique.

> si le runner souhaite aussi conserver une trace opérationnelle “absolue”, il doit l’écrire dans un autre champ (ex. `monde_canonique.direction`), sans changer `decision.action`.

## contrat python

le type `Action` (snake) est importé depuis `commun.actions_snake` dans :
- `services/agent_service/app/contrats_agents.py`

toute implémentation d’agent snake doit retourner une valeur conforme à ce type.

## compatibilité et migration

les valeurs absolues (`haut`, `bas`, `gauche`, `droite`) ne font pas partie du langage canonique des agents.
elles peuvent exister comme **données d’état** du monde, mais pas comme action d’agent.
