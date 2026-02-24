# Chapitre 2 --- Les Instruments

Version générée le 2026-02-24

------------------------------------------------------------------------

# 1️⃣ Définition générale

## Définition

Un instrument est une **entité de médiation** entre le monde et un
système interprétatif.

Il ne donne jamais accès directement à l'état du monde.

Il produit une projection.

Un instrument : - sélectionne - transforme - discrétise - encode

Il est une réduction structurée du monde.

Exemple :

Types d’instruments dans ton architecture :
🔹 Instrument incarné
    • Caméra auto-centrée
    • GPS local
    • Capteurs directionnels
    • Champ visuel limité
→ Vision partielle, située, égocentrée.
🔹 Instrument épistémique
    • Caméra globale
    • Chronomètre
    • Journaux
    • Registres
→ Vision externe, désincarnée, d’observation scientifique.
------------------------------------------------------------------------

# I. Formalisation mathématique

## Monde

S : espace des états possibles du monde\
sₜ ∈ S : état du monde à l'instant t

------------------------------------------------------------------------

## Ensemble des instruments

I : ensemble des instruments disponibles

Un instrument particulier est noté :

i ∈ I

------------------------------------------------------------------------

## Espace des observations

O : espace des observations possibles

oₜ ∈ O : observation produite à l'instant t

------------------------------------------------------------------------

## Fonction instrumentale

Chaque instrument définit une fonction de projection :

g : S × I → O

Observation produite :

oₜ = g(sₜ, i)

Important :

sₜ ≠ oₜ

L'observation est une transformation partielle de l'état du monde.
---

## Relation formelle entre actions et instruments

Soit :

A : ensemble des actions possibles

On distingue :

A = A_moteur ∪ A_instr ∪ A_exogène

où :

A_instr ⊆ A

Les activations instrumentales sont des éléments de A.

Une activation instrumentale est une action a ∈ A telle qu’il existe
une application :

φ : A_instr → I

qui associe chaque activation instrumentale à l’instrument concerné.

Ainsi :

- i ∈ I est une entité structurelle
- a ∈ A est un événement dynamique
- certaines actions modifient l’état interne d’un instrument

Un instrument peut recevoir plusieurs activations au même instant t.

Dans ce cas :

A_t_instr ⊆ A_t

peut contenir plusieurs actions liées au même instrument.

------------------------------------------------------------------------

# II. Nature des instruments

## 1️⃣ Instruments passifs

Ils projettent sans modifier la dynamique du monde.

Dans ce cas :

sₜ₊₁ = f(sₜ, Aₜ)\
oₜ = g(sₜ, i)

L'instrument est causalement neutre.

Cependant, l’observation est produite à partir de l’état courant :

oₜ = g(sₜ, iₜ)

avec :

g : S × 𝓘 → O

et non nécessairement après la transition.

------------------------------------------------------------------------

## 2️⃣ Instruments actifs

Ils peuvent :

-   consommer des ressources
-   introduire du bruit
-   révéler ou masquer de l'information
-   perturber l'environnement

Les instruments peuvent posséder un état interne dynamique :

Soit 𝓘 l’espace des états internes possibles d’un instrument.

À l’instant t :

iₜ ∈ 𝓘

On distingue donc :

- l’instrument structurel i ∈ I
- son état dynamique iₜ ∈ 𝓘

Les activations instrumentales peuvent modifier cet état :

iₜ₊₁ = ψ(iₜ, Aₜ_instr)

où ψ est la dynamique interne des instruments.

Dans ce cas, ils deviennent des entités causales.

La dynamique devient :

sₜ₊₁ = f(sₜ, Aₜ)

avec :

f : S × 𝒫(A) → S
où Aₜ inclut les activations instrumentales.

Le monde évolue donc sous l’effet d’un ensemble
d’actions concurrentes, incluant :

- actions motrices
- activations instrumentales
- actions d’autres entités
- perturbations exogènes

------------------------------------------------------------------------

# III. Activation instrumentale

L'activation d'un instrument est une sous-catégorie d'action.

Soit :

A : ensemble des actions possibles

Les activations instrumentales appartiennent à A_instr ⊆ A.

À l'instant t :

Aₜ ⊆ A

peut inclure :

-   actions motrices
-   activations instrumentales
-   actions concurrentes d'autres entités

Les instruments peuvent fonctionner :

- automatiquement
- en continu
- simultanément

Les instruments peuvent être :

-   déclenchés volontairement
-   automatiques
-   permanents
-   concurrents

L'observation peut être simultanée à l'action.

------------------------------------------------------------------------

# IV. Instruments comme mini-acteurs

Dans notre cadre théorique, un instrument peut être considéré comme :

-   une entité primitive
-   un acteur minimal
-   un témoin simultané

 Cela implique :
   l'observation est une projection dépendante d'un instrument
   plusieurs instruments peuvent observer simultanément
   l'activation instrumentale peut consommer des ressources
   seules les actions (et non l'observation elle-même) modifient le monde

------------------------------------------------------------------------

# V. Types d'instruments dans SnakeAI

## Instruments incarnés

-   caméra auto-centrée
-   capteurs directionnels
-   projection égocentrée

Caractéristiques :

-   situés
-   partiels
-   dépendants de la position de l'agent

------------------------------------------------------------------------

## Instruments épistémiques

-   caméra globale
-   journaux
-   registres
-   chronomètre

Caractéristiques :

-   vue externe
-   désincarnée
-   souvent complète ou plus large

------------------------------------------------------------------------

# VI. Position théorique adoptée

1.  Le monde n'est jamais observé directement.
2.  Toute connaissance commence par une projection instrumentale.
3.  Les instruments peuvent être passifs ou actifs.
4.  L'observation peut être concurrentielle.
5.  Les instruments structurent ce qui est connaissable.

------------------------------------------------------------------------

# Synthèse

Le monde évolue indépendamment.

Les instruments produisent des observations :

oₜ = g(sₜ, i)

Ces observations alimentent ensuite :

-   l'encodage
-   la compression
-   le tronc latent
-   les têtes spécialisées

Les instruments déterminent les limites épistémiques du système.
