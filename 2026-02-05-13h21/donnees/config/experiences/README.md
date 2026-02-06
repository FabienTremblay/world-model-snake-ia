# Expériences (bacs à sable)

Ce répertoire regroupe des **expériences reproductibles** :

- un fichier `experience.yml` (intention + paramètres de référence)
- un sous-répertoire `artefacts/` où sont déposés les résultats

Le but est d'éviter le “gros répertoire artefacts” non structuré : on range par expérience, puis par run.

## Structure

```
donnees/config/experiences/
  _template/
    experience.yml
    README.md
    artefacts/
  <experience_id>/
    experience.yml
    artefacts/
      runs/
        <run_id>/
          journal_episodes.jsonl
          metrics.jsonl
          stdout.log
          meta_run.json
```

## ui_cli et création automatique

Le `ui_cli` accepte :

- `--experience <id>` : active la convention ci-dessus et **crée** les répertoires manquants
- `--run-tag <texte>` : suffixe lisible
- `--capture-stdout` : écrit `stdout.log`

Exemple :

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --arene cours4_tiny_planification \
  --agent aleatoire \
  --episodes 50 --max-ticks 2000 --seed 123 \
  --capture-stdout
```

> Pour le moment, `experience.yml` est surtout un support de documentation. Une itération ultérieure pourra faire en sorte que le `ui_cli` lise ce fichier et applique automatiquement les défauts.
ence.yml
    README.md
    artefacts/
  cours4/
    experience.yml
    artefacts/
      runs/
        <run_id>/
          journal_episodes.jsonl
          stdout.log
          meta_run.json
          metrics.jsonl
```

## Création automatique

Le `ui_cli` crée un bac à sable à la volée lorsqu'on lance une expérience inexistante :

```bash
PYTHONPATH=services python -m ui_cli.app.main --experience cours4 --arene cours4_tiny_planification --agent aleatoire --episodes 10
```

Cela crée :

- `donnees/config/experiences/cours4/`
- `donnees/config/experiences/cours4/experience.yml` (template)
- `donnees/config/experiences/cours4/artefacts/runs/<run_id>/...`

## Voir le template

Le répertoire `_template/` contient :

- un exemple `experience.yml`
- un `README.md` décrivant le fonctionnement
