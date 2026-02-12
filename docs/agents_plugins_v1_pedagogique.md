# agents plug-ins v1 — vision pédagogique

ce document explique l’intention (le « pourquoi ») et la place de la norme plug-ins dans le cours.

## le problème (avant)

quand la liste des agents est codée en dur (if/elif), on obtient :
- du couplage (runner ↔ agents)
- des régressions fréquentes lors des ajouts
- une difficulté à enseigner la séparation « description vs exécution »

## le changement (après)

on passe à une sélection déclarative :

```
yaml → catalogue → fabrique → agent
```

## ce que l’étudiant doit comprendre

- un **type d’agent** est une *définition* instanciable
- une **incarnation** est une *instance préparée* (artefact runtime)
- une **expérience** est un *bac-à-sable* reproductible (contexte + artefacts)

## lien avec la pédagogie world models

le catalogue facilite :
- la comparaison d’agents (même arène, même journal, mêmes instruments)
- l’évolution progressive des agents (du simple au planificateur)
- la mise en évidence des prérequis (ex. journaux d’entraînement) comme partie du contrat

## lien avec sai-e107

sai-e107 traite l’agent “personne” et l’idée d’incarnation.
le catalogue, lui, ne référence que les types sélectionnables par `--agent`.
l’incarnation reste un objet distinct, produit par une étape de préparation.
