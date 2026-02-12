# Campagne expérimentale --- snake_collectif_v1

## 1. Objectif principal

Démontrer expérimentalement qu'un collectif structuré d'agents
(incarné + observateur + registre épistémique) apprend à jouer au Snake
de manière plus efficace qu'un agent incarné seul.

Cette campagne utilise exclusivement les outils déjà définis dans les
activités SAI-A1\*\*\* : - bac à sable d'expérience - arènes YAML
existantes - agents déclarés via CLI - journal JSONL - métriques déjà
calculées (support0_ratio, entropie, etc.)

Aucune nouvelle mécanique n'est introduite.

------------------------------------------------------------------------

## 2. Hypothèse

H1 : L'agent incarné assisté d'un observateur améliore le score moyen et
la survie moyenne par rapport à l'agent incarné seul.

H2 : L'ajout du registre épistémique réduit le taux de collisions
mortelles contre les murs.

------------------------------------------------------------------------

## 3. Conditions expérimentales

  Code   Description
  ------ ----------------------------------------------------
  C0     Agent aléatoire
  C1     Agent incarné seul
  C2     Agent incarné + observateur
  C3     Agent incarné + observateur + registre épistémique

------------------------------------------------------------------------

## 4. Arènes

Deux arènes existantes doivent être utilisées :

-   Arène TRAIN : arène standard déjà utilisée dans SAI-A1\*\*\*
-   Arène EVAL : variante ou arène équivalente non identique

Aucune modification structurelle du moteur.

------------------------------------------------------------------------

## 5. Paramètres communs

-   Seeds : 0 à 4 (5 seeds)
-   Episodes TRAIN : 300
-   Episodes EVAL : 100
-   max_ticks : 2000
-   latent : celui déjà validé comme exploitable

------------------------------------------------------------------------

## 6. Convention d'artefacts

Les artefacts doivent respecter la structure suivante :

artefacts/experiences/snake_collectif_v1/ C1/ seed_0/ train.jsonl
eval.jsonl resume_seed.json C2/ seed_0/ ...

Un agrégat global : resume_global.csv

------------------------------------------------------------------------

## 7. Métriques minimales

Par épisode : - score_final - ticks_survecus - raison_fin -
longueur_finale - nb_nourritures

Si observateur actif : - action_recommandee - action_finale -
source_decision

------------------------------------------------------------------------

## 8. Critères de succès

Succès C2 si : score_moyen_eval(C2) \>= score_moyen_eval(C1) \* 1.10 sur
au moins 3 seeds sur 5.

Succès C3 si : taux_mur_eval(C3) \<= taux_mur_eval(C2) \* 0.85

------------------------------------------------------------------------

## 9. Procédure opérable via outils actuels

Exemple de commande pour une condition :

PYTHONPATH=services python -m ui_cli.app.main --experience
snake_collectif_v1 --arene arene_train_existante --agent agent_cible
--latent latent_existant --episodes 300 --max-ticks 2000 --seed 0
--journal artefacts/experiences/snake_collectif_v1/C1/seed_0/train.jsonl
--truncate

Puis répéter pour eval avec 100 épisodes.

------------------------------------------------------------------------

## 10. Première démonstration minimale

Phase 1 : - Exécuter C1 et C2 uniquement - 5 seeds - Comparer
score_moyen_eval

Si C2 \> C1 de manière cohérente, l'hypothèse collective commence à être
validée.

------------------------------------------------------------------------

Fin du document.
