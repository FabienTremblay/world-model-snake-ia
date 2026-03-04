
# NOTE — Tests runner événementiel v1

Ce patch ajoute des tests visant à verrouiller :

- l'ordre des événements dans un tick (`tick_annonce` → actions → `tick_survenu`)
- la distinction des modes :
  - entraînement (E/pull) : le runner appelle `emettre_evenements(ctx, bus)` pour les objets actifs
  - épreuve (F/push) : le runner ne force pas l'émission
- la règle `publier_ticks=false` : aucun événement `tick_*` n'est généré

Fichier principal :
- `services/runner_service/tests/test_runner_evenements_v2_timeline.py`
