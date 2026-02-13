# SAI-A107 : préparer un agent-personne (tronc + têtes)

## rôle dans la chaîne

SAI-A107 consomme un **registre épistémique** produit à partir d'un run (observateur estrade) et prépare
un **agent-personne** déclaratif (plugin v1) composé d'un **tronc** et de **têtes**.

- **entrée** : `registre_epistemique_v2.json` (dans `.../artefacts/runs/<run-id>/`)
- **sortie** : un agent-personne déclaratif (YAML plugin v1) + ses paramètres (tronc/têtes/gouvernance)

> important : dans la version actuelle de l'outillage, l'assemblage est **déclaratif** (fichiers YAML)
> et s'exécute via `ui_cli` en choisissant l'agent par son id.

---

## prérequis (ce qui doit exister)

1) une expérience bac-à-sable exécutable (`donnees/config/experiences/<id>/experience.yml`)
2) au moins un run sous `.../artefacts/runs/<run-id>/` avec :
   - `journal.jsonl` (obligatoire)
   - `metrics.jsonl` (optionnel mais fortement recommandé, ex: checksum avant/après)

---

## étape 1 — produire le registre (observateur estrade)

Dans la racine du repo :

```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli \
  --experience <id_experience> \
  --run-id <run-id>
```

Sortie :
- `donnees/config/experiences/<id>/artefacts/runs/<run-id>/registre_epistemique_v2.json`

### contenu minimal attendu du registre
- `indices` : agrégats (raisons de fin, actions, etc.)
- `hypotheses` : diagnostic (biais, stationnaire, revisite, etc.)
- `concepts_candidates` : **concepts instillables** issus de `metrics.jsonl` (actions nulles, transitions dominantes, etc.)

---

## étape 2 — préparer l'agent-personne (déclaratif)

### 2.1 contrat (plugin v1)
Un agent-personne est déclaré comme un agent plugin v1.

- un **tronc** : construit la représentation de base à partir des signaux (caméra, gps, etc.)
- des **têtes** : modules spécialisés activables par gouvernance
- une **gouvernance** : comment choisir/combiner les propositions des têtes

### 2.2 ce qu'on instille depuis le registre (sans “coder dûr”)
On ne hardcode pas “mur/nourriture”. On instille d'abord des invariants observables :

1) **veto actions nulles**  
   si `checksum == checksum_avant` pour (etat, action) : empêcher l'action dans cet état.

2) **brise-cycle** (heuristique)  
   si revisite élevée / états dominants : favoriser une action “non encore vue” dans l'état courant.

3) **priorité exploration** (phase fourmi)  
   augmenter la couverture d'états uniques (etats_uniques).

Ces règles peuvent être injectées dans une tête (ex: `tete_veto_transition`) pilotée par gouvernance.

---

## étape 3 — validation (ce que tu dois observer)

Le critère d'échec typique : `score=0` + `ticks≈max_ticks` + revisite extrême.

Après instillation :
- baisse du `ratio_stationnaire`
- hausse de `etats_uniques`
- baisse de `ratio_revisite_etats`
- si nourriture est atteinte : `score` devient > 0

---

## nomenclature recommandée (pour s'y retrouver)
- expérience : `snake_collectif_v1`
- run : `YYYY-MM-DD_HHmm_<tag>`
- agents (conditions) : `snake_collectif_v1_<condition>`
- têtes : `tete_<objectif>_<v1>`
- concepts instillés : `concept_<type>_<v1>`
