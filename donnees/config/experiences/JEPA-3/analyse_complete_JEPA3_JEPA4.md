# Analyse complète des résultats --- JEPA-3 et JEPA-4

Date : 2026-02-25

------------------------------------------------------------------------

# 1. Contexte général

Deux expériences ont été menées :

-   **JEPA-3 : compétition entre deux hypothèses**
-   **JEPA-4 : ensemble + désaccord**

Les deux utilisent le même dataset (4969 transitions, dimension 560).

------------------------------------------------------------------------

# 2. JEPA-3 --- Compétition

## 2.1 Résultats principaux

-   win_rate_h1 = 0.00181
-   win_rate_h2 = 0.99818

Conclusion : H2 gagne 99.8% du temps.

## 2.2 Analyse des erreurs

Moyennes :

-   s1 (H1) = 0.0016168
-   s2 (H2) = 0.0008324

H2 a une erreur environ deux fois plus faible.

## 2.3 Surprise et Gate

Seuil calibré (quantile 0.9) : 0.001900175

Effets : - ratio_connu ≈ 91.35% - ratio_inconnu ≈ 8.65%

La calibration fonctionne correctement.

## 2.4 Conclusion JEPA-3

Compétition réelle mais déséquilibrée. Il y a domination, pas rivalité
structurée.

------------------------------------------------------------------------

# 3. JEPA-4 --- Ensemble + Désaccord

## 3.1 Surprise ensemble

-   moyenne = 0.001143
-   q90 = 0.0022405

Gate surprise produit environ 9.36% d'inconnu.

## 3.2 Désaccord

-   moyenne = 0.000325
-   max = 0.0004598
-   q90 = 0.0004598 (égal au max)

Conséquence : - ratio_inconnu_par_disagree = 0

Le désaccord existe mais ne participe pas à la décision car le seuil est
trop élevé.

## 3.3 Corrélation

Corrélation(disagree, surprise_ens) = -0.358

Interprétation : Quand le désaccord augmente, la surprise ensemble tend
à diminuer modérément.

------------------------------------------------------------------------

# 4. Diagnostic global

Points positifs : - Pipeline stable - Calibration correcte - Désaccord
non nul - Distribution des erreurs saine

Points à enrichir : - Compétition trop déséquilibrée - Désaccord non
actif dans la décision

------------------------------------------------------------------------

# 5. Interprétation scientifique

JEPA-3 montre une hiérarchie claire des hypothèses. JEPA-4 révèle une
dynamique non triviale entre consensus et divergence.

La richesse future viendra de : - créer des zones où les hypothèses
alternent en performance - activer le désaccord comme signal décisionnel
réel

------------------------------------------------------------------------

# 6. Pistes d'évolution

A. Introduire un biais plus contrasté pour H2 
B. Ajuster le seuil de désaccord (quantile plus bas) 
C. Étudier les zones du dataset où les erreurs divergent
D. Introduire une troisième hypothèse

------------------------------------------------------------------------

Fin du document.
