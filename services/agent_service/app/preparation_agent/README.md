# ui_cli — préparer un agent-personne (sai-a107)

ce module expose un mini-cli pour prototyper le pipeline **sai-a107 préparer un agent**.

## objectif

fournir une orchestration reproductible (bac-à-sable) pour :

1. **déclarer** un catalogue de têtes (slots instanciables)
2. **assembler** un agent-personne (tronc + têtes + gouvernance initiale)
3. **entraîner** l’agent-personne (prototype) et produire un rapport

> note : ce module est volontairement minimal. il vise d’abord à stabiliser les contrats, les chemins d’artefacts et la trajectoire sai-a107.

---

## où ça se branche

- logique **métier** (offline) : `agent_service.app.preparation_agent.*`
- orchestration **ui** : `ui_cli.app.preparation_agent.*`
- exécution en arène (tick → action) : `agent_service.app.agents.*` + `runner` (hors scope ici)

---

## commandes

toutes les commandes ci-dessous supposent :

- exécution depuis la racine du projet
- `PYTHONPATH=services`

### 1) éditer une tête (catalogue)

crée ou met à jour une entrée dans le catalogue des têtes.

```bash
PYTHONPATH=services python -m ui_cli.app.main preparer-agent editer-tete \
  --experience cours4 \
  --tete-id structure_locale \
  --nom "structure locale" \
  --type classification_multiclasse \
  --role categorie_contenu \
  --classes "couloir,impasse,espace_ouvert"
```

champs principaux :

- `--tete-id` : identifiant stable (utilisé dans les plans)
- `--type` : type de sortie (classification, score, gate, policy, etc.)
- `--role` : rôle de la tête (contenu / contrôle / policy / gouvernance)
- `--classes` : liste csv (si multiclasse / multi-label)

### 2) assembler un agent-personne

assemble un agent-personne **sans apprentissage** :

- sélection des têtes
- initialisation de la gouvernance (intentions + influences)
- production d’un artefact “agent-personne assemblé” + plan

```bash
PYTHONPATH=services python -m ui_cli.app.main preparer-agent assembler \
  --experience cours4 \
  --arene-id cours4_tiny_planification \
  --agent-personne-id ap_cours4_v1 \
  --tronc-id tronc_tabulaire_v1 \
  --type-tronc tabulaire_v1 \
  --tetes "structure_locale"
```

notes :

- `--tetes` : ids csv des têtes à instancier (doivent exister dans le catalogue)
- `--tronc-poids` : optionnel (pointeur vers poids existants)

### 3) entraîner (prototype)

exécute le pipeline sai-a107 :

- assemble (au besoin)
- entraîne (prototype)
- écrit l’agent-personne final + rapport

```bash
PYTHONPATH=services python -m ui_cli.app.main preparer-agent entrainer \
  --experience cours4 \
  --agent-personne-id ap_cours4_v1
```

---

## artefacts (bac-à-sable)

dans `donnees/config/experiences/<experience>/artefacts/` :

- `catalogues/`
  - `catalogue_tetes.json`
- `plans_preparation/`
  - `<agent_personne_id>.plan.json`
- `agent_personne/`
  - `<agent_personne_id>/agent_personne_assemble.json`
  - `<agent_personne_id>/agent_personne.json`
- `runs_preparation/`
  - `<agent_personne_id>/...` (logs, checkpoints à venir)
- `rapports_preparation/`
  - `<agent_personne_id>.rapport.json`

---

## conventions de conception

- une **tête** est déclarée avant d’être entraînée : on décrit un “slot instanciable”.
- un **agent-personne** est un artefact offline : identité + structure interne + pointeurs de poids.
- l’agent en arène (runtime) **consomme** l’agent-personne mais n’en modifie pas la définition.
- l’expérimentateur gouverne la sélection des concepts et leur instanciation en têtes.

---

## prochaine itération (prévue)

- accepter `--supervision` et `--influence` en json (sur `editer-tete`)
- intégrer des intentions explicites dans le plan (ex : mission_validation, exploration)
- brancher un backend torch minimal (tronc + 1 tête classification)
- produire des checkpoints dans `runs_preparation/<id>/`
- lier un registre épistémique (lecture) pour proposer automatiquement des têtes candidates
