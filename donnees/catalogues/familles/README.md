# Catalogue — familles (gabarits)

Chaque famille est un gabarit autonome (analogue à un ADN / paramètres de naissance).

- fa_<id>/
  - famille.yaml
  - schemas/ (optionnel)

## Rôle

Une famille définit :

- la structure génétique de base (gabarits de génération)
- des politiques par défaut (si applicable)
- des règles de compatibilité / validation

Les individus sont des **instances** d'une famille, puis évoluent sans dépendre de la famille durant les runs.

Relation conceptuelle :

famille → individu → runs
