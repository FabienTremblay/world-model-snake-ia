# Chapitre 3 --- Transformation de l'état naturel en état compréhensible

Version générée le 2026-02-24

------------------------------------------------------------------------

# 1️⃣ Position générale

Rendre un état compréhensible n'est pas une simple opération de codage.

C'est le résultat de :

-   projections instrumentales multiples,
-   sélection attentionnelle,
-   apprentissage par expérience,
-   arbitrage sous contrainte de ressources.

Un état compréhensible est un **artefact interne orienté vers
l'action**.

------------------------------------------------------------------------

# I. État naturel, observations et représentation

## Monde

S : espace des états du monde\
sₜ ∈ S : état naturel à l'instant t

------------------------------------------------------------------------

## Canaux sensoriels

Soit :

𝓒 = {C₁, C₂, C₃, C₄, C₅}

Chaque canal C_k reçoit des instruments compatibles :

I_k ⊆ I

I = ⋃ I_k

------------------------------------------------------------------------

## Instrument actif par canal

À l'instant t :

iₖ,ₜ ∈ I_k

Chaque canal active un instrument particulier.

------------------------------------------------------------------------

## Échelle / résolution

Chaque instrument peut fonctionner à une échelle :

λₖ,ₜ ∈ Λ_k

L'observation produite est :

oₖ,ₜ = gₖ(sₜ, iₖ,ₜ, λₖ,ₜ)

------------------------------------------------------------------------

# II. Encodage et tronc multi-canaux

Chaque canal est encodé séparément :

zₖ,ₜ = hₖ(oₖ,ₜ)

Le tronc agrège :

zₜ = H(z₁,ₜ, z₂,ₜ, z₃,ₜ, z₄,ₜ, z₅,ₜ)

zₜ est la représentation latente intégrée.

------------------------------------------------------------------------

# III. Attention comme ressource

Soit :

Bₜ : budget d'attention disponible à l'instant t

Toute opération instrumentale possède un coût :

cost(a) ≥ 0

Contrainte :

Σ cost(a) ≤ Bₜ

Les opérations coûteuses incluent :

-   changer d'instrument
-   modifier l'échelle λ
-   élargir la focale
-   augmenter la résolution
-   permuter entre instruments compatibles

L'attention structure ce qui devient accessible au tronc.

------------------------------------------------------------------------

# IV. Sélection et arbitrage inter-canaux

Les canaux produisent des candidats d'objets ou d'événements.

Exemple :

-   Canal visuel : objet dans la focale
-   Canal thermique : signal de chaleur hors champ

Le système doit arbitrer :

-   agir immédiatement
-   réorienter un instrument
-   changer d'échelle
-   ignorer un signal

Cette sélection peut être :

1.  Réflexe (au niveau du tronc)
2.  Délibérative (via les têtes)

------------------------------------------------------------------------

# V. Réflexes et intervention des têtes

Le tronc peut contenir des mécanismes réflexes entraînés :

-   détection d'urgence
-   priorisation automatique
-   inhibition locale

Ces mécanismes sont appris par expérience.

Les têtes peuvent :

-   amplifier un canal
-   atténuer un réflexe
-   rediriger l'attention
-   imposer un changement d'échelle

Ainsi :

Attention = combinaison de : - dynamiques réflexes entraînées -
modulation stratégique des têtes

------------------------------------------------------------------------

# VI. Apprentissage et expérience

Les réseaux de neurones interviennent pour :

-   extraire des invariants
-   apprendre des priorités
-   modéliser des corrélations inter-canaux
-   ajuster les réflexes

L'apprentissage modifie :

-   hₖ (encodeurs)
-   H (fusion)
-   mécanismes attentionnels
-   seuils réflexes

------------------------------------------------------------------------

# VII. Définition formelle de l'état compréhensible

Un état compréhensible à l'instant t est :

zₜ = H(h₁(g₁(sₜ,...)), ..., h₅(g₅(sₜ,...)))

sous contrainte :

Σ cost(a) ≤ Bₜ

Il dépend :

-   des instruments actifs
-   des échelles sélectionnées
-   du budget d'attention
-   des paramètres appris

------------------------------------------------------------------------

# Synthèse

Le monde produit sₜ.

Les instruments projettent selon : - compatibilité canal - échelle λ -
activation choisie

Le tronc encode et fusionne.

L'attention sélectionne sous contrainte.

Les têtes peuvent moduler, mais des réflexes entraînés existent au
niveau du tronc.

Un état compréhensible est donc :

Une représentation latente multi-canaux, orientée par l'attention,
apprise par expérience, et construite pour agir.
