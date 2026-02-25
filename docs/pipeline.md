# pipeline (ui_cli)

Ce document formalise le **pipeline canonique** pour exécuter une expérience et verrouiller la reproductibilité.

## principes

- **un pipeline = un plan** : chaque exécution écrit `plan_pipeline.json` dans un run.
- **reproductibilité** : le plan contient seed + versions + sha256 des configs.
- **immutabilité** : les artefacts principaux sont copiés sous le run (`artefacts/runs/<run_id>/...`).
- **compat** : des *pointeurs stables* restent mis à jour sous `artefacts/` de l'expérience (pour rester compatible avec les usages actuels).

## commandes

Depuis la racine du repo :

```bash
export PYTHONPATH=services

# exécuter toutes les phases
python -m ui_cli.app.main pipeline run --experience JEPA-1 --phase all --seed 0

# ne faire que la collecte
python -m ui_cli.app.main pipeline run --experience JEPA-1 --phase collecte --seed 0

# lister les runs
python -m ui_cli.app.main pipeline list-runs --experience JEPA-1

# décrire un run
python -m ui_cli.app.main pipeline describe-run --experience JEPA-1 --run-id <run_id>

# rejouer un run (strict par défaut)
python -m ui_cli.app.main pipeline replay --experience JEPA-1 --run-id <run_id>

# exporter
python -m ui_cli.app.main pipeline export-run --experience JEPA-1 --run-id <run_id> --out /tmp/run.zip
```

## phases

Par défaut (`--phase all`) :

1. `collecte` : lance `ui_cli` (agent fourmi) pour produire `journal_episodes.jsonl` puis copie un pointeur stable.
2. `enrichissement` : ajoute des champs d'étiquetage (agent_id, role_agent, objectif).
3. `dataset` : extrait les paires (t→t+1) depuis `capteurs_compact`.
4. `entrainement` : entraîne le modèle prédictif et écrit `agent_personne.json` + `agent_personne.poids.pt`.
5. `epreuve` : calcule la surprise, calibre un gate et écrit `journal_agent.jsonl` + `registre_epistemique.json`.

## conventions d'expérience

Chaque expérience doit fournir dans `experience.yml` :

- `arene.id` (chemin relatif à l'expérience, ou au repo, ou absolu)
- `agent.id`
- `pipeline.*` (chemins stables + configs)

Voir `donnees/config/experiences/JEPA-1/experience.yml` et `JEPA-2/experience.yml`.
