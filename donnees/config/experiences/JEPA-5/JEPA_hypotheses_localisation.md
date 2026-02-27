# JEPA --- Définition et Localisation des Hypothèses

Version : 2026-02-26

------------------------------------------------------------------------

# 1. Où les hypothèses sont définies ?

Les hypothèses sont définies principalement dans :

donnees/config/experiences/JEPA-5/epreuve/config_epreuve.json

Section :

"hypotheses": { "h1": { ... }, "h2": { ... } }

C'est ici que l'on précise : - le type de modèle - les hyperparamètres -
le biais structurel

Le code pipeline_runner.py instancie simplement ces hypothèses.

------------------------------------------------------------------------

# 2. Où est implémentée la comparaison ?

services/ui_cli/app/pipeline/pipeline_runner.py

Fonction : \_epreuve_multi_depuis_cfg

On y trouve : - calcul s1 / s2 - compétition - ensemble - adaptation
(JEPA-5) - désaccord - gate

------------------------------------------------------------------------

# 3. Où sont stockés les résultats ?

donnees/config/experiences/JEPA-5/artefacts/runs/`<run_id>`{=html}/epreuve/

-   journal_agent.jsonl
-   registre_epistemique.json

Le registre est le dépôt statistique officiel.

------------------------------------------------------------------------

# 4. Recommandation

Créer :

donnees/config/experiences/JEPA-5/conclusions.md

Pour formaliser : - synthèse - interprétation - limites - décisions
suivantes

Fin.
