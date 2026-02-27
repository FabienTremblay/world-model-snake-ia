# SAI-A105 --- Catalogue de diagnostics (Factorisation JEPA-5)

Version générée le 2026-02-27 18:27 UTC

------------------------------------------------------------------------

## 1. Objectif

SAI-A105 introduit un **catalogue de diagnostics factorisé** permettant
d'analyser tout run expérimental sans dépendre d'un script spécifique à
une expérience donnée (ex. JEPA-5).

L'objectif est double :

1.  Standardiser l'analyse scientifique des runs.
2.  Séparer clairement :
    -   Artefacts machine (générés automatiquement)
    -   Conclusions scientifiques humaines (interprétation versionnée)

------------------------------------------------------------------------

## 2. Architecture

Emplacement :

    services/agent_service/app/analyse/

Structure :

    analyse/
      noyau/
        types.py
        lecture_artefacts.py
        stats_base.py
        gabarits_rapport.py
      catalogue/
        catalogue.py
        diagnostics/
          diag_poids_adaptatifs_v1.py
          diag_gate_v1.py
          diag_disagree_plateau_v1.py
      cli/
        main.py

### Rôle des composants

-   **noyau/** : infrastructure stable (types, lecture des artefacts,
    statistiques de base, rendu rapport).
-   **catalogue/** : registre des diagnostics + documentation embarquée.
-   **cli/** : point d'entrée exécutable.

------------------------------------------------------------------------

## 3. Utilisation CLI

Commande générique :

    PYTHONPATH=services python -m agent_service.app.analyse.cli.main --run <path_run>

Options :

-   `--diagnostics <ids>` : exécuter un sous-ensemble
-   `--out-md <nom>` : nom du rapport Markdown
-   `--out-json <nom>` : nom du JSON machine

Sorties générées dans :

    <run>/epreuve/

Fichiers produits :

-   `rapport_diagnostics.md`
-   `diagnostics.json`

------------------------------------------------------------------------

## 4. Contrat d'un diagnostic

Chaque diagnostic déclare :

-   id stable (ex. `diag.poids_adaptatifs.v1`)
-   titre
-   doc_courte
-   doc_longue
-   preconditions
-   executer(contexte)
-   sections_rapport

Le résultat contient :

-   statut (ok \| warn \| fail \| skip)
-   resume
-   mesures (dict JSON sérialisable)
-   alertes (message + action recommandée)

------------------------------------------------------------------------

## 5. Diagnostics minimum viable (JEPA-5)

### diag.poids_adaptatifs.v1

Analyse la dynamique des poids adaptatifs (w1, w2).

### diag.gate_partition.v1

Analyse la partition connu/inconnu et les seuils.

### diag.disagree_plateau.v1

Détecte les plateaux statistiques du signal disagree.

------------------------------------------------------------------------

## 6. Où déposer ce document

Document principal :

    docs/sai-a105_catalogue_diagnostics.md

Recommandé :

-   Ajouter une référence dans :
    -   docs/architecture_vision_systeme.md (section Analyse)
    -   docs/runner.md (section Post-traitement scientifique)
    -   services/agent_service/app/README.md (si existant)

------------------------------------------------------------------------

## 7. Cycle scientifique recommandé

1.  Exécuter une expérience.
2.  Lancer SAI-A105.
3.  Lire rapport_diagnostics.md.
4.  Rédiger conclusions humaines dans :

```{=html}
<!-- -->
```
    donnees/config/experiences/<EXP>/rapports/conclusions.md

SAI-A105 produit le diagnostic. L'expérimentateur produit la
connaissance.

------------------------------------------------------------------------

## 8. Évolution future

-   Ajout de sets nommés (ex. set_jepa5_v1).
-   Reconstruction autonome de partitions depuis le journal.
-   Intégration TUI complète (doc + alertes + métriques clés).

------------------------------------------------------------------------

Fin du document.
