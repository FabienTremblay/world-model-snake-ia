# Catalogue — individus (transportables)

Chaque individu est un package auto-suffisant : transportable, chiffrable et isolé (rien “hors de lui” n'appartient à l'individu).

- ia_<id>/
  - individu.yaml
  - gabarits/        # R2 autonome : copie locale de gabarit(s)
  - poids/
  - memoire/
  - manifest.json
  - signature.txt (optionnel)
  - historique/      # versions immuables (créées lors des promotions)

## État courant

Le fichier :

- `individu.yml` (ou `individu.yaml` selon convention)

représente l'état **courant actif** de l'individu (celui utilisé comme entrée de run).

## Historique (versions immuables)

Lorsqu'on promeut un individu après un run d'entraînement :

- on archive une version immuable :
  - `historique/<hash>.yml`

Ce mécanisme supporte :

- audit
- comparaison
- sélection / évolution
- transport sécurisé d'états

## Relation avec les runs

Les runs produisent des snapshots :

- `individu_entree.yml`
- `individu_sortie.yml` (entraînement seulement)
- `lineage.json`

Ces snapshots sont la vérité expérimentale. Le catalogue ne bouge que si on **promote** explicitement.
