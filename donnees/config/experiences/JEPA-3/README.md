# JEPA-3 — deux hypothèses concurrentes en compétition

## intention

Deux modèles expliquent le même flux (x → y). À chaque transition, on *élit* l’hypothèse la plus prédictive.

- h1 : MLP (non-linéaire)
- h2 : baseline linéaire (biais différent)

Objectif : une compétition **saillante** (winner non trivial) et une surprise **calibrable**.

## signaux (par transition)

- s1 = MSE(h1(x), y)
- s2 = MSE(h2(x), y)
- winner = argmin(s1, s2)
- surprise = min(s1, s2)  (surprise « optimiste » : meilleur expert disponible)

## gate

- connu/inconnu basé sur `surprise`
- seuil calibré par quantile (par défaut q=0.90, comme JEPA-1)

## ce qui est journalisé (journal_agent.jsonl)

Par transition :

- `s1`, `s2`, `winner`, `surprise`, `seuil_connu`, `mode`, `action`

## ce qui est mis dans le registre (registre_epistemique.json)

- `win_rate_h1`, `win_rate_h2`
- stats/quantiles de `s1`, `s2`, `surprise`
- effets du gate (ratio connu/inconnu)

## critères de succès

- `winner` non trivial (pas 99.9% identique)
- `surprise` stable (distribution exploitable) et `gate` calibrable
- `action` conforme au contrat (3 actions)

## exécution (pipeline ui_cli)

Depuis la racine du repo :

```bash
export PYTHONPATH=services
python -m ui_cli.app.pipeline.cli_pipeline run --experience JEPA-3 --phase all --seed 123
```

## artefacts attendus

- `artefacts/datasets/journal_episodes_fourmi.jsonl`
- `artefacts/datasets/journal_episodes_fourmi.enrichi.jsonl`
- `artefacts/datasets/paires_capteurs.pt`
- `artefacts/poids/hypotheses/h1.pt` et `h2.pt`
- `artefacts/journaux/journal_agent.jsonl`
- `artefacts/journaux/registre_epistemique.json`

## note « compétition riche »

Pour que la compétition soit informative, h2 n’est **pas** « le même MLP un peu différent » :

- h2 est volontairement **linéaire** (capacité limitée)
- cela favorise un winner variable (selon les motifs de transition)

