# Chapitre 1 --- Le Monde

Version générée le 2026-02-24

------------------------------------------------------------------------

# 1️⃣ Définition générale

## Définition

Le monde est un **système dynamique génératif d'états**.

Il produit : - des configurations - des transitions - des régularités -
des perturbations

Dans SnakeAI, le monde est instancié par : - une arène YAML - une
dynamique (règles de transition) - un moteur d'évolution (tick → tick+1)

Mais théoriquement, le monde est plus large.

> Le monde est une source de phénomènes, indépendante de l'agent.

Il possède : - une structure - des lois (explicites ou implicites) - une
causalité locale - une temporalité

------------------------------------------------------------------------

# I. Formalisation mathématique

Nous définissons formellement les objets fondamentaux.

## Espace d'états

Soit :

S : espace des états possibles du monde.

Un état à l'instant t est noté :

sₜ ∈ S

------------------------------------------------------------------------

## Espace d'actions

Soit :

A : espace des actions possibles.

Une action à l'instant t est notée :

aₜ ∈ A

Dans notre cadre, A inclut : - actions motrices de l'agent - activations
instrumentales - actions d'autres entités - perturbations exogènes

------------------------------------------------------------------------

## Ensemble d'actions concurrentes

À chaque instant t, plusieurs actions peuvent agir simultanément.

On définit :

Aₜ ⊆ A

comme l'ensemble des actions actives à l'instant t.

------------------------------------------------------------------------

## Dynamique du monde

La transition du monde est définie par :

f : S × 𝒫(A) → S

où 𝒫(A) est l'ensemble des sous‑ensembles de A.

La transition est alors :

sₜ₊₁ = f(sₜ, Aₜ)

Le monde évolue sous l'effet d'actions concurrentes.

------------------------------------------------------------------------

## Instruments

Soit :

I : ensemble des instruments disponibles.

Un instrument i ∈ I est une entité capable de produire une observation.

------------------------------------------------------------------------

## Observations

Soit :

O : espace des observations possibles.

Une observation à l'instant t est notée :

oₜ ∈ O

Elle est produite par :

g : S × I → O

Donc :

oₜ = g(sₜ, i)

Les instruments peuvent être : - activés volontairement - automatiques -
concurrents - permanents

 L'observation n'est pas un événement ontologique du monde.
 Elle est une projection instrumentale produite à partir de l'état du monde.
 Le monde évolue indépendamment du fait qu'il soit observé.

------------------------------------------------------------------------

# II. Distinction Monde / Observation

Nous affirmons que :

sₜ ≠ oₜ

L'état du monde n'est jamais directement accessible. Il est toujours
médiatisé par un instrument.

------------------------------------------------------------------------

# III. Monde et récompense

Le monde : - ne répond pas - ne récompense pas - n'enseigne pas - il
évolue

La récompense n'est pas une propriété ontologique du monde.

Elle est une **appréciation normative acquise** par un système à partir
des régularités structurelles observées.

------------------------------------------------------------------------

# IV. Instruments comme mini-acteurs

Les instruments peuvent être considérés comme :

-   des entités primitives
-   des acteurs concurrentiels
-   des témoins simultanés

Ils peuvent : - agir automatiquement - produire du bruit - consommer des
ressources - être intégrés dans la dynamique

Dans ce cas, la dynamique devient :

sₜ₊₁ = f(sₜ, Aₜ)

où Aₜ inclut les activations instrumentales.

------------------------------------------------------------------------

# V. Position théorique adoptée

1.  Le monde est indépendant de la représentation.
2.  L'agent fait partie du monde.
    Cependant, le modèle cognitif (tronc, mémoire, têtes)
    est une description interne du système interprétatif,
    et n'est pas explicitement inclus dans S
    au niveau de cette formalisation.
3.  L'observation est un événement du monde.
4.  L'évaluation (récompense) est normative et acquise.
5.  La dynamique est concurrentielle.

------------------------------------------------------------------------

# Synthèse

Interaction complète :

sₜ₊₁ = f(sₜ, Aₜ)

oₜ = g(sₜ, i)

Le monde évolue. Les instruments projettent. L'agent interprète.
L'action modifie le monde.

Boucle fermée.
