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
