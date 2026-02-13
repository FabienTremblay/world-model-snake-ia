# pipeline — snake_collectif_v1 — observateurs collectifs (SAI-A105 → SAI-A107)

ce document fixe une recette reproductible pour générer un **registre épistémique collectif** à partir des runs de `snake_collectif_v1`.

## conventions non négociables

### actions

les agents « en arène » doivent respecter le contrat : `docs/contrats/CONTRAT_ACTIONS_SNAKE.md`.

actions canoniques :
- `avant`
- `observer_gauche`
- `observer_droite`

côté code : `services/commun/actions_snake.py` et `services/agent_service/app/contrats_agents.py`.

### organisation des artefacts

un run est un dossier `donnees/config/experiences/snake_collectif_v1/artefacts/runs/<run-id>/`.

un run contient typiquement :
- `journal.jsonl`
- `metrics.jsonl`
- `meta.json`
- (optionnel, produit par sai-a106) `registre_epistemique_v2.json`

les registres consolidés (sorties des observateurs) vont dans :
`donnees/config/experiences/snake_collectif_v1/artefacts/registres/`.

## responsabilités par activité

### sai-a105 — diagnostic minimal (qualité des runs)

objectif : vérifier qu’un run a assez de diversité pour être intéressant (pas stationnaire, pas 1 seul état, etc.).

outil :
```bash
python donnees/config/experiences/snake_collectif_v1/outils/a105_diagnostic_snake_collectif_v1.py \
  --runs-dir donnees/config/experiences/snake_collectif_v1/artefacts/runs \
  --sortie-dir donnees/config/experiences/snake_collectif_v1/artefacts/analyses
```

sorties :
- `artefacts/analyses/a105_diagnostic_par_run.csv`
- `artefacts/analyses/a105_diagnostic_global.csv`

### sai-a106 — produire (ou au minimum créer) le registre épistémique v2

objectif : produire un fichier `registre_epistemique_v2.json` *par run*.

points importants :
- le registre peut être « vide » au départ, mais le fichier doit exister si le pipeline veut être strict.
- la mort est un concept particulier : seul l’observateur peut constater le **fait** de la terminalité, et le registre doit pouvoir pondérer « danger ultime ».

attendu :
`donnees/config/experiences/snake_collectif_v1/artefacts/runs/<run-id>/registre_epistemique_v2.json`

### sai-a107 — observateurs collectifs + convention

objectif : convertir les propositions de différents observateurs en un flux unique (jsonl) et fusionner.

outils :
- `o2_transformer_registre_epistemique_v2.py` : transforme `registre_epistemique_v2.json` en propositions jsonl.
- `o1_observateur_surprise_v1.py` : détecte des surprises (bris d’anticipation) à partir des transitions.
- `conventionneur_v1.py` : fusionne plusieurs flux de propositions.

## pipeline canon (exécutable)

### 0) choisir un run

```bash
RUN_DIR=$(ls -1dt donnees/config/experiences/snake_collectif_v1/artefacts/runs/* | head -n 1)
echo "RUN_DIR=$RUN_DIR"
```

### 1) o2 — propositions issues du registre v2 (sai-a106)

cas normal (registre présent) :
```bash
python donnees/config/experiences/snake_collectif_v1/outils/o2_transformer_registre_epistemique_v2.py \
  --run-dir "$RUN_DIR" \
  --sortie donnees/config/experiences/snake_collectif_v1/artefacts/registres/o2_propositions.jsonl
```

cas dégradé (registre absent) :
- l’outil produit un flux vide (0 proposition) et affiche un avertissement.
- la correction structurelle reste : produire le fichier via sai-a106.

### 2) o1 — surprises (bris / étonnement)

```bash
python donnees/config/experiences/snake_collectif_v1/outils/o1_observateur_surprise_v1.py \
  --run-dir "$RUN_DIR" \
  --prefix-bits 16 \
  --sortie donnees/config/experiences/snake_collectif_v1/artefacts/registres/o1_surprises.jsonl
```

notes :
- si `actions ignorées (non canoniques ActionSnake)` est élevé, c’est que l’agent ne respecte pas le contrat d’actions.
- `0 surprise détectée` peut être normal si l’état est trop « complet » ou l’environnement trop déterministe.

### 3) convention — fusion des observateurs

```bash
python donnees/config/experiences/snake_collectif_v1/outils/conventionneur_v1.py \
  --sortie donnees/config/experiences/snake_collectif_v1/artefacts/registres/registre_epistemique_collectif.jsonl \
  --inputs \
    donnees/config/experiences/snake_collectif_v1/artefacts/registres/o2_propositions.jsonl \
    donnees/config/experiences/snake_collectif_v1/artefacts/registres/o1_surprises.jsonl
```

## diagnostic rapide quand ça bloque

### symptôme : le snake ne bouge pas / capteurs inchangés

cause typique : actions non conformes (ex. `N/E/S/W` au lieu de `avant/observer_gauche/observer_droite`).

vérification :
```bash
grep -m 20 '"action"' "$RUN_DIR/journal.jsonl" | head
```

### symptôme : o2 échoue « registre introuvable »

cause : `registre_epistemique_v2.json` absent du run.

solution :
- produire (ou créer) le registre via sai-a106, ou
- accepter le mode dégradé (sortie vide) pour continuer la démo.

