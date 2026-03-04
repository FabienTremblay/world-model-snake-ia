# NOTE — Promotion contrôlée (v1)

Ajout de `--promouvoir` (ou `experience.yml: evenements.promouvoir: true`).

## Règles

- `mode=entrainement` : si promouvoir
  - écrit `individu_sortie.yml` vers `donnees/catalogues/individus/<id>/individu.yml`
  - archive immuable dans `historique/<hash>.yml`
- `mode=epreuve` : promotion interdite (erreur explicite)

## But

Décorréler :

- vérité expérimentale (runs immuables)
- état courant (catalogue) — modifié seulement par décision explicite
