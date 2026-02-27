# Glossaire JEPA --- Terminologie simplifiée

Version : 2026-02-25

------------------------------------------------------------------------

## Hypothèse (H1, H2, etc.)

Un modèle mathématique qui tente de prédire l'état futur du monde à
partir de l'état présent.

------------------------------------------------------------------------

## Modèle

Implémentation concrète d'une hypothèse (réseau de neurones, modèle
linéaire, etc.).

------------------------------------------------------------------------

## Transition

Passage d'un état t vers un état t+1.

------------------------------------------------------------------------

## Erreur (MSE --- erreur quadratique moyenne)

Mesure de l'écart entre la prédiction du modèle et la réalité observée.
Plus elle est faible, meilleure est la prédiction.

------------------------------------------------------------------------

## s1, s2

Erreurs respectives des hypothèses H1 et H2 sur une transition donnée.

------------------------------------------------------------------------

## Winner

Hypothèse ayant produit l'erreur la plus faible sur une transition.

------------------------------------------------------------------------

## Win rate

Proportion de transitions où une hypothèse gagne.

------------------------------------------------------------------------

## Surprise

Erreur utilisée pour décider si une situation est connue ou inconnue.
Dans JEPA-3 : surprise = min(s1, s2)

------------------------------------------------------------------------

## Gate (porte décisionnelle)

Règle qui classe une transition comme : - connue (erreur faible) -
inconnue (erreur élevée)

------------------------------------------------------------------------

## Quantile (ex : 0.9)

Valeur seuil telle que 90% des erreurs sont en dessous.

------------------------------------------------------------------------

## Désaccord (disagree)

Mesure de la différence entre les prédictions de deux hypothèses. Ce
n'est pas une erreur par rapport au monde, mais une divergence entre
modèles.

------------------------------------------------------------------------

## Surprise ensemble

Erreur de la moyenne des prédictions des hypothèses.

------------------------------------------------------------------------

## Incertitude d'erreur

Le modèle se trompe.

------------------------------------------------------------------------

## Incertitude structurelle

Les modèles ne sont pas d'accord.

------------------------------------------------------------------------

## Corrélation

Mesure du lien statistique entre deux variables. - 1 : évoluent
ensemble - 0 : indépendantes - négatif : évoluent en sens opposé

------------------------------------------------------------------------

Fin du glossaire.
