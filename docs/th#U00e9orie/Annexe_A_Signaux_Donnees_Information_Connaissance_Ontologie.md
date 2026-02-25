# Chapitre 5 --- Signaux, Données, Information, Connaissance, Ontologie

Version générée le 2026-02-24

------------------------------------------------------------------------

# 1️⃣ Position générale

Dans l'architecture proposée, il est nécessaire de distinguer clairement
:

-   Signal
-   Donnée
-   Information
-   Connaissance
-   Ontologie

Ces niveaux ne sont pas synonymes. Ils correspondent à des
transformations successives dans le système interprétatif.

------------------------------------------------------------------------

# I. Le Signal

## Définition

Un signal est une variation physique ou instrumentale mesurable.

Formellement :

Un instrument i ∈ I produit un signal brut :

s\_{k,t}\^{signal}

Le signal :

-   est continu ou discret
-   peut contenir du bruit
-   n'a pas encore de signification interne

Le signal appartient au niveau instrument → buffer.

Il précède toute interprétation.

------------------------------------------------------------------------

# II. La Donnée

## Définition

Une donnée est un signal structuré.

Elle résulte d'une première opération de transformation :

d\_{k,t} = T(s\_{k,t}\^{signal})

où T peut être :

-   discrétisation
-   normalisation
-   échantillonnage
-   filtrage

La donnée :

-   est encodable
-   est manipulable par des fonctions algorithmiques
-   ne porte pas encore nécessairement de signification

La donnée correspond au niveau d'encodage rapide.

------------------------------------------------------------------------

# III. L'Information

## Définition

Une information est une donnée contextualisée.

Formellement :

i\_{t} = C(d\_{t}, contexte)

Elle dépend :

-   du contexte courant
-   de l'état interne
-   des attentes du système

L'information est orientée vers l'action.

Exemple :

-   Donnée : pixel rouge détecté
-   Information : obstacle à proximité

L'information émerge lors de la fusion primitive ou du traitement
attentionnel.

------------------------------------------------------------------------

# IV. La Connaissance

## Définition

La connaissance est une structure stable permettant :

-   prédiction
-   généralisation
-   inférence
-   compression

Formellement :

K = ensemble de modèles internes appris

Elle modifie :

-   h_k (encodeurs)
-   H (fusion)
-   Γ (routage)
-   ρ (réflexes)
-   μ (automatismes)

La connaissance est le résultat de l'apprentissage.

Elle agit rétroactivement sur la perception.

------------------------------------------------------------------------

# V. L'Ontologie

## Définition

Une ontologie est une organisation structurée des concepts manipulables
par le système.

Elle définit :

-   les types d'objets
-   les relations possibles
-   les catégories pertinentes
-   les contraintes structurelles

Formellement :

O\_{conceptuel} = (Entités, Relations, Contraintes)

L'ontologie permet :

-   la cohérence inter-modules
-   la compatibilité entre têtes
-   la structuration de la mémoire

Elle opère principalement au niveau des têtes conscientes.

------------------------------------------------------------------------

# VI. Chaîne de transformation complète

Monde → Signal → Donnée → Information → Connaissance → Ontologie

Plus précisément :

1.  Monde produit s_t
2.  Instrument génère s\_{k,t}\^{signal}
3.  Transformation produit d\_{k,t}
4.  Fusion produit information i_t
5.  Apprentissage structure K
6.  Ontologie organise les concepts manipulables

------------------------------------------------------------------------

# VII. Hiérarchie de stabilité

Du plus instable au plus stable :

Signal \< Donnée \< Information \< Connaissance \< Ontologie

-   Le signal est instantané.
-   La donnée est locale.
-   L'information est contextuelle.
-   La connaissance est durable.
-   L'ontologie est structurante.

------------------------------------------------------------------------

# VIII. Rôle dans l'architecture

-   Les signaux nourrissent les buffers.
-   Les données alimentent l'encodage rapide.
-   L'information guide le routage.
-   La connaissance ajuste les paramètres internes.
-   L'ontologie structure le traitement conscient.

------------------------------------------------------------------------

# Synthèse

Un système interprétatif transforme des variations physiques en
structures conceptuelles manipulables.

La progression n'est pas linéaire mais hiérarchique.

Chaque niveau contraint le suivant.

Ainsi, comprendre n'est pas recevoir un signal.

Comprendre est insérer une information dans une structure ontologique
cohérente, stabilisée par la connaissance acquise.
