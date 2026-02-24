# Chapitre 4 --- Architecture : Tronc et Satellites

Version générée le 2026-02-24

------------------------------------------------------------------------

# 1️⃣ Vue d'ensemble

L'architecture de l'agent repose sur une organisation hiérarchique et
circulaire :

Monde → Instruments → Tronc → Classification de voie → Modules
spécialisés → Moteur → Monde

Le tronc n'est pas un simple encodeur passif.\
Il reçoit l'ensemble des flux instrumentaux et décide dynamiquement de
la voie de traitement.

------------------------------------------------------------------------

# I. Entrée : Instruments et encodage multi-canaux

Soit :

S : espace des états du monde\
sₜ ∈ S

𝓒 = {C₁, ..., C₅} : ensemble des canaux

Chaque canal reçoit des instruments compatibles :

I_k ⊆ I


## Buffers instrumentaux (pré-encodage)

Chaque canal dispose d’un buffer court terme :

o_{k,t}^{raw}

Ce buffer conserve temporairement une trace quasi-brute
permettant une relecture ou une réanalyse ultérieure.

## Encodage rapide (fast path)

Un encodage rapide est appliqué pour les fonctions réflexes
et la classification de voie :

zₖ,ₜ^fast = hₖ^fast(oₖ,ₜ)

Cet encodage est orienté détection et saillance.

Fusion primitive du tronc :

zₜ^primitive = H_fast(z₁,ₜ^fast, ..., z₅,ₜ^fast)

Cette fusion primitive alimente :
- les réflexes
- la classification de voie
- les mécanismes d’alerte

Encodage par canal :

## Encodage approfondi (voie lente)

Un encodage plus riche peut être calculé
pour les traitements délibératifs :

zₖ,ₜ^deep = hₖ^deep(oₖ,ₜ^raw, zₖ,ₜ^fast)


## Fusion latente intégrée

Une fusion plus complète peut être construite pour
les traitements délibératifs :

zₜ = H(z₁,ₜ^deep, ..., z₅,ₜ^deep, mₜ)

zₜ constitue la représentation latente intégrée.

## Mémoire

Deux formes de mémoire sont distinguées :

1. Mémoire globale :

mₜ = M_global(zₜ)

Représente un "sentiment" global :
urgence, confiance, incohérence, etc.

2. Mémoire par canal :

Mₖ,ₜ = M_canal(oₖ,ₜ^raw, zₖ,ₜ^fast)

Permet à la voie Attention de revisiter
un canal spécifique après coup.

------------------------------------------------------------------------

# II. Classification de voie (sortie du tronc)

Le tronc produit une décision de traitement :

cₜ = Γ(zₜ^primitive)

où :

cₜ ∈ {𝓡, 𝓤, 𝓐}

-   𝓡 : Réflexe
-   𝓤 : Automatisme acquis (inconscient appris)
-   𝓐 : Attention (voie consciente / délibérative)

Cette classification est apprise et modulable par entraînement.

------------------------------------------------------------------------

# III. Voies de traitement

## 1️⃣ Voie Réflexe (𝓡)

Traitement rapide, seuils simples, réponse immédiate.

Aₜ^rapide = ρ(zₜ^primitive)

Caractéristiques : - faible latence - compression locale - déclenchement
automatique

------------------------------------------------------------------------

## 2️⃣ Voie Automatisme acquis (𝓤)

Comportements complexes devenus inconscients par apprentissage.

Aₜ\^auto = μ(zₜ)

Caractéristiques : - rapide - plus riche qu'un réflexe simple - résulte
d'un entraînement antérieur

------------------------------------------------------------------------

## 3️⃣ Voie Attention / Conscience (𝓐)

Transmission aux têtes délibératives :

zₜ → Têtes

La voie Attention peut également consulter :
- Mₖ,ₜ (mémoire canal)
- mₜ (mémoire globale)

Elle peut demander :
- modification d’échelle
- changement d’instrument
- relecture ciblée

Les têtes peuvent : - planifier - simuler - comparer scénarios - imposer
une stratégie instrumentale

Actions planifiées :

Aₜ\^plan

------------------------------------------------------------------------

# IV. Rôle du Moteur

Les différentes actions sont arbitrées :

Aₜ = Arbitrage(Aₜ\^rapide, Aₜ\^auto, Aₜ\^plan)

Puis envoyées au monde :

sₜ₊₁ = f(sₜ, Aₜ)

Le moteur peut : - prioriser certaines voies - résoudre conflits -
appliquer contraintes physiques

------------------------------------------------------------------------

# V. Boucle instrumentale

Les têtes peuvent générer des actions instrumentales :

Aₜ\^instr ⊆ Aₜ

Ces actions modifient : - instrument actif - échelle λ - focale φ

Nouvelle observation au temps suivant.

Boucle complète :

Buffers → Encodage rapide → Fusion primitive → Classification →
Modules → Actions instrumentales → Instruments → Nouveau cycle

------------------------------------------------------------------------

# VI. Plasticité et apprentissage

L'entraînement modifie :

-   H (fusion latente)
-   Γ (classification de voie)
-   ρ (réflexes)
-   μ (automatismes)

Effet : - ce qui était attentionnel peut devenir automatique - certains
réflexes peuvent être inhibés - la voie Attention peut être favorisée
selon contexte

L'architecture est dynamique et évolutive.

------------------------------------------------------------------------

# VII. Schéma synthétique

Instruments
↓
Buffers bruts (oₖ,ₜ^raw)
↓
Encodage rapide (zₖ,ₜ^fast)
↓
Fusion primitive (zₜ^primitive)
↓
Classification Γ
↓\
--------------------------------------\
\| Réflexe \| Automatisme \| Attention → Têtes\
\| (ρ) \| (μ) \| ↓\
\| Actions \| Actions \| Planification\
--------------------------------------\
↓\
Moteur\
↓\
Monde

------------------------------------------------------------------------

# Conclusion

L'architecture repose sur :

-   un tronc multi-canaux
-   une classification de voie adaptative
-   trois niveaux de traitement (réflexe, automatisme, conscience)
-   un moteur d'arbitrage
-   une boucle instrumentale active

La perception est modulée par expérience. La voie cognitive activée
dépend du contexte. L'agent évolue en intégrant progressivement ses
acquis.
