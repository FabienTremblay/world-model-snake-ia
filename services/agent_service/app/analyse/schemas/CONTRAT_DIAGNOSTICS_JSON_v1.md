# Schéma JSON — sorties diagnostics SAI-A105 (v1)

Ce document décrit le **contrat machine** produit par :

```bash
PYTHONPATH=services python -m agent_service.app.analyse.cli.main --run <path> --set <set>
```

Le fichier visé est généralement :

- `<run>/epreuve/diagnostics.json`

Le schéma JSON correspondant est fourni dans :

- `sai_a105_diagnostics_schema_v1.json`

---

## Objectif du schéma

- Permettre au TUI / scripts de campagne de consommer `diagnostics.json` **sans dépendre du code Python**.
- Autoriser l’extension (champs additionnels) sans casser la compat.

Principe : **stabilité des clés principales**, flexibilité dans `mesures`.

---

## Top-level (racine)

Champs attendus :

- `schema_version` (obligatoire) : `"sai-a105.diagnostics.v1"`
- `diagnostics` (obligatoire) : liste de résultats de diagnostics

Champs optionnels (traçabilité) :

- `experience_id`, `run_id`
- `run_dir_entree`, `run_dir_resolu`, `epreuve_dir`
- `date_utc`
- `renderer`, `renderer_signature`

---

## Objet `ResultatDiagnostic`

Champs minimaux :

- `diagnostic_id` (obligatoire) : ID stable, versionné
- `statut` (obligatoire) : `ok|warn|fail|skip|error`

Champs usuels :

- `resume` : une ligne “pilotage”
- `mesures` : dict JSON (clés libres)
- `alertes` : liste d’alertes structurées
- `fragments_md` : fragments markdown (tables, notes)

---

## Règles de compat / versionnage

On incrémente la version **(v2, v3, …)** si :
- on change la sémantique d’une clé existante,
- on renomme/supprime une clé principale,
- on change le type d’un champ clé (`statut`, `diagnostics`, etc.).

On peut rester en **v1** si :
- on ajoute des champs optionnels,
- on ajoute des clés dans `mesures`,
- on améliore la doc ou les alertes.

---

## Où déposer dans le repo

Recommandé :

- `services/agent_service/app/analyse/schemas/sai_a105_diagnostics_schema_v1.json`
- `services/agent_service/app/analyse/docs/CONTRAT_DIAGNOSTICS_JSON.md`

(Le TUI peut charger le schéma pour valider/afficher le contrat.)
