# JEPA-4 — ensemble + désaccord (épistémique plus riche)

## intention

On ne cherche pas seulement « le meilleur ». On exploite :

- l’accord (consensus fort → « connu robuste »)
- le désaccord (histoires incompatibles → « incertitude structurelle »)

Deux hypothèses (biais différents) :

- h1 : MLP (non-linéaire)
- h2 : baseline linéaire

## signaux (par transition)

- s1 = MSE(h1(x), y)
- s2 = MSE(h2(x), y)
- yhat_ens = (yhat1 + yhat2) / 2
- surprise_ens = MSE(yhat_ens, y)
- disagree = MSE(yhat1, yhat2)

## gate (double)

Inconnu si :

- `surprise_ens > seuil_surprise` **ou**
- `disagree > seuil_disagree`

Seuils calibrés par quantiles (par défaut q=0.90 / q=0.90).

## ce qui est journalisé (journal_agent.jsonl)

Par transition :

- `s1`, `s2`, `surprise_ens`, `disagree`, `seuil_surprise`, `seuil_disagree`, `mode`, `action`

## ce qui est mis dans le registre (registre_epistemique.json)

- stats/quantiles de `surprise_ens` et `disagree`
- corrélation `disagree` vs `surprise_ens`
- ratio inconnu dû au désaccord vs dû à surprise

## critères de succès

- `disagree` non dégénéré (pas ~0 partout)
- gate double produit une partition intéressante
- `action` conforme au contrat

## exécution (pipeline ui_cli)

Depuis la racine du repo :

```bash
export PYTHONPATH=services
python -m ui_cli.app.pipeline.cli_pipeline run --experience JEPA-4 --phase all --seed 123
```

## artefacts attendus

- `artefacts/poids/hypotheses/h1.pt` et `h2.pt`
- `artefacts/journaux/journal_agent.jsonl`
- `artefacts/journaux/registre_epistemique.json`

