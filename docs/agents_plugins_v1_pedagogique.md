# Agents Plug-ins v1 — Vision pédagogique

## Pourquoi les plug-ins ?

Passer d’une sélection codée en dur à un catalogue déclaratif permet :
- extensibilité
- séparation claire des responsabilités
- alignement avec une architecture évolutive

---

## Changement architectural

Avant :
code → agent

Après :
YAML → catalogue → fabrique → agent

---

## Séparation conceptuelle

Type d’agent : Déclaré via YAML
Fabrique : Instancie l’agent
Incarnation : Artefact runtime
Expérience : Contexte d’exécution

---

## Impact pédagogique

Cette structure permet :
- d’illustrer la distinction entre description et exécution
- d’introduire la notion de contrat déclaratif
- de préparer l’évolution vers des agents plus abstraits

---

## Alignement avec SAI-E107

L’incarnation n’est pas un type d’agent.
Elle représente une instance préparée.

Le catalogue ne référence que des types instanciables.
