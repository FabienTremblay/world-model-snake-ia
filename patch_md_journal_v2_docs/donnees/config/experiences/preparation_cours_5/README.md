# bac à sable (expérience) — preparation_cours_5

une **expérience** (bac à sable) est une manière de regrouper :
- la configuration (le *quoi* et le *comment* on exécute)
- les artefacts produits (journaux, stdout, métriques)

…dans un répertoire unique, afin de pouvoir répéter, comparer, archiver.

## emplacement

un bac à sable vit sous :

```
donnees/config/experiences/<experience_id>/
  experience.yml
  README.md
  artefacts/
    runs/
      <run_id>/
        meta.json
        journal.jsonl
        obs/
        stdout.log      # si --capture-stdout
        metrics.jsonl   # optionnel
```

- `meta.json` : paramètres **résolus** (source de vérité pour rejouer)
- `journal.jsonl` : **journal v2** (un événement par tick)
- `obs/` : payloads lourds référencés depuis le journal (ex. caméras)

le `ui_cli` crée automatiquement ce squelette si vous lancez une expérience qui n'existe pas.

## lancer un run dans une expérience

exemple (création automatique du bac à sable si absent) :

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience preparation_cours_5 \
  --arene cours5_tiny_planification \
  --agent planif_mpc_observateur_tabulaire \
  --latent signaux_percus_hash_v1 \
  --episodes 200 --max-ticks 2000 --seed 123 \
  --capture-stdout
```

### ce que le ui_cli fait

- résout `donnees/config/experiences/<experience_id>/`
- crée `artefacts/runs/<run_id>/`
- écrit le journal v2 dans `journal.jsonl`
- écrit `meta.json` (paramètres résolus)
- si `--capture-stdout` : écrit aussi `stdout.log`

## `experience.yml`

ce fichier sert de **point d'ancrage** pour l'expérience.
au stade actuel, le ui_cli :
- le crée s'il manque (template minimal)
- n'en consomme pas encore les champs pour injecter des défauts

on garde la place pour la suite (ex.: défauts, variantes, notes, etc.).

## bonnes pratiques

- une expérience = une intention claire (ex.: `cours5`, `cours5_variantes`, `preparation_cours_5`).
- ne pas réutiliser un même `run_id`.
- archiver un run : `tar -czf run_<run_id>.tgz .../artefacts/runs/<run_id>`
