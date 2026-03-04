# Chapitre 4 — Architecture : Tronc et Satellites

Version consolidée le 2026-02-24

---

# 1️⃣ Vue d'ensemble

L'architecture de l'agent repose sur une organisation hiérarchique et circulaire :

Monde → Instruments → Tronc → Classification de voie → Modules spécialisés → Moteur → Monde

Le tronc est une structure interne au système interprétatif. Il n'est pas modélisé comme une composante explicite de S et reçoit l'ensemble des flux instrumentaux et décide dynamiquement de la voie de traitement.

---

# I. Entrée : Instruments, buffers et encodage

Soit :

S : espace des états du monde  
sₜ ∈ S  

𝓒 = {C₁, …, C₅} : ensemble des canaux  

Chaque canal reçoit des instruments compatibles :

Iₖ ⊆ I

---

## Buffers instrumentaux (pré-encodage)

Chaque canal dispose d'un buffer court terme :

oₖ,ₜʳᵃʷ

Ce buffer conserve temporairement une trace quasi-brute permettant une relecture ou une réanalyse ultérieure.

---

## Encodage rapide (voie rapide)

zₖ,ₜᶠᵃˢᵗ = hₖᶠᵃˢᵗ(oₖ,ₜʳᵃʷ)

Fusion primitive :

zₜᵖʳⁱᵐⁱᵗⁱᵛᵉ = H_fast(z₁,ₜᶠᵃˢᵗ, …, z₅,ₜᶠᵃˢᵗ)

Cette fusion primitive alimente :
- les réflexes
- la classification de voie
- les mécanismes d’alerte

---

## Encodage approfondi (voie lente)

zₖ,ₜᵈᵉᵉᵖ = hₖᵈᵉᵉᵖ(oₖ,ₜʳᵃʷ, zₖ,ₜᶠᵃˢᵗ)

Fusion intégrée :

zₜ = H(z₁,ₜᵈᵉᵉᵖ, …, z₅,ₜᵈᵉᵉᵖ, mₜ)

zₜ constitue la représentation latente complète.

---

## Mémoire

Mémoire globale :

mₜ = M_global(zₜ)

Mémoire par canal :

Mₖ,ₜ = M_canal(oₖ,ₜʳᵃʷ, zₖ,ₜᶠᵃˢᵗ)

## Nature de la mémoire

Il est nécessaire de distinguer strictement :

1. Mémoire courte (épisodique)
   - Propre à l’instance.
   - Alimentée en situation d’arène.
   - Non partagée.
   - Disparaît avec l’instance.

2. Mémoire longue (consolidation individuelle)
   - Propre à l’instance.
   - Peut être alimentée à la suite d’un traitement conscient approfondi.
   - Ne constitue pas une ontologie partagée.
   - Ne correspond pas au registre épistémique.

Aucune mémoire n’est globale ou inter-individuelle.

Toute structure partagée entre agents est produite par le registre
épistémique et intégrée uniquement lors de l’entraînement
par mise à jour des paramètres internes.

---

# II. Classification de voie

cₜ = Γ(zₜᵖʳⁱᵐⁱᵗⁱᵛᵉ)

cₜ ∈ {𝓡, 𝓤, 𝓐}

𝓡 : Réflexe  
𝓤 : Automatisme acquis  
𝓐 : Attention  

---

# III. Voies de traitement

Voie Réflexe :

Aₜʳᵃᵖⁱᵈᵉ = ρ(zₜᵖʳⁱᵐⁱᵗⁱᵛᵉ)

Voie Automatisme acquis :

Aₜᵃᵘᵗᵒ = μ(zₜ)

Voie Attention :

zₜ → Têtes  
Consultation possible : Mₖ,ₜ et mₜ  
Production : Aₜᵖˡᵃⁿ

---

# IV. Rôle du Moteur

Aₜ = Arbitrage(Aₜʳᵃᵖⁱᵈᵉ, Aₜᵃᵘᵗᵒ, Aₜᵖˡᵃⁿ)

Transition du monde :

sₜ₊₁ = f(sₜ, Aₜ)
