# runner — événements (v2)

Ce répertoire contient le runner “canonique” du projet.

- `app/runner_evenements_v2.py` : boucle E/F basée sur le bus d'événements
- `tests/` : verrouillage du runner (timeline / modes / publier_ticks)

Note: `services/runner_service` a été supprimé; le runner canonique est maintenant `services/runner`.
