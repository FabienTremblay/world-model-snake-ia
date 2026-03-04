# Évolution des individus

## Où a lieu l'évolution ?

- uniquement en `mode=entrainement`
- jamais en `mode=epreuve`

## Cycle

1. charger l'état courant depuis le catalogue
2. écrire `individu_entree.yml`
3. exécuter le run (monde événementiel)
4. appliquer une évolution post-run (v1 : mémoire courte + provenance + version)
5. écrire `individu_sortie.yml`
6. écrire `lineage.json`
7. (optionnel) promouvoir dans le catalogue

## Promotion (opt-in)

Si promotion :

- `donnees/catalogues/individus/<id>/individu.yml` devient l'état courant
- `donnees/catalogues/individus/<id>/historique/<hash>.yml` archive la version

Sinon :

- le catalogue reste inchangé
- le run conserve la vérité expérimentale
