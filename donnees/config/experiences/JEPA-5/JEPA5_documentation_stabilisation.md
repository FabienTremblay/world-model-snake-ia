# JEPA-5 --- Documentation Scientifique (Version stabilisation)

Version : 2026-02-26\
Analyste principal : ChatGPT (rôle explicitement assumé dans ce
document)\
Collaborateur : Fabien (évolutif selon modifications futures)

------------------------------------------------------------------------

# 1. Clarification des hypothèses

## H1 --- Modèle non-linéaire expressif

Un modèle "non-linéaire" signifie que la relation entre l'entrée (x) et
la sortie (y) n'est pas une simple combinaison proportionnelle.

Un modèle non-linéaire peut représenter : - des interactions complexes
entre variables - des effets seuils - des comportements en régime - des
structures internes multiples

"Expressif" signifie : - capable de représenter beaucoup de formes
différentes - flexible - potentiellement plus puissant - mais aussi plus
instable si mal régularisé

Dans JEPA-5 : H1 = MLP (réseau de neurones à couches cachées)

------------------------------------------------------------------------

## H2 --- Modèle linéaire simple

Un modèle linéaire suppose que :

y ≈ a1*x1 + a2*x2 + ... + b

Il n'introduit pas d'interactions complexes ni de transformation interne
profonde.

"Simple" signifie : - structure stable - interprétation plus claire -
faible variance - mais moins capable de capturer des structures
complexes

Dans JEPA-5 : H2 = modèle linéaire

------------------------------------------------------------------------

# 2. Ce que JEPA-5 démontre actuellement

-   H2 domine globalement (meilleure erreur moyenne)
-   H1 capture des régimes locaux
-   Les poids adaptatifs ne sont plus constants
-   Le désaccord est décisionnel
-   La partition du monde est riche (\~31% transitions incertaines)

JEPA-5 valide donc : - Compétition réelle - Désaccord structurel actif -
Adaptation dynamique

------------------------------------------------------------------------

# 3. Décision stratégique (stabilisation)

Il est prématuré d'ajouter H3.

Nous n'avons pas encore : - exploré différentes températures - testé
différentes valeurs de alpha_ema - analysé multi-seeds - mesuré
l'entropie des poids - étudié la dynamique temporelle des régimes

Conclusion : Il est plus scientifique de stabiliser JEPA-5 avant
d'ajouter une troisième hypothèse.

------------------------------------------------------------------------

# 4. Prochaines étapes pour stabilisation

1.  Tester temperature ∈ {0.00025, 0.0005, 0.001}
2.  Tester alpha_ema ∈ {0.9, 0.95, 0.97}
3.  Mesurer :
    -   entropie moyenne des poids
    -   proportion w1 \> 0.7
    -   proportion w2 \> 0.7
4.  Comparer plusieurs seeds

------------------------------------------------------------------------

# 5. Dépôt officiel des conclusions

Les conclusions doivent être formalisées dans :

donnees/config/experiences/JEPA-5/rapports/conclusions.md

Ce document constitue : - la mémoire scientifique - la synthèse
validée - la base pour JEPA-6

Fin du document.
