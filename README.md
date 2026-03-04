# Patch — API stricte `executer(...)` : mise à jour du test smoke

Date : 2026-03-04

Contexte : le test `services/agent_service/tests/test_analyse_diagnostics_smoke.py`
appelle `executer(str(run_dir))`, mais `executer()` exige maintenant :

- diagnostics
- out_md
- out_json

Ce patch **n'ajoute aucune rétrocompatibilité** : il met à jour le test
pour fournir explicitement les 3 paramètres requis.

## Application (recommandé)

```bash
git apply patchs/0001-test-smoke-adapte-signature-executer.patch
pytest -q
```

## Application (manuelle)

Voir le fichier `exemples/test_analyse_diagnostics_smoke.py` pour le contenu attendu.
