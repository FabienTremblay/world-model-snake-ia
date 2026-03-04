# Note — template conforme au ui_cli + defaults evenements

## Pourquoi `git grep` a échoué

`git grep` attend les options AVANT les chemins.
Exemple correct:

```bash
git grep -n "BacASableV1" -- services/ui_cli/app
```

## Changement

- Le template `_template/experience.yml` est aligné sur les clés consommées par `BacASableV1` et `ui_cli`.
- `ui_cli evenements` applique maintenant les defaults de `evenements:` dans `experience.yml` si l'utilisateur n'a pas surchargé en CLI.
